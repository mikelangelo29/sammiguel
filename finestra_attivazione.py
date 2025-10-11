import os
import json
import hashlib
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QSizePolicy, QApplication, QFrame
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
        self.resize(800, 870)
        self.setMinimumSize(800, 780)
        self.setStyleSheet("font-size: 12pt; background-color: #fdfdfd;")

        from licenza import PREZZO_LICENZA, IBAN, PAYPAL_LINK, SUPPORT_EMAIL

        # --- Layout principale ---
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(22)

        # --- Titolo ---
        titolo = QLabel("<b>🧩 Gestione Licenza Franca Dys</b>")
        titolo.setAlignment(Qt.AlignCenter)
        titolo.setStyleSheet("font-size: 18pt; color: #023047;")
        layout.addWidget(titolo)

        # --- Stato licenza ---
        self.lbl_stato = QLabel()
        self.lbl_stato.setAlignment(Qt.AlignCenter)
        self.lbl_stato.setStyleSheet("color: #555; font-size: 11pt;")
        layout.addWidget(self.lbl_stato)
        self.aggiorna_stato()

        # --- Pulsanti principali ---
        btn_style = """
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #219ebc;
                color: #023047;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12pt;
                min-width: 240px;
            }
            QPushButton:hover {
                background-color: #e0f3ff;
                border-color: #023047;
            }
        """

        btn_hwid = QPushButton("📄 Genera codice macchina")
        btn_hwid.setStyleSheet(btn_style)
        btn_hwid.clicked.connect(self.genera_hwid)
        layout.addWidget(btn_hwid, alignment=Qt.AlignCenter)

        btn_carica = QPushButton("📂 Inserisci file di licenza")
        btn_carica.setStyleSheet(btn_style)
        btn_carica.clicked.connect(self.carica_licenza)
        layout.addWidget(btn_carica, alignment=Qt.AlignCenter)

        # --- Riquadro istruzioni + pagamento ---
        info_box = QWidget()
        info_box.setStyleSheet("""
            QWidget {
                background-color: #f7fbff;
                border: 1px solid #bcd4e6;
                border-radius: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)

        lbl_info = QLabel(f"""
        <b>💳 Attivazione della licenza completa</b><br><br>
        Prezzo licenza singola: <b>{PREZZO_LICENZA} €</b><br><br>
        <b>Cosa devi fare:</b><br><br>
        <div style="text-align:left; margin-left:60px; line-height:1.6;">
            <span>1️⃣&nbsp;&nbsp;Clicca “Genera codice macchina” (si salva un file sul Desktop).</span><br><br>
            <span>2️⃣&nbsp;&nbsp;Effettua il pagamento su:</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;🏦 <b>IBAN:</b> <span style="color:#035388;">{IBAN}</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;💰 <b>PayPal:</b> <a href="{PAYPAL_LINK}" style="color:#0077cc; text-decoration:none;">{PAYPAL_LINK}</a><br><br>
            <span>3️⃣&nbsp;&nbsp;Invia codice macchina e ricevuta di pagamento a:</span><br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>{SUPPORT_EMAIL}</b>
        </div><br>
        <b>Riceverai via email il file di licenza personalizzato<br>
        da caricare con “Inserisci file di licenza”.</b>
        """)

        lbl_info.setAlignment(Qt.AlignCenter)
        lbl_info.setWordWrap(True)
        lbl_info.setTextFormat(Qt.RichText)
        lbl_info.setOpenExternalLinks(True)
        lbl_info.setStyleSheet("font-size: 11pt; color: #023047;")
        info_layout.addWidget(lbl_info)

        # --- Linea divisoria ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bbb; margin-top: 10px; margin-bottom: 10px;")
        info_layout.addWidget(line)

        # --- Pulsanti copia IBAN e PayPal affiancati ---
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(30)

        copy_style = """
            QPushButton {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 11pt;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """

        btn_iban = QPushButton("📋 Copia IBAN")
        btn_iban.setStyleSheet(copy_style)
        btn_iban.clicked.connect(lambda: self.copia_testo(IBAN, "IBAN copiato negli appunti!"))
        btn_row.addWidget(btn_iban)

        btn_paypal = QPushButton("📋 Copia link PayPal")
        btn_paypal.setStyleSheet(copy_style)
        btn_paypal.clicked.connect(lambda: self.copia_testo(PAYPAL_LINK, "Link PayPal copiato negli appunti!"))
        btn_row.addWidget(btn_paypal)

        info_layout.addLayout(btn_row)
        layout.addWidget(info_box)
        self.setLayout(layout)

    # --- Copia testo negli appunti ---
    def copia_testo(self, testo, messaggio):
        app_instance = QApplication.instance()
        if app_instance:
            app_instance.clipboard().setText(testo)
            QMessageBox.information(self, "Copiato", f"✅ {messaggio}")
        else:
            QMessageBox.warning(self, "Errore", "❌ Clipboard non disponibile.")

    # --- Genera codice macchina ---
    def genera_hwid(self):
        try:
            hwid = hashlib.sha256(os.getenv("COMPUTERNAME").encode()).hexdigest()[:16]
            desktop_path = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
            file_hwid = desktop_path / "codice_macchina_FrancaDys.txt"
            with open(file_hwid, "w", encoding="utf-8") as f:
                f.write("CODICE MACCHINA (univoco per questa installazione)\n")
                f.write("-------------------------------------------------\n")
                f.write(hwid + "\n")
            QMessageBox.information(
                self, "Codice generato",
                f"✅ Codice macchina generato!\n\n📄 Salvato sul Desktop:\n{file_hwid}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nella generazione del codice:\n{e}")

    # --- Carica licenza ---
    def carica_licenza(self):
        try:
            percorso, _ = QFileDialog.getOpenFileName(
                self, "Seleziona il file di licenza", "", "File JSON (*.json)"
            )
            if not percorso:
                return
            with open(percorso, "r", encoding="utf-8") as f:
                data = json.load(f)
            destinazione = APPDATA_PATH / "licenza_attiva.json"
            with open(destinazione, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(
                self, "Licenza caricata",
                "✅ Licenza importata con successo!\nRiavvia Franca Dys per applicarla."
            )
            self.aggiorna_stato()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento:\n{e}")

    # --- Aggiorna stato licenza ---
    def aggiorna_stato(self):
        if DEMO_MODE:
            if LIC_FILE.exists():
                self.lbl_stato.setText("🔸 Versione DEMO attiva (tempo limitato)")
            else:
                self.lbl_stato.setText("⚠️ Nessun file di licenza trovato")
        else:
            self.lbl_stato.setText("🟢 Licenza completa attiva")
