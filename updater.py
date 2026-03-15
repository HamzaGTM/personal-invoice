import os
import sys
import subprocess
import urllib.request
import json

CURRENT_VERSION = "v1.8.0"
REPO = "HamzaGTM/personal-invoice"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
SETTINGS_DIR = os.path.expanduser("~/.invoicer")
CHANGELOG_FILE = os.path.join(SETTINGS_DIR, "pending_changelog.json")


def get_latest_release():
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "PersonalInvoice"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def check_and_update(parent_widget=None):
    release = get_latest_release()
    if not release:
        return

    latest_version = release.get("tag_name", "")
    if latest_version == CURRENT_VERSION:
        return

    exe_url = None
    for asset in release.get("assets", []):
        if asset["name"].endswith(".exe"):
            exe_url = asset["browser_download_url"]
            break
    if not exe_url:
        return

    from PyQt6.QtWidgets import QMessageBox
    msg = QMessageBox(parent_widget)
    msg.setWindowTitle("Update Available")
    msg.setText(f"Version {latest_version} is available.\n\nWould you like to update now?")
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    if msg.exec() != QMessageBox.StandardButton.Yes:
        return

    current_exe = sys.executable if getattr(sys, "frozen", False) else None
    if not current_exe:
        return

    _show_download_dialog(parent_widget, exe_url, latest_version, release, current_exe)


def _show_download_dialog(parent_widget, exe_url, latest_version, release, current_exe):
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
    )
    from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal

    class Downloader(QObject):
        progress = pyqtSignal(int)
        finished = pyqtSignal()
        error = pyqtSignal(str)

        def __init__(self, url, dest):
            super().__init__()
            self.url = url
            self.dest = dest

        def run(self):
            try:
                req = urllib.request.Request(self.url, headers={"User-Agent": "PersonalInvoice"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    total = int(r.headers.get("Content-Length", 0))
                    downloaded = 0
                    with open(self.dest, "wb") as f:
                        while True:
                            chunk = r.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                self.progress.emit(int(downloaded * 100 / total))
                self.finished.emit()
            except Exception as e:
                self.error.emit(str(e))

    dlg = QDialog(parent_widget)
    dlg.setWindowTitle("Updating InvoiceR")
    dlg.setFixedSize(440, 200)
    dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
    dlg.setStyleSheet("background: #1A1A1A;")

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(16)

    status_lbl = QLabel(f"Downloading {latest_version}...")
    status_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600; background: transparent;")
    layout.addWidget(status_lbl)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setFixedHeight(22)
    bar.setStyleSheet("""
        QProgressBar {
            background: #2A2A2A;
            border: 1px solid #3A3A3A;
            border-radius: 8px;
            color: white;
            font-size: 11px;
            text-align: center;
        }
        QProgressBar::chunk {
            background: #6C63FF;
            border-radius: 7px;
        }
    """)
    layout.addWidget(bar)

    sub_lbl = QLabel("Please wait while the update is being downloaded.")
    sub_lbl.setStyleSheet("color: #AAAAAA; font-size: 11px; background: transparent;")
    layout.addWidget(sub_lbl)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    restart_btn = QPushButton("Restart Now")
    restart_btn.setVisible(False)
    restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    restart_btn.setFixedHeight(38)
    restart_btn.setStyleSheet("""
        QPushButton {
            background: #6C63FF; color: white; border: none;
            border-radius: 8px; padding: 0 28px;
            font-size: 13px; font-weight: bold;
        }
        QPushButton:hover { background: #5a52e0; }
    """)
    btn_row.addWidget(restart_btn)
    layout.addLayout(btn_row)

    import tempfile
    new_exe = os.path.join(tempfile.gettempdir(), "InvoiceR_update.exe")

    thread = QThread()
    worker = Downloader(exe_url, new_exe)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.progress.connect(bar.setValue)

    def on_finished():
        thread.quit()
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        notes = release.get("body", "").strip() or "Bug fixes and improvements."
        with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": latest_version, "notes": notes}, f)
        status_lbl.setText("Download complete!")
        status_lbl.setStyleSheet("color: #5CDB95; font-size: 14px; font-weight: 600; background: transparent;")
        sub_lbl.setText("Click 'Restart Now' to apply the update.")
        bar.setValue(100)
        restart_btn.setVisible(True)

    def on_error(msg):
        thread.quit()
        from PyQt6.QtWidgets import QMessageBox
        dlg.reject()
        QMessageBox.critical(parent_widget, "Update Failed", f"Could not download update:\n{msg}")

    def on_restart():
        ps_cmd = (
            f"Start-Sleep -Seconds 4; "
            f"Copy-Item -Path '{new_exe}' -Destination '{current_exe}' -Force; "
            f"Remove-Item -Path '{new_exe}' -Force -ErrorAction SilentlyContinue; "
            f"Start-Process -FilePath '{current_exe}'"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        sys.exit(0)

    worker.finished.connect(on_finished)
    worker.error.connect(on_error)
    restart_btn.clicked.connect(on_restart)

    thread.start()
    dlg.exec()


def show_pending_changelog(parent_widget=None):
    if not os.path.exists(CHANGELOG_FILE):
        return
    try:
        with open(CHANGELOG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        os.remove(CHANGELOG_FILE)
    except Exception:
        return

    version = data.get("version", "")
    notes = data.get("notes", "")

    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
    from PyQt6.QtCore import Qt

    dlg = QDialog(parent_widget)
    dlg.setWindowTitle(f"Updated to {version}")
    dlg.setMinimumWidth(460)
    dlg.setStyleSheet("background: #1A1A1A;")

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(28, 24, 28, 24)
    layout.setSpacing(14)

    title = QLabel(f"What's new in {version}")
    title.setStyleSheet("color: #6C63FF; font-size: 18px; font-weight: bold; background: transparent;")
    layout.addWidget(title)

    box = QTextEdit()
    box.setReadOnly(True)
    box.setPlainText(notes)
    box.setStyleSheet("""
        QTextEdit {
            background: #2A2A2A;
            color: #FFFFFF;
            border: 1px solid #3A3A3A;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
        }
    """)
    box.setFixedHeight(180)
    layout.addWidget(box)

    close_btn = QPushButton("Got it!")
    close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    close_btn.setStyleSheet("""
        QPushButton {
            background: #6C63FF; color: white; border: none;
            border-radius: 8px; padding: 10px 28px;
            font-size: 13px; font-weight: bold;
        }
        QPushButton:hover { background: #5a52e0; }
    """)
    close_btn.clicked.connect(dlg.accept)
    layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    dlg.exec()
