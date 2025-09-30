import json
import os
import shutil
from functools import partial
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QDialog, QFormLayout, QLineEdit, QDateEdit, QMessageBox, QApplication, QHeaderView
)
from PyQt5.QtCore import Qt, QDate

from scheda_paziente import SchedaPazienteWindow
from pazienti_dimessi import PazientiDimessiWindow
from config import FILE_ATTIVI, FILE_DIMESSI, DIR_ATTIVI, DIR_DIMESSI


class NuovoPazienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuovo paziente")
        layout = QFormLayout(self)

        self.nome_edit = QLineEdit()
        self.cognome_edit = QLineEdit()
        self.data_nascita_edit = QDateEdit()
        self.data_nascita_edit.setCalendarPopup(True)
        self.data_nascita_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_nascita_edit.setMinimumDate(QDate(1920, 1, 1))
        self.data_nascita_edit.setMaximumDate(QDate.currentDate())
        self.data_nascita_edit.setDate(QDate(1980, 1, 1))

        self.data_ricovero_edit = QDateEdit()
        self.data_ricovero_edit.setCalendarPopup(True)
        self.data_ricovero_edit.setDisplayFormat("dd/MM/yyyy")
        oggi = QDate.currentDate()
        self.data_ricovero_edit.setMinimumDate(oggi.addYears(-1))
        self.data_ricovero_edit.setMaximumDate(oggi.addYears(5))
        self.data_ricovero_edit.setDate(oggi)

        layout.addRow("Nome:", self.nome_edit)
        layout.addRow("Cognome:", self.cognome_edit)
        layout.addRow("Data di nascita:", self.data_nascita_edit)
        layout.addRow("Data di ricovero:", self.data_ricovero_edit)

        btn_layout = QHBoxLayout()
        salva_btn = QPushButton("Salva")
        salva_btn.clicked.connect(self.accept)
        annulla_btn = QPushButton("Annulla")
        annulla_btn.clicked.connect(self.reject)
        btn_layout.addWidget(salva_btn)
        btn_layout.addWidget(annulla_btn)
        layout.addRow(btn_layout)

    def get_dati(self):
        return (
            self.nome_edit.text().strip(),
            self.cognome_edit.text().strip(),
            self.data_nascita_edit.date().toString("dd/MM/yyyy"),
            self.data_ricovero_edit.date().toString("dd/MM/yyyy")
        )


class PazientiAttiviWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pazienti Attivi")
        self.setMinimumWidth(900)
        self.setMinimumHeight(320)

        self.dati = self.carica_pazienti()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        label = QLabel("Elenco Pazienti Attivi")
        label.setStyleSheet("font-size: 22px; font-weight: bold; color: #023047; padding-bottom: 9px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        btn_layout = QHBoxLayout()
        self.dimetti_btn = QPushButton("Dimetti paziente")
        self.dimetti_btn.setStyleSheet("font-size:14px; background:#ffa726; color:white; padding:2px 11px; border-radius:6px;")
        self.dimetti_btn.clicked.connect(self.dimetti_paziente)

        self.nuovo_btn = QPushButton("Nuovo paziente")
        self.nuovo_btn.setStyleSheet("font-size:14px; background:#43a047; color:white; padding:2px 11px; border-radius:6px;")
        self.nuovo_btn.clicked.connect(self.nuovo_paziente)

        self.elimina_btn = QPushButton("Elimina selezionato")
        self.elimina_btn.setStyleSheet("font-size:14px; background:#e53935; color:white; padding:2px 11px; border-radius:6px;")
        self.elimina_btn.clicked.connect(self.elimina_paziente)

        self.visualizza_dimessi_btn = QPushButton("Visualizza Dimessi")
        self.visualizza_dimessi_btn.setStyleSheet("font-size:14px; background:#1976d2; color:white; padding:2px 11px; border-radius:6px;")
        self.visualizza_dimessi_btn.clicked.connect(self.apri_finestra_dimessi)

        btn_layout.addWidget(self.dimetti_btn)
        btn_layout.addWidget(self.nuovo_btn)
        btn_layout.addWidget(self.elimina_btn)
        btn_layout.addWidget(self.visualizza_dimessi_btn)

        # Barra di ricerca come box compatto accanto a "Visualizza Dimessi"
        self.search_edit = QLineEdit()
        self.search_edit.setFixedWidth(250)
        self.search_edit.setFixedHeight(25)
        self.search_edit.setPlaceholderText("🔍 Cerca...")
        self.search_edit.textChanged.connect(self.filtra_tabella)
        # stile con bordo blu scuro sottile
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #0D47A1;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #1565C0;
            }
        """)

        btn_layout.addWidget(self.search_edit)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)



        self.table = QTableWidget()
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 13px;
                border: none;
                background-color: #e6e6e6;   /* grigio chiaro uniforme */
            }
            QHeaderView::section {
                background-color: #d6d6d6;   /* header grigio medio */
                font-size: 14px;
                font-weight: bold;
                color: #212121;
                padding: 6px;
                border: none;
            }
            QTableWidget::item {
                padding: 6px 8px;
            }
            QTableWidget::item:selected {
                background: #B3E5FC;
                color: #212121;
            }
                                 
            QTableView::focus {
                outline: none;
                border: none;   /* 🔹 elimina contorno focus */
            }
                                                     
            QScrollBar:vertical {
                width: 14px;
                background: #e0e0e0;
                margin: 0px;
                border-radius: 6px;
            }                                
            QScrollBar::handle:vertical {
                background: #9e9e9e;
                min-height: 24px;
                border-radius: 6px;
            }
            QScrollBar:horizontal {
                height: 14px;
                background: #e0e0e0;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #9e9e9e;
                min-width: 24px;
                border-radius: 6px;
            }
        """)


        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome", "Cognome", "Data di nascita", "Data di ricovero", ""])
        for i in range(self.table.columnCount()):
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        self.table.setMinimumWidth(700)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setFocusPolicy(Qt.StrongFocus)

        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount() - 1):  # tutte meno l'ultima
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        # ultima colonna (pulsanti "Scheda")
        header.setSectionResizeMode(self.table.columnCount() - 1, QHeaderView.ResizeToContents)


        self.aggiorna_tabella()
        layout.addWidget(self.table)
        self.adjustSize()
        self.setMinimumWidth(900)
        self.setMinimumHeight(320)   # o il valore che preferivi



    def carica_pazienti(self):
        if FILE_ATTIVI.exists():
            try:
                with open(FILE_ATTIVI, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def salva_pazienti(self):
        with open(FILE_ATTIVI, "w", encoding="utf-8") as f:
            json.dump(self.dati, f, ensure_ascii=False, indent=2)

    def apri_finestra_dimessi(self):
        self.window_dimessi = PazientiDimessiWindow()
        self.window_dimessi.show()

    def aggiorna_tabella(self):
        self.table.setRowCount(len(self.dati))
        for riga, paziente in enumerate(self.dati):
            nome = paziente.get("nome", "")
            cognome = paziente.get("cognome", "")
            nascita = paziente.get("data_nascita", "")
            ricovero = paziente.get("data_ricovero", "")

            for i, value in enumerate([nome, cognome, nascita, ricovero]):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(riga, i, item)

        btn = QPushButton("Scheda")
        btn.setFixedWidth(100)   # leggermente più largo
        btn.setFixedHeight(25)   # altezza invariata
        btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                background-color: #455A64;   /* blu petrolio elegante */
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #546E7A;  /* più chiaro al passaggio */
            }
            QPushButton:pressed {
                background-color: #37474F;  /* più scuro quando cliccato */
                padding-top: 2px;
                padding-bottom: 0px;
            }
        """)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.clicked.connect(partial(self.apri_scheda, riga))

        # 🔹 Wrappo il bottone in un layout con margini a destra
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setContentsMargins(0, 0, 10, 0)  # margine destro
        cell_layout.addWidget(btn)
        cell_layout.setAlignment(Qt.AlignRight)
        self.table.setCellWidget(riga, 4, cell_widget)

        self.table.resizeRowsToContents()


    def nuovo_paziente(self):
        dlg = NuovoPazienteDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            nome, cognome, nascita, ricovero = dlg.get_dati()
            if nome and cognome:
                nuovo = {"nome": nome, "cognome": cognome, "data_nascita": nascita, "data_ricovero": ricovero}
                self.dati.append(nuovo)
                self.salva_pazienti()

                # crea cartella paziente
                eta = self.calcola_eta(nascita)
                cart = DIR_ATTIVI / f"{nome}_{cognome}_{eta}a"
                cart.mkdir(parents=True, exist_ok=True)

                dati_file = cart / "dati.json"
                if not dati_file.exists():
                    with open(dati_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "valutazioni_aperte": [],
                            "valutazioni_completate": [],
                            "report_indici": [],
                            "report_completi": [],
                            "grafici": []
                        }, f, ensure_ascii=False, indent=2)

                self.aggiorna_tabella()
            else:
                QMessageBox.warning(self, "Errore", "Compila nome e cognome!")

    def elimina_paziente(self):
        r = self.table.currentRow()
        if r < 0 or r >= len(self.dati):
            QMessageBox.information(self, "Seleziona paziente", "Seleziona un paziente dalla tabella.")
            return

        paziente = self.dati[r]
        nome, cognome = paziente["nome"], paziente["cognome"]

        reply = QMessageBox.question(self, "Conferma eliminazione", f"Eliminare definitivamente {nome} {cognome}?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        del self.dati[r]
        self.salva_pazienti()
        self.aggiorna_tabella()

        prefix = f"{nome}_{cognome}_"
        for d in os.listdir(DIR_ATTIVI):
            if d.startswith(prefix):
                p = DIR_ATTIVI / d
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)

    def dimetti_paziente(self):
        riga = self.table.currentRow()
        if riga < 0:
            QMessageBox.warning(self, "Selezione", "Seleziona un paziente da dimettere.")
            return

        paziente = self.dati[riga]
        nome, cognome = paziente["nome"], paziente["cognome"]

        # 🔹 Popup di conferma con pulsanti localizzati
        msgbox = QMessageBox(self)
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setWindowTitle("Conferma dimissione")
        msgbox.setText(f"Vuoi davvero dimettere il paziente {nome} {cognome}?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.button(QMessageBox.Yes).setText("Sì")
        msgbox.button(QMessageBox.No).setText("No")

        if msgbox.exec_() != QMessageBox.Yes:
            return  # annullato dall’utente

        # 🔹 Procedi con dimissione
        paziente = self.dati.pop(riga)
        self.salva_pazienti()

        dimessi = []
        if FILE_DIMESSI.exists():
            with open(FILE_DIMESSI, "r", encoding="utf-8") as f:
                dimessi = json.load(f)
        dimessi.append(paziente)
        with open(FILE_DIMESSI, "w", encoding="utf-8") as f:
            json.dump(dimessi, f, indent=2, ensure_ascii=False)

        eta = self.calcola_eta(paziente["data_nascita"])
        src = DIR_ATTIVI / f"{paziente['nome']}_{paziente['cognome']}_{eta}a"
        dst = DIR_DIMESSI / f"{paziente['nome']}_{paziente['cognome']}_{eta}a"
        if src.exists():
            shutil.move(str(src), str(dst))

        self.aggiorna_tabella()
        if hasattr(self, "window_dimessi"):
            self.window_dimessi.aggiorna_dati_dimessi()


    def apri_scheda(self, riga):
        paziente = self.dati[riga]
        nome = paziente["nome"]
        cognome = paziente["cognome"]
        nascita = paziente["data_nascita"]
        eta = self.calcola_eta(nascita)
        cart = DIR_ATTIVI / f"{nome}_{cognome}_{eta}a"

        self.scheda = SchedaPazienteWindow(
            nome, cognome, eta,
            path_cartella=str(cart)
        )
        self.scheda.show()

    def filtra_tabella(self):
        testo = self.search_edit.text().lower().strip()
        for riga in range(self.table.rowCount()):
            nome = self.table.item(riga, 0).text().lower()
            cognome = self.table.item(riga, 1).text().lower()
            visibile = testo in nome or testo in cognome
            self.table.setRowHidden(riga, not visibile)


    def calcola_eta(self, data_nascita):
        try:
            nascita = datetime.strptime(data_nascita, "%d/%m/%Y")
            oggi = datetime.today()
            return oggi.year - nascita.year - ((oggi.month, oggi.day) < (nascita.month, nascita.day))
        except Exception:
            return "?"


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = PazientiAttiviWindow()
    win.showMaximized()
    sys.exit(app.exec_())
