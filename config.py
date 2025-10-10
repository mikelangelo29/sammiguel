import os
from pathlib import Path
import sys, os
from pathlib import Path

def res_path(*parts):
    """Percorso compatibile per risorse statiche (sviluppo + eseguibile PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, *parts)

APP_NAME = "Franca"

def get_base_dir():
    """Restituisce la cartella base dei dati dell'app a seconda del sistema operativo."""
    if os.name == "nt":  # Windows
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    elif os.name == "posix":
        if "darwin" in os.sys.platform:  # macOS
            return Path.home() / "Library" / "Application Support" / APP_NAME
        else:  # Linux
            return Path.home() / f".{APP_NAME.lower()}"
    else:
        return Path.home() / f".{APP_NAME.lower()}"

# cartella principale
BASE_DIR = get_base_dir()

# cartelle pazienti attivi e dimessi
DIR_ATTIVI = BASE_DIR / "pazienti"
DIR_DIMESSI = BASE_DIR / "dimessi"

# file JSON con l’elenco
FILE_ATTIVI = BASE_DIR / "pazienti.json"
FILE_DIMESSI = BASE_DIR / "dimessi.json"

# crea cartelle all’avvio
for d in (DIR_ATTIVI, DIR_DIMESSI):
    d.mkdir(parents=True, exist_ok=True)

# crea file JSON vuoti se non esistono
for f in (FILE_ATTIVI, FILE_DIMESSI):
    if not f.exists():
        with open(f, "w", encoding="utf-8") as handle:
            handle.write("[]")
