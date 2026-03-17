import subprocess
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
def _linux_audit(logger):
    logger.section("AUDITORÍA Y LOGS — Linux")
    applied = skipped = errors = 0

    # 1. Estado de auditd
    print(f"\n{C['info']}[*] Verificando servicio auditd...{C['reset']}")
    out, _ = _run(["systemctl", "is-active", "auditd"])
    logger.log("Auditoría", "Estado auditd", "INFO", out)
    if out != "active":
        print(f"{C['warn']}[!] auditd no está activo.{C['reset']}")
        if _ask("¿Instalar y activar auditd?"):
            _run(["apt-get", "install", "-y", "auditd"])
            _run(["systemctl", "enable", "--now", "auditd"])
            print(f"{C['ok']}[✔] auditd activado.{C['reset']}")
            logger.log("Auditoría", "auditd activado", "OK")
            applied += 1
        else:
            skipped += 1
    else:
        print(f"{C['ok']}[✔] auditd activo.{C['reset']}")
        logger.log("Auditoría", "auditd activo", "OK")

    # 2. Retención de logs
    print(f"\n{C['info']}[*] Verificando retención de logs (/etc/logrotate.conf)...{C['reset']}")
    logrotate = "/etc/logrotate.conf"
    out, _ = _run(["grep", "-i", "rotate", logrotate])
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Auditoría", "Rotación de logs actual", "INFO", out)
    if _ask("¿Configurar retención mínima de 90 días?"):
        bak = backup_file(logrotate)
        logger.log("Auditoría", "Backup logrotate.conf", "OK", bak)
        _run("sed -i 's/^rotate .*/rotate 13/' /etc/logrotate.conf", shell=True)
        print(f"{C['ok']}[✔] Retención configurada (13 semanas ≈ 90 días).{C['reset']}")
        logger.log("Auditoría", "Retención logs 13 semanas", "OK")
        applied += 1
    else:
        skipped += 1

    # 3. Integridad de archivos críticos
    print(f"\n{C['info']}[*] Verificando permisos de archivos críticos...{C['reset']}")
    critical = {
        "/etc/passwd": "644",
        "/etc/shadow": "640",
        "/etc/sudoers": "440",
    }
    for fpath, expected in critical.items():
        if os.path.exists(fpath):
            out, _ = _run(["stat", "-c", "%a", fpath])
            status = "OK" if out == expected else "WARN"
            color = C["ok"] if status == "OK" else C["warn"]
            print(f"{color}  {fpath}: {out} (esperado: {expected}){C['reset']}")
            logger.log("Auditoría", f"Permisos {fpath}", status, f"actual={out} esperado={expected}")

    # 4. Últimos accesos fallidos
    print(f"\n{C['info']}[*] Últimos 10 accesos fallidos (lastb)...{C['reset']}")
    out, _ = _run("lastb -n 10 2>/dev/null || echo 'Sin datos'", shell=True)
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Auditoría", "Últimos accesos fallidos", "INFO", out)

    return applied, skipped, errors


# ── WINDOWS ───────────────────────────────────
def _windows_audit(logger):
    logger.section("AUDITORÍA Y LOGS — Windows")
    applied = skipped = errors = 0

    # 1. Política de auditoría
    print(f"\n{C['info']}[*] Verificando política de auditoría...{C['reset']}")
    out, _ = _run(["auditpol", "/get", "/category:*"])
    print(f"{C['info']}  {out[:500]}{C['reset']}")
    logger.log("Auditoría", "Política de auditoría actual", "INFO", out[:500])
    if _ask("¿Habilitar auditoría de inicio/cierre de sesión?"):
        _run('auditpol /set /subcategory:"Logon" /success:enable /failure:enable', shell=True)
        _run('auditpol /set /subcategory:"Logoff" /success:enable /failure:enable', shell=True)
        print(f"{C['ok']}[✔] Auditoría de sesión habilitada.{C['reset']}")
        logger.log("Auditoría", "Auditoría sesión habilitada", "OK")
        applied += 1
    else:
        skipped += 1

    # 2. Retención de logs de eventos
    print(f"\n{C['info']}[*] Tamaño actual del log de Seguridad...{C['reset']}")
    ps_cmd = "Get-EventLog -List | Where-Object {$_.Log -eq 'Security'} | Select-Object MaximumKilobytes"
    out, _ = _run(["powershell", "-Command", ps_cmd])
    print(f"{C['info']}  {out}{C['reset']}")
    logger.log("Auditoría", "Tamaño log Seguridad", "INFO", out)
    if _ask("¿Ampliar tamaño máximo del log de Seguridad a 128MB?"):
        _run(["wevtutil", "sl", "Security", "/ms:131072"])
        print(f"{C['ok']}[✔] Log de Seguridad ampliado a 128MB.{C['reset']}")
        logger.log("Auditoría", "Log Seguridad 128MB", "OK")
        applied += 1
    else:
        skipped += 1

    # 3. Últimos eventos de inicio de sesión fallido (ID 4625)
    print(f"\n{C['info']}[*] Últimos 5 inicios de sesión fallidos (Event 4625)...{C['reset']}")
    ps_cmd2 = "Get-EventLog -LogName Security -InstanceId 4625 -Newest 5 2>$null | Format-List TimeGenerated,Message | Out-String"
    out, _ = _run(["powershell", "-Command", ps_cmd2])
    print(f"{C['info']}  {out[:600] if out else 'Sin eventos recientes'}{C['reset']}")
    logger.log("Auditoría", "Eventos 4625 recientes", "INFO", out[:300] if out else "Ninguno")

    # 4. Credential Guard / VBS
    print(f"\n{C['info']}[*] Verificando Windows Defender Credential Guard...{C['reset']}")
    ps_cmd3 = "(Get-ItemProperty HKLM:\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard).EnableVirtualizationBasedSecurity"
    out, _ = _run(["powershell", "-Command", ps_cmd3])
    print(f"{C['info']}  VBS habilitado: {out}{C['reset']}")
    logger.log("Auditoría", "VBS / Credential Guard", "INFO", f"Valor: {out}")

    return applied, skipped, errors


def run(os_type, logger):
    print(f"\n{C['bold']}{'═'*56}{C['reset']}")
    print(f"{C['bold']}   OPCIÓN 3 — Auditoría y Logs{C['reset']}")
    print(f"{C['bold']}{'═'*56}{C['reset']}")
    if os_type == "linux":
        return _linux_audit(logger)
    else:
        return _windows_audit(logger)
