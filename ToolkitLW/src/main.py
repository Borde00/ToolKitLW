#!/usr/bin/env python3
import os
import sys
from core.detector import detect_os
from menu import main_menu

C = {
    "cyan":   "\033[96m",
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}

ASCII_ART = f"""
{C['cyan']}{C['bold']}
  ████████   █████    █████   ██      ██  ██  ███  ██████  ██      ██   ██
     ██     ██   ██  ██   ██  ██      ██ ██    ██    ██    ██      ██   ██
     ██     ██   ██  ██   ██  ██      ████     ██    ██    ██      ██ █ ██
     ██     ██   ██  ██   ██  ██      ██ ██    ██    ██    ██      ███ ███
     ██      █████    █████   ██████  ██  ██  ███    ██    ██████  ██   ██
{C['reset']}
{C['green']}        Linux & Windows Hardening Toolkit v1.0{C['reset']}
{C['yellow']}           Developed for educational purposes{C['reset']}
"""

def check_privileges():
    if os.name == "nt":
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.geteuid() == 0

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(ASCII_ART)

    os_type = detect_os()

    if os_type == "unsupported":
        print(f"{C['red']}[!] Sistema operativo no soportado. Solo Linux y Windows.{C['reset']}")
        sys.exit(1)

    print(f"{C['cyan']}[*] Sistema detectado: {os_type.upper()}{C['reset']}")

    if not check_privileges():
        print(f"{C['red']}[!] ADVERTENCIA: Este script requiere privilegios de administrador/root.{C['reset']}")
        print(f"{C['yellow']}    Algunas operaciones pueden fallar sin permisos elevados.{C['reset']}")
        cont = input(f"{C['yellow']}    ¿Continuar de todas formas? (s/n): {C['reset']}").strip().lower()
        if cont != "s":
            sys.exit(0)

    main_menu(os_type)

if __name__ == "__main__":
    main()
