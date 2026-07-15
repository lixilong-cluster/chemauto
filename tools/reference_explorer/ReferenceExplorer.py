
# ver 2.* is created by PyQt5 


'''
    ver 2.1 stable version
    
    ver 2.2
        Added:
            complete download function
        Fixed:
            DeprecationWarning:sipPyTypeDict() is deprecated, the extension module should use sipPyTypeDictRef() instead
            InsecureRequestWarning of SSL  
    ver 2.2.2 <- ver 2.2
        Added:
            add save dialog for download button
    ver 2.3  <- ver 2.2.2
        Added 
            export ciw file function
            export ris file function

    ver 2.3.2
        Added
            add Clean button
            change the position of Clean button and Search button.
    ver 2.3.3
        Added 
            add search history text  box
            add current search result text box
    ver 2.3.4
        Added
            set font siz 12.
    ver 2.3.5
        Added
            Place the input box below the parameter label
            Remove unnecessary stroll bar
    ver 2.3.6
        Added
            change the layout
    ver 2.3.6.1
        set text font size 10.
        
    ver 2.3.7.1
        set style using stylesheet
    ver 2.3.7.2
        set color configuration
    ver 2.3.8 -- stable
        complete clean and save functions for search history
        add ico but don't installer
    ver 2.3.9 -- stable
        add menu bar
        add File Save Print Help munu
        add copyright announcement
    ver 2.3.9.1
        define reference search history file to be .rsh file
        default save file .rsh file
    ver 2.3.9.2
        fixed search errror exists both DOI and other params
    ver 2.3.9.2 (beautified)
        modernized UI with polished styling
        all functionality remains unchanged
    ver 3.0
        increased font sizes for labels, inputs, and buttons (+2)
        renamed Download -> Download PDF, Export -> Export Citation
        download PDF auto-saves to last-used directory, no confirmation dialog
        auto-opens the save directory after download
'''

import sys
import os
import re
import time
import json
import platform
import subprocess
import urllib.parse
import urllib.request
import urllib.error
import urllib3
import requests
import webbrowser
import xml.etree.ElementTree as ET
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QLinearGradient
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QMenu, QAction, QMessageBox, QFileDialog, QGraphicsDropShadowEffect, QGroupBox,
                             QSplitter, QFrame, QSizePolicy)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def resource_path(name):
    """Return a bundled resource path in source and PyInstaller builds."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def _configure_portable_playwright():
    """Point Playwright to the Chromium folder shipped beside the EXE."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(base, "pw-browsers")
    if os.path.isdir(bundled):
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", bundled)


_configure_portable_playwright()

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

# ─── Global Stylesheet ──────────────────────────────────────────────────────────
STYLESHEET = """

/* ── Main Window ── */
QMainWindow {
    background-color: #F0F4F8;
}

/* ── Menu Bar ── */
QMenuBar {
    background-color: #FFFFFF;
    color: #334155;
    border-bottom: 1px solid #E2E8F0;
    padding: 2px 0px;
    font-size: 13px;
}
QMenuBar::item {
    padding: 6px 14px;
    border-radius: 4px;
    margin: 2px 2px;
}
QMenuBar::item:selected {
    background-color: #EEF2FF;
    color: #4338CA;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 28px;
    border-radius: 4px;
    color: #334155;
}
QMenu::item:selected {
    background-color: #EEF2FF;
    color: #4338CA;
}
QMenu::separator {
    height: 1px;
    background-color: #E2E8F0;
    margin: 4px 8px;
}

/* ── Group Boxes (Card Style) ── */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    margin-top: 8px;
    padding: 20px 16px 16px 16px;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: #1E293B;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 20px;
    top: 2px;
    padding: 0 8px;
    background-color: #FFFFFF;
    color: #4338CA;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ── Labels ── */
QLabel {
    color: #475569;
    background: transparent;
    border: none;
    border-radius: 0px;
    padding: 2px 0px;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
QLabel#fieldLabel {
    font-size: 17px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
}
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #1E293B;
    padding: 4px 0px;
}

/* ── Line Edits (Input Fields) ── */
QLineEdit {
    background-color: #F8FAFC;
    color: #1E293B;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: "Segoe UI", "Consolas", monospace;
    font-size: 18px;
    selection-background-color: #C7D2FE;
}
QLineEdit:focus {
    border-color: #6366F1;
    background-color: #FFFFFF;
}
QLineEdit:hover {
    border-color: #94A3B8;
}
QLineEdit::placeholder {
    color: #94A3B8;
}

/* ── Buttons (Primary - Green/Indigo family) ── */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #6366F1, stop:1 #4F46E5);
    color: #FFFFFF;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 18px;
    font-weight: 600;
    min-height: 30px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4F46E5, stop:1 #4338CA);
}
QPushButton:pressed {
    background-color: #3730A3;
}

/* ── Search Button (special accent) ── */
QPushButton#searchButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22C55E, stop:1 #16A34A);
    font-size: 19px;
    min-height: 34px;
    letter-spacing: 0.5px;
}
QPushButton#searchButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #16A34A, stop:1 #15803D);
}
QPushButton#searchButton:pressed {
    background-color: #166534;
}

/* ── Danger Buttons (Clean / Exit) ── */
QPushButton#cleanButton1, QPushButton#cleanButton2 {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #F87171, stop:1 #EF4444);
}
QPushButton#cleanButton1:hover, QPushButton#cleanButton2:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #EF4444, stop:1 #DC2626);
}
QPushButton#cleanButton1:pressed, QPushButton#cleanButton2:pressed {
    background-color: #B91C1C;
}

QPushButton#exitButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #94A3B8, stop:1 #64748B);
}
QPushButton#exitButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #64748B, stop:1 #475569);
}
QPushButton#exitButton:pressed {
    background-color: #334155;
}

/* ── Text Edits (Display Areas) ── */
QTextEdit {
    background-color: #FAFBFC;
    color: #1E293B;
    border: 1.5px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px;
    font-family: "Consolas", "SF Mono", "Menlo", monospace;
    font-size: 16px;
    selection-background-color: #C7D2FE;
    line-height: 1.5;
}
QTextEdit:focus {
    border-color: #6366F1;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 4px 0px;
}
QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
    margin: 0px 4px;
}
QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ── Splitter Handle ── */
QSplitter::handle {
    background-color: #E2E8F0;
    height: 2px;
    margin: 4px 40px;
    border-radius: 1px;
}
QSplitter::handle:hover {
    background-color: #6366F1;
}

/* ── Message Box Overrides ── */
QMessageBox {
    background-color: #FFFFFF;
}
QMessageBox QLabel {
    color: #1E293B;
    background: transparent;
    font-size: 13px;
}
QMessageBox QPushButton {
    background-color: #6366F1;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-size: 13px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background-color: #4F46E5;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #1E293B;
    color: #F1F5F9;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}
"""


