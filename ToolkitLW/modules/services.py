import subprocess
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
RISKY_SERVICES_LINUX = [
    "telnet", "rsh", "rlogin", "vsftpd",
    "xinetd", "avahi-daemon", "cups", "nfs-server",
]

def _linux_services(logger):
    logger.section("SERVICIOS Y SOFTWARE — Linux")
    applied = skipped = errors = 0

    # 1. Servicios riesgosos activos
    print(f"\n{C['info']}[*] Verificando servicios innecesarios/riesgosos...{C['reset']}")
    for svc in RISKY_SERVICES_LINUX:
        out, _ = _run(f"systemctl is-active {svc} 2>/dev/null", shell=True)
        if out == "active":
            print(f"{C['warn']}[!] Servicio activo: {svc}{C['reset']}")
            logger.log("Servicios", f"Servicio riesgoso activo: {svc}", "WARN")
            if _ask(f"¿Deshabilitar {svc}?"):
                _, rc = _run(["systemctl", "disable", "--now", svc])
                if rc == 0:
                    print(f"{C['ok']}[✔] {svc} deshabilitado.{C['reset']}")
                    logger.log("Servicios", f"{svc} deshabilitado", "OK")
                    applied += 1
                else:
                    logger.log("Servicios", f"Error deshabilitando {svc}", "ERROR")
                    errors += 1
            else:
                skipped += 1
        else:
            print(f"{C['ok']}[✔] {svc}: inactivo.{C['reset']}")
            logger.log("Servicios", f"{svc} inactivo", "OK")

    # 2. Actualizaciones pendientes
    print(f"\n{C['info']}[*] Verificando actualizaciones de seguridad pendientes...{C['reset']}")
    out, _ = _run("apt-get -s upgrade 2>/dev/null | grep -i 'security' | head -20", shell=True)
    if out:
        print(f"{C['warn']}[!] Actualizaciones de seguridad pendientes:\n{out}{C['reset']}")
        logger.log("Servicios", "Actualizaciones de seguridad pendientes", "WARN", out)
        if _ask("¿Aplicar actualizaciones de seguridad ahora?"):
            _run("apt-get update && apt-get upgrade -y", shell=True)
            print(f"{C['ok']}[✔] Actualizaciones aplicadas.{C['reset']}")
            logger.log("Servicios", "Actualizaciones de seguridad aplicadas", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] Sin actualizaciones de seguridad pendientes.{C['reset']}")
        logger.log("Servicios", "Sin actualizaciones pendientes", "OK")

    # 3. Cron jobs del sistema
    print(f"\n{C['info']}[*] Cron jobs activos en /etc/cron.d y crontab root...{C['reset']}")
    out, _ = _run("crontab -l 2>/dev/null; ls /etc/cron.d/ 2>/dev/null", shell=True)
    print(f"{C['info']}  {out if out else 'Sin cron jobs'}{C['reset']}")
    logger.log("Servicios", "Cron jobs sistema", "INFO", out if out else "Ninguno")

    # 4. SUID binarios sospechosos
    print(f"\n{C['info']}[*] Buscando binarios SUID no estándar...{C['reset']}")
    out, _ = _run(
        "find / -perm -4000 -type f 2>/dev/null | grep -Ev '/bin/|/usr/bin/|/usr/sbin/|/sbin/' | head -10",
        shell=True
    )
    if out:
        print(f"{C['warn']}[!] Binarios SUID sospechosos:\n{out}{C['reset']}")
        logger.log("Servicios", "SUID sospechosos", "WARN", out)
    else:
        print(f"{C['ok']}[✔] No se detectaron SUID fuera de rutas estándar.{C['reset']}")
        logger.log("Servicios", "Sin SUID sospechosos", "OK")

    return applied, skipped, errors


# ── WINDOWS ───────────────────────────────────
RISKY_SERVICES_WIN = [
    "TelnetServer", "RemoteRegistry", "SNMP",
    "Fax", "XblAuthManager", "WMPNetworkSvc", "Browser",
]

