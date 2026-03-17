# ToolkitLW — Linux & Windows Hardening Toolkit

## Descripción
Script de bastionado de sistemas que detecta automáticamente si el sistema es Linux o Windows y aplica medidas de seguridad con confirmación previa y backup automático.

## Requisitos
- Python 3.6+
- Privilegios de administrador/root
- Sin dependencias externas (solo librería estándar)

## Uso
```bash
# Linux
sudo python3 main.py

# Windows (PowerShell como Administrador)
python main.py
```

## Estructura
```
ToolkitLW/
├── main.py              # Entry point + ASCII art
├── menu.py              # Menú interactivo
├── modules/
│   ├── users.py         # Opción 1: Usuarios y contraseñas
│   ├── network.py       # Opción 2: Red y firewall
│   ├── audit.py         # Opción 3: Auditoría y logs
│   └── services.py      # Opción 4: Servicios y software
├── core/
│   ├── detector.py      # Detección del SO
│   ├── backup.py        # Backups automáticos antes de cambios
│   └── logger.py        # Generación de informes
├── backups/             # Backups automáticos (generado en ejecución)
└── reports/             # Informes de bastionado (generado en ejecución)
```

## Opciones de Bastionado
| Opción | Nombre | Linux | Windows |
|--------|--------|-------|---------|
| 1 | Usuarios y Contraseñas | shadow, sshd, login.defs, sudoers | Guest, Admin, net accounts |
| 2 | Red y Firewall | UFW, IPv6, Telnet, puertos | Firewall, SMBv1, RDP |
| 3 | Auditoría y Logs | auditd, logrotate, lastb | auditpol, Event Log, 4625 |
| 4 | Servicios y Software | SUID, cron, apt, servicios | AutoRun, Task Scheduler, sc |

## Notas
- Siempre se pide confirmación antes de aplicar cambios
- Los backups se guardan en `backups/` con timestamp
- Los informes se guardan en `reports/` con timestamp
