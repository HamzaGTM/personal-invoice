import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFileDialog, QSlider, QScrollArea,
    QFrame, QGridLayout, QSizePolicy, QSpacerItem, QCalendarWidget, QDialog,
    QComboBox
)
from PyQt6.QtCore import Qt, QSize, QDate, QPoint
from PyQt6.QtGui import QPixmap, QFont, QDoubleValidator, QIntValidator

from settings import load_settings


ACCENT = "#6C63FF"
BG = "#1A1A1A"
CARD = "#2A2A2A"
INPUT_BG = "#333333"
TEXT = "#FFFFFF"
SUBTEXT = "#AAAAAA"
BORDER = "#3A3A3A"


def styled_label(text, bold=False, small=False, accent=False):
    lbl = QLabel(text)
    color = ACCENT if accent else (TEXT if not small else SUBTEXT)
    size = "10px" if small else "13px"
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"color: {color}; font-size: {size}; font-weight: {weight}; background: transparent;")
    return lbl


def styled_input(placeholder="", validator=None):
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    if validator:
        inp.setValidator(validator)
    inp.setStyleSheet(f"""
        QLineEdit {{
            background: {INPUT_BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT};
        }}
    """)
    return inp


def section_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {ACCENT};
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
        background: transparent;
        padding-bottom: 4px;
    """)
    return lbl


def card_frame():
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {CARD};
            border-radius: 10px;
            border: 1px solid {BORDER};
        }}
    """)
    return f


class DatePickerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("YYYY-MM-DD")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
                padding: 7px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
                border-right: none;
            }}
        """)

        self.cal_btn = QPushButton("📅")
        self.cal_btn.setFixedSize(36, 36)
        self.cal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cal_btn.setStyleSheet(f"""
            QPushButton {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                font-size: 15px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {ACCENT};
                border-color: {ACCENT};
            }}
        """)
        self.cal_btn.clicked.connect(self._open_calendar)

        layout.addWidget(self.input, stretch=1)
        layout.addWidget(self.cal_btn)

    def _open_calendar(self):
        popup = QDialog(self, Qt.WindowType.Popup)
        popup.setStyleSheet(f"""
            QDialog {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QCalendarWidget QAbstractItemView {{
                background: {CARD};
                color: {TEXT};
                selection-background-color: {ACCENT};
                selection-color: white;
                outline: none;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background: #222222;
                padding: 4px;
            }}
            QCalendarWidget QToolButton {{
                color: {TEXT};
                background: transparent;
                border: none;
                font-size: 13px;
                padding: 4px 10px;
                border-radius: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background: {ACCENT};
            }}
            QCalendarWidget QSpinBox {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 2px 6px;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background: {CARD};
                color: {TEXT};
                alternate-background-color: #252525;
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: #555555;
            }}
        """)

        cal = QCalendarWidget(popup)
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        # Pre-select current value if valid
        try:
            d = QDate.fromString(self.input.text(), "yyyy-MM-dd")
            if d.isValid():
                cal.setSelectedDate(d)
        except Exception:
            pass

        cal.clicked.connect(lambda date: self._pick_date(date, popup))

        vbox = QVBoxLayout(popup)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.addWidget(cal)

        # Position below the button
        btn_pos = self.cal_btn.mapToGlobal(QPoint(0, self.cal_btn.height()))
        popup.move(btn_pos)
        popup.exec()

    def _pick_date(self, date: QDate, popup: QDialog):
        self.input.setText(date.toString("yyyy-MM-dd"))
        popup.accept()

    def text(self):
        return self.input.text()

    def setText(self, val: str):
        self.input.setText(val)


class LineItemRow(QWidget):
    def __init__(self, parent=None, on_change=None, currency_symbol="$"):
        super().__init__(parent)
        self.on_change = on_change
        self.currency_symbol = currency_symbol
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.desc = QTextEdit()
        self.desc.setPlaceholderText("Description")
        self.desc.setMinimumWidth(220)
        self.desc.setFixedHeight(62)
        self.desc.setStyleSheet(f"""
            QTextEdit {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        self.qty = styled_input("1")
        self.qty.setValidator(QDoubleValidator(0, 99999, 2))
        self.qty.setFixedWidth(60)
        self.qty.setText("1")
        self.unit_price = styled_input("0.00")
        self.unit_price.setValidator(QDoubleValidator(0, 9999999, 2))
        self.unit_price.setFixedWidth(100)
        self.total_lbl = QLabel("$0.00")
        self.total_lbl.setFixedWidth(80)
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px; background: transparent;")

        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {SUBTEXT};
                border: none;
                font-size: 18px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ color: #FF6B6B; }}
        """)

        layout.addWidget(self.desc, stretch=1)
        layout.addWidget(self.qty, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.unit_price, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.total_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.remove_btn, alignment=Qt.AlignmentFlag.AlignTop)

        self.qty.textChanged.connect(self._recalc)
        self.unit_price.textChanged.connect(self._recalc)

    def _recalc(self):
        try:
            total = float(self.qty.text() or 0) * float(self.unit_price.text() or 0)
        except ValueError:
            total = 0.0
        self.total_lbl.setText(f"{self.currency_symbol}{total:,.2f}")
        if self.on_change:
            self.on_change()

    def set_currency(self, symbol):
        self.currency_symbol = symbol
        self._recalc()

    def get_data(self):
        try:
            qty = float(self.qty.text() or 0)
            unit = float(self.unit_price.text() or 0)
        except ValueError:
            qty, unit = 0.0, 0.0
        return {
            "description": self.desc.toPlainText(),
            "qty": qty,
            "unit_price": unit,
        }


class DiscountRow(QWidget):
    def __init__(self, parent=None, on_change=None, currency_symbol="$"):
        super().__init__(parent)
        self.on_change = on_change
        self.mode = "pct"
        self.currency_symbol = currency_symbol
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.desc = styled_input("Discount label (e.g. Early payment discount)")
        self.desc.setMinimumWidth(180)

        self.pct_btn = QPushButton("%")
        self.pct_btn.setFixedSize(34, 34)
        self.pct_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pct_btn.clicked.connect(lambda: self._set_mode("pct"))

        self.fixed_btn = QPushButton("$")
        self.fixed_btn.setFixedSize(34, 34)
        self.fixed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fixed_btn.clicked.connect(lambda: self._set_mode("fixed"))

        self.amount_input = styled_input("0")
        self.amount_input.setValidator(QDoubleValidator(0, 9999999, 2))
        self.amount_input.setFixedWidth(80)
        self.amount_input.textChanged.connect(self._on_change)

        self.discount_lbl = QLabel("-$0.00")
        self.discount_lbl.setFixedWidth(80)
        self.discount_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.discount_lbl.setStyleSheet("color: #5CDB95; font-size: 13px; background: transparent;")

        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {SUBTEXT};
                border: none; font-size: 18px; border-radius: 4px;
            }}
            QPushButton:hover {{ color: #FF6B6B; }}
        """)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self.desc, stretch=1)
        layout.addWidget(self.pct_btn)
        layout.addWidget(self.fixed_btn)
        layout.addWidget(self.amount_input)
        layout.addWidget(self.discount_lbl)
        layout.addWidget(self.remove_btn)

        self._update_toggle_style()

    def _set_mode(self, mode):
        self.mode = mode
        self._update_toggle_style()
        self._on_change()

    def _update_toggle_style(self):
        for btn, m in [(self.pct_btn, "pct"), (self.fixed_btn, "fixed")]:
            if self.mode == m:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #5CDB95; color: #1A1A1A;
                        border: none; border-radius: 6px;
                        font-size: 13px; font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {INPUT_BG}; color: {SUBTEXT};
                        border: 1px solid {BORDER}; border-radius: 6px;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{ color: {TEXT}; border-color: #5CDB95; }}
                """)

    def _on_change(self):
        if self.on_change:
            self.on_change()

    def get_value(self):
        try:
            val = float(self.amount_input.text() or 0)
        except ValueError:
            val = 0.0
        return self.mode, val

    def set_currency(self, symbol):
        self.currency_symbol = symbol

    def set_display(self, dollar_amount: float):
        self.discount_lbl.setText(f"-{self.currency_symbol}{dollar_amount:,.2f}")

    def get_data(self):
        mode, val = self.get_value()
        return {
            "description": self.desc.text(),
            "mode": mode,
            "value": val,
        }


_CURRENCIES = [
    ("USD – $",  "$"),
    ("EUR – €",  "€"),
    ("GBP – £",  "£"),
    ("PKR – ₨",  "₨"),
    ("INR – ₹",  "₹"),
    ("CNY – ¥",  "¥"),
    ("JPY – ¥",  "¥"),
    ("AED – د.إ", "د.إ"),
    ("SAR – ﷼",  "﷼"),
    ("CAD – CA$", "CA$"),
    ("AUD – A$",  "A$"),
]

_INVOICE_COLORS = [
    ("#6C63FF", "Purple"),
    ("#1A1A1A", "Black"),
    ("#E53E3E", "Red"),
    ("#38A169", "Green"),
    ("#3182CE", "Blue"),
    ("#DD6B20", "Orange"),
]


class InvoiceEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo_path = None
        self.logo_width = 120
        self.line_rows: list[LineItemRow] = []
        self.discount_rows: list[DiscountRow] = []
        self.terms_visible = False
        self.invoice_accent = "#6C63FF"
        self.currency_symbol = "$"
        self._color_btns = {}
        self._settings = load_settings()

        self.setStyleSheet(f"background: {BG};")
        self._build_ui()
        self._prefill_from_settings()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background: {BG};")
        scroll.setWidget(container)

        main = QVBoxLayout(container)
        main.setContentsMargins(32, 32, 32, 32)
        main.setSpacing(20)

        # ── Invoice Color Selector ────────────────────────────────────────────
        color_card = card_frame()
        color_outer = QHBoxLayout(color_card)
        color_outer.setContentsMargins(20, 12, 20, 12)
        color_outer.setSpacing(12)
        color_outer.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        color_lbl = section_label("INVOICE COLOR")
        color_outer.addWidget(color_lbl)
        color_outer.addSpacing(8)

        for hex_color, name in _INVOICE_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._style_color_btn(btn, hex_color, hex_color == self.invoice_accent)
            btn.clicked.connect(lambda checked, c=hex_color: self._select_invoice_color(c))
            self._color_btns[hex_color] = btn
            color_outer.addWidget(btn)

        color_outer.addStretch()
        main.addWidget(color_card)

        # ── Top row: logo + invoice meta ─────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(24)

        # Logo card
        logo_card = card_frame()
        logo_layout = QVBoxLayout(logo_card)
        logo_layout.setContentsMargins(16, 16, 16, 16)
        logo_layout.setSpacing(10)

        self.logo_label = QLabel("+ Upload Logo")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(120)
        self.logo_label.setMinimumWidth(200)
        self.logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_label.setStyleSheet(f"""
            QLabel {{
                color: {SUBTEXT};
                font-size: 14px;
                border: 2px dashed {BORDER};
                border-radius: 8px;
                background: {INPUT_BG};
            }}
            QLabel:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
        """)
        self.logo_label.mousePressEvent = self._upload_logo

        self.logo_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_slider.setMinimum(50)
        self.logo_slider.setMaximum(300)
        self.logo_slider.setValue(120)
        self.logo_slider.setToolTip("Logo width")
        self.logo_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px; background: {BORDER}; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT}; width: 14px; height: 14px;
                margin: -5px 0; border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
        """)
        self.logo_slider.valueChanged.connect(self._on_logo_slider)

        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.logo_slider)
        top_row.addWidget(logo_card, stretch=1)

        # Invoice meta card
        meta_card = card_frame()
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(20, 20, 20, 20)
        meta_layout.setSpacing(12)

        inv_title = QLabel("INVOICE")
        inv_title.setStyleSheet(f"color: {ACCENT}; font-size: 24px; font-weight: bold; background: transparent; letter-spacing: 2px;")
        meta_layout.addWidget(inv_title)

        def field_row(label_text, widget):
            row = QHBoxLayout()
            row.setSpacing(12)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(68)
            lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px; background: transparent;")
            row.addWidget(lbl)
            row.addWidget(widget, stretch=1)
            return row

        self.inv_number = styled_input("0001")
        self.inv_number.setText(str(self._settings.get("last_invoice_number", 1)).zfill(4))
        meta_layout.addLayout(field_row("#", self.inv_number))

        self.inv_date = DatePickerWidget()
        self.inv_date.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        meta_layout.addLayout(field_row("Date", self.inv_date))

        self.inv_due = DatePickerWidget()
        self.inv_due.setText(QDate.currentDate().addDays(30).toString("yyyy-MM-dd"))
        meta_layout.addLayout(field_row("Due Date", self.inv_due))

        self.currency_combo = QComboBox()
        for label, _ in _CURRENCIES:
            self.currency_combo.addItem(label)
        self.currency_combo.setStyleSheet(f"""
            QComboBox {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QComboBox:focus {{ border: 1px solid {ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{ image: none; width: 0; }}
            QComboBox QAbstractItemView {{
                background: {CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                selection-color: white;
                outline: none;
            }}
        """)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_change)
        meta_layout.addLayout(field_row("Currency", self.currency_combo))

        meta_layout.addStretch()
        top_row.addWidget(meta_card, stretch=1)
        main.addLayout(top_row)

        # ── From / Bill To ────────────────────────────────────────────────────
        contacts_row = QHBoxLayout()
        contacts_row.setSpacing(20)

        from_card = card_frame()
        from_layout = QVBoxLayout(from_card)
        from_layout.setContentsMargins(20, 16, 20, 16)
        from_layout.setSpacing(8)
        from_layout.addWidget(section_label("FROM"))
        self.from_name = styled_input("Your Name / Company")
        self.from_address = styled_input("Address")
        self.from_email = styled_input("email@example.com")
        from_layout.addWidget(self.from_name)
        from_layout.addWidget(self.from_address)
        from_layout.addWidget(self.from_email)
        contacts_row.addWidget(from_card, stretch=1)

        to_card = card_frame()
        to_layout = QVBoxLayout(to_card)
        to_layout.setContentsMargins(20, 16, 20, 16)
        to_layout.setSpacing(8)
        to_layout.addWidget(section_label("BILL TO"))
        self.to_name = styled_input("Client Name / Company")
        self.to_address = styled_input("Address")
        self.to_email = styled_input("client@example.com")
        to_layout.addWidget(self.to_name)
        to_layout.addWidget(self.to_address)
        to_layout.addWidget(self.to_email)
        contacts_row.addWidget(to_card, stretch=1)

        main.addLayout(contacts_row)

        # ── Line Items ────────────────────────────────────────────────────────
        items_card = card_frame()
        items_outer = QVBoxLayout(items_card)
        items_outer.setContentsMargins(20, 16, 20, 16)
        items_outer.setSpacing(8)

        items_outer.addWidget(section_label("LINE ITEMS"))

        # Column headers
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        for text, stretch, width in [
            ("DESCRIPTION", 1, None),
            ("QTY", 0, 60),
            ("UNIT PRICE", 0, 100),
            ("TOTAL", 0, 80),
            ("", 0, 28),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 10px; font-weight: bold; background: transparent;")
            if width:
                lbl.setFixedWidth(width)
            if text == "TOTAL":
                lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            header_row.addWidget(lbl, stretch=stretch)
        items_outer.addLayout(header_row)

        self.items_container = QVBoxLayout()
        self.items_container.setSpacing(6)
        items_outer.addLayout(self.items_container)

        # Default 3 rows
        for _ in range(3):
            self._add_line_item()

        add_btn = QPushButton("+ Add Line")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {ACCENT}22; }}
        """)
        add_btn.clicked.connect(self._add_line_item)

        add_discount_btn = QPushButton("+ Add Discount")
        add_discount_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_discount_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #5CDB95;
                border: 1px solid #5CDB95;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover { background: #5CDB9522; }
        """)
        add_discount_btn.clicked.connect(self._add_discount_row)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(8)
        btns_row.addWidget(add_btn)
        btns_row.addWidget(add_discount_btn)
        btns_row.addStretch()
        items_outer.addLayout(btns_row)

        self.discounts_container = QVBoxLayout()
        self.discounts_container.setSpacing(6)
        items_outer.addLayout(self.discounts_container)

        # Totals
        totals_layout = QGridLayout()
        totals_layout.setSpacing(6)
        totals_layout.setColumnStretch(0, 1)

        def _totals_row(label_text, value_lbl, row_i, label_style="", value_style=""):
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(label_style or f"color: {SUBTEXT}; font-size: 12px; background: transparent;")
            value_lbl.setStyleSheet(value_style or f"color: {TEXT}; font-size: 12px; background: transparent;")
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            rw = QHBoxLayout(row_w)
            rw.setContentsMargins(0, 0, 0, 0)
            rw.addStretch()
            rw.addWidget(lbl)
            rw.addWidget(value_lbl)
            totals_layout.addWidget(row_w, row_i, 1)
            return lbl, row_w

        # Row 0: Subtotal
        self.subtotal_lbl = QLabel("$0.00")
        self.subtotal_lbl.setFixedWidth(80)
        self.subtotal_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        _totals_row("Subtotal", self.subtotal_lbl, 0)

        # Row 1: Discounts (hidden until a discount row is added)
        self.discounts_lbl = QLabel("-$0.00")
        self.discounts_lbl.setFixedWidth(80)
        self.discounts_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        _, self._discounts_row_widget = _totals_row(
            "Discounts", self.discounts_lbl, 1,
            value_style="color: #5CDB95; font-size: 12px; background: transparent;",
        )
        self._discounts_row_widget.hide()

        # Row 2: Tax
        tax_row_widget = QWidget()
        tax_row_widget.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(tax_row_widget)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(4)
        tr.addStretch()
        tax_lbl = QLabel("Tax (%)")
        tax_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tax_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px; background: transparent;")
        self.tax_input = styled_input("0")
        self.tax_input.setValidator(QDoubleValidator(0, 100, 2))
        self.tax_input.setFixedWidth(55)
        self.tax_input.textChanged.connect(self._recalc_totals)
        self.tax_amount_lbl = QLabel("$0.00")
        self.tax_amount_lbl.setFixedWidth(80)
        self.tax_amount_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.tax_amount_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; background: transparent;")
        tr.addWidget(tax_lbl)
        tr.addWidget(self.tax_input)
        tr.addWidget(self.tax_amount_lbl)
        totals_layout.addWidget(tax_row_widget, 2, 1)

        # Row 3: Total
        self.total_lbl = QLabel("$0.00")
        self.total_lbl.setFixedWidth(80)
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        _totals_row(
            "TOTAL", self.total_lbl, 3,
            label_style=f"color: {ACCENT}; font-size: 14px; font-weight: bold; background: transparent;",
            value_style=f"color: {ACCENT}; font-size: 14px; font-weight: bold; background: transparent;",
        )

        items_outer.addLayout(totals_layout)
        main.addWidget(items_card)

        # ── Payment Details ───────────────────────────────────────────────────
        payment_card = card_frame()
        payment_layout = QVBoxLayout(payment_card)
        payment_layout.setContentsMargins(20, 16, 20, 16)
        payment_layout.setSpacing(8)
        payment_layout.addWidget(section_label("PAYMENT DETAILS"))
        self.payment_text = QTextEdit()
        self.payment_text.setPlaceholderText("Bank: ...\nAccount: ...\nReference: ...")
        self.payment_text.setFixedHeight(80)
        self.payment_text.setStyleSheet(f"""
            QTextEdit {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        payment_layout.addWidget(self.payment_text)
        main.addWidget(payment_card)

        # ── Terms & Conditions ────────────────────────────────────────────────
        terms_card = card_frame()
        terms_layout = QVBoxLayout(terms_card)
        terms_layout.setContentsMargins(20, 16, 20, 16)
        terms_layout.setSpacing(8)

        self.terms_toggle_btn = QPushButton("+ Add Terms & Conditions")
        self.terms_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.terms_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {SUBTEXT};
                border: none;
                font-size: 12px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{ color: {ACCENT}; }}
        """)
        self.terms_toggle_btn.clicked.connect(self._toggle_terms)
        terms_layout.addWidget(self.terms_toggle_btn)

        self.terms_text = QTextEdit()
        self.terms_text.setPlaceholderText("Enter your terms and conditions...")
        self.terms_text.setFixedHeight(80)
        self.terms_text.setStyleSheet(f"""
            QTextEdit {{
                background: {INPUT_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        self.terms_text.hide()
        terms_layout.addWidget(self.terms_text)
        main.addWidget(terms_card)

        # ── Generate Button ───────────────────────────────────────────────────
        self.generate_btn = QPushButton("Generate Invoice PDF")
        self.generate_btn.setFixedHeight(50)
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #5a52e0; }}
            QPushButton:pressed {{ background: #4a43cc; }}
        """)
        main.addWidget(self.generate_btn)
        main.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def _prefill_from_settings(self):
        s = self._settings
        if s.get("from_name"):
            self.from_name.setText(s["from_name"])
        if s.get("from_address"):
            self.from_address.setText(s["from_address"])
        if s.get("from_email"):
            self.from_email.setText(s["from_email"])
        if s.get("payment_details"):
            self.payment_text.setPlainText(s["payment_details"])

    def _upload_logo(self, event=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.svg *.bmp)"
        )
        if path:
            self.logo_path = path
            self._update_logo_preview()

    def _update_logo_preview(self):
        if not self.logo_path:
            return
        px = QPixmap(self.logo_path)
        if px.isNull():
            return
        scaled = px.scaledToWidth(self.logo_width, Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(scaled)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet(f"""
            QLabel {{
                background: {INPUT_BG};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)

    def _on_logo_slider(self, value):
        self.logo_width = value
        self._update_logo_preview()

    def _add_line_item(self):
        row = LineItemRow(on_change=self._recalc_totals, currency_symbol=self.currency_symbol)
        row.remove_btn.clicked.connect(lambda: self._remove_line(row))
        self.line_rows.append(row)
        self.items_container.addWidget(row)
        self._recalc_totals()

    def _remove_line(self, row):
        if len(self.line_rows) <= 1:
            return
        self.line_rows.remove(row)
        self.items_container.removeWidget(row)
        row.deleteLater()
        self._recalc_totals()

    def _add_discount_row(self):
        row = DiscountRow(on_change=self._recalc_totals, currency_symbol=self.currency_symbol)
        row.remove_btn.clicked.connect(lambda: self._remove_discount(row))
        self.discount_rows.append(row)
        self.discounts_container.addWidget(row)
        self._recalc_totals()

    def _remove_discount(self, row):
        self.discount_rows.remove(row)
        self.discounts_container.removeWidget(row)
        row.deleteLater()
        self._recalc_totals()

    def _on_currency_change(self, index):
        self.currency_symbol = _CURRENCIES[index][1]
        for row in self.line_rows:
            row.set_currency(self.currency_symbol)
        for dr in self.discount_rows:
            dr.set_currency(self.currency_symbol)
        self._recalc_totals()

    def _recalc_totals(self):
        if not hasattr(self, "subtotal_lbl"):
            return
        subtotal = 0.0
        for row in self.line_rows:
            d = row.get_data()
            try:
                subtotal += float(d["qty"]) * float(d["unit_price"])
            except (ValueError, TypeError):
                pass
        sym = self.currency_symbol
        self.subtotal_lbl.setText(f"{sym}{subtotal:,.2f}")

        discount_total = 0.0
        for dr in self.discount_rows:
            mode, val = dr.get_value()
            amt = subtotal * val / 100 if mode == "pct" else val
            discount_total += amt
            dr.set_display(amt)
        has_discounts = bool(self.discount_rows)
        self._discounts_row_widget.setVisible(has_discounts)
        if has_discounts:
            self.discounts_lbl.setText(f"-{sym}{discount_total:,.2f}")

        after_discount = subtotal - discount_total
        try:
            tax_pct = float(self.tax_input.text() or 0)
        except ValueError:
            tax_pct = 0.0
        tax_amt = after_discount * tax_pct / 100
        self.tax_amount_lbl.setText(f"{sym}{tax_amt:,.2f}")
        self.total_lbl.setText(f"{sym}{after_discount + tax_amt:,.2f}")

    def _toggle_terms(self):
        self.terms_visible = not self.terms_visible
        self.terms_text.setVisible(self.terms_visible)
        if self.terms_visible:
            self.terms_toggle_btn.setText("− Remove Terms & Conditions")
        else:
            self.terms_toggle_btn.setText("+ Add Terms & Conditions")

    def _style_color_btn(self, btn, color, selected):
        ring = "3px solid white" if selected else f"2px solid {BORDER}"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border: {ring};
                border-radius: 14px;
            }}
            QPushButton:hover {{ border: 2px solid white; }}
        """)

    def _select_invoice_color(self, color):
        self.invoice_accent = color
        for c, btn in self._color_btns.items():
            self._style_color_btn(btn, c, c == color)

    def get_invoice_data(self) -> dict:
        return {
            "accent_color": self.invoice_accent,
            "logo_path": self.logo_path,
            "logo_width": self.logo_width,
            "invoice_number": self.inv_number.text().strip() or "0001",
            "date": self.inv_date.text().strip(),
            "due_date": self.inv_due.text().strip(),
            "from_name": self.from_name.text().strip(),
            "from_address": self.from_address.text().strip(),
            "from_email": self.from_email.text().strip(),
            "to_name": self.to_name.text().strip(),
            "to_address": self.to_address.text().strip(),
            "to_email": self.to_email.text().strip(),
            "currency_symbol": self.currency_symbol,
            "line_items": [r.get_data() for r in self.line_rows],
            "discounts": [dr.get_data() for dr in self.discount_rows],
            "tax_percent": self.tax_input.text().strip() or "0",
            "payment_details": self.payment_text.toPlainText().strip(),
            "terms": self.terms_text.toPlainText().strip() if self.terms_visible else "",
        }
