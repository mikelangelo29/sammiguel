import json
import os
import subprocess
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from schede_valutazione import SchedeValutazioneWindow
from PyPDF2 import PdfMerger
# Per PDF multipagina
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
from config import DIR_ATTIVI




# === Radice pazienti ===


class SchedaPazienteWindow(QWidget):
    def __init__(self, nome, cognome, eta,
                 valutazioni_aperte=None, valutazioni_completate=None,
                 report_indici=None, report_completi=None, grafici=None,
                 path_cartella=None, sola_lettura=False):
        super().__init__()
        self.setWindowTitle(f"Scheda di {nome} {cognome}")
        self.resize(650, 700)
        self.nome = nome
        self.cognome = cognome
        self.eta = eta
        self.sola_lettura = sola_lettura


        # 🔹 Imposta la cartella paziente
        if path_cartella:  # se passo un percorso (es. dai dimessi), uso quello
            self.cartella_paziente = Path(path_cartella)
        else:  # altrimenti creo in DIR_ATTIVI (config.py)
            self.cartella_paziente = DIR_ATTIVI / f"{self.nome}_{self.cognome}_{self.eta}a"

        # creo cartella principale e sottocartelle
        self.cartella_paziente.mkdir(parents=True, exist_ok=True)
        self.data_file = self.cartella_paziente / "dati.json"
        self.cartella_report_completi = self.cartella_paziente / "report_completi"
        self.cartella_report_indici = self.cartella_paziente / "report_indici"
        self.cartella_grafici = self.cartella_paziente / "grafici"
        self.cartella_report_completi.mkdir(exist_ok=True)
        self.cartella_report_indici.mkdir(exist_ok=True)
        self.cartella_grafici.mkdir(exist_ok=True)

        # valori di default se non passati
        if valutazioni_aperte is None:
            valutazioni_aperte = []
        if valutazioni_completate is None:
            valutazioni_completate = []
        if report_indici is None:
            report_indici = []
        if report_completi is None:
            report_completi = []
        if grafici is None:
            grafici = []

        # carica dati se esiste dati.json
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    dati = json.load(f)
                    self.valutazioni_aperte = dati.get("valutazioni_aperte", [])
                    self.valutazioni_completate = dati.get("valutazioni_completate", [])
                    self.report_indici = dati.get("report_indici", [])
                    self.report_completi = dati.get("report_completi", [])
                    self.grafici = dati.get("grafici", [])
            except Exception:
                # fallback se file corrotto
                self.valutazioni_aperte = valutazioni_aperte
                self.valutazioni_completate = valutazioni_completate
                self.report_indici = report_indici
                self.report_completi = report_completi
                self.grafici = grafici
        else:
            self.valutazioni_aperte = valutazioni_aperte
            self.valutazioni_completate = valutazioni_completate
            self.report_indici = report_indici
            self.report_completi = report_completi
            self.grafici = grafici

        # === UI ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        dati_label = QLabel(f"<b>{self.nome} {self.cognome}</b>  {self.eta}A")
        dati_label.setStyleSheet("font-size: 16px; color: #023047; padding-bottom: 8px;")
        layout.addWidget(dati_label)

        btn_layout = QHBoxLayout()
        self.elimina_btn = QPushButton("Elimina selezionato")
        self.elimina_btn.setStyleSheet("""
            QPushButton {
                background:#e53935; 
                color:white; 
                font-weight:bold; 
                font-size:15px; 
                padding:12px 22px;
            }
            QPushButton:disabled {
                background:#cccccc; 
                color:#666666;
            }
        """)
        self.elimina_btn.clicked.connect(self.elimina_selezionato)
        btn_layout.addWidget(self.elimina_btn)

        self.nuova_valutazione_btn = QPushButton("+ Avvia nuova valutazione")

        self.nuova_valutazione_btn.setStyleSheet("""
            QPushButton {
                background:#43a047; 
                color:white; 
                font-weight:bold; 
                font-size:15px; 
                padding:12px 22px;
            }
            QPushButton:disabled {
                background:#cccccc; 
                color:#666666;
            }
        """)

        self.nuova_valutazione_btn.clicked.connect(self.apri_schede_valutazione)
        if getattr(self, "sola_lettura", False):
            self.elimina_btn.setDisabled(True)
            self.nuova_valutazione_btn.setDisabled(True)
        btn_layout.addStretch()
        btn_layout.addWidget(self.nuova_valutazione_btn)
        btn_layout.addStretch()

        self.apri_cartella_btn = QPushButton("Apri cartella paziente")
        self.apri_cartella_btn.setStyleSheet("background:#1976d2; color:white; font-weight:bold; font-size:15px; padding:12px 22px")
        self.apri_cartella_btn.clicked.connect(self.apri_cartella_paziente)
        btn_layout.addWidget(self.apri_cartella_btn)

        layout.addLayout(btn_layout)

        font_date = QFont()
        font_date.setPointSize(12)

        print("DEBUG cartella paziente:", self.cartella_paziente)


        # Valutazioni aperte
        box_val = QGroupBox("Valutazioni aperte")
        val_layout = QVBoxLayout(box_val)
        self.lista_val = QListWidget()
        self.aggiorna_lista_valutazioni()
        self.lista_val.itemDoubleClicked.connect(self.apri_fascicolo_valutazione)
        val_layout.addWidget(self.lista_val)
        layout.addWidget(box_val)

        # Valutazioni completate
        box_val_comp = QGroupBox("Valutazioni completate")
        val_comp_layout = QVBoxLayout(box_val_comp)
        self.lista_val_comp = QListWidget()
        self.aggiorna_lista_valutazioni_completate()
        self.lista_val_comp.itemDoubleClicked.connect(self.apri_fascicolo_valutazione_completata)
        val_comp_layout.addWidget(self.lista_val_comp)
        layout.addWidget(box_val_comp)

        # Report indici
        report_indici_box = QGroupBox("Report Indici Critici")
        report_indici_layout = QVBoxLayout(report_indici_box)
        self.lista_report_indici = QListWidget()
        for data in self.report_indici:
            item = QListWidgetItem(f"⚠️ {data}")
            item.setFont(font_date)
            # abilita checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lista_report_indici.addItem(item)

        self.lista_report_indici.itemDoubleClicked.connect(self.apri_report_indice_critico)
        report_indici_layout.addWidget(self.lista_report_indici)
        layout.addWidget(report_indici_box)
        from PyQt5.QtWidgets import QAbstractItemView

        # Report completi
        report_completi_box = QGroupBox("Report completi")
        report_completi_layout = QVBoxLayout(report_completi_box)
        self.lista_report_completi = QListWidget()
        for data in self.report_completi:
            item = QListWidgetItem(f"💾 {data}")
            item.setFont(font_date)
            # abilita checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lista_report_completi.addItem(item)
        self.lista_report_completi.itemDoubleClicked.connect(self.apri_report_completo)
        report_completi_layout.addWidget(self.lista_report_completi)
        layout.addWidget(report_completi_box)
        
        # abilita selezione multipla
        
        #self.lista_report_completi.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Grafici



    # === Salvataggio su file ===
    def salva_su_file(self):
        dati = {
            "valutazioni_aperte": self.valutazioni_aperte,
            "valutazioni_completate": self.valutazioni_completate,
            "report_indici": self.report_indici,
            "report_completi": self.report_completi,
            "grafici": self.grafici,
        }
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(dati, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Errore salvataggio", f"Errore nel salvataggio: {e}")


    # === Liste aggiornamento ===
    def aggiorna_lista_valutazioni(self):
        self.lista_val.clear()
        font_date = QFont()
        font_date.setPointSize(12)
        for valutazione in self.valutazioni_aperte:
            data = valutazione.get("timestamp", "") if isinstance(valutazione, dict) else str(valutazione)
            item = QListWidgetItem(f"🚧 {data}")
            item.setFont(font_date)
            self.lista_val.addItem(item)

    def aggiorna_lista_valutazioni_completate(self):
        self.lista_val_comp.clear()
        font_date = QFont()
        font_date.setPointSize(12)
    from PyQt5.QtCore import Qt

    def aggiorna_lista_valutazioni_completate(self):
        self.lista_val_comp.clear()
        font_date = QFont()
        font_date.setPointSize(12)
        for valutazione in self.valutazioni_completate:
            data = valutazione.get("timestamp", "") if isinstance(valutazione, dict) else str(valutazione)
            item = QListWidgetItem(f"🟢 {data}")
            item.setFont(font_date)
            self.lista_val_comp.addItem(item)

    # === Eliminazione selezione ===
    def elimina_selezionato(self):
        removed = False

        # valutazioni aperte
        idx = self.lista_val.currentRow()
        if idx != -1 and idx < len(self.valutazioni_aperte):
            del self.valutazioni_aperte[idx]
            self.lista_val.takeItem(idx)
            removed = True

        # valutazioni completate
        idx = self.lista_val_comp.currentRow()
        if idx != -1 and idx < len(self.valutazioni_completate):
            del self.valutazioni_completate[idx]
            self.lista_val_comp.takeItem(idx)
            removed = True

        # report indici
        idx = self.lista_report_indici.currentRow()
        if idx != -1 and idx < len(self.report_indici):
            del self.report_indici[idx]
            self.lista_report_indici.takeItem(idx)
            removed = True

        # report completi
        idx = self.lista_report_completi.currentRow()
        if idx != -1 and idx < len(self.report_completi):
            del self.report_completi[idx]
            self.lista_report_completi.takeItem(idx)
            removed = True

        # grafici
      #  idx = self.lista_grafici.currentRow()
       # if idx != -1 and idx < len(self.grafici):
        #    del self.grafici[idx]
         #   self.lista_grafici.takeItem(idx)
          #  removed = True

       # if removed:
        #    self.salva_su_file()
        #else:
         #   QMessageBox.information(self, "Nessuna selezione", "Seleziona una voce da eliminare.")

    # === Apertura/creazione valutazioni ===
    def apri_fascicolo_valutazione(self, item):
        idx = self.lista_val.row(item)
        if idx >= 0 and idx < len(self.valutazioni_aperte):
            valutazione = self.valutazioni_aperte[idx]
            if not isinstance(valutazione, dict):
                QMessageBox.warning(self, "Valutazione non valida", "Il dato selezionato non è una valutazione valida.")
                return
            # apri finestra di valutazione con callback per salvare/aggiornare
            self.schede_valutazione = SchedeValutazioneWindow(
                self.nome, self.cognome, self.eta,
                callback_salva=self.aggiorna_valutazione_aperta,
                valutazione_precaricata=valutazione,
                indice_valutazione=idx
            )
            self.schede_valutazione.paziente_window = self
            self.schede_valutazione.show()

    def apri_fascicolo_valutazione_completata(self, item):
        idx = self.lista_val_comp.row(item)
        if idx >= 0 and idx < len(self.valutazioni_completate):
            valutazione = self.valutazioni_completate[idx]
            if not isinstance(valutazione, dict):
                QMessageBox.warning(self, "Valutazione non valida", "Il dato selezionato non è una valutazione valida.")
                return
            # apri in sola lettura (nessun callback per aggiornare)
            self.schede_valutazione = SchedeValutazioneWindow(
                self.nome, self.cognome, self.eta,
                callback_salva=None,
                valutazione_precaricata=valutazione,
                indice_valutazione=idx
            )
            self.schede_valutazione.paziente_window = self
            self.schede_valutazione.show()

    def apri_schede_valutazione(self):
        # crea una nuova valutazione (nessun indice)
        self.schede_valutazione = SchedeValutazioneWindow(
            self.nome, self.cognome, self.eta,
            callback_salva=self.aggiungi_valutazione
        )
        self.schede_valutazione.paziente_window = self
        self.schede_valutazione.show()

    # === Callback / aggiornamento dopo salvataggio valutazione ===
    def aggiorna_valutazione_aperta(self, valutazione, idx=None, completata=False):
        # chiamato quando la finestra di valutazione salva e passa qui i dati
        if completata:
            # sposta da aperte a completate
            self.valutazioni_completate.append(valutazione)
            if idx is not None and 0 <= idx < len(self.valutazioni_aperte):
                try:
                    del self.valutazioni_aperte[idx]
                except Exception:
                    pass
            self.aggiorna_lista_valutazioni()
            self.aggiorna_lista_valutazioni_completate()
            self.salva_su_file()
        else:
            # aggiornamento o aggiunta tra le aperte
            if idx is not None and 0 <= idx < len(self.valutazioni_aperte):
                self.valutazioni_aperte[idx] = valutazione
            else:
                self.valutazioni_aperte.append(valutazione)
            self.aggiorna_lista_valutazioni()
            self.salva_su_file()

    def aggiorna_valutazione_completata(self, valutazione, idx=None):
        if idx is not None and 0 <= idx < len(self.valutazioni_completate):
            self.valutazioni_completate[idx] = valutazione
        else:
            self.valutazioni_completate.append(valutazione)
        self.aggiorna_lista_valutazioni_completate()
        self.salva_su_file()

    def aggiungi_valutazione(self, valutazione, idx=None, completata=False):
        # callback per nuova valutazione creata dalla finestra
        if completata:
            self.valutazioni_completate.append(valutazione)
            self.aggiorna_lista_valutazioni_completate()
        else:
            self.valutazioni_aperte.append(valutazione)
            self.aggiorna_lista_valutazioni()
        self.salva_su_file()

    def aggiungi_valutazione_completata(self, valutazione, idx=None):
        self.valutazioni_completate.append(valutazione)
        self.aggiorna_lista_valutazioni_completate()
        self.salva_su_file()

    # === Report / Grafici ===
    def apri_report_indice_critico(self, item):
        idx = self.lista_report_indici.row(item)
        if idx >= 0 and idx < len(self.report_indici):
            data_val_safe = self.report_indici[idx]
            try:
                possibili = [
                    f for f in os.listdir(self.cartella_report_indici)
                    if f.startswith(f"report_indici_{data_val_safe}_")
                ]
            except Exception:
                possibili = []
            if possibili:
                possibili.sort()
                percorso = os.path.join(self.cartella_report_indici, possibili[-1])
                self._apri_file(percorso)
            else:
                QMessageBox.warning(
                    self,
                    "File non trovato",
                    f"Nessun PDF trovato per {data_val_safe}"
                )

    def apri_report_completo(self, item):
        idx = self.lista_report_completi.row(item)
        if idx >= 0 and idx < len(self.report_completi):
            data_val_safe = self.report_completi[idx]  # ora già "sicura"
            try:
                possibili = [
                    f for f in os.listdir(self.cartella_report_completi)
                    if f.startswith(f"report_completo_{data_val_safe}_")
                ]
            except Exception:
                possibili = []
            if possibili:
                possibili.sort()
                percorso = os.path.join(self.cartella_report_completi, possibili[-1])
                self._apri_file(percorso)
            else:
                QMessageBox.warning(
                    self,
                    "File non trovato",
                    f"Nessun PDF trovato per {data_val_safe}"
                )


    def aggiungi_report_completo(self, data_valutazione):
        font_date = QFont()
        font_date.setPointSize(12)
        self.report_completi.append(data_valutazione)
        item = QListWidgetItem(f"💾 {data_valutazione}")
        item.setFont(font_date)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self.lista_report_completi.addItem(item)
        self.salva_su_file()

    def aggiungi_report_indici(self, data_valutazione):
        self.report_indici.append(data_valutazione)
        self.lista_report_indici.addItem(f"⚠️ {data_valutazione}")

        self.salva_su_file()


   # def crea_nuovo_grafico(self):
    #    # placeholder semplice
     #   self.grafici.append("Nuovo grafico")
      #  self.lista_grafici.addItem(QListWidgetItem("📈 Nuovo grafico"))
       # self.salva_su_file()

 #   def visualizza_grafico_salvato(self, item):
 #       QMessageBox.information(self, "Grafico", f"Visualizza: {item.text()}")

        self.salva_su_file()

    


    # === Helper apertura file ===
    def _apri_file(self, percorso):
        if not os.path.exists(percorso):
            QMessageBox.warning(self, "File non trovato", f"File non trovato: {percorso}")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(percorso)
            elif sys.platform.startswith("darwin"):
                subprocess.call(("open", percorso))
            else:
                subprocess.call(("xdg-open", percorso))
        except Exception as e:
            QMessageBox.warning(self, "Errore apertura file", f"Errore aprendo il file: {e}")

    import os
    import subprocess
    import platform

    def apri_cartella(self):
        from PyQt5.QtCore import QUrl
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtWidgets import QMessageBox
        import os

        path = str(self.cartella_paziente)
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Cartella non trovata", f"La cartella {path} non esiste.")

    def apri_cartella_paziente(self):
        return self.apri_cartella()

    def ApriCartella(self):
        return self.apri_cartella()


