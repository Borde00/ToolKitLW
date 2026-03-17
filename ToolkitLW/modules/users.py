import subprocess
import platform
import os
from core.backup import backup_file, backup_registry_key
from core.logger import Logger

C = {
    "ok":    "\033[92m",
    "warn":  "\033[93m",
    "err":   "\033[91m",
    "info":  "\033[96m",
    "bold":  "\033[1m",
    "reset": "\033[0m",
}

def _ask(prompt):
    return input(f"{C['warn']}[?] {prompt} (s/n): {C['reset']}").strip().lower() == "s"

def _run(cmd, shell=False):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, shell=shell)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), -1

# ── LINUX ─────────────────────────────────────
def _linux_users(logger):
    logger.section("USUARIOS Y CONTRASEÑAS — Linux")
    applied = skipped = errors = 0

    # 1. Usuarios sin contraseña
    print(f"\n{C['info']}[*] Buscando usuarios sin contraseña...{C['reset']}")
    out, _ = _run(['awk', '-F:', '($2=="" || $2=="!") {print $1}', '/etc/shadow'])
    if out:
        print(f"{C['warn']}[!] Usuarios sin contraseña: {out}{C['reset']}")
        logger.log("Usuarios", "Usuarios sin contraseña detectados", "WARN", out)
        if _ask("¿Bloquear estas cuentas?"):
            bak = backup_file("/etc/shadow")
            logger.log("Usuarios", "Backup /etc/shadow", "OK", bak)
            for user in out.splitlines():
                _, rc = _run(["usermod", "-L", user])
                if rc == 0:
                    print(f"{C['ok']}[✔] Bloqueado: {user}{C['reset']}")
                    logger.log("Usuarios", f"Cuenta bloqueada: {user}", "OK")
                    applied += 1
                else:
                    logger.log("Usuarios", f"Error bloqueando: {user}", "ERROR")
                    errors += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] No se encontraron usuarios sin contraseña.{C['reset']}")
        logger.log("Usuarios", "Sin cuentas vacías", "OK")

    # 2. Deshabilitar root SSH
    print(f"\n{C['info']}[*] Verificando acceso root por SSH...{C['reset']}")
    ssh_conf = "/etc/ssh/sshd_config"
    out, _ = _run(f"grep -i PermitRootLogin {ssh_conf}", shell=True)
    if "no" not in out.lower():
        print(f"{C['warn']}[!] PermitRootLogin no está deshabilitado.{C['reset']}")
        logger.log("Usuarios", "PermitRootLogin activo", "WARN", out)
        if _ask("¿Deshabilitar login root por SSH?"):
            bak = backup_file(ssh_conf)
            logger.log("Usuarios", f"Backup sshd_config", "OK", bak)
            _run(f"sed -i 's/.*PermitRootLogin.*/PermitRootLogin no/' {ssh_conf}", shell=True)
            _run(["systemctl", "restart", "sshd"])
            print(f"{C['ok']}[✔] PermitRootLogin deshabilitado.{C['reset']}")
            logger.log("Usuarios", "PermitRootLogin deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] PermitRootLogin ya está deshabilitado.{C['reset']}")
        logger.log("Usuarios", "PermitRootLogin OK", "OK")

    # 3. Política de contraseñas (PAM / login.defs)
    print(f"\n{C['info']}[*] Verificando política de contraseñas (/etc/login.defs)...{C['reset']}")
    login_defs = "/etc/login.defs"
    bak = backup_file(login_defs)
    out, _ = _run(f"grep -E 'PASS_MAX_DAYS|PASS_MIN_LEN' {login_defs}", shell=True)
    print(f"{C['info']}  Actual: {out}{C['reset']}")
    logger.log("Usuarios", "Política actual login.defs", "INFO", out)
    if _ask("¿Aplicar política segura (MAX_DAYS=90, MIN_LEN=12)?"):
        logger.log("Usuarios", "Backup login.defs", "OK", bak)
        _run(f"sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' {login_defs}", shell=True)
        _run(f"sed -i 's/^PASS_MIN_LEN.*/PASS_MIN_LEN    12/' {login_defs}", shell=True)
        print(f"{C['ok']}[✔] Política de contraseñas actualizada.{C['reset']}")
        logger.log("Usuarios", "Política contraseñas aplicada", "OK")
        applied += 1
    else:
        skipped += 1

    # 4. Revisar sudoers
    print(f"\n{C['info']}[*] Usuarios en grupo sudo/wheel...{C['reset']}")
    out, _ = _run("getent group sudo wheel 2>/dev/null | awk -F: '{print $1, $4}'", shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Usuarios", "Grupos privilegiados", "INFO", out)

    return applied, skipped, errors


# ── WINDOWS ───────────────────────────────────
def _windows_users(logger):
    logger.section("USUARIOS Y CONTRASEÑAS — Windows")
    applied = skipped = errors = 0

    # 1. Deshabilitar cuenta Invitado
    print(f"\n{C['info']}[*] Verificando cuenta Invitado/Guest...{C['reset']}")
    out, _ = _run('net user Guest', shell=True)
    if "Account active" in out and "Yes" in out:
        print(f"{C['warn']}[!] Cuenta Guest activa.{C['reset']}")
        logger.log("Usuarios", "Cuenta Guest activa", "WARN")
        if _ask("¿Deshabilitar cuenta Guest?"):
            _, rc = _run("net user Guest /active:no", shell=True)
            if rc == 0:
                print(f"{C['ok']}[✔] Cuenta Guest deshabilitada.{C['reset']}")
                logger.log("Usuarios", "Guest deshabilitada", "OK")
                applied += 1
            else:
                logger.log("Usuarios", "Error deshabilitando Guest", "ERROR")
                errors += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] Cuenta Guest ya deshabilitada.{C['reset']}")
        logger.log("Usuarios", "Guest ya deshabilitada", "OK")

    # 2. Política de contraseñas
    print(f"\n{C['info']}[*] Verificando política de contraseñas...{C['reset']}")
    out, _ = _run("net accounts", shell=True)
    print(f"{C['info']}  {out[:300]}{C['reset']}")
    logger.log("Usuarios", "Política actual net accounts", "INFO", out[:300])
    if _ask("¿Aplicar política segura (min 12 chars, max 90 días)?"):
        bak = backup_registry_key("HKLM\\SAM")
        logger.log("Usuarios", "Backup registro SAM", "OK", str(bak))
        _run("net accounts /minpwlen:12 /maxpwage:90 /minpwage:1 /uniquepw:5", shell=True)
        print(f"{C['ok']}[✔] Política de contraseñas actualizada.{C['reset']}")
        logger.log("Usuarios", "Política contraseñas aplicada", "OK")
        applied += 1
    else:
        skipped += 1

    # 3. Deshabilitar cuenta Administrador built-in
    print(f"\n{C['info']}[*] Verificando cuenta Administrador built-in...{C['reset']}")
    out, _ = _run('net user Administrator', shell=True)
    if "Account active" in out and "Yes" in out:
        print(f"{C['warn']}[!] Cuenta Administrator built-in activa.{C['reset']}")
        logger.log("Usuarios", "Administrador built-in activo", "WARN")
        if _ask("¿Deshabilitar cuenta Administrador built-in?"):
            _, rc = _run("net user Administrator /active:no", shell=True)
            if rc == 0:
                print(f"{C['ok']}[✔] Administrador deshabilitado.{C['reset']}")
                logger.log("Usuarios", "Administrador deshabilitado", "OK")
                applied += 1
            else:
                logger.log("Usuarios", "Error deshabilitando Administrador", "ERROR")
                errors += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] Cuenta Administrador ya deshabilitada.{C['reset']}")
        logger.log("Usuarios", "Administrador ya deshabilitado", "OK")

    # 4. Listar admins locales
    print(f"\n{C['info']}[*] Administradores locales actuales...{C['reset']}")
    out, _ = _run("net localgroup Administrators", shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Usuarios", "Admins locales", "INFO", out)

    return applied, skipped, errors


def run(os_type, logger):
    print(f"\n{C['bold']}{'═'*56}{C['reset']}")
    print(f"{C['bold']}   OPCIÓN 1 — Gestión de Usuarios y Contraseñas{C['reset']}")
    print(f"{C['bold']}{'═'*56}{C['reset']}")
    if os_type == "linux":
        return _linux_users(logger)
    else:
        return _windows_users(logger)
