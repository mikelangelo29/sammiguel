from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QFormLayout, QLineEdit, QComboBox, QGridLayout, QLabel,
    QSpinBox, QHBoxLayout, QPushButton, QGroupBox, QTextEdit, QCheckBox, QLabel, QSizePolicy, QMessageBox, QScrollArea, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QStylePainter, QStyleOptionTab, QTabBar
from datetime import datetime
import os


# === Costanti globali per le prassie bucco-linguo-facciali ===
PRASSIE_VOCI = [
    "Protrusione lingua",
    "Lingua in avanti e indietro",
    "Lingua a destra",
    "Lingua a sinistra",
    "Schioccare la lingua",
    "Sorridere",
    "Mandare un bacio",
    "Schema alternato bacio-sorriso",
    "Gonfiare le guance",
    "Aprire e chiudere la bocca",
    "Spostare il labbro a sinistra",
    "Spostare il labbro a destra",
    "Soffiare",
    "Fischiare",
    "Tossire"
]

PRASSIE_MAPPA_DESCRIZIONI = {
    0: "0 - risposta assente o non adeguata",
    1: "1 - risposta parziale o ottenuta con facilitazione",
    2: "2 - risposta immediata e adeguata al comando"
}

class FixedTabBar(QTabBar):
    """Corregge il taglio della prima lettera nei tab selezionati (bug Qt5-Windows)."""
    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            # Sposta di 2 pixel a destra SOLO il tab attivo
            if opt.state & QStyle.State_Selected:
                opt.rect.adjust(2, 0, 0, 0)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)



