import os
import sys
import json
import datetime
import uuid
import winreg
from pathlib import Path
from PyQt5.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt
import hashlib
import stat, subprocess
DEV_MODE = False # True = sviluppo (file visibile e scrivibile). Metti False in produzione.


licenza_valida = False

# ==============================================================
# CONFIGURAZIONE LICENZA - FRANCA DYS
# ==============================================================
DEMO_MODE = True              # Lascia sempre True: serve anche per la versione completa
DURATA_DEMO = 30              # Giorni di prova
APP_NAME = "Franca Dys"

# 📧 Dati contatto e pagamento
SUPPORT_EMAIL = "francadys.supporto@gmail.com"
PREZZO_LICENZA = "Licenza singola: €59 iva inclusa"
IBAN = "IT03T0347501605CC0011851438"               # ⬅️ Inserisci il tuo IBAN reale
PAYPAL_LINK = "https://paypal.me/tuolinkpaypal"   # ⬅️ Inserisci il tuo link PayPal (facoltativo)

# Percorsi locali (AppData + Registro)
APPDATA_PATH = Path(os.getenv("APPDATA")) / APP_NAME
LIC_FILE = APPDATA_PATH / "licenza.json"          # File che registra la data di inizio demo
REG_PATH = rf"Software\\{APP_NAME}"
REG_KEY = "Licenza"

licenza_valida = True


# ==============================================================
# FUNZIONI DI SUPPORTO
# ==============================================================
def _scrivi_registro(data_str):
    """Scrive la data di attivazione demo nel Registro di Windows."""
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        winreg.SetValueEx(key, REG_KEY, 0, winreg.REG_SZ, data_str)
        winreg.CloseKey(key)
    except Exception as e:
        print("Errore registro:", e)

