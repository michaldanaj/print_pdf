"""GUI for print-pdf with live preview (PyQt6)."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
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


class PrintPdfApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Print PDF - Przygotowanie wydruku")
        self.setMinimumSize(750, 550)

        self.current_page = 0
        self.total_pages = 0
        self._current_pixmap: QPixmap | None = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left panel: options ---
        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Input file
        left.addWidget(QLabel("Plik wejściowy:"))
        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Wybierz plik PDF...")
        input_row.addWidget(self.input_edit)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.setToolTip("Wybierz plik PDF do przetworzenia")
        browse_btn.clicked.connect(self._browse_input)
        input_row.addWidget(browse_btn)
        left.addLayout(input_row)

        # Output base
        left.addWidget(QLabel("Nazwa wyjściowa (bez .pdf):"))
        self.output_edit = QLineEdit()
        self.output_edit.setToolTip("Bazowa nazwa pliku wyjściowego (bez rozszerzenia)")
        left.addWidget(self.output_edit)

        # Separator
        left.addSpacing(12)

        # Checkboxes
        self.cb_landscape = QCheckBox("Orientacja pozioma")
        self.cb_landscape.setToolTip("Układ poziomy (landscape) zamiast pionowego")
        self.cb_landscape.stateChanged.connect(self._update_preview)
        left.addWidget(self.cb_landscape)

        self.cb_two_up = QCheckBox("2 strony na arkuszu")
        self.cb_two_up.setToolTip("Umieszcza dwie strony źródłowe na jednym arkuszu")
        self.cb_two_up.stateChanged.connect(self._update_preview)
        left.addWidget(self.cb_two_up)

        self.cb_numbers = QCheckBox("Numery stron")
        self.cb_numbers.setToolTip("Dodaje numery stron na dolnym marginesie")
        self.cb_numbers.stateChanged.connect(self._update_preview)
        left.addWidget(self.cb_numbers)

        self.cb_duplex = QCheckBox("Druk dwustronny (ręczny)")
        self.cb_duplex.setToolTip(
            "Rozdziela strony parzyste i nieparzyste do osobnych plików\n"
            "z odwróconą kolejnością, do ręcznego druku dwustronnego"
        )
        self.cb_duplex.stateChanged.connect(self._update_preview)
        left.addWidget(self.cb_duplex)

        left.addSpacing(12)

        # Generate button
        gen_btn = QPushButton("Generuj PDF")
        gen_btn.setToolTip("Przetwórz i zapisz wynikowy PDF")
        gen_btn.clicked.connect(self._generate)
        left.addWidget(gen_btn)

        left.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(260)
        main_layout.addWidget(left_widget)

        # --- Right panel: preview ---
        right = QVBoxLayout()

        right.addWidget(QLabel("<b>Podgląd:</b>"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #e0e0e0;")
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.preview_label)
        right.addWidget(self.scroll, stretch=1)

        # Navigation
        nav = QHBoxLayout()
        nav.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_prev = QPushButton("◀ Poprzednia")
        self.btn_prev.clicked.connect(self._prev_page)
        nav.addWidget(self.btn_prev)

        self.page_label = QLabel("— / —")
        nav.addWidget(self.page_label)

        self.btn_next = QPushButton("Następna ▶")
        self.btn_next.clicked.connect(self._next_page)
        nav.addWidget(self.btn_next)

        right.addLayout(nav)
        main_layout.addLayout(right, stretch=1)

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
        margin = 10
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
    window = PrintPdfApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
