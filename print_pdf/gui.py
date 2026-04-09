"""GUI for print-pdf with live preview (PyQt6)."""

import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from print_pdf.core import (
    create_test_pdf,
    prepare_preview_pdfs,
    print_pdf_file,
    process_pdf,
    render_page_from_pdf,
    render_preview,
)

STYLESHEET = """
QWidget#centralWidget {
    background-color: #f5f5f5;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #444444;
}

QLabel#sectionLabel {
    font-size: 11px;
    color: #666666;
    font-weight: bold;
    margin-bottom: 2px;
}

QLineEdit {
    padding: 5px 8px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #ffffff;
}
QLineEdit:focus {
    border-color: #5b9bd5;
}

QPushButton#browseBtn, QPushButton#smallBtn {
    padding: 5px 10px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #f0f0f0;
}
QPushButton#browseBtn:hover, QPushButton#smallBtn:hover {
    background: #e0e0e0;
}

QPushButton#previewActiveBtn {
    padding: 5px 10px;
    border: 1px solid #5b9bd5;
    border-radius: 4px;
    background: #e0edfa;
    font-weight: bold;
}

QPushButton#generateBtn {
    padding: 10px;
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
    background-color: #4a86c8;
    border: none;
    border-radius: 6px;
}
QPushButton#generateBtn:hover {
    background-color: #3a76b8;
}
QPushButton#generateBtn:pressed {
    background-color: #2a5a8c;
}

QPushButton#secondaryBtn {
    padding: 10px;
    font-size: 13px;
    color: #333333;
    background-color: #e8e8e8;
    border: 1px solid #c0c0c0;
    border-radius: 6px;
}
QPushButton#secondaryBtn:hover {
    background-color: #d8d8d8;
}

QPushButton#navBtn {
    padding: 6px 18px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #ffffff;
    font-size: 16px;
}
QPushButton#navBtn:hover {
    background: #e8f0fe;
    border-color: #5b9bd5;
}

QPushButton#iconBtn {
    padding: 5px 9px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #f0f0f0;
    font-size: 15px;
    min-width: 28px;
}
QPushButton#iconBtn:hover {
    background: #e0e0e0;
}

QPushButton#iconBtnActive {
    padding: 5px 9px;
    border: 1px solid #5b9bd5;
    border-radius: 4px;
    background: #e0edfa;
    font-size: 15px;
    font-weight: bold;
    min-width: 28px;
}

QPushButton#linkBtn {
    border: none;
    background: transparent;
    color: #4a86c8;
    text-decoration: underline;
    padding: 2px;
}
QPushButton#linkBtn:hover {
    color: #2a5a8c;
}

QScrollArea#previewArea {
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    background-color: #e8e8e8;
}

QLabel#pageLabel {
    font-size: 12px;
    color: #555555;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #333333;
}

QLabel#locationLabel {
    font-size: 10px;
    color: #666666;
    padding: 2px 0;
}

QCheckBox {
    spacing: 6px;
    padding: 3px 0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""


class PrintPdfApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("centralWidget")
        self.setWindowTitle("Print PDF - Przygotowanie wydruku")
        self.setMinimumSize(900, 620)

        self.current_page = 0
        self.total_pages = 0
        self._current_pixmap: QPixmap | None = None
        self.save_dir = os.getcwd()
        self.preview_mode = "processed"  # "input", "processed", "odd", "even"
        self._preview_pdfs: dict[str, str] = {}  # mode -> /tmp path

        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # --- Left panel ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        title = QLabel("Print PDF")
        title.setObjectName("titleLabel")
        left_panel.addWidget(title)

        subtitle = QLabel("Przygotowanie wydruku")
        subtitle.setStyleSheet("color: #888888; font-size: 11px; margin-bottom: 4px;")
        left_panel.addWidget(subtitle)

        # --- File group ---
        file_group = QGroupBox("Pliki")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(6)

        # Input file
        lbl_input = QLabel("Plik wejściowy")
        lbl_input.setObjectName("sectionLabel")
        file_layout.addWidget(lbl_input)

        input_btn_row = QHBoxLayout()
        browse_btn = QPushButton("Otwórz")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setToolTip("Wybierz plik PDF do przetworzenia")
        browse_btn.clicked.connect(self._browse_input)
        input_btn_row.addWidget(browse_btn)

        test_btn = QPushButton("Testowy")
        test_btn.setObjectName("smallBtn")
        test_btn.setToolTip("Wygeneruj testowy PDF (4 strony) i załaduj go")
        test_btn.clicked.connect(self._load_test_pdf)
        input_btn_row.addWidget(test_btn)
        input_btn_row.addStretch()
        file_layout.addLayout(input_btn_row)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Wybierz plik PDF...")
        self.input_edit.setReadOnly(True)
        input_row.addWidget(self.input_edit)

        self.btn_preview_input = QPushButton("→")
        self.btn_preview_input.setObjectName("iconBtn")
        self.btn_preview_input.setToolTip("Pokaż w podglądzie")
        self.btn_preview_input.clicked.connect(lambda: self._set_preview_mode("input"))
        input_row.addWidget(self.btn_preview_input)

        self.btn_open_input = QPushButton("↗")
        self.btn_open_input.setObjectName("iconBtn")
        self.btn_open_input.setToolTip("Otwórz w zewnętrznym programie")
        self.btn_open_input.clicked.connect(self._open_input_external)
        input_row.addWidget(self.btn_open_input)

        file_layout.addLayout(input_row)
        file_layout.addSpacing(10)

        # Output preview 1
        output1_row = QHBoxLayout()
        self.preview_lbl_output1 = QLabel("Podgląd")
        self.preview_lbl_output1.setStyleSheet("color: #444; padding: 5px 8px; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px;")
        output1_row.addWidget(self.preview_lbl_output1, stretch=1)

        self.btn_preview_output1 = QPushButton("→")
        self.btn_preview_output1.setObjectName("iconBtn")
        self.btn_preview_output1.setToolTip("Pokaż w podglądzie")
        self.btn_preview_output1.clicked.connect(self._preview_output1)
        output1_row.addWidget(self.btn_preview_output1)

        self.btn_open_output1 = QPushButton("↗")
        self.btn_open_output1.setObjectName("iconBtn")
        self.btn_open_output1.setToolTip("Otwórz w zewnętrznym programie")
        self.btn_open_output1.clicked.connect(lambda: self._open_output_external(1))
        output1_row.addWidget(self.btn_open_output1)

        file_layout.addLayout(output1_row)

        # Output preview 2 (duplex only)
        output2_file_row_widget = QWidget()
        self.output2_file_row = output2_file_row_widget
        output2_row = QHBoxLayout(output2_file_row_widget)
        output2_row.setContentsMargins(0, 0, 0, 0)

        self.preview_lbl_output2 = QLabel("Podgląd parzyste")
        self.preview_lbl_output2.setStyleSheet("color: #444; padding: 5px 8px; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px;")
        output2_row.addWidget(self.preview_lbl_output2, stretch=1)

        self.btn_preview_output2 = QPushButton("→")
        self.btn_preview_output2.setObjectName("iconBtn")
        self.btn_preview_output2.setToolTip("Pokaż w podglądzie")
        self.btn_preview_output2.clicked.connect(lambda: self._set_preview_mode("even"))
        output2_row.addWidget(self.btn_preview_output2)

        self.btn_open_output2 = QPushButton("↗")
        self.btn_open_output2.setObjectName("iconBtn")
        self.btn_open_output2.setToolTip("Otwórz w zewnętrznym programie")
        self.btn_open_output2.clicked.connect(lambda: self._open_output_external(2))
        output2_row.addWidget(self.btn_open_output2)

        file_layout.addWidget(output2_file_row_widget)

        # Initially hide output2 (shown only for duplex)
        self.output2_file_row.setVisible(False)

        left_panel.addWidget(file_group)

        # --- Options group ---
        opts_group = QGroupBox("Opcje wydruku")
        opts_layout = QVBoxLayout(opts_group)
        opts_layout.setSpacing(4)

        self.cb_landscape = QCheckBox("Orientacja pozioma")
        self.cb_landscape.setToolTip("Układ poziomy (landscape) zamiast pionowego")
        self.cb_landscape.stateChanged.connect(self._on_option_changed)
        opts_layout.addWidget(self.cb_landscape)

        self.cb_two_up = QCheckBox("2 strony na arkuszu")
        self.cb_two_up.setToolTip("Umieszcza dwie strony źródłowe na jednym arkuszu")
        self.cb_two_up.stateChanged.connect(self._on_option_changed)
        opts_layout.addWidget(self.cb_two_up)

        self.cb_numbers = QCheckBox("Numery stron")
        self.cb_numbers.setToolTip("Dodaje numery stron na dolnym marginesie")
        self.cb_numbers.stateChanged.connect(self._on_option_changed)
        opts_layout.addWidget(self.cb_numbers)

        self.cb_duplex = QCheckBox("Druk dwustronny (ręczny)")
        self.cb_duplex.setToolTip(
            "Rozdziela strony parzyste i nieparzyste do osobnych plików\n"
            "z odwróconą kolejnością, do ręcznego druku dwustronnego"
        )
        self.cb_duplex.stateChanged.connect(self._on_duplex_changed)
        opts_layout.addWidget(self.cb_duplex)

        # Page range
        range_row = QHBoxLayout()
        self.cb_range = QCheckBox("Zakres stron:")
        self.cb_range.setToolTip("Ogranicz przetwarzanie do podanego zakresu stron oryginału")
        self.cb_range.stateChanged.connect(self._on_range_changed)
        range_row.addWidget(self.cb_range)

        self.spin_from = QSpinBox()
        self.spin_from.setMinimum(1)
        self.spin_from.setMaximum(9999)
        self.spin_from.setValue(1)
        self.spin_from.setToolTip("Pierwsza strona zakresu")
        self.spin_from.setEnabled(False)
        self.spin_from.setFixedWidth(56)
        self.spin_from.valueChanged.connect(self._on_option_changed)
        range_row.addWidget(self.spin_from)

        range_row.addWidget(QLabel("–"))

        self.spin_to = QSpinBox()
        self.spin_to.setMinimum(1)
        self.spin_to.setMaximum(9999)
        self.spin_to.setValue(1)
        self.spin_to.setToolTip("Ostatnia strona zakresu")
        self.spin_to.setEnabled(False)
        self.spin_to.setFixedWidth(56)
        self.spin_to.valueChanged.connect(self._on_option_changed)
        range_row.addWidget(self.spin_to)
        range_row.addStretch()
        opts_layout.addLayout(range_row)

        left_panel.addWidget(opts_group)

        # --- Save group ---
        save_group = QGroupBox("Zapis")
        save_layout = QVBoxLayout(save_group)
        save_layout.setSpacing(6)

        # Output filenames
        self.lbl_save_output1 = QLabel("Plik wyjściowy")
        self.lbl_save_output1.setObjectName("sectionLabel")
        save_layout.addWidget(self.lbl_save_output1)

        self.output1_edit = QLineEdit()
        self.output1_edit.setPlaceholderText("nazwa_pliku.pdf")
        self.output1_edit.textChanged.connect(self._update_output_tooltips)
        save_layout.addWidget(self.output1_edit)

        self.lbl_save_output2 = QLabel("Strony parzyste")
        self.lbl_save_output2.setObjectName("sectionLabel")
        save_layout.addWidget(self.lbl_save_output2)

        self.output2_edit = QLineEdit()
        self.output2_edit.setPlaceholderText("nazwa_pliku.pdf")
        self.output2_edit.textChanged.connect(self._update_output_tooltips)
        save_layout.addWidget(self.output2_edit)

        # Initially hide output2 save fields
        self.lbl_save_output2.setVisible(False)
        self.output2_edit.setVisible(False)

        loc_row = QHBoxLayout()
        loc_label = QLabel("Lokalizacja:")
        loc_label.setObjectName("sectionLabel")
        loc_row.addWidget(loc_label)

        self.location_btn = QPushButton("")
        self.location_btn.setObjectName("linkBtn")
        self.location_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.location_btn.setToolTip("Otwórz w menedżerze plików")
        self.location_btn.clicked.connect(self._open_save_dir)
        loc_row.addWidget(self.location_btn, stretch=1)
        save_layout.addLayout(loc_row)

        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Zapisz PDF")
        gen_btn.setObjectName("generateBtn")
        gen_btn.setToolTip("Zapisz w lokalizacji oryginalnego pliku")
        gen_btn.clicked.connect(self._save_default)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(gen_btn)

        save_as_btn = QPushButton("Zapisz w lokalizacji")
        save_as_btn.setObjectName("secondaryBtn")
        save_as_btn.setToolTip("Wybierz inną lokalizację i zapisz")
        save_as_btn.clicked.connect(self._save_choose_location)
        save_as_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(save_as_btn)

        save_layout.addLayout(btn_row)
        left_panel.addWidget(save_group)

        left_panel.addStretch()

        self.print_btn = QPushButton("Drukuj")
        self.print_btn.setObjectName("generateBtn")
        self.print_btn.setToolTip("Wyślij do drukarki")
        self.print_btn.clicked.connect(self._print_document)
        self.print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.print_btn.setEnabled(False)
        left_panel.addWidget(self.print_btn)

        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(320)
        main_layout.addWidget(left_widget)

        # --- Right panel: preview ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        preview_title = QLabel("Podgląd")
        preview_title.setObjectName("titleLabel")
        right_panel.addWidget(preview_title)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("previewArea")
        self.scroll.setWidgetResizable(True)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        self.preview_label.setStyleSheet("background: transparent;")
        self.scroll.setWidget(self.preview_label)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(Qt.GlobalColor.gray)
        self.scroll.setGraphicsEffect(shadow)

        right_panel.addWidget(self.scroll, stretch=1)

        # Navigation
        nav = QHBoxLayout()
        nav.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.setSpacing(12)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("navBtn")
        self.btn_prev.setToolTip("Poprzednia strona")
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        nav.addWidget(self.btn_prev)

        self.page_label = QLabel("— / —")
        self.page_label.setObjectName("pageLabel")
        nav.addWidget(self.page_label)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("navBtn")
        self.btn_next.setToolTip("Następna strona")
        self.btn_next.clicked.connect(self._next_page)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        nav.addWidget(self.btn_next)

        right_panel.addLayout(nav)
        main_layout.addLayout(right_panel, stretch=1)

        self._update_location_display()

    # --- File browsing ---

    def _load_test_pdf(self):
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), "print_pdf_test.pdf")
        try:
            create_test_pdf(tmp)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wygenerować PDF testowego:\n{e}")
            return
        # Load test file without changing save_dir
        saved_dir = self.save_dir
        self._load_input(tmp)
        self.save_dir = saved_dir
        self._update_location_display()

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz PDF", "", "PDF (*.pdf)")
        if path:
            self._load_input(path)

    def _load_input(self, path: str):
        self.input_edit.setText(path)
        self.input_edit.setToolTip(os.path.basename(path))
        self.save_dir = os.path.dirname(path)
        self._update_location_display()
        base = os.path.splitext(os.path.basename(path))[0]
        if self.cb_duplex.isChecked():
            self.output1_edit.setText(f"{base}_print_odd.pdf")
            self.output2_edit.setText(f"{base}_print_even.pdf")
        else:
            self.output1_edit.setText(f"{base}_print.pdf")

        import fitz as _fitz
        doc = _fitz.open(path)
        n = len(doc)
        doc.close()
        self.spin_from.setMaximum(n)
        self.spin_to.setMaximum(n)
        self.spin_from.setValue(1)
        self.spin_to.setValue(n)
        self.print_btn.setEnabled(True)

        self.current_page = 0
        self._regenerate_preview_pdfs(path)
        self._update_preview_buttons()
        self._update_preview()

    # --- Duplex toggle ---

    def _on_duplex_changed(self, _state=None):
        is_duplex = self.cb_duplex.isChecked()

        # Pliki section
        self.output2_file_row.setVisible(is_duplex)

        # Zapis section
        self.lbl_save_output2.setVisible(is_duplex)
        self.output2_edit.setVisible(is_duplex)

        if is_duplex:
            self.preview_lbl_output1.setText("Podgląd nieparzyste")
            self.lbl_save_output1.setText("Strony nieparzyste")
            current = self.output1_edit.text()
            base = current.replace(".pdf", "").replace("_print", "")
            self.output1_edit.setText(f"{base}_print_odd.pdf")
            self.output2_edit.setText(f"{base}_print_even.pdf")
            if self.preview_mode == "processed":
                self.preview_mode = "odd"
        else:
            self.preview_lbl_output1.setText("Podgląd")
            self.lbl_save_output1.setText("Plik wyjściowy")
            current = self.output1_edit.text()
            base = current.replace(".pdf", "").replace("_print_odd", "").replace("_print", "")
            self.output1_edit.setText(f"{base}_print.pdf")
            self.output2_edit.clear()
            if self.preview_mode in ("odd", "even"):
                self.preview_mode = "processed"

        self.current_page = 0
        self._regenerate_preview_pdfs()
        self._update_preview_buttons()
        self._update_preview()

    def _on_range_changed(self, _state=None):
        enabled = self.cb_range.isChecked()
        self.spin_from.setEnabled(enabled)
        self.spin_to.setEnabled(enabled)
        self._on_option_changed()

    def _on_option_changed(self, _state=None):
        self.current_page = 0
        self._regenerate_preview_pdfs()
        self._update_preview()

    # --- Preview mode ---

    def _set_preview_mode(self, mode: str):
        self.preview_mode = mode
        self.current_page = 0
        self._update_preview_buttons()
        self._update_preview()

    def _preview_output1(self):
        mode = "odd" if self.cb_duplex.isChecked() else "processed"
        self._set_preview_mode(mode)

    def _update_preview_buttons(self):
        mode_to_btn = {
            "input": self.btn_preview_input,
            "processed": self.btn_preview_output1,
            "odd": self.btn_preview_output1,
            "even": self.btn_preview_output2,
        }
        active_btn = mode_to_btn.get(self.preview_mode)
        for btn in (self.btn_preview_input, self.btn_preview_output1, self.btn_preview_output2):
            name = "iconBtnActive" if btn is active_btn else "iconBtn"
            btn.setObjectName(name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # --- Tooltips ---

    def _update_output_tooltips(self):
        name1 = self.output1_edit.text()
        self.output1_edit.setToolTip(name1)
        name2 = self.output2_edit.text()
        self.output2_edit.setToolTip(name2)

    # --- Location ---

    def _update_location_display(self):
        if self.save_dir:
            display = self.save_dir
            if len(display) > 45:
                display = "..." + display[-42:]
            self.location_btn.setText(display)
            self.location_btn.setToolTip(self.save_dir)
        else:
            self.location_btn.setText("(nie wybrano)")
            self.location_btn.setToolTip("")
        self._update_output_tooltips()

    def _open_save_dir(self):
        if self.save_dir and os.path.isdir(self.save_dir):
            subprocess.Popen(["xdg-open", self.save_dir])
        else:
            QMessageBox.warning(self, "Brak lokalizacji", "Nie wybrano pliku wejściowego.")

    # --- Open external ---

    def _open_input_external(self):
        path = self.input_edit.text()
        if path and os.path.isfile(path):
            subprocess.Popen(["xdg-open", path])
        else:
            QMessageBox.warning(self, "Brak pliku", "Nie wybrano pliku wejściowego.")

    def _open_output_external(self, which: int):
        key = ("odd" if self.cb_duplex.isChecked() else "processed") if which == 1 else "even"
        pdf_path = self._preview_pdfs.get(key)
        if pdf_path and os.path.isfile(pdf_path):
            subprocess.Popen(["xdg-open", pdf_path])
        else:
            QMessageBox.warning(
                self,
                "Brak podglądu",
                "Załaduj plik wejściowy, aby wygenerować podgląd.",
            )

    # --- Preview ---

    def _page_range(self) -> tuple[int, int]:
        if self.cb_range.isChecked():
            return self.spin_from.value(), self.spin_to.value()
        return 0, 0

    def _regenerate_preview_pdfs(self, path: str = None):
        if path is None:
            path = self.input_edit.text()
        if not path:
            return
        page_from, page_to = self._page_range()
        try:
            self._preview_pdfs = prepare_preview_pdfs(
                input_path=path,
                page_numbers=self.cb_numbers.isChecked(),
                two_up=self.cb_two_up.isChecked(),
                landscape=self.cb_landscape.isChecked(),
                duplex=self.cb_duplex.isChecked(),
                page_from=page_from,
                page_to=page_to,
            )
        except Exception as e:
            QMessageBox.critical(self, "Błąd podglądu", str(e))

    def _update_preview(self, _state=None):
        path = self.input_edit.text()
        if not path:
            return

        try:
            if self.preview_mode == "input":
                png_bytes, total = render_preview(
                    input_path=path,
                    preview_mode="input",
                    page_index=self.current_page,
                    target_width=1200,
                )
            else:
                pdf_path = self._preview_pdfs.get(self.preview_mode)
                if not pdf_path or not os.path.isfile(pdf_path):
                    return
                png_bytes, total = render_page_from_pdf(
                    pdf_path,
                    page_index=self.current_page,
                    target_width=1200,
                )
            self.total_pages = total
        except Exception as e:
            QMessageBox.critical(self, "Błąd podglądu", str(e))
            return

        qimg = QImage.fromData(png_bytes)
        self._current_pixmap = QPixmap.fromImage(qimg)
        self._fit_preview()
        self.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")

    def _fit_preview(self):
        if self._current_pixmap is None:
            return
        viewport = self.scroll.viewport().size()
        margin = 20
        available_w = viewport.width() - margin
        available_h = viewport.height() - margin
        scaled = self._current_pixmap.scaled(
            available_w,
            available_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_preview()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_preview()

    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_preview()

    # --- Save ---

    def _validate_for_save(self) -> bool:
        if not self.input_edit.text():
            QMessageBox.warning(self, "Brak pliku", "Wybierz plik wejściowy.")
            return False
        if not self.output1_edit.text():
            QMessageBox.warning(self, "Brak nazwy", "Podaj nazwę pliku wyjściowego.")
            return False
        if self.cb_duplex.isChecked() and not self.output2_edit.text():
            QMessageBox.warning(
                self, "Brak nazwy", "Podaj nazwę pliku dla stron parzystych."
            )
            return False
        return True

    def _do_save(self, save_dir: str):
        if not self._validate_for_save():
            return
        if not self._preview_pdfs:
            QMessageBox.warning(self, "Brak podglądu", "Załaduj plik wejściowy.")
            return

        import shutil
        try:
            outputs = []
            if self.cb_duplex.isChecked():
                for key, name_edit in [
                    ("odd", self.output1_edit),
                    ("even", self.output2_edit),
                ]:
                    src = self._preview_pdfs.get(key)
                    dst = os.path.join(save_dir, name_edit.text())
                    shutil.copy2(src, dst)
                    outputs.append(dst)
            else:
                src = self._preview_pdfs.get("processed")
                dst = os.path.join(save_dir, self.output1_edit.text())
                shutil.copy2(src, dst)
                outputs.append(dst)
            QMessageBox.information(
                self, "Gotowe", "Utworzono pliki:\n" + "\n".join(outputs)
            )
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def _print_document(self):
        if not self._preview_pdfs:
            QMessageBox.warning(self, "Brak podglądu", "Załaduj plik wejściowy.")
            return

        is_duplex = self.cb_duplex.isChecked()

        if is_duplex:
            even_path = self._preview_pdfs.get("even")
            odd_path = self._preview_pdfs.get("odd")
            if not even_path or not odd_path:
                QMessageBox.warning(self, "Błąd", "Brak plików podglądu duplex.")
                return

            QMessageBox.information(
                self, "Drukowanie", "Drukuję strony parzyste..."
            )
            ok, msg = print_pdf_file(even_path)
            if not ok:
                QMessageBox.critical(self, "Błąd drukowania", msg)
                return

            reply = QMessageBox.information(
                self,
                "Przekręć kartki",
                "Przekręć kartki na drukarce aby wydrukować strony nieparzyste.\n\n"
                "Naciśnij OK gdy jesteś gotowy.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                return

            QMessageBox.information(
                self, "Drukowanie", "Drukuję strony nieparzyste..."
            )
            ok, msg = print_pdf_file(odd_path)
            if not ok:
                QMessageBox.critical(self, "Błąd drukowania", msg)
        else:
            processed_path = self._preview_pdfs.get("processed")
            if not processed_path:
                QMessageBox.warning(self, "Błąd", "Brak pliku podglądu.")
                return
            QMessageBox.information(
                self, "Drukowanie", "Drukuję dokument..."
            )
            ok, msg = print_pdf_file(processed_path)
            if not ok:
                QMessageBox.critical(self, "Błąd drukowania", msg)

    def _save_default(self):
        if not self.save_dir:
            QMessageBox.warning(
                self, "Brak lokalizacji", "Najpierw wybierz plik wejściowy."
            )
            return
        self._do_save(self.save_dir)

    def _save_choose_location(self):
        if not self._validate_for_save():
            return
        chosen = QFileDialog.getExistingDirectory(
            self, "Wybierz lokalizację zapisu", self.save_dir or ""
        )
        if chosen:
            self.save_dir = chosen
            self._update_location_display()
            self._do_save(chosen)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))
    window = PrintPdfApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