def _leggi_registro():
    """Legge la data di attivazione demo dal Registro di Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        val, _ = winreg.QueryValueEx(key, REG_KEY)
        winreg.CloseKey(key)
        return val
    except FileNotFoundError:
        return None

def calc_hwid():
    """Genera un codice macchina unico e stabile."""
    base = str(uuid.getnode())
    return "-".join([base[i:i + 4] for i in range(0, len(base), 4)])

import time
def _hide_and_lock_file_windows(path, readonly=True, hide=True, force_dev=False):
    """Nasconde (+h) e rende sola-lettura (+r) un file su Windows.
       In DEV_MODE non fa nulla."""
    try:
        if force_dev:
            return  # In sviluppo non si blocca niente

        path = str(Path(path).resolve())
        if not os.path.exists(path):
            print("DEBUG: file non trovato:", path)
            return

        time.sleep(0.3)  # attesa per sicurezza

        if sys.platform == "win32":
            subprocess.run(f'attrib +h +r "{path}"', shell=True)
            print(f"DEBUG: nascosto e bloccato {path}")
    except Exception as e:
        print("DEBUG: errore in _hide_and_lock_file_windows:", e)

import subprocess, os, sys

def _hide_franca_folder(dev_mode=False):
    """Rende la cartella Franca Dys completamente invisibile (anche con 'Mostra file nascosti')."""
    try:
        folder = str(APPDATA_PATH.resolve())
        if sys.platform != "win32" or not os.path.exists(folder):
            return

        if not dev_mode:
            # 🔒 Nasconde la cartella in modo totale (solo visibile se si disattivano le protezioni di sistema)
            subprocess.run(f'attrib +s +h "{folder}"', shell=True)
            print(f"DEBUG: cartella {folder} resa completamente invisibile")
        else:
            # 🧰 In sviluppo la riportiamo visibile
            subprocess.run(f'attrib -s -h "{folder}"', shell=True)
            print(f"DEBUG: cartella {folder} resa visibile per sviluppo")

    except Exception as e:
        print("DEBUG: errore in _hide_franca_folder:", e)


# ==============================================================
# FINESTRA DI ATTIVAZIONE / SCADENZA
# ==============================================================
class FinestraLicenza(QDialog):
    """Finestra che appare quando la demo è in scadenza o terminata."""

    def __init__(self, giorni_restanti):
        super().__init__()
        self.setWindowTitle("Attivazione Franca Dys")
        self.setFixedSize(620, 540)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Messaggio iniziale
        if giorni_restanti <= 0:
            testo = (
                "<b>Il periodo di prova di Franca Dys è terminato.</b><br><br>"
                "Per continuare a utilizzare il programma è necessario attivare la licenza completa.<br><br>"
                "Segui le istruzioni qui sotto per completare l’attivazione."
            )
        else:
            testo = (
                f"<b>Franca Dys</b> è in modalità di prova.<br>"
                f"Hai ancora <b>{giorni_restanti} giorni</b> di utilizzo.<br><br>"
                "Puoi già attivare la versione completa per evitare interruzioni future."
            )

        label = QLabel(testo)
        label.setWordWrap(True)
        layout.addWidget(label)

        # ----------------------------------------------------------
        # TESTO ISTRUZIONI PER IL CLIENTE
        # ----------------------------------------------------------
        istruzioni = (
            "<hr>"
            "<b>🔑 Come attivare Franca Dys</b><br><br>"
            f"<b>{PREZZO_LICENZA}</b><br><br>"
            "1️⃣ Clicca su <b>“📄 Genera codice macchina”</b>.<br>"
            " Il programma creerà un file chiamato <code>richiesta_attivazione.txt</code>.<br>"
            "2️⃣ Invia questo file via email a <b>{support}</b><br>"
            " insieme al tuo nome e ai dati del pagamento.<br><br>"
            "3️⃣ Riceverai entro 24 ore il tuo file di licenza personale.<br>"
            " Il file avrà un nome simile a <code>license_full_TuoNome.json</code>.<br><br>"
            "4️⃣ Apri di nuovo Franca Dys e clicca su <b>“📂 Inserisci file di licenza”</b>.<br>"
            " Seleziona il file ricevuto via email e conferma.<br>"
            "5️⃣ Riavvia il programma: la tua licenza sarà attiva in modo permanente.<br><br>"
            "<b>ℹ️ Informazioni importanti sulla licenza:</b><br>"
            "• La licenza è legata al computer in cui viene attivata.<br>"
            "• Se desideri installare Franca Dys su un altro PC,<br>"
            " è necessario richiedere una nuova licenza al supporto tecnico.<br>"
            "• In caso di formattazione o cambio hardware,<br>"
            " potrebbe essere necessario rigenerare la licenza.<br><br>"
            "<b>📧 Supporto:</b> {support}<br>"
            "Riceverai assistenza entro 24 ore lavorative."
        ).format(support=SUPPORT_EMAIL)

        label_pag = QLabel(istruzioni)
        label_pag.setOpenExternalLinks(True)
        label_pag.setWordWrap(True)
        layout.addWidget(label_pag)

        # ----------------------------------------------------------
        # PULSANTI
        # ----------------------------------------------------------
        btn_generacodice = QPushButton("📄 Genera codice macchina")
        btn_generacodice.clicked.connect(self.genera_hwid)
        layout.addWidget(btn_generacodice)

        btn_caricalicenza = QPushButton("📂 Inserisci file di licenza")
        btn_caricalicenza.clicked.connect(self.carica_licenza)
        layout.addWidget(btn_caricalicenza)

        btn_chiudi = QPushButton("❌ Chiudi programma")
        btn_chiudi.clicked.connect(self.chiudi)
        layout.addWidget(btn_chiudi)

    # ----------------------------------------------------------
    # FUNZIONE: GENERA CODICE MACCHINA
    # ----------------------------------------------------------
    def genera_hwid(self):
        hwid = calc_hwid()
        APPDATA_PATH.mkdir(parents=True, exist_ok=True)
        dest = APPDATA_PATH / "richiesta_attivazione.txt"
        with open(dest, "w", encoding="utf-8") as f:
            f.write("=== RICHIESTA ATTIVAZIONE FRANCA DYS ===\n\n")
            f.write(f"CODICE MACCHINA (HWID): {hwid}\n\n")
            f.write(f"Invia questo file a: {SUPPORT_EMAIL}\n")
            f.write("Allega la ricevuta o i dati del pagamento.\n")
        QMessageBox.information(
            self, "Codice macchina generato",
            f"File salvato in:\n{dest}\n\n"
            f"CODICE: {hwid}\n\n"
            f"Invia questo file o codice all’autore:\n{SUPPORT_EMAIL}"
        )

    # ----------------------------------------------------------
    # FUNZIONE: CARICA FILE DI LICENZA
    # ----------------------------------------------------------
    def carica_licenza(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona il file di licenza", "", "File JSON (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lic = json.load(f)

            # Verifica che la licenza appartenga a questo PC
            if lic.get("hwid") != calc_hwid():
                QMessageBox.critical(self, "Licenza non valida",
                                     "Questa licenza è stata emessa per un altro computer.")
                return

            dest = APPDATA_PATH / "license_full.json"
            with open(dest, "w", encoding="utf-8") as out:
                json.dump(lic, out, indent=2)
            _hide_and_lock_file_windows(dest, readonly=True, hide=True, force_dev=DEV_MODE)

            QMessageBox.information(
                self, "Licenza inserita",
                "Licenza copiata correttamente.\n"
                "Riavvia Franca Dys per completare l’attivazione."
            )
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile leggere la licenza:\n{e}")

    # ----------------------------------------------------------
    # CHIUDI PROGRAMMA
    # ----------------------------------------------------------
    def chiudi(self):
        self.close()
        sys.exit()


# ==============================================================
# CONTROLLO LICENZA ALL’AVVIO
# ==============================================================
def check_licenza():
    """
    Controlla lo stato della licenza demo o completa.
    Crea la cartella in AppData, gestisce il countdown e riconosce la licenza full.
    """
    global finestra_attivazione_instance
    global licenza_valida

    try:
        print("DEBUG: check_licenza() avviata...")

        # --- Percorsi di ricerca per licenza completa ---
                # --- Percorsi di ricerca per licenza completa ---
        percorsi_possibili = [
            Path(os.path.join(os.path.expanduser("~"), "Desktop")) / "Franca Dys" / "licenza_attiva.json",
            Path.cwd() / "licenza_attiva.json",
            APPDATA_PATH / "licenza_attiva.json"
        ]

        licenza_valida = False

        for percorso in percorsi_possibili:
            if percorso.exists():
                print(f"DEBUG: trovata licenza in {percorso}")
                try:
                    with open(percorso, "r", encoding="utf-8") as f:
                        lic = json.load(f)
                    hwid_corrente = hashlib.sha256(os.getenv("COMPUTERNAME").encode()).hexdigest()[:16]
                    hwid_file = lic.get("hwid")

                    if hwid_file == hwid_corrente:
                        print(f"🟢 Licenza completa valida trovata in: {percorso}")
                        licenza_valida = True

                        # Copia automatica della licenza in AppData (backup permanente)
                        try:
                            APPDATA_PATH.mkdir(parents=True, exist_ok=True)
                            import shutil
                            copia_destinazione = APPDATA_PATH / "licenza_attiva.json"
                            if not copia_destinazione.exists():
                                shutil.copy(percorso, copia_destinazione)
                                print(f"DEBUG: licenza copiata in AppData -> {copia_destinazione}")
                            _hide_and_lock_file_windows(copia_destinazione, readonly=True, hide=True, force_dev=DEV_MODE)

                        except Exception as e:
                            print(f"DEBUG: errore nel salvataggio della licenza in AppData: {e}")

                        break  # ← Fermati appena trovi una licenza valida
                    else:
                        print(f"⚠️ HWID non corrisponde ({hwid_file} ≠ {hwid_corrente})")

                except Exception as e:
                    print(f"❌ Errore nella lettura di {percorso}: {e}")

        # --- Se trovata licenza full, esci subito ---
        if licenza_valida:
            print("DEBUG: licenza valida, salto modalità demo.")
            return


        # --- Se modalità demo attiva ---
        print("DEBUG: modalità demo attiva.")
        APPDATA_PATH.mkdir(parents=True, exist_ok=True)
        print("DEBUG: cartella AppData:", APPDATA_PATH)

        oggi = datetime.date.today()

        # Percorso file demo
        LIC_FILE = APPDATA_PATH / "licenza_demo.json"

        # --- Crea o legge file di licenza demo ---
        if LIC_FILE.exists():
            with open(LIC_FILE, "r", encoding="utf-8") as f:
                data_inizio = datetime.date.fromisoformat(json.load(f)["data"])
        else:
            data_inizio = oggi
            with open(LIC_FILE, "w", encoding="utf-8") as f:
                json.dump({"data": data_inizio.isoformat()}, f)
            _hide_and_lock_file_windows(LIC_FILE, readonly=True, hide=True, force_dev=DEV_MODE)
            print("DEBUG: creato nuovo file demo:", LIC_FILE)

            # --- Protezione file di licenza (solo in modalità distribuzione) ---
            if not DEV_MODE:
                try:
                    import subprocess
                    # Rende il file di sola lettura e nascosto
                    subprocess.run(f'attrib +r +h "{LIC_FILE}"', shell=True)
                    
                    print("DEBUG: file licenza reso nascosto e di sola lettura")
                except Exception as e:
                    print("DEBUG: errore protezione file licenza:", e)

        # --- Calcolo giorni rimanenti ---
        giorni_passati = (oggi - data_inizio).days
        giorni_restanti = DURATA_DEMO - giorni_passati
        print(f"DEBUG: giorni passati={giorni_passati}, restanti={giorni_restanti}")

        # --- Verifica scadenza ---
        if giorni_restanti <= 0:
            # Finestra modale obbligatoria: o attivi o esci. Non si torna nella home.
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Franca Dys – Licenza scaduta")
            msg.setText(
                "⛔ Il periodo di prova di 30 giorni è terminato.\n\n"
                "Per continuare a usare Franca Dys è necessario attivare la licenza completa."
            )
            btn_chiudi = msg.addButton("Chiudi", QMessageBox.RejectRole)
            btn_attiva = msg.addButton("Apri finestra di attivazione", QMessageBox.ActionRole)
            # FORZA la modalità applicazione modale: blocca tutte le altre finestre finché l'utente risponde
            msg.setWindowModality(Qt.ApplicationModal)
            msg.exec_()

            # Se l'utente ha scelto "Apri finestra di attivazione" apri la finestra, altrimenti esci
            if msg.clickedButton() == btn_attiva:
                from finestra_attivazione import FinestraAttivazione
                finestra_attivazione_instance = FinestraAttivazione()
                finestra_attivazione_instance.setWindowModality(Qt.ApplicationModal)
                finestra_attivazione_instance.show()
                # blocca tutto il resto finché non chiude la finestra
                loop = QApplication.instance()
                while finestra_attivazione_instance.isVisible():
                    loop.processEvents()

                # dopo la chiusura della finestra di attivazione ricontrolla lo stato licenza
                # (puoi reinvocare check_licenza() o terminare per sicurezza)
                # Per semplicità, termina l'app e chiedi di riavviare:
                QMessageBox.information(None, "Riavvia", "Riavvia il programma dopo l'attivazione.")
                sys.exit(0)
            else:
                # Chiudere senza tornare alla home
                sys.exit(0)

        elif giorni_restanti <= 10:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Franca Dys – Licenza in scadenza")
            msg.setText(
                f"⚠️ Il periodo di prova scadrà tra {giorni_restanti} giorni.\n"
                "Puoi continuare a usare la versione demo fino alla scadenza\n"
                "oppure attivare subito la licenza completa."
            )
            msg.addButton("Continua", QMessageBox.AcceptRole)
            msg.addButton("Apri finestra di attivazione", QMessageBox.ActionRole)
            msg.exec_()

            if msg.clickedButton().text() == "Apri finestra di attivazione":
                from finestra_attivazione import FinestraAttivazione
                finestra_attivazione_instance = FinestraAttivazione()
                finestra_attivazione_instance.setWindowModality(Qt.ApplicationModal)
                finestra_attivazione_instance.show()

        _hide_franca_folder(dev_mode=DEV_MODE)

        # --- Sblocco automatico in modalità sviluppo ---
        if DEV_MODE:
            try:
                import subprocess
                subprocess.run(f'attrib -r -h "{LIC_FILE}"', shell=True)
                subprocess.run(f'attrib -s -h "{APPDATA_PATH}"', shell=True)
                print("DEBUG: DEV_MODE attivo: file licenza reso visibile e modificabile")
            except Exception as e:
                print("DEBUG: errore rimozione protezione DEV_MODE:", e)


        print("DEBUG: controllo licenza completato senza errori.")

        

    except Exception as e:
        import traceback
        print("❌ ERRORE IN check_licenza() ❌")
        traceback.print_exc()
        QMessageBox.critical(None, "Errore Licenza", f"Errore durante il controllo licenza:\n{e}")
        sys.exit()



# ==============================================================
# FUNZIONE DI UTILITÀ
# ==============================================================
def giorni_rimasti():
    """Ritorna i giorni di prova rimanenti."""
    if not DEMO_MODE:
        return None
    if not LIC_FILE.exists():
        return DURATA_DEMO
    oggi = datetime.date.today()
    with open(LIC_FILE, "r", encoding="utf-8") as f:
        data_inizio = datetime.date.fromisoformat(json.load(f)["data"])
    return max(0, DURATA_DEMO - (oggi - data_inizio).days)
