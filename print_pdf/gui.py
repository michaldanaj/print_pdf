"""GUI for print-pdf with live preview (PyQt6)."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QImage, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from print_pdf.core import process_pdf, render_preview

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

QPushButton#browseBtn {
    padding: 5px 10px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #f0f0f0;
}
QPushButton#browseBtn:hover {
    background: #e0e0e0;
}

QCheckBox {
    spacing: 6px;
    padding: 3px 0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
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

QPushButton#navBtn {
    padding: 6px 14px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #ffffff;
}
QPushButton#navBtn:hover {
    background: #e8f0fe;
    border-color: #5b9bd5;
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
"""


class PrintPdfApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("centralWidget")
        self.setWindowTitle("Print PDF - Przygotowanie wydruku")
        self.setMinimumSize(800, 580)

        self.current_page = 0
        self.total_pages = 0
        self._current_pixmap: QPixmap | None = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # --- Left panel ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        # Title
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

        lbl_input = QLabel("Plik wejściowy")
        lbl_input.setObjectName("sectionLabel")
        file_layout.addWidget(lbl_input)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Wybierz plik PDF...")
        input_row.addWidget(self.input_edit)
        browse_btn = QPushButton("Otwórz")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setToolTip("Wybierz plik PDF do przetworzenia")
        browse_btn.clicked.connect(self._browse_input)
        input_row.addWidget(browse_btn)
        file_layout.addLayout(input_row)

        lbl_output = QLabel("Nazwa wyjściowa")
        lbl_output.setObjectName("sectionLabel")
        file_layout.addWidget(lbl_output)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("bez rozszerzenia .pdf")
        self.output_edit.setToolTip("Bazowa nazwa pliku wyjściowego (bez rozszerzenia)")
        file_layout.addWidget(self.output_edit)

        left_panel.addWidget(file_group)

        # --- Options group ---
        opts_group = QGroupBox("Opcje wydruku")
        opts_layout = QVBoxLayout(opts_group)
        opts_layout.setSpacing(4)

        self.cb_landscape = QCheckBox("Orientacja pozioma")
        self.cb_landscape.setToolTip("Układ poziomy (landscape) zamiast pionowego")
        self.cb_landscape.stateChanged.connect(self._update_preview)
        opts_layout.addWidget(self.cb_landscape)

        self.cb_two_up = QCheckBox("2 strony na arkuszu")
        self.cb_two_up.setToolTip("Umieszcza dwie strony źródłowe na jednym arkuszu")
        self.cb_two_up.stateChanged.connect(self._update_preview)
        opts_layout.addWidget(self.cb_two_up)

        self.cb_numbers = QCheckBox("Numery stron")
        self.cb_numbers.setToolTip("Dodaje numery stron na dolnym marginesie")
        self.cb_numbers.stateChanged.connect(self._update_preview)
        opts_layout.addWidget(self.cb_numbers)

        self.cb_duplex = QCheckBox("Druk dwustronny (ręczny)")
        self.cb_duplex.setToolTip(
            "Rozdziela strony parzyste i nieparzyste do osobnych plików\n"
            "z odwróconą kolejnością, do ręcznego druku dwustronnego"
        )
        self.cb_duplex.stateChanged.connect(self._update_preview)
        opts_layout.addWidget(self.cb_duplex)

        left_panel.addWidget(opts_group)

        # Generate button
        left_panel.addSpacing(8)
        gen_btn = QPushButton("Generuj PDF")
        gen_btn.setObjectName("generateBtn")
        gen_btn.setToolTip("Przetwórz i zapisz wynikowy PDF")
        gen_btn.clicked.connect(self._generate)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        left_panel.addWidget(gen_btn)

        left_panel.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(280)
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
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
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

        self.btn_prev = QPushButton("  Poprzednia")
        self.btn_prev.setObjectName("navBtn")
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        nav.addWidget(self.btn_prev)

        self.page_label = QLabel("— / —")
        self.page_label.setObjectName("pageLabel")
        nav.addWidget(self.page_label)

        self.btn_next = QPushButton("Następna  ")
        self.btn_next.setObjectName("navBtn")
        self.btn_next.clicked.connect(self._next_page)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        nav.addWidget(self.btn_next)

        right_panel.addLayout(nav)
        main_layout.addLayout(right_panel, stretch=1)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz PDF", "", "PDF (*.pdf)")
        if path:
            self.input_edit.setText(path)
            if not self.output_edit.text():
                self.output_edit.setText(path.rsplit(".", 1)[0] + "_print")
            self.current_page = 0
            self._update_preview()

    def _update_preview(self, _state=None):
        path = self.input_edit.text()
        if not path:
            return

        try:
            png_bytes, total = render_preview(
                input_path=path,
                page_numbers=self.cb_numbers.isChecked(),
                two_up=self.cb_two_up.isChecked(),
                landscape=self.cb_landscape.isChecked(),
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
            available_w, available_h,
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

    def _generate(self):
        path = self.input_edit.text()
        base = self.output_edit.text()
        if not path:
            QMessageBox.warning(self, "Brak pliku", "Wybierz plik wejściowy.")
            return
        if not base:
            QMessageBox.warning(self, "Brak nazwy", "Podaj nazwę pliku wyjściowego.")
            return

        try:
            outputs = process_pdf(
                input_path=path,
                output_base=base,
                duplex=self.cb_duplex.isChecked(),
                page_numbers=self.cb_numbers.isChecked(),
                two_up=self.cb_two_up.isChecked(),
                landscape=self.cb_landscape.isChecked(),
            )
            QMessageBox.information(self, "Gotowe", "Utworzono pliki:\n" + "\n".join(outputs))
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))
    window = PrintPdfApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
