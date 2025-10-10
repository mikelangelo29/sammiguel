import os
import json
import hashlib
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from licenza import APPDATA_PATH, LIC_FILE, DEMO_MODE


class FinestraAttivazione(QWidget):
    """
    Finestra per la gestione della licenza di Franca Dys.
    Permette di generare il codice macchina e caricare un file di licenza.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attivazione Franca Dys")
        self.setFixedWidth(800)
        self.setFixedHeight(600)
        self.setStyleSheet("font-size: 12pt;")

        # --- Layout principale con margini più ampi e spaziatura equilibrata ---
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 30, 40, 30)   # margini (sinistra, alto, destra, basso)
        layout.setSpacing(20)                       # spazio verticale tra i vari widget

        # --- Titolo ---
        titolo = QLabel("<b>Gestione Licenza Franca Dys</b>")
        titolo.setAlignment(Qt.AlignCenter)
        titolo.setWordWrap(True)                    # consente di andare a capo se serve
        layout.addWidget(titolo)


        # Stato licenza
        self.lbl_stato = QLabel()
        self.lbl_stato.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_stato)
        self.aggiorna_stato()

        # Pulsanti principali
        btn_hwid = QPushButton("📄 Genera codice macchina")
        btn_hwid.clicked.connect(self.genera_hwid)
        layout.addWidget(btn_hwid)

        btn_carica = QPushButton("📂 Inserisci file di licenza")
        btn_carica.clicked.connect(self.carica_licenza)
        layout.addWidget(btn_carica)

        # Info
        # Info con pagamento
        # --- Sezione pagamento elegante ---
               # --- Sezione pagamento elegante ---
        from licenza import PREZZO_LICENZA, IBAN, PAYPAL_LINK, SUPPORT_EMAIL  # valori già definiti in licenza.py

        self.lbl_info = QLabel()
        self.lbl_info.setTextFormat(Qt.RichText)
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setWordWrap(True)

        self.lbl_info.setText(
            f"""
            <b>Attivazione della licenza completa di Franca Dys</b><br><br>
            Prezzo licenza singola: <b>{PREZZO_LICENZA},00 €</b><br><br>
            <b>Cosa devi fare:</b><br>
            1) Clicca <i>“Genera codice macchina”</i> (si salva un file sul Desktop).<br>
            2) Effettua il pagamento su:<br>
            &nbsp;&nbsp;• <b>IBAN:</b> {IBAN}<br>
            &nbsp;&nbsp;• <b>PayPal:</b> {PAYPAL_LINK}<br>
            3) Invia <b>codice macchina + ricevuta</b> a: <b>{SUPPORT_EMAIL}</b><br><br>
            Riceverai il file di licenza personalizzato da caricare con<br>
            <i>“Inserisci file di licenza”</i>.
            """
        )

        layout.addWidget(self.lbl_info)



        self.setLayout(layout)

    # --- genera codice macchina (HWID) ---
    def genera_hwid(self):
        try:
            # Calcola codice macchina
            hwid = hashlib.sha256(os.getenv("COMPUTERNAME").encode()).hexdigest()[:16]

            # Percorso Desktop dell'utente
            desktop_path = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
            desktop_path.mkdir(exist_ok=True)

            # File di output sul desktop
            file_hwid = desktop_path / "codice_macchina_FrancaDys.txt"

            # Scrittura file
            with open(file_hwid, "w", encoding="utf-8") as f:
                f.write("CODICE MACCHINA (univoco per questa installazione)\n")
                f.write("-------------------------------------------------\n")
                f.write(hwid + "\n")

            # Messaggio di conferma
            QMessageBox.information(
                self,
                "Codice generato",
                f"✅ Codice macchina generatocon successo!\n\n"
                f"📄 File salvato sul tuo Desktop:\n{file_hwid}\n\n"
                "Invialo a:\nfrancadys.supporto@gmail.com"
            )

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nella generazione del codice:\n{e}")


    # --- carica licenza (file JSON) ---
    def carica_licenza(self):
        try:
            percorso, _ = QFileDialog.getOpenFileName(
                self, "Seleziona il file di licenza", "", "File JSON (*.json)"
            )
            if not percorso:
                return

            with open(percorso, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Copia il file nella cartella ufficiale
            destinazione = APPDATA_PATH / "licenza_attiva.json"
            with open(destinazione, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            QMessageBox.information(
                self, "Licenza caricata",
                "✅ File di licenza importato correttamente!\n"
                "Riavvia Franca Dys per applicare l'attivazione completa."
            )
            self.aggiorna_stato()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento della licenza:\n{e}")

    # --- aggiorna label stato ---
    def aggiorna_stato(self):
        if DEMO_MODE:
            if LIC_FILE.exists():
                self.lbl_stato.setText("🔸 Versione DEMO attiva (tempo limitato)")
            else:
                self.lbl_stato.setText("⚠️ Nessun file di licenza trovato")
        else:
            self.lbl_stato.setText("🟢 Licenza completa attiva")
