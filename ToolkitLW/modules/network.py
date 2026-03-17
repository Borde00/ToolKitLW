import subprocess
import platform
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
def _linux_network(logger):
    logger.section("RED Y FIREWALL — Linux")
    applied = skipped = errors = 0

    # 1. UFW status
    print(f"\n{C['info']}[*] Verificando estado del firewall (UFW)...{C['reset']}")
    out, rc = _run(["ufw", "status"])
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Red", "Estado UFW", "INFO", out)
    if "inactive" in out.lower():
        print(f"{C['warn']}[!] UFW está desactivado.{C['reset']}")
        if _ask("¿Habilitar UFW con política por defecto deny-incoming?"):
            _run(["ufw", "--force", "enable"])
            _run(["ufw", "default", "deny", "incoming"])
            _run(["ufw", "default", "allow", "outgoing"])
            _run(["ufw", "allow", "ssh"])
            print(f"{C['ok']}[✔] UFW activado.{C['reset']}")
            logger.log("Red", "UFW activado + deny incoming", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] UFW ya está activo.{C['reset']}")

    # 2. Puertos abiertos
    print(f"\n{C['info']}[*] Puertos en escucha...{C['reset']}")
    out, _ = _run("ss -tlnp | grep LISTEN", shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Red", "Puertos en escucha", "INFO", out)

    # 3. Deshabilitar IPv6 si no se usa
    print(f"\n{C['info']}[*] Verificando IPv6...{C['reset']}")
    out, _ = _run("sysctl net.ipv6.conf.all.disable_ipv6", shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    if "= 0" in out:
        print(f"{C['warn']}[!] IPv6 está habilitado.{C['reset']}")
        logger.log("Red", "IPv6 habilitado", "WARN")
        if _ask("¿Deshabilitar IPv6?"):
            sysctl_conf = "/etc/sysctl.conf"
            bak = backup_file(sysctl_conf)
            logger.log("Red", "Backup sysctl.conf", "OK", bak)
            with open(sysctl_conf, "a") as f:
                f.write("\nnet.ipv6.conf.all.disable_ipv6 = 1\n")
                f.write("net.ipv6.conf.default.disable_ipv6 = 1\n")
            _run(["sysctl", "-p"])
            print(f"{C['ok']}[✔] IPv6 deshabilitado.{C['reset']}")
            logger.log("Red", "IPv6 deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] IPv6 ya deshabilitado.{C['reset']}")
        logger.log("Red", "IPv6 ya deshabilitado", "OK")

    # 4. Deshabilitar Telnet
    print(f"\n{C['info']}[*] Verificando servicio Telnet...{C['reset']}")
    out, _ = _run("systemctl is-active telnet.socket 2>/dev/null || echo inactive", shell=True)
    if "active" in out:
        print(f"{C['warn']}[!] Telnet activo.{C['reset']}")
        logger.log("Red", "Telnet activo", "WARN")
        if _ask("¿Deshabilitar Telnet?"):
            _run(["systemctl", "disable", "--now", "telnet.socket"])
            print(f"{C['ok']}[✔] Telnet deshabilitado.{C['reset']}")
            logger.log("Red", "Telnet deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] Telnet no está activo.{C['reset']}")
        logger.log("Red", "Telnet inactivo", "OK")

    return applied, skipped, errors


# ── WINDOWS ───────────────────────────────────
def _windows_network(logger):
    logger.section("RED Y FIREWALL — Windows")
    applied = skipped = errors = 0

    # 1. Windows Firewall
    print(f"\n{C['info']}[*] Verificando Windows Firewall...{C['reset']}")
    out, _ = _run("netsh advfirewall show allprofiles state", shell=True)
    print(f"{C['info']}  {out[:400]}{C['reset']}")
    logger.log("Red", "Estado Firewall", "INFO", out[:400])
    if "OFF" in out.upper():
        print(f"{C['warn']}[!] Firewall desactivado en algún perfil.{C['reset']}")
        if _ask("¿Activar firewall en todos los perfiles?"):
            _run("netsh advfirewall set allprofiles state on", shell=True)
            print(f"{C['ok']}[✔] Firewall activado en todos los perfiles.{C['reset']}")
            logger.log("Red", "Firewall activado todos los perfiles", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] Firewall activo en todos los perfiles.{C['reset']}")
        logger.log("Red", "Firewall activo", "OK")

    # 2. Deshabilitar SMBv1
    print(f"\n{C['info']}[*] Verificando SMBv1...{C['reset']}")
    out, _ = _run('powershell -Command "Get-SmbServerConfiguration | Select EnableSMB1Protocol"', shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Red", "Estado SMBv1", "INFO", out)
    if "True" in out:
        print(f"{C['warn']}[!] SMBv1 está habilitado (riesgo EternalBlue).{C['reset']}")
        if _ask("¿Deshabilitar SMBv1?"):
            bak = backup_registry_key("HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters")
            logger.log("Red", "Backup reg SMB", "OK", str(bak))
            _run('powershell -Command "Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force"', shell=True)
            print(f"{C['ok']}[✔] SMBv1 deshabilitado.{C['reset']}")
            logger.log("Red", "SMBv1 deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] SMBv1 ya deshabilitado.{C['reset']}")
        logger.log("Red", "SMBv1 ya deshabilitado", "OK")

    # 3. Puertos en escucha
    print(f"\n{C['info']}[*] Puertos en escucha...{C['reset']}")
    out, _ = _run("netstat -ano | findstr LISTENING", shell=True)
    print(f"{C['info']}  {out[:600]}{C['reset']}")
    logger.log("Red", "Puertos en escucha", "INFO", out[:600])

    # 4. Deshabilitar RDP si no es necesario
    print(f"\n{C['info']}[*] Verificando RDP...{C['reset']}")
    out, _ = _run('reg query "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections', shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Red", "Estado RDP", "INFO", out)
    if "0x0" in out:
        print(f"{C['warn']}[!] RDP está habilitado.{C['reset']}")
        if _ask("¿Deshabilitar RDP?"):
            bak = backup_registry_key("HKLM\\System\\CurrentControlSet\\Control\\Terminal Server")
            logger.log("Red", "Backup reg RDP", "OK", str(bak))
            _run('reg add "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f', shell=True)
            print(f"{C['ok']}[✔] RDP deshabilitado.{C['reset']}")
            logger.log("Red", "RDP deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] RDP ya deshabilitado.{C['reset']}")
        logger.log("Red", "RDP ya deshabilitado", "OK")

    return applied, skipped, errors


def run(os_type, logger):
    print(f"\n{C['bold']}{'═'*56}{C['reset']}")
    print(f"{C['bold']}   OPCIÓN 2 — Hardening de Red y Firewall{C['reset']}")
    print(f"{C['bold']}{'═'*56}{C['reset']}")
    if os_type == "linux":
        return _linux_network(logger)
    else:
        return _windows_network(logger)
