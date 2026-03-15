import sys
import os
import subprocess
import shutil
from datetime import date

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QDialog, QSizePolicy, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QThread, pyqtSignal, QObject, QRect
)
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QIcon

from editor import InvoiceEditorWidget
from pdf_gen import build_pdf
from settings import load_settings, save_settings
from updater import check_and_update, show_pending_changelog

ACCENT = "#6C63FF"
BG = "#1A1A1A"
CARD = "#2A2A2A"
TEXT = "#FFFFFF"
SUBTEXT = "#AAAAAA"
BORDER = "#3A3A3A"

DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Invoices")


def resource_path(relative):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


# ── PDF Worker Thread ─────────────────────────────────────────────────────────

class PdfWorker(QObject):
    finished = pyqtSignal(str)   # output path
    error = pyqtSignal(str)

    def __init__(self, data: dict, output_path: str):
        super().__init__()
        self.data = data
        self.output_path = output_path

    def run(self):
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            build_pdf(self.output_path, self.data)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


# ── Spinner Widget ────────────────────────────────────────────────────────────

class SpinnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height())
        cx, cy = self.width() // 2, self.height() // 2
        r = size // 2 - 4
        pen = QPen(QColor(ACCENT), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.translate(cx, cy)
        p.rotate(self._angle)
        p.drawArc(-r, -r, r * 2, r * 2, 0, 270 * 16)

    def stop(self):
        self._timer.stop()


# ── Generating Overlay ────────────────────────────────────────────────────────

class GeneratingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        # Semi-transparent backdrop
        self.setStyleSheet("background: rgba(0,0,0,0);")

        # Center the card
        backdrop_layout = QVBoxLayout(self)
        backdrop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The card itself
        self.card = QFrame()
        self.card.setFixedWidth(420)
        self.card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spinner = SpinnerWidget()
        self.spinner.setFixedSize(56, 56)
        card_layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_lbl = QLabel("Rendering your invoice...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600; background: transparent;")
        card_layout.addWidget(self.status_lbl)

        self.path_lbl = QLabel("")
        self.path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_lbl.setWordWrap(True)
        self.path_lbl.setFixedWidth(340)
        self.path_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px; background: transparent;")
        self.path_lbl.hide()
        card_layout.addWidget(self.path_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_widget = QWidget()
        btn_widget.setStyleSheet("background: transparent;")
        self.btn_row = QHBoxLayout(btn_widget)
        self.btn_row.setSpacing(10)
        self.btn_row.setContentsMargins(0, 8, 0, 0)
        self.btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.open_folder_btn = self._make_btn("Open Folder", primary=True)
        self.save_as_btn = self._make_btn("Save As...")
        self.close_btn = self._make_btn("Close")

        for btn in (self.open_folder_btn, self.save_as_btn, self.close_btn):
            self.btn_row.addWidget(btn)

        btn_widget.hide()
        self.btn_container = btn_widget
        card_layout.addWidget(btn_widget)

        backdrop_layout.addWidget(self.card)

    def paintEvent(self, event):
        from PyQt6.QtGui import QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 180))

    def _make_btn(self, text, primary=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ACCENT}; color: white; border: none;
                    border-radius: 8px; padding: 9px 18px; font-size: 12px; font-weight: bold;
                }}
                QPushButton:hover {{ background: #5a52e0; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {SUBTEXT};
                    border: 1px solid {BORDER}; border-radius: 8px;
                    padding: 9px 18px; font-size: 12px;
                }}
                QPushButton:hover {{ border-color: {ACCENT}; color: {TEXT}; }}
            """)
        return btn

    def show_success(self, path: str):
        self.spinner.stop()
        self.spinner.hide()
        self.status_lbl.setText("Invoice saved!")
        self.status_lbl.setStyleSheet(f"color: #5CDB95; font-size: 18px; font-weight: bold; background: transparent;")
        self.path_lbl.setText(path)
        self.path_lbl.show()
        self.btn_container.show()

    def show_error(self, msg: str):
        self.spinner.stop()
        self.spinner.hide()
        self.status_lbl.setText(f"Error: {msg}")
        self.status_lbl.setStyleSheet(f"color: #FF6B6B; font-size: 14px; background: transparent;")
        self.btn_container.show()


# ── Save Payment Dialog ───────────────────────────────────────────────────────

class SavePaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(400, 180)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        lbl = QLabel("Save your payment details for next time?")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 14px; background: transparent;")
        layout.addWidget(lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        yes_btn = QPushButton("Yes, Save")
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: white; border: none;
                border-radius: 8px; padding: 10px 28px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #5a52e0; }}
        """)
        yes_btn.clicked.connect(self.accept)

        no_btn = QPushButton("No thanks")
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {SUBTEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                padding: 10px 28px; font-size: 13px;
            }}
            QPushButton:hover {{ color: {TEXT}; border-color: #555; }}
        """)
        no_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(yes_btn)
        btn_row.addWidget(no_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)


# ── Splash Screen ─────────────────────────────────────────────────────────────

class SplashScreen(QWidget):
    done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background: {BG};")
        self.setFixedSize(520, 300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Welcome to your\npersonal invoicing")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"""
            color: {TEXT};
            font-size: 30px;
            font-weight: 300;
            background: transparent;
            line-height: 1.4;
        """)
        layout.addWidget(self.label)

        sub = QLabel("Professional invoices, instantly.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {ACCENT}; font-size: 14px; background: transparent; margin-top: 10px;")
        layout.addWidget(sub)

        # Fade in
        self._opacity = 0.0
        self.setWindowOpacity(0.0)
        self._fade_in()

    def _fade_in(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(700)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self._wait)
        self._anim.start()

    def _wait(self):
        QTimer.singleShot(1400, self._fade_out)

    def _fade_out(self):
        self._anim2 = QPropertyAnimation(self, b"windowOpacity")
        self._anim2.setDuration(500)
        self._anim2.setStartValue(1.0)
        self._anim2.setEndValue(0.0)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim2.finished.connect(self._finish)
        self._anim2.start()

    def _finish(self):
        self.hide()
        self.done.emit()


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Invoice")
        self.setMinimumSize(900, 700)
        self.resize(1050, 820)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        self._generated_path = None
        self._thread = None
        self._worker = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Top bar ───────────────────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet(f"background: {BG}; border-bottom: 1px solid #2E2E2E;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(16, 0, 16, 0)
        top_bar_layout.addStretch()

        self.save_dir_btn = QPushButton("Default Save Place")
        self.save_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {SUBTEXT};
                border: 1px solid #3A3A3A;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {TEXT};
                border-color: {ACCENT};
            }}
        """)
        self.save_dir_btn.clicked.connect(self._ask_save_dir)
        top_bar_layout.addWidget(self.save_dir_btn)
        root.addWidget(top_bar)

        self.editor = InvoiceEditorWidget()
        root.addWidget(self.editor)

        self.editor.generate_btn.clicked.connect(self._generate_pdf)

        # Overlay (hidden)
        self.overlay = GeneratingOverlay(central)
        self.overlay.hide()
        self.overlay.open_folder_btn.clicked.connect(self._open_folder)
        self.overlay.save_as_btn.clicked.connect(self._save_as)
        self.overlay.close_btn.clicked.connect(self._close_overlay)

        # Ask for save directory on first launch
        if not load_settings().get("save_dir"):
            QTimer.singleShot(200, self._ask_save_dir)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.centralWidget().rect())

    def _ask_save_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Where would you like to save your invoices?",
            os.path.expanduser("~"),
        )
        if folder:
            save_settings({"save_dir": folder})
        else:
            # User cancelled — use default and save it
            os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)
            save_settings({"save_dir": DEFAULT_SAVE_DIR})

    def _generate_pdf(self):
        data = self.editor.get_invoice_data()
        inv_num = data["invoice_number"]
        filename = f"INV-{inv_num}.pdf"
        save_dir = load_settings().get("save_dir", DEFAULT_SAVE_DIR)
        os.makedirs(save_dir, exist_ok=True)
        output_path = os.path.join(save_dir, filename)

        self.overlay.setGeometry(self.centralWidget().rect())
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.status_lbl.setText("Rendering your invoice...")
        self.overlay.status_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 16px; background: transparent;"
        )
        self.overlay.spinner.show()
        self.overlay.path_lbl.hide()
        self.overlay.btn_container.hide()

        self._thread = QThread()
        self._worker = PdfWorker(data, output_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_pdf_done)
        self._worker.error.connect(self._on_pdf_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_pdf_done(self, path: str):
        self._generated_path = path
        self.overlay.show_success(path)

        # Increment invoice number
        settings = load_settings()
        try:
            current = int(self.editor.inv_number.text())
        except ValueError:
            current = settings.get("last_invoice_number", 1)
        save_settings({"last_invoice_number": current + 1})
        self.editor.inv_number.setText(str(current + 1).zfill(4))

        # Ask to save payment details — only if not already saved
        if not load_settings().get("payment_saved"):
            QTimer.singleShot(300, self._ask_save_payment)

    def _on_pdf_error(self, msg: str):
        self.overlay.show_error(msg)

    def _ask_save_payment(self):
        dlg = SavePaymentDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = self.editor.get_invoice_data()
            save_settings({
                "from_name": data["from_name"],
                "from_address": data["from_address"],
                "from_email": data["from_email"],
                "payment_details": data["payment_details"],
                "payment_saved": True,
            })
        else:
            # Mark as answered so we don't ask again
            save_settings({"payment_saved": True})

    def _open_folder(self):
        if self._generated_path:
            folder = os.path.dirname(self._generated_path)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _save_as(self):
        if not self._generated_path:
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save Invoice As",
            os.path.basename(self._generated_path),
            "PDF Files (*.pdf)"
        )
        if dest:
            shutil.copy2(self._generated_path, dest)

    def _close_overlay(self):
        self.overlay.hide()


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(QIcon(resource_path("icon.ico")))

    window = MainWindow()
    window.show()

    QTimer.singleShot(800, lambda: show_pending_changelog(window))
    QTimer.singleShot(1500, lambda: check_and_update(window))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