def _windows_services(logger):
    logger.section("SERVICIOS Y SOFTWARE — Windows")
    applied = skipped = errors = 0

    # 1. Servicios riesgosos
    print(f"\n{C['info']}[*] Verificando servicios innecesarios/riesgosos...{C['reset']}")
    for svc in RISKY_SERVICES_WIN:
        out, _ = _run(f"sc query {svc}", shell=True)
        if "RUNNING" in out:
            print(f"{C['warn']}[!] Servicio activo: {svc}{C['reset']}")
            logger.log("Servicios", f"Servicio riesgoso activo: {svc}", "WARN")
            if _ask(f"¿Deshabilitar {svc}?"):
                _run(f"sc stop {svc}", shell=True)
                _, rc = _run(f"sc config {svc} start= disabled", shell=True)
                if rc == 0:
                    print(f"{C['ok']}[✔] {svc} deshabilitado.{C['reset']}")
                    logger.log("Servicios", f"{svc} deshabilitado", "OK")
                    applied += 1
                else:
                    logger.log("Servicios", f"Error deshabilitando {svc}", "ERROR")
                    errors += 1
            else:
                skipped += 1
        else:
            print(f"{C['ok']}[✔] {svc}: inactivo/no instalado.{C['reset']}")
            logger.log("Servicios", f"{svc} inactivo", "OK")

    # 2. Actualizaciones pendientes
    print(f"\n{C['info']}[*] Verificando actualizaciones pendientes...{C['reset']}")
    ps_cmd = "Get-WindowsUpdate -IsInstalled:$false | Select-Object -First 10 -ExpandProperty Title 2>$null"
    out, _ = _run(["powershell", "-Command", ps_cmd])
    if out:
        print(f"{C['warn']}[!] Actualizaciones pendientes:\n{out}{C['reset']}")
        logger.log("Servicios", "Actualizaciones pendientes", "WARN", out)
    else:
        print(f"{C['ok']}[✔] Sin actualizaciones pendientes detectadas.{C['reset']}")
        logger.log("Servicios", "Sin actualizaciones pendientes", "OK")

    # 3. Tareas programadas activas
    print(f"\n{C['info']}[*] Tareas programadas activas...{C['reset']}")
    ps_cmd2 = "Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'} | Select-Object TaskName,TaskPath | Select-Object -First 20 | Format-Table -AutoSize | Out-String"
    out, _ = _run(["powershell", "-Command", ps_cmd2])
    print(f"{C['info']}  {out[:800]}{C['reset']}")
    logger.log("Servicios", "Tareas programadas activas", "INFO", out[:400])

    # 4. Deshabilitar AutoRun
    print(f"\n{C['info']}[*] Verificando AutoPlay/AutoRun...{C['reset']}")
    out, _ = _run(
        'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoDriveTypeAutoRun',
        shell=True
    )
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Servicios", "Estado AutoRun", "INFO", out)
    if "0xff" not in out.lower():
        print(f"{C['warn']}[!] AutoRun no está completamente deshabilitado.{C['reset']}")
        if _ask("¿Deshabilitar AutoRun para todas las unidades?"):
            bak = backup_registry_key("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer")
            logger.log("Servicios", "Backup reg Explorer", "OK", str(bak))
            _run(
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoDriveTypeAutoRun /t REG_DWORD /d 255 /f',
                shell=True
            )
            print(f"{C['ok']}[✔] AutoRun deshabilitado.{C['reset']}")
            logger.log("Servicios", "AutoRun deshabilitado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] AutoRun ya deshabilitado.{C['reset']}")
        logger.log("Servicios", "AutoRun ya deshabilitado", "OK")

    return applied, skipped, errors


def run(os_type, logger):
    print(f"\n{C['bold']}{'═'*56}{C['reset']}")
    print(f"{C['bold']}   OPCIÓN 4 — Servicios y Software{C['reset']}")
    print(f"{C['bold']}{'═'*56}{C['reset']}")
    if os_type == "linux":
        return _linux_services(logger)
    else:
        return _windows_services(logger)
