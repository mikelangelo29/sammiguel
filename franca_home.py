from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys

from pazienti_attivi import PazientiAttiviWindow
from pazienti_dimessi import PazientiDimessiWindow

class HomeFranca(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Franca – Home")
        self.resize(400, 380)
        self.setMinimumSize(300, 250)

        layout = QVBoxLayout(self)

        # Logo
        logo = QLabel()
        pixmap = QPixmap("logo_franca.png")
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Titolo
        label_title = QLabel("Franca")
        label_title.setStyleSheet("font-size: 32px; font-weight: bold; color: #023047;")
        label_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_title)

        # Sottotitolo
        label_sub = QLabel("Valutazione logopedica della disfagia")
        label_sub.setStyleSheet("font-size: 16px; color: #219ebc;")
        label_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_sub)

        layout.addSpacing(40)

        # Pulsanti navigazione
        btn_layout = QHBoxLayout()
        btn_attivi = QPushButton("Pazienti Attivi")
        btn_attivi.clicked.connect(self.open_attivi)
        btn_dimessi = QPushButton("Pazienti Dimessi")
        btn_dimessi.clicked.connect(self.open_dimessi)
        btn_layout.addWidget(btn_attivi)
        btn_layout.addWidget(btn_dimessi)
        layout.addLayout(btn_layout)

        layout.addSpacing(30)

        # Pulsante copyright
        btn_copyright = QPushButton("Copyright")
        btn_copyright.clicked.connect(self.show_copyright)
        layout.addWidget(btn_copyright, alignment=Qt.AlignRight)

        # Conserva le finestre figlie per evitare che vengano chiuse
        self.attivi_window = None
        self.dimessi_window = None

    def show_copyright(self):
        QMessageBox.information(
            self,
            "Copyright",
            "© 2024 Dr. Michelangelo Zanelli\n \n Logopedista \n Dottore in Scienze della Comunicazione\n \nmichelangelozanelli@gmail.com\n \n ®Tutti i diritti riservati."
        )

    def open_attivi(self):
        self.attivi_window = PazientiAttiviWindow()
        self.attivi_window.show()

    def open_dimessi(self):
        self.dimessi_window = PazientiDimessiWindow()
        self.dimessi_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = HomeFranca()
    win.show()
    sys.exit(app.exec_())