class SchedeValutazioneWindow(QWidget):
    def __init__(self, nome, cognome, eta, callback_salva=None, valutazione_precaricata=None, indice_valutazione=None):
        super().__init__()
        # 🔧 Fix per il taglio della prima lettera nei tab: stile Fusion solo qui
        from PyQt5.QtWidgets import QStyleFactory
        self.setStyle(QStyleFactory.create("Fusion"))
        self.resize(1300, 800)      # 👈 apre la finestra un po’ più larga e alta
        self.setMinimumSize(1100, 700)
        self.setWindowTitle(f"Valutazione Disfagia - {nome} {cognome}")
        self.setMinimumSize(1024, 700)
        self.callback_salva = callback_salva
        self.valutazione_precaricata = valutazione_precaricata
        self.indice_valutazione = indice_valutazione

        base_font = QFont("Arial", 11)
        bold_font = QFont("Arial", 11, QFont.Bold)
        section_font = QFont("Arial", 13, QFont.Bold)

        layout = QVBoxLayout(self)
        layout.setSpacing(13)

        salva_layout = QHBoxLayout()

        # === Bottoni salvataggio ===
        self.salva_btn = QPushButton("💾 Salva valutazione")
        self.salva_btn.setStyleSheet(
            "font-size:15px; font-weight:bold; background:#43a047; color:white; padding:7px 28px; border-radius:8px;"
        )
        self.salva_btn.clicked.connect(self.salva_valutazione)

        self.salva_chiudi_btn = QPushButton("🟠 Salva e chiudi valutazione")
        self.salva_chiudi_btn.setStyleSheet(
            "font-size:15px; font-weight:bold; background:#ff9800; color:white; padding:7px 28px; border-radius:8px;"
        )
        self.salva_chiudi_btn.clicked.connect(self.salva_e_chiudi_valutazione)

        # === Bottoni report ===
        self.report_completo_btn = QPushButton("📄 Crea Report completo")
        self.report_completo_btn.setStyleSheet(
            "font-size:15px; font-weight:bold; background:#1976d2; color:white; padding:7px 28px; border-radius:8px;"
        )
        self.report_completo_btn.clicked.connect(self.crea_report_completo)

        self.report_indici_btn = QPushButton("⚠️ Report indici critici")
        self.report_indici_btn.setStyleSheet(
            "font-size:15px; font-weight:bold; background:#d32f2f; color:white; padding:7px 28px; border-radius:8px;"
        )
        self.report_indici_btn.clicked.connect(self.crea_report_indici)

        salva_layout.addStretch()

        # === Gestione Logo Report ===
        self.logo_label = QLabel("Logo report:")
        self.logo_path_line = QLineEdit()
        self.logo_path_line.setReadOnly(True)
        self.logo_btn = QPushButton("Scegli logo…")
        self.logo_btn.clicked.connect(self.scegli_logo)
        self.logo_remove_btn = QPushButton("Rimuovi logo")
        self.logo_remove_btn.clicked.connect(self.rimuovi_logo)
        self.no_logo_checkbox = QCheckBox("Non inserire logo nel report")
        self.no_logo_checkbox.stateChanged.connect(self.check_no_logo)

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.logo_path_line)
        logo_layout.addWidget(self.logo_btn)
        logo_layout.addWidget(self.logo_remove_btn)
        logo_layout.addWidget(self.no_logo_checkbox)
        layout.addLayout(logo_layout)

        self.carica_logo_default()

        # Se valutazione aperta → bottoni di salvataggio
        if self.callback_salva is not None:
            salva_layout.addWidget(self.salva_btn)
            salva_layout.addWidget(self.salva_chiudi_btn)
        # Se valutazione completata → bottoni di report
        else:
            salva_layout.addWidget(self.report_completo_btn)
            salva_layout.addWidget(self.report_indici_btn)

        salva_layout.addStretch()
        layout.addLayout(salva_layout)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.tabBar().setElideMode(Qt.ElideNone) 

        self.tab_widget.setStyleSheet("""
            /* Tutti i tab (normali) */
            QTabBar::tab {
                background: #ffffff;
                border: 2px solid #90a4c2;
                padding: 6px 14px;
                margin-right: 2px;
                margin-left: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 90px;
                text-align: center;
                color: #000000;
            }

            /* Tab selezionato - solo cambio colore, senza ridisegno */
            QTabBar::tab:selected:!hover {
                background-color: #d9e7ff;   /* azzurrino leggerissimo */
                color: #0d47a1;               /* testo blu ma stabile */
                border-color: #90a4c2;        /* stesso bordo per non ricreare il rettangolo */
            }

            /* Tab al passaggio del mouse - effetto leggero */
            QTabBar::tab:hover {
                background-color: #f2f7ff;
            }
        """)


        layout.addWidget(self.tab_widget)
        
        self.tab_checkboxes = []
        self.tab_forms = []

        self.add_tab(self.tab_anamnesi(base_font, section_font), "Dati Anamnestici")
        self.add_tab(self.tab_osservazione(base_font, section_font), "Osservazione")
        self.add_tab(self.tab_morfodinamica(base_font, section_font), "Valutazione Morfo-Dinamica")
        self.add_tab(self.tab_prassie_blf(base_font, bold_font, section_font), "Prassie BLF")
        self.add_tab(self.tab_bedside(base_font, section_font), "Bedside Swallowing Assessment")
        self.add_tab(self.tab_pasto(base_font, section_font), "Osservazione del Pasto")
        self.add_tab(self.tab_gets(base_font, section_font), "Autovalutazione (GETS)")
        self.add_tab(self.tab_conclusioni(base_font, section_font), "Conclusioni")

        if self.valutazione_precaricata:
            self.carica_valutazione(self.valutazione_precaricata)

        # Se la callback è None, la scheda è completata: disabilita tutti i controlli
        if self.callback_salva is None:
            self.disabilita_tutti_i_controlli()  

        self.setLayout(layout)


        # --- Filigrana logo Franca Dys in basso a destra ---
        self.filigrana = QLabel(self)
        logo_path = os.path.join(os.path.dirname(__file__), "logo_franca.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.filigrana.setPixmap(scaled)
            self.filigrana.setStyleSheet("opacity: 0.12;")  # 👈 trasparente al 12%
            self.filigrana.resize(scaled.width(), scaled.height())
            self.filigrana.move(
                self.width() - scaled.width() - 20,
                self.height() - scaled.height() - 20
            )
            self.filigrana.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.filigrana.setText("Franca Dys")
            self.filigrana.setStyleSheet(
                "color: rgba(0, 0, 0, 30%); font-size: 14pt;"
            )

        # --- Mantiene la filigrana in basso a destra anche se ridimensioni la finestra ---
        def _posiziona_filigrana():
            if self.filigrana.pixmap():
                self.filigrana.move(
                    self.width() - self.filigrana.width() - 20,
                    self.height() - self.filigrana.height() - 20
                )

# --- Mantiene la filigrana in basso a destra anche se ridimensioni la finestra ---
        def resizeEvent(event):
            _posiziona_filigrana()
            super(SchedeValutazioneWindow, self).resizeEvent(event)

        # Riassegna l'evento di resize
        self.resizeEvent = resizeEvent


    def add_tab(self, tab_widget, title):
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setSpacing(6)

        # --- Checkbox nascosta (manteniamo per compatibilità logica) ---
        cb = QCheckBox("Usa questa scheda")
        cb.setChecked(True)      # sempre attiva
        cb.setVisible(False)     # non visibile nella GUI
        # 🔹 Non la aggiungiamo al layout

        # --- Aggiungi il contenuto reale del tab ---
        wrapper_layout.addWidget(tab_widget)
        self.tab_widget.addTab(wrapper, title)

        # --- Manteniamo gli array allineati ai tab (serve per salvataggio) ---
        self.tab_checkboxes.append(cb)
        self.tab_forms.append(tab_widget)


    def _scheda_ha_dati(self, scheda: dict) -> bool:
        """
        Ritorna True se la scheda contiene davvero dati significativi.
        Caso speciale per 'Prassie BLF': se TUTTE le combo sono '' o '0', la consideriamo vuota.
        """
        if not isinstance(scheda, dict):
            return False

        nome = (scheda.get("nome") or "").strip()
        combos = scheda.get("combos", []) or []
        lines = scheda.get("lines", []) or []
        descr = scheda.get("descrizioni", {}) or {}
        note = (scheda.get("note") or "").strip()
        diagnosi = (scheda.get("diagnosi") or "").strip()

        # 🔹 Caso speciale: PRASSIE BLF
        if nome == "Prassie BLF":
            # Combo può essere: stringa ("0", "") oppure dict {"valore": int, "descrizione": str}
            def _is_zero_or_empty(x):
                if isinstance(x, dict):
                    try:
                        return int(x.get("valore", 0)) == 0
                    except Exception:
                        return True
                return str(x or "").strip() in ("", "0")

            if combos and all(_is_zero_or_empty(v) for v in combos):
                # se però ci sono altri campi significativi, allora considerala compilata
                if any((str(v or "").strip() for v in lines)) \
                or any((str(v or "").strip() for v in descr.values())) \
                or note or diagnosi:
                    return True
                return False

            
         # 🔹 Caso speciale: AUTOVALUTAZIONE (GETS)
        if nome == "Autovalutazione (GETS)":
            if combos and all((str(v or "").strip() in ("", "0")) for v in combos):
                if note:   # l’unico campo extra in GETS è la nota
                    return True
                return False    

        # Regola generale per TUTTE le altre schede
        if any((str(v or "").strip() for v in combos)):
            return True
        if any((str(v or "").strip() for v in lines)):
            return True
        if any((str(v or "").strip() for v in descr.values())):
            return True
        if note or diagnosi:
            return True

        return False




    def tab_anamnesi(self, base_font, section_font):
        tab = QWidget()
        tab.form = QFormLayout()
        tab.form.setVerticalSpacing(7)

                # === Campo Diagnosi (in cima) ===
        diagnosi_label = QLabel("Diagnosi:")
        diagnosi_label.setFont(section_font)  # un po' più grande come "Note"
        diagnosi_label.setStyleSheet("color: #232323; font-size: 15px; font-weight: bold;")
        tab.diagnosi_edit = QTextEdit()
        tab.diagnosi_edit.setFont(base_font)
        tab.diagnosi_edit.setFixedHeight(60)   # più alta delle combo
        tab.diagnosi_edit.setPlaceholderText("Inserisci la diagnosi...")
        tab.form.addRow(diagnosi_label, tab.diagnosi_edit)
        tab.diagnosi_edit.setMaximumWidth(400)  # 🔹 restringe la larghezza


        combo_items = {
            "Livello di vigilanza:": ["", "nessuna risposta", "risposta generalizzata", "risposta localizzata", "confuso-agitato", "confuso-inappropriato", "confuso-appropriato", "automatico-appropriato", "finalizzato-appropriato"],
            "Via di somministrazione alimenti:": ["", "os-non autonoma", "os-monitorata", "os-indipendente", "parenterale", "enterale-Sng", "enterale-Peg"],
            "Modificazioni recenti dello stato nutrizionale:": ["", "si", "no"],
            "Eventuali polmoniti pregresse:": ["", "si", "no"],
            "Modalità assunzione farmaci:": ["", "regolare", "intere in semisolido", "tritate in semisolido", "via enterale"],
            "Alimentazione attuale:": ["", "per os", "SNG", "PEG"],
            "Consistenze bevande assunte (IDDSI):": ["", "0-liquido", "1-leggermente denso", "2-moderatamente denso", "3-denso-sciropposo", "4-molto denso"],
            "Consistenze alimenti assunti (IDDSI):": ["", "3-sciropposo", "4-cremoso", "5-tritato fine&umido", "6-tenero spezzettao", "7-facilmente masticabile"]
        }

        tab.combos = []
        for label_text, values in combo_items.items():
            combo = QComboBox()
            combo.setFont(base_font)
            combo.setMaximumWidth(220)
            combo.addItems(values)
            combo.setCurrentIndex(0)
            tab.combos.append(combo)
            label = QLabel(label_text)
            label.setFont(base_font)
            label.setStyleSheet("color: #232323; font-size: 13px;")  # Uniforma stile
            tab.form.addRow(label, combo)

        # Note (label in grassetto)
        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("color: #232323; font-size: 15px; font-weight: bold;")  # Uniforma stile titolo note
        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(60)
        tab.note.setReadOnly(False)
        tab.form.addRow(note_label, tab.note)

        tab.setLayout(tab.form)
        return tab
       
        
    def tab_osservazione(self, base_font, section_font):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # --- Sezione domande ---
        form = QFormLayout()
        form.setVerticalSpacing(6)
        form.setContentsMargins(0, 0, 0, 0)

        combo_items = {
            "Livello igiene orale:": ["", "buono", "sufficiente", "scarso", "molto scarso"],
            "Residui alimentari orali:": ["", "si", "no"],
            "Cannula tracheale:": ["", "si", "no"],
            "Riflessi patologici:": ["", "presenti", "assenti"],
            "Controllo posturale:": ["", "fisiologico", "patologico"],
            "Scialorrea:": ["", "si", "no"],
            "Voce gorgogliante:": ["", "si", "no"],
            "Tosse volontaria:": ["", "efficace", "ipovalida", "assente"],
            "Dispnea:": ["", "si", "no"],
            "Deficit visivi:": ["", "si", "no"],
            "Deficit uditivi:": ["", "si", "no"],
            "Presenza di neglect:": ["", "si", "no"],
            "Presenza di disartria:": ["", "si", "no"]
        }

        with_descrizione = [
            "Residui alimentari orali:",
            "Cannula tracheale:",
            "Controllo posturale:",
            "Riflessi patologici:",
            "Scialorrea:",
            "Deficit visivi:",
            "Deficit uditivi:",
            "Presenza di neglect:",
            "Presenza di disartria:"
        ]

        tab.combos = []
        tab.descrizioni = {}

        for label_text, values in combo_items.items():
            lbl = QLabel(label_text)
            lbl.setFont(base_font)

            combo = QComboBox()
            combo.setFont(base_font)
            combo.setMaximumWidth(150)
            combo.addItems(values)
            combo.setCurrentIndex(0)
            tab.combos.append(combo)

            if label_text in with_descrizione:
                # Combo + campo descrizione sulla stessa riga
                hbox = QHBoxLayout()
                hbox.setSpacing(6)
                hbox.addWidget(combo)

                descrizione = QLineEdit()
                descrizione.setPlaceholderText("descrizione")
                descrizione.setFont(base_font)
                descrizione.setMinimumWidth(120)
                descrizione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                tab.descrizioni[label_text] = descrizione
                hbox.addWidget(descrizione)

                form.addRow(lbl, hbox)
            else:
                form.addRow(lbl, combo)

        main_layout.addLayout(form)

        # --- Sezione Note ---
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)

        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #232323;")

        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(100)

        grid.addWidget(note_label, 0, 0, 1, 2)
        grid.addWidget(tab.note,   1, 0, 1, 2)

        main_layout.addLayout(grid)
        main_layout.addStretch(1)

        tab.setLayout(main_layout)
        return tab


    def tab_morfodinamica(self, base_font, section_font):
        print(">>> DEBUG: funzione tab_morfodinamica eseguita!")
        from PyQt5.QtWidgets import QScrollArea, QSizePolicy

        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        tab.combos = []
        tab.descrizioni = {}

        def make_label(text):
            lbl = QLabel(text)
            lbl.setFont(base_font)
            lbl.setStyleSheet("font-size: 12px; font-weight: normal; min-width:120px;")
            return lbl

        def add_grid_rows(grid, fields):
            for row, (label, options, descr_key) in enumerate(fields):
                lbl = make_label(label)
                grid.addWidget(lbl, row, 0, alignment=Qt.AlignVCenter)

                combo = QComboBox()
                combo.addItems([""] + options)
                combo.setFont(base_font)
                combo.setMinimumWidth(110)
                combo.setMaximumWidth(140)
                combo.setStyleSheet("font-size: 12px; font-weight: normal;")
                tab.combos.append(combo)
                grid.addWidget(combo, row, 1, alignment=Qt.AlignVCenter)

                if descr_key:
                    descr = QLineEdit()
                    descr.setPlaceholderText("descrizione")
                    descr.setFont(base_font)
                    descr.setMinimumWidth(220)
                    descr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    descr.setStyleSheet("font-size: 12px; font-weight: normal;")
                    tab.descrizioni[descr_key] = descr
                    grid.addWidget(descr, row, 2, alignment=Qt.AlignVCenter)
                else:
                    spacer = QWidget()
                    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    grid.addWidget(spacer, row, 2)

        # --- Labbra ---
        labbra_box = QGroupBox("Labbra")
        labbra_box.setFont(section_font)
        labbra_box.setMaximumWidth(700)
        labbra_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        labbra_grid = QGridLayout()
        labbra_grid.setHorizontalSpacing(8)
        labbra_grid.setVerticalSpacing(6)
        labbra_fields = [
            ("Protrusione:", ["fisiologica", "ridotta", "deviata", "assente"], "Labbra protrusione descrizione"),
            ("Retrazione:", ["fisiologica", "ridotta", "deviata", "assente"], "Labbra retrazione descrizione"),
            ("Competenza:", ["buona", "sufficiente", "deficitaria"], None),
            ("Tono:", ["ipotono", "normale", "ipertono"], None),
            ("Deviazione a riposo:", ["destra", "sinistra", "nessuna"], "Labbra descrizione generale"),
        ]
        add_grid_rows(labbra_grid, labbra_fields)
        labbra_box.setLayout(labbra_grid)
        layout.addWidget(labbra_box)

        # --- Lingua ---
        lingua_box = QGroupBox("Lingua")
        lingua_box.setFont(section_font)
        lingua_box.setMaximumWidth(700)
        lingua_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        lingua_grid = QGridLayout()
        lingua_grid.setHorizontalSpacing(8)
        lingua_grid.setVerticalSpacing(6)
        lingua_fields = [
            ("Protrusione:", ["adeguata", "ridotta", "assente", "deviata"], "Lingua protrusione descrizione"),
            ("Retropulsione:", ["adeguata", "ridotta", "assente"], "Lingua retropulsione descrizione"),
            ("Lateralizzazione dx:", ["adeguata", "ridotta", "assente"], "Lingua lateralizzazione dx descrizione"),
            ("Lateralizzazione sx:", ["adeguata", "ridotta", "assente"], "Lingua lateralizzazione sx descrizione"),
            ("Trofismo:", ["adeguato", "alterato"], "Lingua trofismo descrizione"),
            ("Tono:", ["ipotono", "normale", "ipertono"], None),
            ("Forza:", ["adeguata", "ridotta", "assente"], "Lingua forza descrizione"),
            ("Velocità:", ["adeguata", "ridotta", "assente"], "Lingua velocità descrizione"),
            ("Ampiezza movimenti:", ["adeguata", "ridotta", "assente"], "Lingua ampiezza descrizione"),
            ("Deficit di lato:", ["nessuno", "destra", "sinistra"], None),
        ]
        add_grid_rows(lingua_grid, lingua_fields)
        lingua_box.setLayout(lingua_grid)
        layout.addWidget(lingua_box)

        # --- Palato duro ---
        palato_box = QGroupBox("Palato duro")
        palato_box.setFont(section_font)
        palato_box.setMaximumWidth(700)
        palato_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        palato_grid = QGridLayout()
        palato_grid.setHorizontalSpacing(8)
        palato_grid.setVerticalSpacing(6)
        palato_fields = [
            ("Aspetto:", ["normale", "alterato"], "Palato duro descrizione"),
        ]
        add_grid_rows(palato_grid, palato_fields)
        palato_box.setLayout(palato_grid)
        layout.addWidget(palato_box)

        # --- Velo del palato ---
        velo_box = QGroupBox("Velo del palato")
        velo_box.setFont(section_font)
        velo_box.setMaximumWidth(700)
        velo_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        velo_grid = QGridLayout()
        velo_grid.setHorizontalSpacing(8)
        velo_grid.setVerticalSpacing(6)
        velo_fields = [
            ("Tono:", ["ipotono", "normale", "ipertono"], None),
            ("Simmetria a riposo:", ["adeguata", "deviazione destra", "deviazione a sinistra"], None),
            ("Elevazione:", ["efficace", "simmetrica", "asimmetrica", "insufficiente"], "Velo elevazione descrizione"),
            ("Iperrinofonia:", ["presente", "assente"], None),
        ]
        add_grid_rows(velo_grid, velo_fields)
        velo_box.setLayout(velo_grid)
        layout.addWidget(velo_box)

        # --- Mandibola ---
        mandibola_box = QGroupBox("Mandibola")
        mandibola_box.setFont(section_font)
        mandibola_box.setMaximumWidth(700)
        mandibola_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        mandibola_grid = QGridLayout()
        mandibola_grid.setHorizontalSpacing(8)
        mandibola_grid.setVerticalSpacing(6)
        mandibola_fields = [
            ("Deviazione in apertura:", ["nessuna", "destra", "sinistra"], None),
            ("Deviazione a riposo:", ["nessuna", "destra", "sinistra"], None),
            ("Tono mm. masticatori:", ["normale", "ipotonici", "rigidità"], "Mandibola descrizione"),
        ]
        add_grid_rows(mandibola_grid, mandibola_fields)
        mandibola_box.setLayout(mandibola_grid)
        layout.addWidget(mandibola_box)

        # --- Elevazione Laringe ---
        laringe_box = QGroupBox("Elevazione Laringe")
        laringe_box.setFont(section_font)
        laringe_box.setMaximumWidth(700)
        laringe_box.setStyleSheet("QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }")
        laringe_grid = QGridLayout()
        laringe_grid.setHorizontalSpacing(8)
        laringe_grid.setVerticalSpacing(6)
        laringe_fields = [
            ("Valutazione:", ["fisiologica", "appena sufficiente", "ridotta", "assente", "ritardata"], "Elevazione laringe descrizione"),
        ]
        add_grid_rows(laringe_grid, laringe_fields)
        laringe_box.setLayout(laringe_grid)
        layout.addWidget(laringe_box)

                # --- Sensibilità buccale ---
        sensibilita_box = QGroupBox("Sensibilità buccale")
        sensibilita_box.setFont(section_font)
        sensibilita_box.setMaximumWidth(700)
        sensibilita_box.setStyleSheet(
            "QGroupBox { background:#f7f7f7; border-radius:8px; margin-top:8px; padding:8px 8px 4px 8px; }"
        )

        sensibilita_grid = QGridLayout()

        sensibilita_fields = [
            ("Sensibilità termica:", ["Normale", "Ridotta", "Assente"], "Sensibilità termica descrizione"),
            ("Sensibilità tattile:", ["Normale", "Ridotta", "Assente"], "Sensibilità tattile descrizione"),
            ("Sensibilità propriocettiva:", ["Normale", "Ridotta", "Assente"], "Sensibilità propriocettiva descrizione"),
        ]

        add_grid_rows(sensibilita_grid, sensibilita_fields)
        print("DEBUG Sensibilità combobox aggiunte:", len(tab.combos))
        sensibilita_box.setLayout(sensibilita_grid)
        layout.addWidget(sensibilita_box)


        # --- Note ---
        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("margin-bottom:2px; margin-top:5px;")
        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMinimumHeight(60)
        tab.note.setMaximumHeight(100)
        tab.note.setMaximumWidth(700)
        tab.note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(note_label)
        layout.addWidget(tab.note)

        layout.addStretch()
        scroll.setWidget(content)

        final_layout = QVBoxLayout(tab)
        final_layout.addWidget(scroll)
        tab.setLayout(final_layout)

        return tab

    def tab_prassie_blf(self, base_font, bold_font, section_font):
        tab = QWidget()
        tab.form = QFormLayout()
        tab.form.setVerticalSpacing(10)  # 🔹 un po' più spazio tra righe

        # --- Checkbox Eseguibili / Non Eseguibili ---
        check_layout = QHBoxLayout()
        tab.rb_eseguibili = QCheckBox("Eseguibili")
        tab.rb_non_eseguibili = QCheckBox("Non Eseguibili")
        tab.rb_eseguibili.setChecked(True)
        check_layout.addWidget(tab.rb_eseguibili)
        check_layout.addWidget(tab.rb_non_eseguibili)
        check_layout.addStretch()
        tab.form.addRow(QLabel(""), check_layout)

        # --- Lista aggiornata delle prassie ---
        prassie_list = PRASSIE_VOCI[:]  # usa la costante globale

        tab.combos = []
        tab.combo_by_voce = {}

        # --- ComboBox per ciascuna prassia ---
        for prassie in prassie_list:
            combo = QComboBox()

            # 🔹 Font leggermente ridotto per migliorare la leggibilità
            combo_font = QFont(base_font)
            combo_font.setPointSize(max(8, base_font.pointSize() + 1))
            combo.setFont(combo_font)

            # 🔹 Dimensioni fisse e padding interno (testo non troncato)
            combo.setFixedWidth(360)
            combo.setFixedHeight(36)  # 🔹 altezza aumentata per non tagliare testo
            combo.setStyleSheet("""
                QComboBox {
                    padding: 4px 6px;
                }
                QComboBox::drop-down {
                    width: 20px;
                }
            """)

            # 🔹 Inserisci item con testo completo (senza abbreviazioni)
            for val in (0, 1, 2):
                descr = PRASSIE_MAPPA_DESCRIZIONI[val]
                combo.addItem(descr, val)

            combo.setCurrentIndex(0)

            # 🔹 Aggiungi al form
            tab.combos.append(combo)
            tab.combo_by_voce[prassie] = combo
            tab.form.addRow(QLabel(prassie), combo)

        # --- Note ---
        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("margin-bottom:2px;")
        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(60)
        tab.note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tab.form.addRow(note_label, tab.note)

        tab.setLayout(tab.form)
        return tab


                # --- Eventi e logica ---



