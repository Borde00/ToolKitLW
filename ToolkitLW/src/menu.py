from modules import users, network, audit, services
from core.logger import Logger

C = {
    "ok":    "\033[92m",
    "warn":  "\033[93m",
    "err":   "\033[91m",
    "info":  "\033[96m",
    "bold":  "\033[1m",
    "cyan":  "\033[36m",
    "reset": "\033[0m",
}

MENU_OPTIONS = {
    "1": ("Gestión de Usuarios y Contraseñas", users),
    "2": ("Hardening de Red y Firewall",       network),
    "3": ("Auditoría y Logs",                  audit),
    "4": ("Servicios y Software",              services),
    "5": ("Ejecutar TODO (opciones 1-4)",      None),
    "0": ("Salir",                             None),
}

def show_menu(os_type):
    os_label = "Linux 🐧" if os_type == "linux" else "Windows 🪟"
    print(f"\n{C['bold']}{C['cyan']}{'═'*56}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}  ToolkitLW — Sistema detectado: {os_label}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}{'═'*56}{C['reset']}")
    for key, (label, _) in MENU_OPTIONS.items():
        if key == "0":
            print(f"  {C['err']}[{key}]{C['reset']} {label}")
        elif key == "5":
            print(f"  {C['warn']}[{key}]{C['reset']} {label}")
            print(f"  {C['cyan']}{'─'*40}{C['reset']}")
        else:
            print(f"  {C['info']}[{key}]{C['reset']} {label}")
    print(f"{C['bold']}{C['cyan']}{'═'*56}{C['reset']}")

def run_module(mod, os_type, logger):
    a, s, e = mod.run(os_type, logger)
    print(f"\n{C['bold']}  Resultado: {C['ok']}✔ {a} aplicados{C['reset']}  "
          f"{C['warn']}✗ {s} omitidos{C['reset']}  "
          f"{C['err']}! {e} errores{C['reset']}")
    return a, s, e

def main_menu(os_type):
    logger = Logger()
    total_a = total_s = total_e = 0

    while True:
        show_menu(os_type)
        choice = input(f"\n{C['bold']}  Selecciona una opción: {C['reset']}").strip()

        if choice == "0":
            logger.summary(total_a, total_s, total_e)
            print(f"\n{C['ok']}[✔] Saliendo de ToolkitLW. ¡Hasta pronto!{C['reset']}")
            break
        elif choice in ("1", "2", "3", "4"):
            _, mod = MENU_OPTIONS[choice]
            a, s, e = run_module(mod, os_type, logger)
            total_a += a; total_s += s; total_e += e
        elif choice == "5":
            for key in ("1", "2", "3", "4"):
                _, mod = MENU_OPTIONS[key]
                a, s, e = run_module(mod, os_type, logger)
                total_a += a; total_s += s; total_e += e
            logger.summary(total_a, total_s, total_e)
        else:
            print(f"{C['err']}[!] Opción no válida.{C['reset']}")
