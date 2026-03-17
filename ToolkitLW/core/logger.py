import os
import datetime

REPORTS_DIR = "reports"

def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def get_log_path():
    _ensure_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(REPORTS_DIR, f"report_{ts}.txt")

class Logger:
    def __init__(self):
        self.path = get_log_path()
        self.entries = []
        self._write_header()

    def _write_header(self):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
╔══════════════════════════════════════════════════════╗
║              ToolkitLW - Informe de Bastionado       ║
╚══════════════════════════════════════════════════════╝
Fecha : {ts}
{'='*56}
"""
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(header)

    def log(self, section, action, status, detail=""):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] [{section}] [{status}] {action}"
        if detail:
            entry += f" — {detail}"
        self.entries.append(entry)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def section(self, title):
        line = f"\n{'─'*56}\n  {title}\n{'─'*56}"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def summary(self, applied, skipped, errors):
        summary = f"""
{'='*56}
  RESUMEN FINAL
{'='*56}
  ✔ Aplicados : {applied}
  ✗ Omitidos  : {skipped}
  ! Errores   : {errors}
{'='*56}
"""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(summary)
        print(f"\n\033[92m[✔] Informe guardado en: {self.path}\033[0m")