#        def abilita_combo(_=None):
            # Abilita se Eseguibili è selezionato (ed eventualmente forza l'esclusione)
 #           enabled = tab.rb_eseguibili.isChecked() and not tab.rb_non_eseguibili.isChecked()
  #          for combo in tab.combos:
   #             combo.setEnabled(enabled)
    #            if not enabled:
     #               # se non eseguibili, riportiamo le combo al valore vuoto ("")
     #               combo.setCurrentIndex(0)
           

        # Rendi i due checkbox mutuamente esclusivi
#        def on_eseguibili_changed(_):
#            if tab.rb_eseguibili.isChecked():
#                tab.rb_non_eseguibili.setChecked(False)
#            abilita_combo()
#
 #       def on_non_eseguibili_changed(_):
#            if tab.rb_non_eseguibili.isChecked():
#                tab.rb_eseguibili.setChecked(False)
 #           abilita_combo()

#        tab.rb_eseguibili.stateChanged.connect(on_eseguibili_changed)
#        tab.rb_non_eseguibili.stateChanged.connect(on_non_eseguibili_changed)

        # Setup iniziale
 #       abilita_combo()

#        return tab


    def tab_bedside(self, base_font, section_font):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(16, 10, 16, 10)
        main_layout.setSpacing(0)

        tab.combos = []  # <-- Colleziona tutte le combo qui!

        # --- Prime due righe con FormLayout per allineamento perfetto ---
        big_font = QFont(base_font)
        big_font.setPointSize(base_font.pointSize() + 2)
        big_font.setBold(False)
        form_top = QFormLayout()
        form_top.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_top.setFormAlignment(Qt.AlignLeft)
        form_top.setHorizontalSpacing(24)
        form_top.setVerticalSpacing(10)

        for key in ["Prova 5ml:", "Prova 60ml:"]:
            label = QLabel(key)
            label.setFont(big_font)
            combo = QComboBox()
            combo.addItems(["", "Superata", "Non superata"])
            combo.setMaximumWidth(180)
            combo.setMinimumWidth(120)
            combo.setFont(big_font)
            form_top.addRow(label, combo)
            tab.combos.append(combo)  # <-- Aggiungi ogni combo qui!

        main_layout.addLayout(form_top)

        # Spazio prima di OSSERVAZIONI
        main_layout.addSpacing(22)

        # --- OSSERVAZIONI ---
        osservazioni_label = QLabel("OSSERVAZIONI")
        osservazioni_font = QFont(section_font)
        osservazioni_font.setBold(True)
        osservazioni_label.setFont(osservazioni_font)
        osservazioni_label.setStyleSheet("margin-bottom:10px; letter-spacing:1px;")
        main_layout.addWidget(osservazioni_label)

        # --- OSSERVAZIONI FormLayout ---
        combo_items = {
            "Gag reflex:": ["assente", "ritardato", "efficace"],
            "Elevazione laringea:": ["assente", "ridotta", "ritardata",  "efficace"],
            "Tosse riflessa:": ["non pervenuta", "ipovalida", "efficace"],
            "Saturazione:": ["stabile", "calo 2%", "calo 5%", "calo >5%"],
            "Tentativi multipli:": ["si", "no"],
            "Voce:": ["inalterata", "gorgogliante", "velata", "strozzata"],
            "Segni di penetrazione/aspirazione:": ["si", "no"]
        }
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(8)

        for key, items in combo_items.items():
            label = QLabel(key)
            combo = QComboBox()
            combo.addItems([""] + items)
            combo.setMaximumWidth(180)
            combo.setMinimumWidth(120)
            form.addRow(label, combo)
            tab.combos.append(combo)  # <-- Aggiungi ogni combo qui!

        main_layout.addLayout(form)

        # Spazio sopra Note
        main_layout.addSpacing(12)

        # --- Note libera ---
        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("font-weight: bold;")
        note_edit = QTextEdit()
        note_edit.setFont(base_font)
        note_edit.setMinimumHeight(60)
        note_edit.setMaximumHeight(120)
        note_edit.setMaximumWidth(420)
        main_layout.addWidget(note_label)
        main_layout.addWidget(note_edit)

        main_layout.addStretch()
        return tab
    
    def tab_pasto(self, base_font, section_font):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        form = QFormLayout()
        form.setVerticalSpacing(4)   # riduce lo spazio verticale tra le righe
        form.setHorizontalSpacing(6) # riduce lo spazio tra label e campo

        combo_items = {
            "Livelli di vigilanza:": ["", "adeguati", "fluttuanti", "insufficienti"],
            "Consistenza(IDDSI):": ["", "3. Sciropposo", "4. Cremoso", "5. Tritato fine & umido", "6. Tenero/spezzettato", "7. Facilmente masticabile"],
            "Autonomo:": ["", "si", "no"],
            "Rifiuta cibo:": ["", "si", "no"],
            "Modalità assunzione:": ["", "sedia", "letto", "carrozzina"],
            "Edentule:": ["", "si", "no"],
            "Protesi dentaria:": ["", "si", "no"],
            "Masticazione:": ["", "efficace", "ridotta", "inefficace", "vorace"],
            "Deglutisce senza masticare": ["", "si", "no"],
            "Fuoriuscita di cibo dalla bocca:": ["", "si", "no"],
            "Fuoriuscita di cibo dal naso:": ["", "si", "no"],
            "Comparsa Tosse riflessa:": ["", "si", "no"],
            "Comparsa Tosse volontaria:": ["", "si", "no"],
            "Si distrae continuamente": ["", "si", "no"],
            "Escursione laringea:": ["", "funzionale", "ridotta", "minima", "multipla"],
            "Voce durante/dopo pasto:": ["", "normale", "afona", "umida", "gorgogliante", "strozzata", "soffiata", "velata", "rauca"],
            "Residui orali:": ["", "si", "no"],
            "Durata del pasto": ["", "< 20 min", "20-30 min", "> 30 min"],
            "Assume farmaci per os durante il PASTO": ["", "si", "no"]
        }

        tab.combos = []
        tab.desc_lineedits = []

        # Per allineare bene, calcoliamo la larghezza minima delle QLabel (la più corta possibile)
        label_width = max(QLabel(text).sizeHint().width() for text in combo_items.keys())
        label_width = min(label_width, 170)  # Limite massimo per evitare label troppo larghe

        for label_text, values in combo_items.items():
            combo = QComboBox()
            combo.setFont(base_font)
            combo.setMaximumWidth(180)
            combo.addItems(values)
            combo.setCurrentIndex(0)
            tab.combos.append(combo)

            desc_edit = QLineEdit()
            desc_edit.setFont(base_font)
            desc_edit.setPlaceholderText("Descrizione")
            desc_edit.setMinimumWidth(220)
            desc_edit.setMaximumWidth(360)
            tab.desc_lineedits.append(desc_edit)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)  # Vicinissimo tra combo e descrizione
            row_layout.addWidget(combo)
            row_layout.addWidget(desc_edit)

            label = QLabel(label_text)
            small_font = QFont(base_font)
            small_font.setPointSize(base_font.pointSize() - 2)  # diminuisce di 2 pt la dimensione, puoi anche provare -3
            label.setFont(small_font)
            label.setFixedWidth(label_width)  # TUTTE LE LABEL HANNO LA STESSA LARGHEZZA, così le tendine sono allineate e vicine
            form.addRow(label, row_widget)

        scroll_layout.addLayout(form)

        # Label Note ben visibile
        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 10px; margin-bottom: 2px; color: #232323;")

        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(60)

        scroll_layout.addWidget(note_label)
        scroll_layout.addWidget(tab.note)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        tab.setLayout(main_layout)
        return tab

    

    def tab_gets(self, base_font, section_font):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # --- Sezione domande (usa QFormLayout per label+combo) ---
        form = QFormLayout()
        form.setVerticalSpacing(6)
        form.setContentsMargins(0, 0, 0, 0)

        gets_domande = [
            "Le sembra di avere qualcosa bloccato in gola?", "Prova dolore?", "Prova fastidio/irritazione?",
            "Ha difficoltà a ingoiare?", "Si sente la gola chiusa?", "Si sente la gola gonfia?",
            "Le sembra di avere catarro?", "Non si sente la gola libera dopo aver deglutito?",
            "Ha bisogno di deglutire in continuazione?", "Quando deglutisce il cibo le rimane attaccato alla gola?",
            "Quanto tempo trascorre a pensare alla sua gola?", "Quanto la infastidisce ciò che prova in gola?"
        ]

        tab.combos = []
        for domanda in gets_domande:
            lbl = QLabel(domanda)
            lbl.setFont(base_font)

            combo = QComboBox()
            combo.setFont(base_font)
            combo.setMaximumWidth(60)
            combo.addItems([str(i) for i in range(8)])
            combo.setCurrentIndex(0)

            tab.combos.append(combo)
            form.addRow(lbl, combo)

        main_layout.addLayout(form)

        # --- Sezione Note (usa QGridLayout per label sopra + box sotto) ---
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)

        note_label = QLabel("Note:")
        note_label.setFont(section_font)
        note_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #232323;")

        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(100)

        grid.addWidget(note_label, 0, 0, 1, 2)
        grid.addWidget(tab.note,   1, 0, 1, 2)

        main_layout.addLayout(grid)
        main_layout.addStretch(1)  # tutto resta in alto, spazio vuoto va sotto

        tab.setLayout(main_layout)
        return tab
    
    def tab_conclusioni(self, base_font, section_font):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # --- Sezione combo ---
        form = QFormLayout()
        form.setVerticalSpacing(6)
        form.setContentsMargins(0, 0, 0, 0)

        combo_items = {
            "Disfagia:": ["", "SI", "NO"],
            "Scala DDOS:": ["", "1. disfagia severa", "2. moderata-severa", "3. moderata", 
                            "4. lieve-moderata", "5. lieve", "6. alcuni limiti funzionali", "7. normale"],
            "Consistenza liquidi suggerita:": ["", "nulla per os", "0. Liquido", "1. Leggermente denso",
                                            "2. Moderatamente denso", "3. Denso/Sciropposo", "4. Molto denso"],
            "Modalità assunzione liquidi suggerita:": ["", "nulla per os", "singoli sorsi lontano dai pasti",
                                                    "piccoli sorsi lontano dai pasti", "con ausili", "regolare"],
            "Consistenza alimenti suggerita:": ["", "nulla per os", "3. Sciropposo", "4. Cremoso",
                                                "5. Tritato fine & umido", "6. Tenero/spezzettato", "7. Facilmente masticabile"],
            "Modalità somministrazione farmaci:": ["", "regolare", "intere in semisolido", 
                                                "tritate in semisolido", "via enterale"],
            "Valutazione strumentale FEES/VFSS consigliata:": ["", "sì", "no"]
        }

        tab.combos = []
        for label_text, values in combo_items.items():
            lbl = QLabel(label_text)
            lbl.setFont(base_font)

            combo = QComboBox()
            combo.setFont(base_font)
            combo.setMaximumWidth(220)
            combo.addItems(values)
            combo.setCurrentIndex(0)

            tab.combos.append(combo)
            form.addRow(lbl, combo)


        main_layout.addLayout(form)

        # --- Sezione Conclusioni (ex Note) ---
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)

        conc_label = QLabel("Note Conclusive")
        conc_label.setFont(section_font)
        conc_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #232323;")

        tab.note = QTextEdit()
        tab.note.setFont(base_font)
        tab.note.setMaximumHeight(100)

        grid.addWidget(conc_label, 0, 0, 1, 2)
        grid.addWidget(tab.note,   1, 0, 1, 2)

        main_layout.addLayout(grid)
        main_layout.addStretch(1)

        tab.setLayout(main_layout)
        return tab

    def salva_valutazione(self):
        if self.valutazione_precaricata and "timestamp" in self.valutazione_precaricata:
            timestamp = self.valutazione_precaricata["timestamp"]
        else:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        valutazione = {
            "timestamp": timestamp,
            "schede": []
    }
    # ... resto della funzione ...
        for idx, cb in enumerate(self.tab_checkboxes):
            if cb.isChecked():
                scheda_nome = self.tab_widget.tabText(idx)
                tab = self.tab_forms[idx]
                scheda_dati = {"nome": scheda_nome}
                if hasattr(tab, "combos"):
                    if scheda_nome == "Prassie BLF":
                        combos_payload = []  # <-- qui la creiamo subito
                        for combo in tab.combos:
                            data = combo.currentData()
                            if data is None:
                                # combo creata con addItems => nessun userData: ricava dal testo "N - ..."
                                txt = combo.currentText()
                                try:
                                    val = int(str(txt).split("-")[0].strip())
                                except Exception:
                                    # estrema sicurezza: usa l'indice 0/1/2
                                    val = int(combo.currentIndex())
                            else:
                                val = int(data)

                            combos_payload.append({
                                "valore": val,
                                "descrizione": combo.currentText()
                            })

                        # se TUTTI i valori sono 0, consideriamo la scheda "vuota" e la saltiamo
                        if combos_payload and all(item["valore"] == 0 for item in combos_payload):
                            continue

                        scheda_dati["combos"] = combos_payload

                    else:
                        # altre schede: comportamento identico a prima
                        valori_combo = [combo.currentText() for combo in tab.combos]
                        scheda_dati["combos"] = valori_combo

                if hasattr(tab, "lines"):
                    scheda_dati["lines"] = [line.text() for line in tab.lines]
                # <<<<<<<<<<<<<<<< AGGIUNTA PER BOX DESCRIZIONE
                if hasattr(tab, "descrizioni") and tab.descrizioni:
                    scheda_dati["descrizioni"] = {key: descrizione.text() for key, descrizione in tab.descrizioni.items()}
                # <<<<<<<<<<<<<<<< FINE AGGIUNTA
                if hasattr(tab, "note"):
                    scheda_dati["note"] = tab.note.toPlainText()
                if hasattr(tab, "diagnosi_edit"):
                    scheda_dati["diagnosi"] = tab.diagnosi_edit.toPlainText()
                if hasattr(tab, "le_nota"):
                    scheda_dati["le_nota"] = tab.le_nota.text()
                if hasattr(tab, "le_conclusioni"):
                    scheda_dati["le_conclusioni"] = tab.le_conclusioni.text()
                if hasattr(tab, "punteggio_totale_label"):
                    scheda_dati["punteggio"] = tab.punteggio_totale_label.text()
                valutazione["schede"].append(scheda_dati)
        if not valutazione["schede"]:
            QMessageBox.warning(self, "Nessuna scheda selezionata", "Seleziona almeno una scheda da compilare!")
            return
        if self.callback_salva:
            # Passa completata=False
            self.callback_salva(valutazione, self.indice_valutazione, completata=False)
        QMessageBox.information(self, "Salvataggio", "Valutazione salvata con successo!")
        self.close()

    def salva_e_chiudi_valutazione(self):
        if self.valutazione_precaricata and "timestamp" in self.valutazione_precaricata:
            timestamp = self.valutazione_precaricata["timestamp"]
        else:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        valutazione = {
            "timestamp": timestamp,
            "schede": []
        }
        # ... resto della funzione (lascia invariato) ...
        for idx, cb in enumerate(self.tab_checkboxes):
            if cb.isChecked():
                scheda_nome = self.tab_widget.tabText(idx)
                tab = self.tab_forms[idx]
                scheda_dati = {"nome": scheda_nome}
                                
                if hasattr(tab, "combos"):
                    if scheda_nome == "Prassie BLF":
                        combos_payload = []
                        for combo in tab.combos:
                            data = combo.currentData()
                            if data is None:
                                txt = combo.currentText()
                                try:
                                    val = int(str(txt).split("-")[0].strip())
                                except Exception:
                                    val = int(combo.currentIndex())
                            else:
                                val = int(data)
                            combos_payload.append({
                                "valore": val,
                                "descrizione": combo.currentText()
                            })
                        if combos_payload and all(item["valore"] == 0 for item in combos_payload):
                            continue
                        scheda_dati["combos"] = combos_payload
                    else:
                        valori_combo = [combo.currentText() for combo in tab.combos]
                        scheda_dati["combos"] = valori_combo


                if hasattr(tab, "lines"):
                    scheda_dati["lines"] = [line.text() for line in tab.lines]
                # <<<<<<<<<<<<<<<< AGGIUNTA PER BOX DESCRIZIONE
                if hasattr(tab, "descrizioni") and tab.descrizioni:
                    scheda_dati["descrizioni"] = {key: descrizione.text() for key, descrizione in tab.descrizioni.items()}
                # <<<<<<<<<<<<<<<< FINE AGGIUNTA
                if hasattr(tab, "note"):
                    scheda_dati["note"] = tab.note.toPlainText()
                if hasattr(tab, "diagnosi_edit"):
                    scheda_dati["diagnosi"] = tab.diagnosi_edit.toPlainText()             
                if hasattr(tab, "le_nota"):
                    scheda_dati["le_nota"] = tab.le_nota.text()
                if hasattr(tab, "le_conclusioni"):
                    scheda_dati["le_conclusioni"] = tab.le_conclusioni.text()
                if hasattr(tab, "punteggio_totale_label"):
                    scheda_dati["punteggio"] = tab.punteggio_totale_label.text()
                valutazione["schede"].append(scheda_dati)
        if not valutazione["schede"]:
            QMessageBox.warning(self, "Nessuna scheda selezionata", "Seleziona almeno una scheda da compilare!")
            return
        if self.callback_salva:
            # Passa completata=True
            self.callback_salva(valutazione, self.indice_valutazione, completata=True)
        QMessageBox.information(self, "Salvataggio", "Valutazione chiusa e salvata con successo!")
        self.close()
        
    def carica_valutazione(self, valutazione):
        print("DEBUG: valutazione che arriva:", valutazione)
        if not isinstance(valutazione, dict):
            QMessageBox.warning(self, "Valutazione non valida", "Il dato selezionato non è una valutazione valida.")
            return
        
        #for cb in self.tab_checkboxes:
         #   cb.setChecked(False)
            
        for scheda in valutazione.get("schede", []):
            print("DEBUG: scheda trovata:", scheda.get("nome", ""))
            for tab_idx in range(self.tab_widget.count()):
                print("DEBUG: tab corrente:", self.tab_widget.tabText(tab_idx))
                if self.tab_widget.tabText(tab_idx) == scheda["nome"]:
                    print("DEBUG: Match trovato! Carico valori su tab:", scheda["nome"])
                    tab = self.tab_forms[tab_idx]
       
                    if hasattr(tab, "combos") and "combos" in scheda and tab.combos is not None:
                        if scheda["nome"] == "Prassie BLF":
                            for combo, value in zip(tab.combos, scheda["combos"]):
                                # --- Estrai il valore numerico dal dict o dalla stringa ---
                                if isinstance(value, dict):
                                    val = int(value.get("valore", 0))
                                else:
                                    try:
                                        val = int(str(value).split("-")[0].strip())
                                    except Exception:
                                        val = 0

                                # --- Cerca l'indice confrontando la parte numerica di ciascun item ---
                                idx = 0
                                for i in range(combo.count()):
                                    text_item = combo.itemText(i)
                                    try:
                                        num_item = int(str(text_item).split("-")[0].strip())
                                    except Exception:
                                        num_item = -1
                                    if num_item == val:
                                        idx = i
                                        break
                                combo.setCurrentIndex(idx)

                        else:
                            # tutte le altre schede come prima
                            for combo, value in zip(tab.combos, scheda["combos"]):
                                if isinstance(value, dict):
                                    text_val = value.get("descrizione", "")
                                else:
                                    text_val = str(value)
                                idx_value = combo.findText(text_val)
                                combo.setCurrentIndex(idx_value if idx_value >= 0 else 0)



                    if hasattr(tab, "lines") and "lines" in scheda and tab.lines is not None:
                        for line, value in zip(tab.lines, scheda["lines"]):
                            print(f"DEBUG: set line {value} in tab {scheda['nome']}")
                            line.setText(value)
                    # <<<<<<<<<<<<<<<< AGGIUNTA PER BOX DESCRIZIONE
                    if hasattr(tab, "descrizioni") and "descrizioni" in scheda and tab.descrizioni is not None:
                        for key, value in scheda["descrizioni"].items():
                            if key in tab.descrizioni:
                                print(f"DEBUG: set descrizione {value} per {key} in tab {scheda['nome']}")
                                tab.descrizioni[key].setText(value)
                    # <<<<<<<<<<<<<<<< FINE AGGIUNTA
                    if hasattr(tab, "note") and "note" in scheda and tab.note is not None:
                        print(f"DEBUG: set note in tab {scheda['nome']}")
                        tab.note.setPlainText(scheda["note"])
                    if hasattr(tab, "diagnosi_edit") and "diagnosi" in scheda:
                        print(f"DEBUG: set diagnosi in tab {scheda['nome']}")
                        tab.diagnosi_edit.setPlainText(scheda["diagnosi"])
                    if getattr(tab, "le_nota", None) is not None and "le_nota" in scheda:
                        print(f"DEBUG: set le_nota in tab {scheda['nome']}")
                        tab.le_nota.setText(scheda["le_nota"])
                    if getattr(tab, "le_conclusioni", None) is not None and "le_conclusioni" in scheda:
                        print(f"DEBUG: set le_conclusioni in tab {scheda['nome']}")
                        tab.le_conclusioni.setText(scheda["le_conclusioni"])
                    if getattr(tab, "punteggio_totale_label", None) is not None and "punteggio" in scheda:
                        print(f"DEBUG: set punteggio in tab {scheda['nome']}")
                        tab.punteggio_totale_label.setText(scheda["punteggio"])

        if self.callback_salva is None:
            by_name = {s.get("nome", ""): s for s in valutazione.get("schede", [])}
            for idx in range(self.tab_widget.count()):
                nome_tab = self.tab_widget.tabText(idx)
                cb = self.tab_checkboxes[idx]
                scheda = by_name.get(nome_tab)

                # 🔹 Prassie BLF: se tutte le combo sono vuote -> considerala non compilata
               # 🔹 Prassie BLF: se tutte le combo hanno valore 0 -> considerala non compilata
                if nome_tab == "Prassie BLF" and scheda:
                    combos = scheda.get("combos", [])

                    def _estrai_val(x):
                        if isinstance(x, dict):
                            try:
                                return int(x.get("valore", 0))
                            except Exception:
                                return 0
                        elif isinstance(x, str):
                            try:
                                return int(x.split("-")[0].strip())
                            except Exception:
                                return 0
                        else:
                            return 0

                    if combos and all(_estrai_val(v) == 0 for v in combos):
                        scheda = None


                cb.setChecked(bool(scheda) and self._scheda_ha_dati(scheda))


    def disabilita_tutti_i_controlli(self):
        self.salva_btn.setEnabled(False)
        self.salva_chiudi_btn.setEnabled(False)
        for tab in self.tab_forms:
            # ComboBox
            if hasattr(tab, "combos"):
                for combo in tab.combos:
                    combo.setEnabled(False)
            # QLineEdit
            if hasattr(tab, "lines"):
                for line in tab.lines:
                    line.setReadOnly(True)
            if hasattr(tab, "desc_lineedits"):
                for line in tab.desc_lineedits:
                    line.setReadOnly(True)
            if hasattr(tab, "descrizioni"):
                for desc in tab.descrizioni.values():
                    desc.setReadOnly(True)
            # QTextEdit
            if hasattr(tab, "note"):
                tab.note.setReadOnly(True)

            if hasattr(tab, "diagnosi_edit"):
                tab.diagnosi_edit.setReadOnly(True)
                tab.diagnosi_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f8f8;
                        border: 1px solid #cccccc;
                        color: #333333;
                    }
                """)     

            # Altri eventuali campi
            if hasattr(tab, "le_nota"):
                tab.le_nota.setReadOnly(True)
            if hasattr(tab, "le_conclusioni"):
                tab.le_conclusioni.setReadOnly(True)
            if hasattr(tab, "punteggio_totale_label"):
                tab.punteggio_totale_label.setEnabled(False)
            if hasattr(tab, "rb_eseguibili"):
                tab.rb_eseguibili.setEnabled(False)
            if hasattr(tab, "rb_non_eseguibili"):
                tab.rb_non_eseguibili.setEnabled(False)

    def scegli_logo(self):
        from PyQt5.QtWidgets import QFileDialog
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Seleziona logo", "", "Immagini (*.png *.jpg *.jpeg *.bmp)"
    )
        if percorso:
            self.logo_path_line.setText(percorso)
            self.no_logo_checkbox.setChecked(False)
            self.salva_logo_default(percorso)

    def rimuovi_logo(self):
        self.logo_path_line.clear()
        self.salva_logo_default("")

    def check_no_logo(self):
        if self.no_logo_checkbox.isChecked():
            self.logo_path_line.clear()
            self.salva_logo_default("")

    def salva_logo_default(self, path):
        import os
        os.makedirs("config", exist_ok=True)
        with open("config/logo_path.txt", "w", encoding="utf-8") as f:
            f.write(path.strip())

    def carica_logo_default(self):
        import os
        try:
            with open("config/logo_path.txt", "r", encoding="utf-8") as f:
                path = f.read().strip()
            if path and os.path.exists(path):
                self.logo_path_line.setText(path)
                self.no_logo_checkbox.setChecked(False)
            else:
                self.logo_path_line.clear()
        except Exception:
            self.logo_path_line.clear()

    def crea_report_completo(self):
        import os
        from datetime import datetime
        from PyQt5.QtWidgets import QMessageBox

        parent = getattr(self, "paziente_window", None)
        if parent is None:
            QMessageBox.warning(self, "Errore", "Apri la valutazione dalla Scheda Paziente per creare il report.")
            return

        valutazione = getattr(self, "valutazione_precaricata", None)
        if not valutazione:
            QMessageBox.warning(self, "Errore", "Nessun dato di valutazione disponibile.")
            return

        # date
        data_valutazione = valutazione.get("timestamp", "N/D")
        # 🔧 rendi sicura la data (niente / : o spazi)
        data_valutazione_safe = (
            data_valutazione.replace("/", "-").replace(":", "-").replace(" ", "_")
        )

        data_creazione = datetime.now().strftime("%Y-%m-%d %H:%M")
        timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M")

        nome_file = f"report_completo_{data_valutazione_safe}_{timestamp_file}.pdf"
        percorso = os.path.join(parent.cartella_report_completi, nome_file)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            from reportlab.lib.utils import simpleSplit
        except ImportError:
            QMessageBox.critical(self, "Reportlab mancante", "Installa con: pip install reportlab")
            return

        import textwrap
        def _wrap(text, font, size, width):
            try:
                return simpleSplit(text, font, size, width)
            except Exception:
                return textwrap.wrap(text, 80)

        # --- LISTE LABELS E DESCRIZIONI PER OGNI TAB ---
        # Puoi modificare/estendere a piacere!
        labels_anamnesi = [
            "Livello di vigilanza",
            "Via di somministrazione alimenti",
            "Modificazioni recenti dello stato nutrizionale",
            "Eventuali polmoniti pregresse",
            "Modalità assunzione farmaci",
            "Alimentazione attuale",
            "Consistenze bevande assunte (IDDSI)",
            "Consistenze alimenti assunti (IDDSI)"
        ]

        labels_osservazione = [
            "Livello igiene orale",
            "Residui alimentari orali",
            "Cannula tracheale",
            "Riflessi patologici",
            "Controllo posturale",
            "Scialorrea",
            "Voce gorgogliante",
            "Tosse volontaria",
            "Dispnea",
            "Deficit visivi",
            "Deficit uditivi",
            "Presenza di neglect",
            "Presenza di disartria"
        ]
        descr_osservazione = [
            "Residui alimentari orali:",
            "Cannula tracheale:",
            "Riflessi patologici:",
            "Scialorrea:",
            "Deficit visivi:",
            "Deficit uditivi:",
            "Presenza di neglect:",
            "Presenza di disartria:"
        ]

        labels_morfodinamica = [
            # Labbra
            "Protrusione (labbra)",
            "Retrazione (labbra)",
            "Competenza (labbra)",
            "Tono (labbra)",
            "Deviazione a riposo (labbra)",
            # Lingua
            "Protrusione (lingua)",
            "Retropulsione (lingua)",
            "Lateralizzazione dx (lingua)",
            "Lateralizzazione sx (lingua)",
            "Trofismo (lingua)",
            "Forza (lingua)",
            "Tono (lingua)",
            "Velocità (lingua)",
            "Ampiezza movimenti (lingua)",
            "Deficit di lato (lingua)",
            # Palato duro
            "Aspetto (palato duro)",
            # Velo del palato
            "Tono (velo del palato)",
            "Simmetria a riposo (velo del palato)",
            "Elevazione (velo del palato)",
            "Iperrinofonia (velo del palato)",
            # Mandibola
            "Deviazione in apertura (mandibola)",
            "Deviazione a riposo (mandibola)",
            "Tono mm. masticatori (mandibola)",
            # Elevazione Laringe
            "Valutazione (elevazione laringe)",
            # Sensibilità buccale
            "Sensibilità termica",
            "Sensibilità tattile",
            "Sensibilità propriocettiva"
        ]
        descr_morfodinamica = [
            "Labbra protrusione descrizione",
            "Labbra retrazione descrizione",
            "Labbra descrizione generale",
            "Lingua protrusione descrizione",
            "Lingua retropulsione descrizione",
            "Lingua lateralizzazione dx descrizione",
            "Lingua lateralizzazione sx descrizione",
            "Lingua trofismo descrizione",
            "Lingua forza descrizione", 
            "Lingua velocità descrizione",
            "Lingua ampiezza descrizione",
            "Palato duro descrizione",
            "Velo elevazione descrizione",
            "Mandibola descrizione",
            "Elevazione laringe descrizione",
            "Sensibilità termica descrizione",
            "Sensibilità tattile descrizione",
            "Sensibilità propriocettiva descrizione"
        ]

        labels_prassie = PRASSIE_VOCI[:]  

        labels_bedside = [
            "Prova 5 ml",
            "Prova 60 ml",
            "Gag reflex",
            "Elevazione laringea",
            "Tosse riflessa",
            "Saturazione",
            "Tentativi multipli",
            "Voce",
            "Segni di penetrazione e/o aspirazione"
]


        labels_pasto = [
            "Livelli di vigilanza", "Consistenza(IDDSI)", "Autonomo", "Rifiuta cibo", "Modalità assunzione",
            "Edentule", "Protesi dentaria", "Masticazione", "Deglutisce senza masticare",
            "Fuoriuscita di cibo dalla bocca", "Fuoriuscita di cibo dal naso", "Comparsa Tosse riflessa",
            "Comparsa Tosse volontaria", "Si distrae continuamente", "Escursione laringea",
            "Voce durante/dopo pasto", "Residui orali", "Durata del pasto", "Assume farmaci per os durante il PASTO"
        ]

        labels_gets = [
            "Le sembra di avere qualcosa bloccato in gola?", "Prova dolore?", "Prova fastidio/irritazione?",
            "Ha difficoltà a ingoiare?", "Si sente la gola chiusa?", "Si sente la gola gonfia?",
            "Le sembra di avere catarro?", "Non si sente la gola libera dopo aver deglutito?",
            "Ha bisogno di deglutire in continuazione?", "Quando deglutisce il cibo le rimane attaccato alla gola?",
            "Quanto tempo trascorre a pensare alla sua gola?", "Quanto la infastidisce ciò che prova in gola?"
        ]

        labels_conclusioni = [
            "Disfagia", "Scala DOSS", "Consistenza liquidi suggerita", "Modalità assunzione liquidi suggerita",
            "Consistenza alimenti suggerita", "Modalità somministrazione farmaci", "Valutazione strumentale FEES/VFSS consigliata"
        ]


        try:
            c = canvas.Canvas(percorso, pagesize=A4)
            width, height = A4
            margin = 2 * cm
            y = height - margin
# --- LOGO intestazione (se presente e non escluso) ---
            import os
            logo_path = self.logo_path_line.text().strip()
            nessun_logo = self.no_logo_checkbox.isChecked()
            if logo_path and not nessun_logo and os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, margin, y-2*cm, width=(4*cm*2/3), preserveAspectRatio=True, mask='auto')
                    y -= 2.5 * cm  # Spazio dopo il logo
                except Exception as e:
                    print(f"Errore caricamento logo: {e}")


            # intestazione
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin, y, f"Report completo - {parent.nome} {parent.cognome}")       
            y -= 1 * cm
            c.setFont("Helvetica", 10)
            c.drawString(margin, y, f"Data valutazione: {data_valutazione}")
            y -= 0.5 * cm
            c.drawString(margin, y, f"Data creazione: {data_creazione}")
            y -= 1 * cm

            # --- Funzione helper per voce in grassetto + valore normale ---
            def _draw_label_value(ypos, lbl, val, size=10, xoff=1*cm):
                """Stampa 'lbl:' in bold e 'val' in regular."""
                c.setFont("Helvetica-Bold", size)
                c.drawString(margin + xoff, ypos, f"{lbl}:")
                w = c.stringWidth(f"{lbl}:", "Helvetica-Bold", size)
                w = c.stringWidth(f"{lbl}:", "Helvetica-Bold", size)
                c.setFont("Helvetica", size)
                # Piccolo spazio più generoso tra etichetta e valore
                c.drawString(margin + xoff + w + 4, ypos, str(val))


            # --- CONTENUTO SCHEDE ---
    # Costruisci l’elenco di schede da stampare in base alle spunte
            schede_da_stampare = []
            by_name = {s.get("nome", ""): s for s in valutazione.get("schede", [])}

            for idx in range(self.tab_widget.count()):
                # considera solo le schede spuntate
                if not self.tab_checkboxes[idx].isChecked():
                    continue

                nome_tab = self.tab_widget.tabText(idx)
                s = by_name.get(nome_tab)
                if not s:
                    continue

                # 🔹 Se PRASSIE BLF e TUTTE le voci sono "0" o vuote → salta
                if nome_tab == "Prassie BLF":
                    vals = s.get("combos", [])

                    def _estrai_val(x):
                        # nuovo formato: {"valore": int, "descrizione": str}
                        if isinstance(x, dict):
                            try:
                                return int(x.get("valore", 0))
                            except Exception:
                                return 0
                        # vecchio formato: "1 - ..." o "1"
                        elif isinstance(x, str):
                            try:
                                return int(x.split("-")[0].strip())
                            except Exception:
                                return 0
                        else:
                            return 0

                    # salta solo se TUTTI i valori sono zero
                    if vals and all(_estrai_val(v) == 0 for v in vals):
                        continue


                # Altrimenti includi
                schede_da_stampare.append(s)


            # === COPILOT FINE: filtro schede selezionate ===

            for scheda in schede_da_stampare:
                if not isinstance(scheda, dict):
                    continue
                nome_scheda = scheda.get("nome", "Scheda")

                c.setFont("Helvetica-Bold", 12)
                c.drawString(margin, y, nome_scheda)
                y -= 0.7 * cm

                # --- ANAMNESI DEGLUTITORIA ---
                
                if nome_scheda == "Dati Anamnestici":
                    # 🔹 Aggiungi Diagnosi se presente
                    diagnosi = scheda.get("diagnosi", "")
                    if diagnosi and diagnosi.strip():
                        c.setFont("Helvetica-Oblique", 10)
                        c.drawString(margin + 1*cm, y, f"Diagnosi: {diagnosi}")
                        y -= 0.5 * cm

                    combos = scheda.get("combos", [])
                    for lbl, val in zip(labels_anamnesi, combos):
                        if val and val.strip():
                            _draw_label_value(y, lbl, val)
                            y -= 0.5 * cm
                    # --# 🔹 Controllo margine pagina
                        if y < 2 * cm:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y = height - 2 * cm
                        
                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm
                    y -= 0.2*cm

                # --- OSSERVAZIONE ---
                # --- OSSERVAZIONE ---
                elif nome_scheda == "Osservazione":
                    combos = scheda.get("combos", [])
                    descr = scheda.get("descrizioni", {})

                    for lbl, val in zip(labels_osservazione, combos):
                        val_clean = str(val).strip()
                        if not val_clean or val_clean.lower() in ["", "none", "seleziona", "n/d", "-", "--"]:
                            continue

                        # 🔹 Etichetta principale
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(margin + 0.5*cm, y, f"{lbl}:")
                        c.setFont("Helvetica", 10)
                        c.drawString(margin + 4.5*cm, y, val_clean)
                        y -= 0.45 * cm

                        # 🔹 Descrizione associata (se esiste)
                        for dk, dv in descr.items():
                            if not dv or not dv.strip():
                                continue
                            dk_norm = dk.lower().replace(":", "").replace("descrizione", "").strip()
                            lbl_norm = lbl.lower().replace(":", "").strip()
                            if dk_norm.startswith(lbl_norm.split()[0]) or lbl_norm.split()[0] in dk_norm:
                                dv_clean = dv.strip().replace("\u200b", "")
                                if dv_clean:
                                    c.setFont("Helvetica-Oblique", 9)
                                    c.drawString(margin + 1.3 * cm, y, dv_clean)
                                    y -= 0.35 * cm
                                break

                        # 🔹 Controllo multipagina
                        if y < 2 * cm:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y = height - 2 * cm

                    # --- Note finali ---
                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm

                    y -= 0.2*cm


                # --- VALUTAZIONE MORFO-DINAMICA ---
                # --- VALUTAZIONE MORFO-DINAMICA ---
                elif nome_scheda == "Valutazione Morfo-Dinamica":
                    combos = scheda.get("combos", [])
                    descr = scheda.get("descrizioni", {})

                    gruppi = {
                        "Labbra": [
                            "Protrusione (labbra)", "Retrazione (labbra)", "Competenza (labbra)",
                            "Tono (labbra)", "Deviazione a riposo (labbra)"
                        ],
                        "Lingua": [
                            "Protrusione (lingua)", "Retropulsione (lingua)", "Lateralizzazione dx (lingua)",
                            "Lateralizzazione sx (lingua)", "Trofismo (lingua)", "Forza (lingua)",
                            "Tono (lingua)", "Velocità (lingua)", "Ampiezza movimenti (lingua)",
                            "Deficit di lato (lingua)"
                        ],
                        "Palato duro": ["Aspetto (palato duro)"],
                        "Velo del palato": [
                            "Tono (velo del palato)", "Simmetria a riposo (velo del palato)",
                            "Elevazione (velo del palato)", "Iperrinofonia (velo del palato)"
                        ],
                        "Mandibola": [
                            "Deviazione in apertura (mandibola)", "Deviazione a riposo (mandibola)",
                            "Tono mm. masticatori (mandibola)"
                        ],
                        "Laringe": ["Valutazione (elevazione laringe)"],

                        "Sensibilità buccale": [
                            "Sensibilità termica",
                            "Sensibilità tattile",
                            "Sensibilità propriocettiva"
                        ],

                    }

                    # Mappa etichetta → valore
                    data_map = {lbl: val for lbl, val in zip(labels_morfodinamica, combos)}

                    for gruppo, sotto_voci in gruppi.items():
                        # 🔹 Verifica: almeno una sottovoce compilata?
                        gruppo_valido = False
                        for voce in sotto_voci:
                            val = str(data_map.get(voce, "")).replace("\u200b", "").strip().lower()
                            if val not in ["", "none", "seleziona", "n/d", "-", "--"]:
                                gruppo_valido = True
                                break
                        if not gruppo_valido:
                            continue  # salta il gruppo intero

                        # --- Stampa titolo gruppo ---
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(margin, y, gruppo)
                        y -= 0.45 * cm

                        for voce in sotto_voci:
                            val = data_map.get(voce, "")
                            val_clean = str(val).replace("\u200b", "").strip()

                            if not val_clean or val_clean.lower() in ["", "none", "seleziona", "n/d", "-", "--"]:
                                continue

                            # --- Sottovoce + valore ---
                            c.setFont("Helvetica", 10)
                            if voce.strip() == "Valutazione (elevazione laringe)":
                                label_pulita = "Elevazione"
                            else:
                                label_pulita = voce.split('(')[0].strip()

                            c.drawString(margin + 1.0 * cm, y, f"{label_pulita}: {val_clean}")


                            y -= 0.45 * cm

                            # --- Eventuale descrizione ---
                            for dk, dv in descr.items():
                                if not dv or not dv.strip():
                                    continue
                                dk_norm = dk.lower().replace("descrizione", "").replace("(", "").replace(")", "").strip()
                                voce_norm = voce.lower().replace("(", "").replace(")", "").strip()
                                if dk_norm.startswith(voce_norm.split()[0]) or voce_norm.split()[0] in dk_norm:
                                    dv_clean = dv.strip().replace("\u200b", "")
                                    if dv_clean:
                                        c.setFont("Helvetica-Oblique", 9)
                                        c.drawString(margin + 1.8 * cm, y, dv_clean)
                                        y -= 0.4 * cm
                                    break

                            # --- Controllo multipagina ---
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                        # Spazio tra gruppi
                        y -= 0.3 * cm

                    # --- Note finali ---
                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1 * cm, y, f"Note: {note}")
                        y -= 0.5 * cm

                    y -= 0.3 * cm





                # --- PRASSIE BLF ---
                elif nome_scheda == "Prassie BLF":
                    combos = scheda.get("combos", [])
                    for lbl, item in zip(labels_prassie, combos):
                        if isinstance(item, dict):
                            txt = item.get("descrizione", "")
                        else:
                            txt = str(item)
                        if txt and txt.strip():
                            _draw_label_value(y, lbl, txt)
                            y -= 0.5 * cm
                              # 🔹 Controllo multipagina (fondamentale)
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    punteggio = scheda.get("punteggio", "")
                    if punteggio:
                        c.setFont("Helvetica", 10)
                        c.drawString(margin + 1*cm, y, f"Punteggio: {punteggio}")
                        y -= 0.5 * cm
                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm
                    y -= 0.2*cm
                                # --- BEDSIDE ---
                elif "Bedside" in nome_scheda:
                    print("📄 BED", scheda)
                    combos = scheda.get("combos", [])
                    for lbl, val in zip(labels_bedside, combos):
                        if val and val.strip():
                            _draw_label_value(y, lbl, val)
                            y -= 0.5 * cm

                            # 🔹 Controllo margine pagina
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    # Descrizioni se presenti (opzionali)
                    descr = scheda.get("descrizioni", {})
                    for k, value in descr.items():
                        if value and value.strip():
                            c.setFont("Helvetica-Oblique", 9)
                            c.drawString(margin + 1.3*cm, y, f"{k}: {value}")
                            y -= 0.4*cm

                            # 🔹 Controllo multipagina
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm

                        if y < 2 * cm:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y = height - 2 * cm

                    y -= 0.2*cm

                # --- OSSERVAZIONE DEL PASTO ---
                elif nome_scheda == "Osservazione del Pasto":
                    combos = scheda.get("combos", [])
                    for lbl, val in zip(labels_pasto, combos):
                        if val and val.strip():
                            _draw_label_value(y, lbl, val)
                            y -= 0.5 * cm
                            # 🔹 Controllo margine pagina
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    # Descrizioni aggiuntive se presenti (non tutte le tab hanno)
                    desc_lineedits = scheda.get("lines", [])
                    for idx, val in enumerate(desc_lineedits):
                        if val and val.strip():
                            c.setFont("Helvetica-Oblique", 9)
                            try:
                                k = labels_pasto[idx]
                            except IndexError:
                                k = "Campo aggiuntivo"
                            c.drawString(margin + 1.3*cm, y, f"{k}: {val}")
                            y -= 0.4*cm
                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm
                    y -= 0.2*cm

                # --- AUTOVALUTAZIONE (GETS) ---
                elif nome_scheda == "Autovalutazione (GETS)":
                    combos = scheda.get("combos", [])
                    for lbl, val in zip(labels_gets, combos):
                        if val and val.strip() and val != "0":
                            _draw_label_value(y, lbl, val)
                            y -= 0.5 * cm
                            # 🔹 Controllo margine pagina
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    note = scheda.get("note", "")
                    if note and note.strip():
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1*cm, y, f"Note: {note}")
                        y -= 0.5*cm
                    y -= 0.2*cm

                # --- CONCLUSIONI ---
                elif nome_scheda == "Conclusioni":
                    combos = scheda.get("combos", [])
                    for lbl, val in zip(labels_conclusioni, combos):
                        if val and val.strip():
                            _draw_label_value(y, lbl, val)
                            y -= 0.5 * cm   # 👈 aggiungi sempre questo per separare le righe
                            # 🔹 Controllo margine pagina
                            if y < 2 * cm:
                                c.showPage()
                                c.setFont("Helvetica", 10)
                                y = height - 2 * cm

                    note = scheda.get("note", "")
                    if note and note.strip():
                        y -= 0.3 * cm      # 👈 spazio prima della nota
                        c.setFont("Helvetica", 9)
                        c.drawString(margin + 1 * cm, y, f"Conclusioni: {note}")
                        y -= 0.5 * cm      # 👈 spazio dopo la nota

                    y -= 0.5 * cm          # 👈 spazio finale di chiusura sezione


                # --- ALTRO ---
                #else:
                    # Se inserirai altre tab in futuro
                 #   for key in ("combos", "lines", "descrizioni", "note", "le_nota", "le_conclusioni", "punteggio"):
                 #       val = scheda.get(key)
                  #      if val not in ("", None, []):
                   #         testo = f"{key}: {val}"
                    #        righe = _wrap(testo, "Helvetica", 10, width - 2*margin)
                     #       for r in righe:
                      #          c.drawString(margin + 1 * cm, y, r)
                       #         y -= 0.5 * cm
                     #   y -= 0.2 * cm

            #    y -= 0.5 * cm

            # firma logopedista
            c.setFont("Helvetica", 11)
            y -= 1.5 * cm
            c.drawString(margin, y, "Logopedista: _______________________________")
           
            # --- Footer con firma del programma ---
            c.setFont("Helvetica-Oblique", 8)
            c.setFillGray(0.5)  # testo grigio tenue
            footer_text = "Generato con Franca Dys © 2026"
            text_width = c.stringWidth(footer_text, "Helvetica-Oblique", 8)
            c.drawString(width - text_width - margin, margin / 2, footer_text)
            c.setFillGray(0)  # ripristina colore testo normale

            c.showPage()
            c.save()

        except Exception as e:
            QMessageBox.critical(self, "Errore PDF", str(e))
            return

        parent.aggiungi_report_completo(data_valutazione_safe)
        QMessageBox.information(self, "Report completo", f"Creato il file:\n{percorso}")
        parent._apri_file(percorso)


    def crea_report_indici(self):
        import os, json
        from datetime import datetime
        from PyQt5.QtWidgets import QMessageBox

        parent = getattr(self, "paziente_window", None)
        if parent is None:
            QMessageBox.warning(self, "Errore", "Apri la valutazione dalla Scheda Paziente per creare il report.")
            return

        valutazione = getattr(self, "valutazione_precaricata", None)
        if not valutazione:
            QMessageBox.warning(self, "Errore", "Nessun dato di valutazione disponibile.")
            return

        # date
        data_valutazione = valutazione.get("timestamp", "N/D")
        data_valutazione_safe = (
            data_valutazione.replace("/", "-").replace(":", "-").replace(" ", "_")
        )
        data_creazione = datetime.now().strftime("%Y-%m-%d %H:%M")
        timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M")

        # percorso cartella paziente
        nome_file = f"report_indici_{data_valutazione_safe}_{timestamp_file}.pdf"
        percorso = os.path.join(parent.cartella_report_indici, nome_file)

        # carica regole critiche
        try:
            from config import res_path
            with open(res_path("config", "indici_rules.json"), "r", encoding="utf-8") as f:

                rules = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare le regole degli indici critici:\n{e}")
            return

        # importa reportlab
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
        except ImportError:
            QMessageBox.critical(self, "Reportlab mancante", "Installa con: pip install reportlab")
            return

        # funzione che valuta criticità in base al JSON
        # Copia questa funzione DENTRO crea_report_indici
        def estrai_critici(valutazione, rules):
    # === 1) Mappe tab/etichette ===
            tab_map = {
                "Dati Anamnestici": "ANAMNESI",
                "Osservazione": "OSSERVAZIONE",
                "Valutazione Morfo-Dinamica": "MORFODINAMICA",
                "Prassie BLF": "PRASSIE BLF",
                "Bedside Swallowing Assessment": "BEDSIDE",
                "Osservazione del Pasto": "OSSERVAZIONE PASTO",
                "Autovalutazione (GETS)": "AUTOVALUTAZIONE (GETS)",
                "Conclusioni": "CONCLUSIONI",
            }

            labels_map = {
                # ANAMNESI
                "ANAMNESI": [
                    "Livello di vigilanza:",
                    "Via di somministrazione alimenti:",
                    "Modificazioni recenti dello stato nutrizionale:",
                    "Eventuali polmoniti pregresse:",
                    "Modalità assunzione farmaci:",
                    "Alimentazione attuale:",
                    "Consistenze bevande assunte (IDDSI):",
                    "Consistenze alimenti assunti (IDDSI):",
                ],
                # OSSERVAZIONE
                "OSSERVAZIONE": [
                    "Livello igiene orale:",
                    "Residui alimentari orali:",
                    "Cannula tracheale:",
                    "Riflessi patologici:",
                    "Controllo posturale:",
                    "Scialorrea:",
                    "Voce gorgogliante:",
                    "Tosse volontaria:",
                    "Dispnea:",
                    "Deficit visivi:",
                    "Deficit uditivi:",
                    "Presenza di neglect:",
                    "Presenza di disartria:",
                ],
                # BEDSIDE
                "BEDSIDE": [
                    "Prova 5ml:",
                    "Prova 60ml:",
                    "Gag reflex:",
                    "Elevazione laringea:",
                    "Tosse riflessa:",
                    "Saturazione:",
                    "Tentativi multipli:",
                    "Voce:",
                    "Segni di penetrazione/aspirazione:",
                ],
                # OSSERVAZIONE PASTO
                "OSSERVAZIONE PASTO": [
                    "Livelli di vigilanza:",
                    "Consistenza(IDDSI):",
                    "Autonomo:",
                    "Rifiuta cibo:",
                    "Modalità assunzione:",
                    "Edentule:",
                    "Protesi dentaria:",
                    "Masticazione:",
                    "Deglutisce senza masticare",
                    "Fuoriuscita di cibo dalla bocca:",
                    "Fuoriuscita di cibo dal naso:",
                    "Comparsa Tosse riflessa:",
                    "Comparsa Tosse volontaria:",
                    "Si distrae continuamente",
                    "Escursione laringea:",
                    "Voce durante/dopo pasto:",
                    "Residui orali:",
                    "Durata del pasto",
                    "Assume farmaci per os durante il PASTO",
                ],
                # GETS
                "AUTOVALUTAZIONE (GETS)": [
                    "Le sembra di avere qualcosa bloccato in gola?",
                    "Prova dolore?",
                    "Prova fastidio/irritazione?",
                    "Ha difficoltà a ingoiare?",
                    "Si sente la gola chiusa?",
                    "Si sente la gola gonfia?",
                    "Le sembra di avere catarro?",
                    "Non si sente la gola libera dopo aver deglutito?",
                    "Ha bisogno di deglutire in continuazione?",
                    "Quando deglutisce il cibo le rimane attaccato alla gola?",
                    "Quanto tempo trascorre a pensare alla sua gola?",
                    "Quanto la infastidisce ciò che prova in gola?",
                ],
                # CONCLUSIONI
                "CONCLUSIONI": [
                    "Disfagia:",
                    "Scala DDOS:",
                    "Consistenza liquidi suggerita:",
                    "Modalità assunzione liquidi suggerita:",
                    "Consistenza alimenti suggerita:",
                    "Modalità somministrazione farmaci:",
                    "Valutazione strumentale FEES/VFSS consigliata:",
                ],
            }

            # === 2) Helpers ===
            def norm(s: str) -> str:
                return str(s or "").lower().replace(":", "").replace("  ", " ").strip()

            def estrai_numero_o_testo(v):
                """
                Accetta valori stringa o dict {"valore": int, "descrizione": "..."}.
                Ritorna (val_num, val_descr) e una forma pulita 'val_clean' per il matching con le regole.
                """
                if isinstance(v, dict):
                    val_num = int(v.get("valore", 0))
                    val_descr = str(v.get("descrizione", "")).strip()
                else:
                    try:
                        val_num = int(str(v).split("-")[0].strip())
                    except Exception:
                        val_num = 0
                    val_descr = str(v or "").strip()

                # Se la descrizione inizia con "0 -", "1 -", "2 -", estrai solo il numero
                if val_descr and val_descr[0].isdigit():
                    val_clean = val_descr.split("-")[0].strip().lower()
                else:
                    val_clean = str(val_num).strip().lower()

                return val_num, val_descr, val_clean

            trovati = []

            # === 3) Ciclo schede ===
            for scheda in valutazione.get("schede", []):
                nome_ui = str(scheda.get("nome", "")).strip()
                nome_json = tab_map.get(nome_ui)
                if not nome_json or nome_json not in rules:
                    continue

                # --- 3A) PRASSIE BLF (speciale) ---
                if nome_json == "PRASSIE BLF":
                    # Ordine/nomi esatti come in GUI/JSON
                    labels_prassie = [
                        "Protrusione lingua",
                        "Lingua in avanti e indietro",
                        "Lingua a destra",
                        "Lingua a sinistra",
                        "Schioccare la lingua",
                        "Sorridere",
                        "Mandare un bacio",
                        "Schema alternato bacio-sorriso",
                        "Gonfiare le guance",
                        "Aprire e chiudere la bocca",
                        "Spostare il labbro a sinistra",
                        "Spostare il labbro a destra",
                        "Soffiare",
                        "Fischiare",
                        "Tossire",
                    ]
                    combos_raw = scheda.get("combos", [])
                    # Normalizza a '0'/'1'/'2'
                    def _estrai_val(x):
                        if isinstance(x, dict):
                            return str(x.get("valore", "0"))
                        s = str(x or "").strip()
                        return s[0] if s and s[0] in ("0", "1", "2") else "0"

                    combos = [_estrai_val(v) for v in combos_raw]
                    regole_scheda = rules[nome_json]

                    for label, val in zip(labels_prassie, combos):
                        if not val or label not in regole_scheda:
                            continue
                        for atteso, regola in regole_scheda[label].items():
                            if str(val).strip() == str(atteso).strip():
                                if str(regola.get("criticita", "")).lower() == "critico":
                                    trovati.append({
                                        "scheda": nome_json,
                                        "campo": label,
                                        "voce": val,
                                        "gravita": regola.get("gravita", ""),
                                        "messaggio": regola.get("messaggio", f"{label}: risposta {val}")
                                    })
                                break
                    continue  # passa alla prossima scheda

                # --- 3B) MORFODINAMICA (speciale, mappa indice -> gruppo/voce) ---
                if nome_json == "MORFODINAMICA":
                    combos = scheda.get("combos", [])
                    reg = rules[nome_json]

                    # indice GUI -> (Gruppo nel JSON, Voce nel JSON)
                    morfo_index_map = {
                        # Labbra (0..4)
                        0: ("Labbra", "Protrusione"),
                        1: ("Labbra", "Retrazione"),
                        2: ("Labbra", "Competenza"),
                        3: ("Labbra", "Tono"),
                        4: ("Labbra", "Deviazione a riposo"),
                        # Lingua (5..14)
                        5: ("Lingua", "Protrusione"),
                        6: ("Lingua", "Retropulsione"),
                        7: ("Lingua", "Lateralizzazione dx"),
                        8: ("Lingua", "Lateralizzazione sx"),
                        9: ("Lingua", "Trofismo"),
                        10: ("Lingua", "Tono"),
                        11: ("Lingua", "Forza"),
                        12: ("Lingua", "Velocità"),
                        13: ("Lingua", "Ampiezza movimenti"),
                        14: ("Lingua", "Deficit di lato"),
                        # Palato duro (15)
                        15: ("Palato duro", "Aspetto"),
                        # Velo del palato (16..19)
                        16: ("Velo del palato", "Tono"),
                        17: ("Velo del palato", "Simmetria a riposo"),
                        18: ("Velo del palato", "Elevazione"),
                        19: ("Velo del palato", "Iperrinofonia"),
                        # Mandibola (20..22)
                        20: ("Mandibola", "Deviazione in apertura"),
                        21: ("Mandibola", "Deviazione a riposo"),
                        22: ("Mandibola", "Tono mm masticatori"),
                        # Elevazione laringe (23) – nel JSON è “Elevazione laringe”
                        23: ("Elevazione laringe", None),
                        # Sensibilità buccale (24..26)
                        24: ("Sensibilità buccale", "Sensibilità termica"),
                        25: ("Sensibilità buccale", "Sensibilità tattile"),
                        26: ("Sensibilità buccale", "Sensibilità propriocettiva"),
                    }

                    for idx, valore in enumerate(combos):
                        if idx not in morfo_index_map:
                            continue
                        gruppo, voce = morfo_index_map[idx]
                        # estrai valore
                        _, _, val_clean = estrai_numero_o_testo(valore)  # per morfo usiamo testo puro (non numeri)
                        if not isinstance(valore, dict):
                            val_txt = str(valore or "").strip()
                        else:
                            val_txt = str(valore.get("descrizione", "") or "").strip()
                        if not val_txt:
                            continue

                        # Group “Elevazione laringe” è piatto (nessuna sotto-voce nel JSON)
                        if voce is None:
                            gkey = next((k for k in reg.keys() if norm(k) == norm(gruppo)), None)
                            if not gkey or not isinstance(reg[gkey], dict):
                                continue
                            for atteso, regola in reg[gkey].items():
                                if norm(val_txt) == norm(atteso):
                                    if str(regola.get("criticita", "")).lower() == "critico":
                                        trovati.append({
                                            "scheda": nome_json,
                                            "campo": "Elevazione laringe",
                                            "voce": val_txt,
                                            "gravita": regola.get("gravita", ""),
                                            "messaggio": regola.get("messaggio", val_txt),
                                        })
                                    break
                            continue

                        # Gruppi standard (Labbra, Lingua, …)
                        gkey = next((k for k in reg.keys() if norm(k) == norm(gruppo)), None)
                        if not gkey or not isinstance(reg[gkey], dict):
                            continue
                        vkey = next((k for k in reg[gkey].keys() if norm(k) == norm(voce)), None)
                        if not vkey:
                            continue

                        for atteso, regola in reg[gkey][vkey].items():
                            if norm(val_txt) == norm(atteso):
                                if str(regola.get("criticita", "")).lower() == "critico":
                                    trovati.append({
                                        "scheda": nome_json,
                                        "campo": f"{gkey} → {vkey}",
                                        "voce": val_txt,
                                        "gravita": regola.get("gravita", ""),
                                        "messaggio": regola.get("messaggio", val_txt),
                                    })
                                break
                    continue  # passa alla prossima scheda

                # --- 3C) Tutte le ALTRE schede (generico) ---
                labels = labels_map.get(nome_json, [])
                combos = scheda.get("combos", [])
                regole_scheda = rules.get(nome_json, {})

                for idx, campo in enumerate(labels):
                    if idx >= len(combos):
                        continue
                    valore = combos[idx]
                    if valore in (None, "", "--", "-", "n/d"):
                        continue

                    # normalizza campo e trova la chiave più vicina nel JSON (ignora i “:” finali)
                    found_key = next(
                        (k for k in regole_scheda.keys() if norm(k) == norm(campo)),
                        None
                    )
                    if not found_key:
                        # prova varianti (campo senza “:”, con “:”, ecc.)
                        for var in (campo, campo + ":", str(campo).replace(":", "")):
                            found_key = next((k for k in regole_scheda.keys() if norm(k) == norm(var)), None)
                            if found_key:
                                break
                    if not found_key:
                        continue

                    voci_rules = regole_scheda[found_key]
                    _, val_descr, val_clean = estrai_numero_o_testo(valore)

                    for voce_attesa, regola in voci_rules.items():
                        if norm(val_descr) == norm(voce_attesa) or val_clean == norm(voce_attesa):
                            if str(regola.get("criticita", "")).lower() == "critico":
                                trovati.append({
                                    "scheda": nome_json,
                                    "campo": campo.rstrip(":"),
                                    "voce": val_descr or val_clean,
                                    "gravita": regola.get("gravita", ""),
                                    "messaggio": regola.get("messaggio", val_descr or val_clean),
                                })
                            break

            return trovati



        # estrai criticità
        critici = estrai_critici(valutazione, rules)

        # genera PDF
        try:
            c = canvas.Canvas(percorso, pagesize=A4)
            width, height = A4
            margin = 2 * cm
            y = height - margin

            # --- LOGO intestazione (se presente e non escluso) ---
            logo_path = self.logo_path_line.text().strip()
            nessun_logo = self.no_logo_checkbox.isChecked()
            if logo_path and not nessun_logo and os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, margin, y-2*cm, width=(4*cm*2/3), preserveAspectRatio=True, mask='auto')
                    y -= 2.5 * cm  # Spazio dopo il logo
                except Exception as e:
                    print(f"Errore caricamento logo: {e}")

            # intestazione
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin, y, f"Report Indici Critici - {parent.nome} {parent.cognome}")
            y -= 1 * cm
            c.setFont("Helvetica", 10)
            c.drawString(margin, y, f"Data valutazione: {data_valutazione}")
            y -= 0.5 * cm
            c.drawString(margin, y, f"Data creazione: {data_creazione}")
            y -= 1 * cm

            from collections import defaultdict

            if critici:
                # Raggruppa criticità per sezione/scheda
                sezioni = defaultdict(list)
                for item in critici:
                    sezioni[item["scheda"]].append(item)

                for nome_sezione, items in sezioni.items():
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(margin, y, nome_sezione)
                    y -= 0.6 * cm
                    for item in items:
                        campo = item.get("campo", "")
                        messaggio = item.get("messaggio", "")
                        gravita = item.get("gravita", "")

                        # campo in grassetto
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(margin + 1*cm, y, campo + ":")
                        w = c.stringWidth(campo + ":", "Helvetica-Bold", 10)

                        # valore e gravità in regolare
                        c.setFont("Helvetica", 10)
                        testo_val = messaggio
                        if gravita:
                            testo_val += f"  (Gravità: {gravita})"

                        c.drawString(margin + 1*cm + w + 8, y, testo_val)
                        y -= 0.8 * cm


                    y -= 0.3 * cm  # Spazio extra tra sezioni
            else:
                c.setFont("Helvetica", 11)
                c.drawString(margin, y, "Nessuna criticità rilevata.")
                y -= 1 * cm

            # firma logopedista
            y -= 2 * cm
            c.setFont("Helvetica", 11)
            c.drawString(margin, y, "Logopedista: _______________________________")

            # --- Footer con firma del programma ---
            c.setFont("Helvetica-Oblique", 8)
            c.setFillGray(0.5)  # testo grigio tenue
            footer_text = "Generato con Franca Dys © 2026"
            text_width = c.stringWidth(footer_text, "Helvetica-Oblique", 8)
            c.drawString(width - text_width - margin, margin / 2, footer_text)
            c.setFillGray(0)  # ripristina colore testo normale

            c.showPage()
            c.save()

        except Exception as e:
            QMessageBox.critical(self, "Errore PDF", str(e))
            return

            # aggiorna lista in scheda paziente
        try:
            parent.aggiungi_report_indici(data_valutazione_safe)
        except AttributeError:
            # se non esiste ancora la funzione, usiamo fallback
            parent.report_indici.append(data_valutazione_safe)
            parent.lista_report_indici.addItem(f"⚠️ {data_valutazione_safe}")
            parent.salva_su_file()

        QMessageBox.information(self, "Report Indici Critici", f"Creato il file:\n{percorso}")

        # apri subito il PDF
        try:
            parent._apri_file(percorso)
        except Exception:
            pass

