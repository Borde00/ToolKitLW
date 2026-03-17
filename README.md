<div align="center">

# ToolkitLW — Linux & Windows Hardening Toolkit

**Herramienta de bastionado de sistemas multiplataforma**  
Detecta automáticamente el SO y aplica medidas de seguridad con confirmación previa y backup automático.

![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![Root Required](https://img.shields.io/badge/Requires-Root%2FAdmin-red?style=for-the-badge)

</div>

---

## 📋 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Módulos de Bastionado](#-módulos-de-bastionado)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Ejecución](#-flujo-de-ejecución)
- [Aviso Legal](#-aviso-legal)
- [Licencia](#-licencia)

---

## 📖 Descripción

**ToolkitLW** es una herramienta de bastionado (*hardening*) de sistemas desarrollada en Python que permite aplicar medidas de seguridad de forma semi-automática sobre sistemas **Linux** y **Windows**.

Está diseñada para administradores de sistemas y profesionales de seguridad que necesiten endurecer la configuración de un sistema de manera rápida, controlada y documentada, sin riesgo de pérdida de configuraciones previas gracias a su sistema de backups automáticos.

> ⚠️ **Esta herramienta ha sido desarrollada con fines educativos y de uso en entornos controlados. Úsala únicamente en sistemas sobre los que tengas autorización.**

---

## ✨ Características

- 🔍 **Detección automática del SO** — Identifica si el sistema es Linux o Windows sin configuración manual
- 🛡️ **4 módulos de bastionado** — Usuarios, Red, Auditoría y Servicios
- 💾 **Backups automáticos** — Guarda copia de cada archivo antes de modificarlo, con timestamp
- 📄 **Generación de informes** — Exporta un reporte detallado de todas las acciones aplicadas
- ✅ **Confirmación previa** — Solicita confirmación antes de aplicar cualquier cambio crítico
- 📊 **Resumen de resultados** — Muestra acciones aplicadas, omitidas y errores al finalizar
- 🎯 **Ejecución modular o total** — Puedes lanzar módulos individuales o todos a la vez

---

## ⚙️ Requisitos

| Requisito | Detalle |
|---|---|
| Python | 3.6 o superior |
| Privilegios | `root` en Linux / Administrador en Windows |
| Dependencias | Solo librería estándar de Python (sin `pip install`) |
| SO soportados | Linux (Debian/Ubuntu/RHEL) · Windows 10/11/Server |

---

## 🚀 Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/ToolkitLW.git

# 2. Entra al directorio
cd ToolkitLW

# 3. (Opcional) Verifica que no hay dependencias externas
cat requirements.txt
```

No se requiere instalación adicional. El proyecto usa únicamente la librería estándar de Python.

---

## 🖥️ Uso

### Linux
```bash
sudo python3 main.py
```

### Windows (PowerShell como Administrador)
```powershell
python main.py
```

Al iniciarse, la herramienta detecta automáticamente el sistema operativo y muestra el menú principal:

```
════════════════════════════════════════════════════════
 ToolkitLW — Sistema detectado: Linux 🐧
════════════════════════════════════════════════════════
 [1] Gestión de Usuarios y Contraseñas
 [2] Hardening de Red y Firewall
 [3] Auditoría y Logs
 [4] Servicios y Software
 ────────────────────────────────────────
 [5] Ejecutar TODO (opciones 1-4)
 [0] Salir
════════════════════════════════════════════════════════
```

---

## 🔧 Módulos de Bastionado

### 1 · Usuarios y Contraseñas
| Acción | Linux | Windows |
|---|---|---|
| Política de contraseñas | `shadow`, `login.defs` | `net accounts` |
| Acceso SSH | Hardening `sshd_config` | — |
| Privilegios | Revisión `sudoers` | Deshabilitar cuenta Guest/Admin |

### 2 · Red y Firewall
| Acción | Linux | Windows |
|---|---|---|
| Firewall | Configuración UFW | Windows Firewall |
| Protocolos inseguros | Deshabilitar Telnet, IPv6 | Deshabilitar SMBv1 |
| Acceso remoto | Cierre de puertos peligrosos | Restricción RDP |

### 3 · Auditoría y Logs
| Acción | Linux | Windows |
|---|---|---|
| Sistema de auditoría | `auditd` | `auditpol` |
| Rotación de logs | `logrotate` | Event Log |
| Intentos fallidos | Monitoreo `lastb` | Evento 4625 |

### 4 · Servicios y Software
| Acción | Linux | Windows |
|---|---|---|
| Permisos especiales | Revisión SUID/SGID | Deshabilitar AutoRun |
| Tareas programadas | Auditoría `cron` | Task Scheduler |
| Actualizaciones | Configuración `apt` | Windows Update |
| Servicios innecesarios | Auditoría y desactivación | `sc` query/stop |

---

## 📁 Estructura del Proyecto

```
ToolkitLW/
├── main.py                  # Entry point + ASCII art + verificación de privilegios
├── menu.py                  # Menú interactivo y gestión de resultados
│
├── modules/                 # Módulos de bastionado
│   ├── __init__.py
│   ├── users.py             # Módulo 1: Usuarios y contraseñas
│   ├── network.py           # Módulo 2: Red y firewall
│   ├── audit.py             # Módulo 3: Auditoría y logs
│   └── services.py          # Módulo 4: Servicios y software
│
├── core/                    # Lógica central
│   ├── __init__.py
│   ├── detector.py          # Detección automática del SO
│   ├── backup.py            # Sistema de backups con timestamp
│   └── logger.py            # Generación de informes
│
├── backups/                 # Backups automáticos (generado en ejecución)
│   └── .gitkeep
├── reports/                 # Informes de bastionado (generado en ejecución)
│   └── .gitkeep
│
├── requirements.txt         # Sin dependencias externas
└── README.md
```

---

## 🔄 Flujo de Ejecución

```
Inicio
  │
  ├─► Detección del SO (Linux / Windows)
  │
  ├─► Verificación de privilegios (root / Admin)
  │
  ├─► Menú interactivo
  │     ├─► Módulo seleccionado
  │     │     ├─► Confirmación del usuario
  │     │     ├─► Backup automático del archivo afectado
  │     │     ├─► Aplicación del cambio
  │     │     └─► Registro en el logger
  │     └─► Repetir hasta salir
  │
  └─► Resumen final: ✔ aplicados | ✗ omitidos | ! errores
        └─► Exportación del informe en reports/
```

---

## ⚠️ Aviso Legal

Esta herramienta está diseñada **exclusivamente para uso en sistemas propios o entornos donde se cuente con autorización explícita**. El uso no autorizado de esta herramienta sobre sistemas ajenos puede constituir un delito según la legislación vigente.

El autor no se hace responsable del mal uso de esta herramienta.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más información.

---

<div align="center">
  Desarrollado con 🛡️ para fines educativos en ciberseguridad
</div>
