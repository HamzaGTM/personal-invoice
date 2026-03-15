import os
import sys
import subprocess
import urllib.request
import json

CURRENT_VERSION = "v1.1.0"
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
    msg.setText(f"A new version is available: {latest_version}\n\nWould you like to update now?")
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)
    if msg.exec() != QMessageBox.StandardButton.Yes:
        return

    current_exe = sys.executable if getattr(sys, "frozen", False) else None
    if not current_exe:
        return

    new_exe = current_exe + ".new"
    old_exe = current_exe + ".old"

    try:
        req = urllib.request.Request(exe_url, headers={"User-Agent": "PersonalInvoice"})
        with urllib.request.urlopen(req, timeout=60) as r, open(new_exe, "wb") as f:
            while chunk := r.read(65536):
                f.write(chunk)
    except Exception as e:
        QMessageBox.critical(parent_widget, "Update Failed", f"Could not download update:\n{e}")
        return

    # Save changelog so it shows on next launch
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    notes = release.get("body", "").strip() or "Bug fixes and improvements."
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"version": latest_version, "notes": notes}, f)

    bat = current_exe + "_update.bat"
    with open(bat, "w") as f:
        f.write(f"""@echo off
ping -n 3 127.0.0.1 > nul
move /Y "{current_exe}" "{old_exe}"
move /Y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")

    subprocess.Popen(["cmd", "/c", bat], creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit(0)


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

    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
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