def add_shadow(widget, blur=20, offset_y=4, color=QColor(0, 0, 0, 25)):
    """Add a subtle drop shadow to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


class ReferenceExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reference Explorer 3.1")
        try:
            self.setWindowIcon(QIcon(resource_path("search.ico")))
        except Exception:
            pass
        self.setGeometry(100, 100, 1050, 850)
        self.setMinimumSize(800, 600)
        
        # Apply global stylesheet
        self.setStyleSheet(STYLESHEET)

        # ── Menu Bar ──
        menubar = self.menuBar()
        file_menu = menubar.addMenu("  File  ")

        open_action = QAction("  Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("  Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_search_history)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        print_action = QAction("  Print", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_search_history)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("  Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu("  Help  ")
        about_action = QAction("  About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        self.reference_info = None
        self.history_records = []
        self.last_download_dir = os.path.expanduser("~")  # Default to home directory

        self.label_font = QFont("Segoe UI", 17)
        self.text_font = QFont("Consolas", 18)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 12, 20, 20)
        main_layout.setSpacing(12)

        # ═══════════════════════════════════════════════════════════════════════
        # ── SEARCH CARD ──
        # ═══════════════════════════════════════════════════════════════════════
        search_card = QGroupBox("  SEARCH PARAMETERS")
        add_shadow(search_card)
        search_card_layout = QVBoxLayout(search_card)
        search_card_layout.setSpacing(12)

        # Row 1: Author, Journal, Volume, SPage, Year
        input_layout1 = QHBoxLayout()
        input_layout1.setSpacing(12)

        # Helper to create labeled input
        def make_field(label_text, placeholder=""):
            container = QVBoxLayout()
            container.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setObjectName("fieldLabel")
            lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
            inp = QLineEdit()
            inp.setFont(self.text_font)
            inp.setPlaceholderText(placeholder)
            container.addWidget(lbl)
            container.addWidget(inp)
            return container, inp

        author_lay, self.author_input = make_field("AUTHOR", "e.g. Einstein")
        journal_lay, self.journal_input = make_field("JOURNAL", "e.g. Phys. Rev.")
        volume_lay, self.volume_input = make_field("VOLUME", "e.g. 47")
        spage_lay, self.spage_input = make_field("START PAGE", "e.g. 777")
        year_lay, self.year_input = make_field("YEAR", "e.g. 1935")

        input_layout1.addLayout(author_lay, 3)
        input_layout1.addLayout(journal_lay, 3)
        input_layout1.addLayout(volume_lay, 1)
        input_layout1.addLayout(spage_lay, 1)
        input_layout1.addLayout(year_lay, 1)

        # Row 2: DOI + Buttons
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(12)

        doi_lay, self.doi_input = make_field("DOI", "e.g. 10.1103/PhysRev.47.777")
        row2_layout.addLayout(doi_lay, 1)

        # Buttons column
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        # Spacer label to align buttons with input field
        spacer_label = QLabel("")
        spacer_label.setObjectName("fieldLabel")
        spacer_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        spacer_label.setFixedHeight(28)
        button_layout.addWidget(spacer_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.clean_button = QPushButton("  Clear")
        self.clean_button.setObjectName("cleanButton1")
        self.clean_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.clean_button.setCursor(Qt.PointingHandCursor)
        self.clean_button.setToolTip("Clear all input fields")
        self.clean_button.clicked.connect(self.clean_inputs)

        self.search_button = QPushButton("  Search")
        self.search_button.setObjectName("searchButton")
        self.search_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setToolTip("Search for reference via CrossRef")
        self.search_button.clicked.connect(self.search_reference)

        btn_row.addWidget(self.clean_button)
        btn_row.addWidget(self.search_button)
        button_layout.addLayout(btn_row)

        row2_layout.addLayout(button_layout)

        search_card_layout.addLayout(input_layout1)
        search_card_layout.addLayout(row2_layout)

        main_layout.addWidget(search_card)

        # ═══════════════════════════════════════════════════════════════════════
        # ── RESULTS AREA (Splitter) ──
        # ═══════════════════════════════════════════════════════════════════════
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        # ── History Card ──
        history_card = QGroupBox("  SEARCH HISTORY")
        add_shadow(history_card)
        history_card_layout = QHBoxLayout(history_card)
        history_card_layout.setSpacing(12)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(self.text_font)
        self.history_display.setPlaceholderText("Search history will appear here...")
        history_card_layout.addWidget(self.history_display, 1)

        history_btn_layout = QVBoxLayout()
        history_btn_layout.setSpacing(8)

        self.clean_history_button = QPushButton("  Clear")
        self.clean_history_button.setObjectName("cleanButton2")
        self.clean_history_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.clean_history_button.setCursor(Qt.PointingHandCursor)
        self.clean_history_button.setToolTip("Clear all search history")
        self.clean_history_button.clicked.connect(self.clean_search_history)
        history_btn_layout.addWidget(self.clean_history_button)

        self.save_button = QPushButton("  Save")
        self.save_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setToolTip("Save search history to .rsh file")
        self.save_button.clicked.connect(self.save_search_history)
        history_btn_layout.addWidget(self.save_button)

        history_btn_layout.addStretch()
        history_card_layout.addLayout(history_btn_layout)

        # ── Current Result Card ──
        current_card = QGroupBox("  CURRENT SEARCH RESULT")
        add_shadow(current_card)
        current_card_layout = QHBoxLayout(current_card)
        current_card_layout.setSpacing(12)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(self.text_font)
        self.result_display.setPlaceholderText("Search results will appear here...")
        current_card_layout.addWidget(self.result_display, 1)

        current_btn_layout = QVBoxLayout()
        current_btn_layout.setSpacing(8)

        self.download_button = QPushButton("Open DOI /\nPDF")
        self.download_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setToolTip("Open the official DOI page for publisher or open-access PDF")
        self.download_button.setMinimumHeight(68)
        self.download_button.setMinimumWidth(135)
        self.download_button.clicked.connect(self.download_refs)
        current_btn_layout.addWidget(self.download_button)

        self.export_button = QPushButton("Export\nRIS")
        self.export_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.setToolTip("Export RIS using the DOI downloader")
        self.export_button.setMinimumHeight(68)
        self.export_button.setMinimumWidth(135)
        self.export_button.clicked.connect(self.export_ris)
        current_btn_layout.addWidget(self.export_button)

        self.exit_button = QPushButton("  Exit")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setFont(QFont("Segoe UI", 17, QFont.Bold))
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.setToolTip("Close the application")
        self.exit_button.clicked.connect(self.close)
        current_btn_layout.addWidget(self.exit_button)

        current_btn_layout.addStretch()
        current_card_layout.addLayout(current_btn_layout)

        splitter.addWidget(history_card)
        splitter.addWidget(current_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        self.journal_input.setFocus()

    # ── File Operations ──────────────────────────────────────────────────────

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Search History File", 
            "",
            "Search History Files (*.rsh);;Text Files (*.txt);;All Files (*)",
            options=options
        )
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                self.history_display.setPlainText(file.read())

    def print_search_history(self):
        if not self.history_display.toPlainText().strip():
            QMessageBox.information(self, "No Content", "There is no search history to print.")
            return
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            self.history_display.print_(printer)

    def show_about_dialog(self):
       about_text = """
                    <div style='text-align: center; font-family: Segoe UI, Arial, sans-serif;'>
                        <div style='margin-bottom: 10px;'>
                            <span style='font-size: 18px; font-weight: bold; color: #4338CA;'>Reference Explorer v3.0</span>
                        </div>
                        <span style='color: #64748B;'>Version 3.0</span><br><br>
                        <span style='color: #475569;'>Copyright &copy; 2024 MRDLAB. All rights reserved.</span><br><br>
                        <span style='color: #64748B; font-size: 11px;'>
                            This program is for internal use only.<br>
                            Do not distribute or use for commercial purposes.
                        </span>
                        <br><br>
                        <div style='text-align: left; display: inline-block;'>
                            <b style='color: #4338CA;'>Author:  </b> <span style='font-weight: normal; color: #334155;'>Li xilong</span><br>
                            <b style='color: #4338CA;'>Last Update:  </b> <span style='font-weight: normal; color: #334155;'>2024.09.06</span><br>
                            <b style='color: #4338CA;'>HomePage:</b> <span style='color: white;'></span><br>
                        </div>
                    </div>
                """
       QMessageBox.about(self, "About Reference Explorer", about_text)

    # ── Core Search Logic ────────────────────────────────────────────────────

    def search_reference(self):
        author = self.author_input.text()
        journal = self.journal_input.text()
        year = self.year_input.text()
        volume = self.volume_input.text()
        spage = self.spage_input.text()
        doi = self.doi_input.text()

        if doi:
            params = {
                "pid": "your_email@example.com",
                "id": doi,
                "redirect": "false"
            }
        else:
            params = {
                "pid": "your_email@example.com",
                "aulast": author if author else None,
                "title": journal if journal else None,
                "volume": volume if volume else None,
                "spage": spage if spage else None,
                "date": year if year else None,
                "redirect": "false"
            }

        result = self.fetch_reference_data(params)
        if result:
            current_search_result = f"Title: {result['Title']}\n" \
                                    f"Authors: {result['Authors']}\n" \
                                    f"Journal: {result['Journal']}\n" \
                                    f"Year: {result['Year']}\n" \
                                    f"Volume: {result['Volume']}\n" \
                                    f"Issue: {result['Issue']}\n" \
                                    f"Pages: {result['SPage']}-{result['EPage']}\n" \
                                    f"DOI: {result['DOI']}"
            self.result_display.setPlainText(current_search_result)
            self.reference_info = result

            self.history_records.append(result)
            self.update_history_display()
        else:
            self.result_display.setPlainText("No references found.")
            self.reference_info = None

    def fetch_reference_data(self, params):
        url = "https://doi.crossref.org/openurl"
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        try:
            response = session.get(url, params=params, verify=False)
            if response.status_code == 200:
                data = response.text
                root = ET.fromstring(data)
                ns = {'ns': 'http://www.crossref.org/qrschema/2.0'}
                if root.find('.//ns:query', ns).get('status') == 'resolved':
                    doi_element = root.find('.//ns:doi', ns)
                    doi = doi_element.text if doi_element is not None else None

                    journal_title_element = root.find('.//ns:journal_title', ns)
                    journal_title = journal_title_element.text if journal_title_element is not None else None

                    year_element = root.find('.//ns:year', ns)
                    year = year_element.text if year_element is not None else None

                    volume_element = root.find('.//ns:volume', ns)
                    volume = volume_element.text if volume_element is not None else None

                    issue_element = root.find('.//ns:issue', ns)
                    issue = issue_element.text if issue_element is not None else None

                    first_page_element = root.find('.//ns:first_page', ns)
                    first_page = first_page_element.text if first_page_element is not None else None

                    last_page_element = root.find('.//ns:last_page', ns)
                    last_page = last_page_element.text if last_page_element is not None else None

                    article_title_element = root.find('.//ns:article_title', ns)
                    article_title = article_title_element.text if article_title_element is not None else None

                    authors = root.findall('.//ns:contributor', ns)
                    author_names = []
                    for author in authors:
                        given_name_element = author.find('ns:given_name', ns)
                        given_name = given_name_element.text if given_name_element is not None else ''
                        surname_element = author.find('ns:surname', ns)
                        surname = surname_element.text if surname_element is not None else ''
                        author_names.append(f"{given_name} {surname}")

                    return {
                        "Title": article_title,
                        "Authors": ", ".join(author_names) if author_names else None,
                        "Journal": journal_title,
                        "Year": year,
                        "Volume": volume,
                        "Issue": issue,
                        "SPage": first_page,
                        "EPage": last_page,
                        "DOI": doi
                    }
                else:
                    print("Query unresolved.")
                    return None
            else:
                print(f"Request failed, status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return None

    # ── Input / History Management ───────────────────────────────────────────

    def clean_inputs(self):
        self.author_input.clear()
        self.journal_input.clear()
        self.volume_input.clear()
        self.spage_input.clear()
        self.year_input.clear()
        self.doi_input.clear()
        self.reference_info = None

    def update_history_display(self):
        history_text = ""
        for record in self.history_records:
            history_text += f"Title: {record['Title']}\n" \
                            f"Authors: {record['Authors']}\n" \
                            f"Journal: {record['Journal']}\n" \
                            f"Year: {record['Year']}\n" \
                            f"Volume: {record['Volume']}\n" \
                            f"Issue: {record['Issue']}\n" \
                            f"Pages: {record['SPage']}-{record['EPage']}\n" \
                            f"DOI: {record['DOI']}\n" \
                            f"{'─' * 50}\n"
        self.history_display.setPlainText(history_text)

    def clean_search_history(self):
        self.history_display.clear()
        self.history_records = []
    
    def save_search_history(self):
        if not self.history_display.toPlainText().strip():
            QMessageBox.information(self, "Information", "No history records to save.")
            return

        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Search History", 
            "refs_record.rsh",
            "Search History Files (*.rsh);;Text Files (*.txt);;All Files (*)",
            options=options
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(self.history_display.toPlainText())
            QMessageBox.information(self, "Saved successfully", f"Search history saved to: {save_path}")

    # ── Download / Export ────────────────────────────────────────────────────

    def download_refs(self):
        """Open the official DOI landing page for publisher/OA PDF access.

        Citation export logic remains unchanged.  PDF access is delegated to
        the publisher or an open-access source rather than a third-party mirror.
        """
        if not self.reference_info or not self.reference_info.get("DOI"):
            QMessageBox.warning(self, "Warning", "Article not found. Please search for an article first!")
            return
        doi = normalize_doi(self.reference_info["DOI"])
        webbrowser.open(f"https://doi.org/{urllib.parse.quote(doi, safe='/()')}")
        QMessageBox.information(
            self, "PDF access",
            "The official DOI page was opened. Download the PDF from the publisher or an available open-access link."
        )

    def _open_directory(self, path):
        """Open the given directory in the system file manager."""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass  # Silently ignore if unable to open

    def export_ciw(self):
        if not self.reference_info:
            QMessageBox.warning(self, "Warning", "No reference found.")
            return

        options = QFileDialog.Options()
        file_dialog = QFileDialog()
        save_path, _ = file_dialog.getSaveFileName(self, "Save CIW file", "reference.ciw", "CIW Files (*.ciw);;All Files (*)", options=options)

        if save_path:
            data = self.reference_info
            ciw_content = []

            ciw_content.append("FN Created by ChemAuto program using data from CrossRef database")
            ciw_content.append("VR 5.3")
            ciw_content.append("PT J")

            authors = data.get("Authors", "").split(", ")
            if authors:
                ciw_content.append(f"AU {authors[0]}")
                for author in authors[1:]:
                    ciw_content.append(f"   {author}")

            if authors:
                ciw_content.append(f"AF {authors[0]}")
                for author in authors[1:]:
                    ciw_content.append(f"   {author}")

            ciw_content.append(f"TI {data.get('Title', '')}")
            ciw_content.append(f"SO {data.get('Journal', '')}")
            ciw_content.append("RI")  
            ciw_content.append("OI")  
            ciw_content.append(f"SN {data.get('ISSN', '')}")
            ciw_content.append(f"EI {data.get('eISSN', '')}")
            ciw_content.append(f"PD {data.get('PubDate', '')}")
            ciw_content.append(f"PY {data.get('Year', '')}")
            ciw_content.append(f"VL {data.get('Volume', '')}")
            ciw_content.append(f"IS {data.get('Issue', '')}")
            ciw_content.append(f"BP {data.get('SPage', '')}")
            ciw_content.append(f"EP {data.get('EPage', '')}")
            ciw_content.append(f"DI {data.get('DOI', '')}")
            ciw_content.append("UT") 
            ciw_content.append("PM")            
            ciw_content.append("ER")
            ciw_content.append("\n")
            ciw_content.append("EF")

            ciw_content_str = "\n".join(ciw_content)

            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(ciw_content_str)
            QMessageBox.information(self, "Saved successfully", f"CIW file saved: {save_path}")

    def export_ris(self):
        if not self.reference_info or not self.reference_info.get("DOI"):
            QMessageBox.warning(self, "Warning", "No DOI found for the current reference.")
            return

        doi = self.reference_info.get("DOI", "").strip()
        if not doi:
            QMessageBox.warning(self, "Warning", "No DOI found for the current reference.")
            return

        try:
            master_downloader(doi, "ris")
            QMessageBox.information(
                self,
                "RIS export started",
                f"RIS export has been triggered using DOI:\n{doi}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export RIS: {e}")


# ==========================================
# RSC
# ==========================================

def download_rsc_fast(doi, fmt="ris"):
    print(f"\n🚀 [RSC 极速直连引擎] 处理 DOI: {doi} ...")

    try:
        article_id = doi.split('/')[1].lower()
    except IndexError:
        print("❌ DOI 格式不正确，请确保包含斜杠 '/'。")
        return

    if fmt.lower() in ["bibtex", "bib"]:
        manager_type = "bibtex"
        ext_name = "BibTeX"
    else:
        manager_type = "endnote"
        ext_name = "RIS/EndNote"

    download_url = f"https://pubs.rsc.org/en/content/formatedresult?markedids={article_id}&downloadtype=article&managertype={manager_type}"

    print(f"🔗 链接组装完毕，正在唤醒浏览器直接下载官方 {ext_name} 文件...\n")
    webbrowser.open(download_url)
    print("🎉 完美秒杀！RSC 也是良心网站，文件已直达下载目录。")


# ==========================================
# Springer
# ==========================================

def download_springer_fast(doi, fmt="ris"):
    print(f"\n🚀 [Springer 极速直连引擎] 处理 DOI: {doi} ...")

    if fmt.lower() in ["bibtex", "bib"]:
        format_str = "bibtex"
        ext_name = "BibTeX"
    else:
        format_str = "refman"
        ext_name = "RIS/EndNote"

    download_url = f"https://citation-needed.springer.com/v2/references/{doi}?format={format_str}&flavour=citation"

    print(f"🔗 链接组装完毕，正在唤醒浏览器直接下载官方 {ext_name} 文件...\n")
    webbrowser.open(download_url)
    print("🎉 完美秒杀！Springer 也是活菩萨，文件已直达下载目录。")


# ==========================================
# Taylor & Francis
# ==========================================

def download_tandf_autoclose(doi, fmt="ris"):
    print(f"\n🚀 [Taylor & Francis 极速引擎] 正在处理 DOI: {doi} ...")

    format_val = "bibtex" if fmt.lower() in ["bibtex", "bib"] else ("endnote" if fmt.lower() in ["enw", "endnote"] else "ris")

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset=\"utf-8\"></head>
    <body style=\"font-family: sans-serif; text-align: center; margin-top: 50px;\">
        <h2 style=\"color: #333;\">正在自动下载 Taylor & Francis 官方引用文件...</h2>
        <h3 style=\"color: #4CAF50;\">✅ 下载触发后，您可以直接关闭此标签页。</h3>
        <form id=\"autoForm\" action=\"https://www.tandfonline.com/action/downloadCitation\" method=\"POST\">
            <input type=\"hidden\" name=\"doi\" value=\"{doi}\">
            <input type=\"hidden\" name=\"format\" value=\"{format_val}\">
            <input type=\"hidden\" name=\"include\" value=\"abs\">
            <input type=\"hidden\" name=\"direct\" value=\"true\">
        </form>
        <script>
            document.getElementById('autoForm').submit();
            setTimeout(function() {{
                window.opener = null;
                window.open('', '_self');
                window.close();
            }}, 2000);
        </script>
    </body>
    </html>
    """

    html_path = os.path.abspath("tandf_temp.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    webbrowser.open(f"file:///{html_path.replace(os.sep, '/')}")

    time.sleep(3)
    try:
        os.remove(html_path)
    except OSError:
        pass
    print("🎉 搞定！文件已掉落至下载目录。")


# ==========================================
# Wiley / Science
# ==========================================

def open_citation_page(doi):
    print(f"\n🚀 [Wiley/Science 一键空降引擎] 正在处理 DOI: {doi} ...")

    if doi.startswith("10.1126"):
        domain = "https://www.science.org"
        name = "Science (AAAS)"
    elif doi.startswith("10.1002") or doi.startswith("10.1111"):
        domain = "https://onlinelibrary.wiley.com"
        name = "Wiley"
    else:
        domain = "https://onlinelibrary.wiley.com"
        name = "未知 (默认走 Wiley 通道尝试)"

    print(f"📡 识别到目标数据库为: {name}")

    encoded_doi = urllib.parse.quote(doi)
    target_url = f"{domain}/action/showCitFormats?doi={encoded_doi}"

    print(f"🔗 正在呼叫系统浏览器，带您直接空降 {name} 的官方格式选择页...\n")
    webbrowser.open(target_url)
    print("🎉 空降成功！请在弹出的网页中直接点击 'Download'。")


# ==========================================
# ACS
# ==========================================

def download_acs_stealth(doi, fmt="ris"):
    print(f"\n🚀 [ACS 隐身直连引擎] 处理 DOI: {doi} ...")

    encoded_doi = urllib.parse.quote(doi)
    file_name = doi.split('/')[-1]

    if fmt.lower() in ["bibtex", "bib"]:
        format_str = "bibtex"
        ext_name = "BibTeX"
    elif fmt.lower() in ["enw", "endnote"]:
        format_str = "endnote"
        ext_name = "EndNote"
    else:
        format_str = "ris"
        ext_name = "RIS"

    download_url = f"https://pubs.acs.org/action/downloadCitation?doi={encoded_doi}&include=cit&format={format_str}&direct=true&downloadFileName={file_name}"

    print(f"🔗 链接组装完毕，已绕过全部前端监控...")
    print(f"🔗 正在唤醒真实浏览器下载官方 {ext_name} 文件...\n")
    webbrowser.open(download_url)
    print("🎉 完美秒杀！ACS 的反爬盾形同虚设，引用文件已直达下载目录。")


# ==========================================
# AIP
# ==========================================

def download_aip_citation_auto(doi, fmt="ris"):
    if sync_playwright is None:
        print("❌ 缺少 playwright，无法运行 AIP 自动化引擎。")
        return

    print(f"\n🚀 启动真实浏览器引擎抓取 DOI: {doi} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("⏳ 正在突破防火墙并等待网页重定向...")
            page.goto(f"https://doi.org/{doi}")
            page.wait_for_url("**/pubs.aip.org/**", timeout=20000)
            final_url = page.url
            print(f"✅ 成功穿透，到达文献主页: {final_url}")

            match = re.search(r'/(\d{6,9})(?:/|\?|$)', final_url)
            if match:
                resource_id = match.group(1)
                print(f"🎯 成功锁定内部 resourceId: {resource_id}")

                fmt_code = 0
                if fmt.lower() == "bibtex":
                    fmt_code = 2
                elif fmt.lower() == "enw":
                    fmt_code = 1

                download_url = f"https://pubs.aip.org/Citation/Download?resourceId={resource_id}&resourceType=3&citationFormat={fmt_code}"

                print(f"🔗 正在唤醒系统默认浏览器下载官方 {fmt.upper()} 文件...\n")
                webbrowser.open(download_url)
                print("🎉 搞定！文件已送达你的浏览器默认下载目录。")
            else:
                print(f"❌ 提取失败：未能在最终链接中找到 ID。最终链接为: {final_url}")

        except Exception as e:
            print(f"❌ 运行报错: {e}")
            print("💡 提示：如果依然报错，可能是 AIP 弹出了极其严格的人机验证码。你可以尝试将代码第 11 行的 headless=True 改为 headless=False 看看浏览器里发生了什么。")
        finally:
            browser.close()


def download_aip(doi, fmt="ris"):
    # 保持与 aps.py 内的 AIP 版本相同行为：headless=False，且格式兼容更宽松
    if sync_playwright is None:
        print("❌ 缺少 playwright，无法运行 AIP 自动化引擎。")
        return

    print(f"\n🚀 [AIP 引擎] 启动真实浏览器引擎抓取 DOI: {doi} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print("⏳ 正在突破防火墙并等待网页重定向...")
            page.goto(f"https://doi.org/{doi}")
            page.wait_for_url("**/pubs.aip.org/**", timeout=20000)
            final_url = page.url
            print(f"✅ 成功穿透，到达文献主页: {final_url}")

            match = re.search(r'/(\d{6,9})(?:/|\?|$)', final_url)
            if match:
                resource_id = match.group(1)
                print(f"🎯 成功锁定内部 resourceId: {resource_id}")

                fmt_code = 0
                if fmt.lower() in ["bibtex", "bib"]:
                    fmt_code = 2
                elif fmt.lower() in ["enw", "endnote"]:
                    fmt_code = 1

                download_url = f"https://pubs.aip.org/Citation/Download?resourceId={resource_id}&resourceType=3&citationFormat={fmt_code}"
                print(f"🔗 正在唤醒浏览器下载官方 {fmt.upper()} 文件...\n")
                webbrowser.open(download_url)
                print("🎉 搞定！AIP 引用文件已送达下载目录。")
            else:
                print(f"❌ 提取失败：未能在最终链接中找到 ID。最终链接为: {final_url}")

        except Exception as e:
            print(f"❌ AIP 引擎运行报错: {e}")
            print("💡 提示：如果依然 timeout，可能是 AIP 弹出了极其严格的验证码，可尝试将 headless=True 改为 False 观察。")
        finally:
            browser.close()


# ==========================================
# APS
# ==========================================

APS_JOURNALS = {
    "Physical Review Letters": "prl",
    "Physical Review A": "pra",
    "Physical Review B": "prb",
    "Physical Review C": "prc",
    "Physical Review D": "prd",
    "Physical Review E": "pre",
    "Physical Review X": "prx",
    "Reviews of Modern Physics": "rmp",
    "Physical Review Applied": "prapplied",
    "Physical Review Fluids": "prfluids",
    "Physical Review Materials": "prmaterials",
    "Physical Review Research": "prresearch",
    "Physical Review Accelerators and Beams": "prab",
    "Physical Review Physics Education Research": "prper",
    "PRX Energy": "prxenergy",
    "PRX Intelligence": "prxintelligence",
    "PRX Life": "prxlife",
    "PRX Quantum": "prxquantum"
}


def download_aps(doi, fmt="ris"):
    print(f"\n🚀 [APS 引擎] 正在通过 Crossref API 秒级解析 DOI: {doi} ...")

    try:
        api_url = f"https://api.crossref.org/works/{doi}"
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "CitationDownloader/2.0 (mailto:scholar@example.com)")

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            journal_name = data['message']['container-title'][0]
            print(f"📖 查到所属期刊: {journal_name}")

            journal_abbrev = APS_JOURNALS.get(journal_name)

            if not journal_abbrev:
                for key, val in APS_JOURNALS.items():
                    if key.lower() in journal_name.lower():
                        journal_abbrev = val
                        break

            if journal_abbrev:
                print(f"🎯 成功匹配缩写: {journal_abbrev}")
                fmt_type = "bibtex" if fmt.lower() in ["bibtex", "bib"] else "ris"
                download_url = f"https://journals.aps.org/{journal_abbrev}/export/{doi}?type={fmt_type}&download=true"

                print(f"🔗 正在唤醒浏览器直接下载: {download_url}\n")
                webbrowser.open(download_url)
                print("🎉 搞定！APS 引用文件已送达下载目录。")
            else:
                print(f"❌ 未能识别该期刊是否属于 APS 核心列表: {journal_name}")

    except urllib.error.HTTPError as e:
        print(f"❌ Crossref API 报错: HTTP {e.code}。请检查 DOI 是否输入有误。")
    except Exception as e:
        print(f"❌ APS 引擎运行报错: {e}")


# ==========================================
# Elsevier
# ==========================================

def download_elsevier_fastest(doi, fmt="ris"):
    print(f"\n🚀 [Elsevier 智能混动引擎] 开始处理 DOI: {doi} ...")
    
    pii = None
    suffix = doi.split("10.1016/", 1)[1] if "10.1016/" in doi else doi
    core = re.sub(r'[^A-Za-z0-9]', '', suffix)
    
    # ==========================================
    # 🟢 第一档：极速纯量拼接 (致敬你的原版逻辑)
    # 针对老实巴交的规矩 DOI，直接秒杀，绝不浪费时间启动浏览器！
    # ==========================================
    legacy_pattern = re.fullmatch(r'\d{4}-\d{4}\(\d{2,4}\)[A-Za-z0-9\-]+', suffix)
    
    # 1. 经典老式 DOI (带括号或横杠)
    if legacy_pattern or "(" in suffix or ")" in suffix:
        pii = core
        print(f"⚡ 极速通道：识别为经典老式 DOI，直出 PII: {pii}")
        
    # 2. 现代标准数字 DOI (不带字母前缀，纯数字组成的底层码)
    elif not suffix.startswith("j.") and not suffix.startswith("S") and len(core) >= 15:
        pii = "S" + core
        print(f"⚡ 极速通道：识别为标准现代 DOI，极速拼装 PII: {pii}")
        
    # 3. 本身就已经带有 S 前缀的完美 DOI
    elif suffix.startswith("S") and len(core) >= 16:
        pii = core
        print(f"⚡ 极速通道：识别为原生标准 PII，直接使用: {pii}")

    # ==========================================
    # 🔴 第二档：Playwright 重装甲 (专治刚才那种 j.tsf. 缩写奇葩 DOI)
    # ==========================================
    if not pii:
        print("🛡️ 识别为缩写型或不规则 DOI，正在启动真实浏览器穿透防火墙...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f"https://doi.org/{doi}")
                page.wait_for_url("**/pii/**", timeout=20000)
                final_url = page.url
                
                match = re.search(r'/pii/([A-Za-z0-9]+)', final_url)
                if match:
                    pii = match.group(1)
                    print(f"🎯 穿透成功！从文献终点站精准提取出隐藏 PII: {pii}")
                browser.close()
        except Exception as e:
            print(f"⚠️ 浏览器穿透遇到阻碍: {e}")

    # ==========================================
    # 🟡 第三档：备用轻量级 HTTP 截获 (原版 HEAD 逻辑兜底)
    # ==========================================
    if not pii:
        print("⏳ 启动最后防线：尝试轻量级 HTTP 链接截获...")
        import urllib.request
        url = f"https://linkinghub.elsevier.com/retrieve/doi/{doi}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        req.get_method = lambda: 'HEAD'
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            final_url = resp.geturl()
            match = re.search(r'/pii/([A-Za-z0-9]+)', final_url)
            if match:
                pii = match.group(1)
                print(f"🎯 HTTP 截获成功: {pii}")
        except Exception as e:
            pass

    # ==========================================
    # 最终拼装直达链接并唤醒浏览器
    # ==========================================
    if pii:
        if fmt.lower() in ["bibtex", "bib"]:
            fmt_type = "text%2Fx-bibtex"
            ext_name = "BibTeX"
        else:
            fmt_type = "application%2Fx-research-info-systems"
            ext_name = "RIS"
            
        download_url = f"https://www.sciencedirect.com/sdfe/arp/cite?pii={pii}&format={fmt_type}&withabstract=true"
        
        print(f"🔗 正在唤醒系统默认浏览器下载官方 {ext_name} 文件...\n")
        import webbrowser
        webbrowser.open(download_url)
        print("🎉 搞定！爱思唯尔文献下载完成。")
    else:
        print("❌ 解析失败，这篇文献的 DOI 格式过于罕见，三道防线均未找到特征码。")


# ==========================================
# IOP
# ==========================================

def download_iop_fast(doi, fmt="ris"):
    print(f"\n🚀 [IOP 光速直连引擎] 处理 DOI: {doi} ...")

    encoded_doi = urllib.parse.quote(doi)

    if fmt.lower() in ["bibtex", "bib"]:
        export_format = "iopexport_bib"
        ext_name = "BibTeX"
    else:
        export_format = "iopexport_ris"
        ext_name = "RIS (兼顾 EndNote)"

    download_url = f"https://iopscience.iop.org/export?type=article&doi={encoded_doi}&exportFormat={export_format}&exportType=abs&navsubmit=Export+abstract"

    print(f"🔗 链接组装完毕，正在唤醒浏览器下载官方 {ext_name} 文件...\n")
    webbrowser.open(download_url)
    print("🎉 完美秒杀！IOP 简直是活菩萨，文件已直达下载目录。")


# ==========================================
# MDPI
# ==========================================

def download_mdpi_standard(doi):
    print(f"\n🚀 [MDPI 官方标准仿真引擎] 正在对标官网格式: {doi} ...")

    api_url = f"https://api.crossref.org/works/{doi}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ReferenceManager/1.0'}

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))['message']

        title = data.get('title', [''])[0]
        journal = data.get('container-title', [''])[0]
        volume = data.get('volume', '')
        issue = data.get('issue', '')
        pages = data.get('page', '')
        doi_val = data.get('DOI', doi)
        issn = data.get('ISSN', [''])[0]
        publisher = data.get('publisher', 'MDPI AG')

        issued = data.get('issued', {}).get('date-parts', [[0, 0, 0]])[0]
        year = str(issued[0])
        full_date = f"{issued[0]}/{issued[1]:02d}/{issued[2]:02d}" if len(issued) > 2 else year

        abstract = data.get('abstract', '')
        abstract = re.sub(r'<[^>]+>', '', abstract).strip()

        authors = []
        for a in data.get('author', []):
            authors.append(f"{a.get('family', '')}, {a.get('given', '')}")

        keywords = data.get('subject', [])

        ris_lines = []
        ris_lines.append("TY  - EJOUR")
        for auth in authors:
            ris_lines.append(f"AU  - {auth}")
        ris_lines.append(f"TI  - {title}")
        ris_lines.append(f"T2  - {journal}")
        ris_lines.append(f"PY  - {year}")
        ris_lines.append(f"VL  - {volume}")
        ris_lines.append(f"IS  - {issue}")
        ris_lines.append(f"SN  - {issn}")
        ris_lines.append(f"SP  - {pages}")
        if abstract:
            ris_lines.append(f"AB  - {abstract}")
        for kw in keywords:
            ris_lines.append(f"KW  - {kw}")
        ris_lines.append(f"DO  - {doi_val}")
        ris_lines.append(f"UR  - http://dx.doi.org/{doi_val}")
        ris_lines.append(f"PB  - {publisher}")
        ris_lines.append(f"DA  - {full_date}")
        ris_lines.append("ER  - ")

        ris_content = "\n".join(ris_lines)

        file_name = f"standard_mdpi_{doi.replace('/', '_')}.ris"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(ris_content)

        print(f"🎉 仿真完成！字段顺序与 MDPI 官网导出高度一致。")
        print(f"📁 文件已保存: {os.path.abspath(file_name)}")

    except Exception as e:
        print(f"❌ 运行报错: {e}")


# ==========================================
# 总控路由
# ==========================================

def normalize_doi(doi):
    return doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip()


def master_downloader(doi, fmt="ris"):
    doi = normalize_doi(doi)

    if doi.startswith("10.1021/"):
        download_acs_stealth(doi, fmt)
    elif doi.startswith("10.1039/"):
        download_rsc_fast(doi, fmt)
    elif doi.startswith("10.1007/"):
        download_springer_fast(doi, fmt)
    elif doi.startswith("10.1080/"):
        download_tandf_autoclose(doi, fmt)
    elif doi.startswith("10.1002/") or doi.startswith("10.1111/") or doi.startswith("10.1126/"):
        open_citation_page(doi)
    elif doi.startswith("10.1063/"):
        # 优先沿用 aps.py 中实际对外暴露的 download_aip 行为
        download_aip(doi, fmt)
    elif doi.startswith("10.1103/"):
        download_aps(doi, fmt)
    elif doi.startswith("10.1016/"):
        download_elsevier_fastest(doi, fmt)
    elif doi.startswith("10.1088/"):
        download_iop_fast(doi, fmt)
    elif doi.startswith("10.3390/"):
        download_mdpi_standard(doi)
    else:
        print("\n⚠️ 暂不支持该 DOI 前缀。")
        print("目前支持：ACS / RSC / Springer / T&F / Wiley / Science / AIP / APS / Elsevier / IOP / MDPI")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon(resource_path("search.ico")))
    except Exception:
        pass
    ex = ReferenceExplorer()
    ex.show()
    sys.exit(app.exec_())
