import os
import shutil
import datetime
import platform

BACKUP_DIR = "backups"

def _ensure_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def _timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_file(filepath):
    """Crea una copia de seguridad de un fichero antes de modificarlo."""
    _ensure_dir()
    if not os.path.exists(filepath):
        return None
    filename = os.path.basename(filepath).replace("/", "_").replace("\\", "_")
    dest = os.path.join(BACKUP_DIR, f"{filename}_{_timestamp()}.bak")
    shutil.copy2(filepath, dest)
    return dest

def backup_registry_key(key_path):
    """Exporta una clave de registro de Windows a un .reg en backups/."""
    import subprocess
    _ensure_dir()
    safe_name = key_path.replace("\\", "_").replace("/", "_")[:60]
    dest = os.path.join(BACKUP_DIR, f"reg_{safe_name}_{_timestamp()}.reg")
    try:
        subprocess.run(["reg", "export", key_path, dest, "/y"],
                       capture_output=True, check=True)
        return dest
    except Exception as e:
        return None

def list_backups():
    _ensure_dir()
    files = sorted(os.listdir(BACKUP_DIR))
    return files

def restore_file(backup_filename, original_path):
    """Restaura un fichero desde su backup."""
    src = os.path.join(BACKUP_DIR, backup_filename)
    if not os.path.exists(src):
        print(f"\033[91m[!] Backup no encontrado: {src}\033[0m")
        return False
    shutil.copy2(src, original_path)
    print(f"\033[92m[✔] Restaurado: {original_path}\033[0m")
    return True
