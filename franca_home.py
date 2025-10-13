from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox,QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys

from pazienti_attivi import PazientiAttiviWindow
from pazienti_dimessi import PazientiDimessiWindow
import licenza


class HomeFranca(QWidget):
    def __init__(self):
        super().__init__()

        import licenza
        print(">>> DEBUG dentro HomeFranca: licenza_valida =", licenza.licenza_valida)

        self.setWindowTitle("Franca Dys– Home")

        # 🔹 Finestra fissa e centrata
        self.setFixedSize(650, 520)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        layout = QVBoxLayout(self)

        # --- Logo con bordo blu ---
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_frame = QLabel()
        from config import res_path
        pixmap = QPixmap(res_path("logo_franca.png"))

        pixmap = pixmap.scaled(170, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_frame.setPixmap(pixmap)
        logo_frame.setAlignment(Qt.AlignCenter)
        logo_frame.setStyleSheet("""
            QLabel {
                border: 2px solid #023047;  /* bordo più sottile e blu scuro come il titolo */
                border-radius: 10px;
                padding: 5px;
                background-color: #ffffff;
            }
        """)

        logo_layout.addWidget(logo_frame)
        layout.addWidget(logo_container, alignment=Qt.AlignCenter)

        # --- Titolo ---
        label_title = QLabel("Franca Dys")
        label_title.setStyleSheet("font-size: 34px; font-weight: bold; color: #023047;")
        label_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_title)

        # --- Sottotitolo ---
        label_sub = QLabel("Ausili alla Valutazione Logopedica della Disfagia")
        label_sub.setStyleSheet("""
            font-size: 21px;
            font-style: italic;
            color: #335d6e;
        """)
        label_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_sub)

        # --- Etichetta versione (demo o full) ---
        import licenza

        self.label_versione = QLabel()
        self.label_versione.setAlignment(Qt.AlignCenter)
        self.label_versione.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")

        if licenza.licenza_valida:
            self.label_versione.setText("🟢 Versione completa – Licenza attiva")
            self.label_versione.setStyleSheet(
                "color: green; font-size: 14px; font-weight: bold; margin-top: 10px;"
            )
        else:
            giorni = licenza.giorni_rimasti()
            giorni_txt = f"{giorni} giorni rimanenti" if giorni is not None else "Periodo di prova attivo"
            self.label_versione.setText(f"🟡 Versione demo – {giorni_txt}")
            self.label_versione.setStyleSheet(
                "color: orange; font-size: 14px; font-weight: bold; margin-top: 10px;"
            )

        layout.addWidget(self.label_versione)


        layout.addSpacing(40)


        # --- Pulsanti principali più compatti (-20%) ---
   # Pulsanti navigazione con icone
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(40)
        btn_layout.setAlignment(Qt.AlignCenter)

        button_style = """
            QPushButton {
                background-color: #ffffff;
                color: #023047;
                border: 2px solid #219ebc;
                border-radius: 10px;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: 500;
                min-width: 180px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e0f3ff;
                border-color: #023047;
            }
        """

        btn_attivi = QPushButton("  👤  Pazienti Attivi")
        btn_attivi.setStyleSheet(button_style)
        btn_attivi.clicked.connect(self.open_attivi)

        btn_dimessi = QPushButton("  📁  Pazienti Dimessi")
        btn_dimessi.setStyleSheet(button_style)
        btn_dimessi.clicked.connect(self.open_dimessi)

        btn_layout.addWidget(btn_attivi)
        btn_layout.addWidget(btn_dimessi)
        layout.addLayout(btn_layout)


        layout.addSpacing(30)

        # --- Pulsanti Guida e Copyright allineati ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(40, 10, 40, 10)
        bottom_layout.setSpacing(0)

        # Pulsante Guida
        btn_guida = QPushButton("Guida")
        btn_guida.clicked.connect(self.open_guide)
        btn_guida.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffe7cc, stop:1 #fff8f0
                );
                color: #6b2f00;
                border: 1px solid #f4a261;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffd9b0, stop:1 #fff1e1
                );
                border-color: #e76f51;
            }
        """)

        # Pulsante Copyright
        btn_copyright = QPushButton("© 2025 Franca Dys")
        btn_copyright.clicked.connect(self.show_copyright)
        btn_copyright.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffe7cc, stop:1 #fff8f0
                );
                color: #6b2f00;
                border: 1px solid #f4a261;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffd9b0, stop:1 #fff1e1
                );
                border-color: #e76f51;
            }
        """)

        bottom_layout.addWidget(btn_guida, alignment=Qt.AlignLeft)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_copyright, alignment=Qt.AlignRight)
        layout.addLayout(bottom_layout)


        # --- Finestre figlie (logica invariata) ---
        self.attivi_window = None
        self.dimessi_window = None



    def show_copyright(self):
        QMessageBox.information(
            self,
            "Copyright",
            "© 2026 Dr. Michelangelo Zanelli\n \n Logopedista \n Dottore in Scienze della Comunicazione\n \nmichelangelozanelli@gmail.com\n \n ®Tutti i diritti riservati."
        )

    def open_guide(self):
        import os
        from PyQt5.QtWidgets import QMessageBox
        from config import res_path

        pdf_path = res_path("guida.pdf")

        if os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)  # apre con il lettore PDF predefinito
            except Exception as e:
                QMessageBox.warning(self, "Errore apertura", f"Impossibile aprire la guida:\n{e}")
        else:
            QMessageBox.warning(
                self, "File mancante",
                "Il file 'guida.pdf' non è stato trovato tra le risorse del programma."
            )

   

    def open_attivi(self):
        self.attivi_window = PazientiAttiviWindow()
        self.attivi_window.show()

    def open_dimessi(self):
        self.dimessi_window = PazientiDimessiWindow()
        self.dimessi_window.show()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    import licenza

    licenza.check_licenza()

    win = HomeFranca()
    win.show()

    print("DEBUG → stato finale licenza_valida:", licenza.licenza_valida)
    sys.exit(app.exec_())




