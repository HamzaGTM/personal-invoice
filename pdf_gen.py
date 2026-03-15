import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
LIGHT_GRAY = colors.HexColor("#F0F0F0")
MID_GRAY = colors.HexColor("#AAAAAA")
DARK = colors.HexColor("#1A1A1A")
WHITE = colors.white


def build_pdf(output_path: str, data: dict):
    ACCENT = colors.HexColor(data.get("accent_color", "#6C63FF"))
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    story = []

    # ── Header: logo + INVOICE block ─────────────────────────────────────────
    logo_cell = ""
    if data.get("logo_path") and os.path.exists(data["logo_path"]):
        from reportlab.platypus import Image as RLImage
        logo_w = float(data.get("logo_width", 120))
        # keep aspect
        from PIL import Image as PILImage
        try:
            with PILImage.open(data["logo_path"]) as im:
                orig_w, orig_h = im.size
            ratio = orig_h / orig_w
            logo_h = logo_w * ratio
        except Exception:
            logo_h = logo_w * 0.4
        logo_cell = RLImage(data["logo_path"], width=logo_w * 0.75, height=logo_h * 0.75)

    has_logo = bool(logo_cell)
    # alignment: right when logo present, left when no logo
    meta_align = 2 if has_logo else 0

    invoice_title_style = ParagraphStyle(
        "InvTitle", fontName="Helvetica-Bold", fontSize=26,
        textColor=ACCENT, alignment=meta_align, leading=32, spaceAfter=6
    )
    invoice_meta_style = ParagraphStyle(
        "InvMeta", fontName="Helvetica", fontSize=10,
        textColor=DARK, alignment=meta_align, leading=18, spaceAfter=0
    )
    invoice_num_style = ParagraphStyle(
        "InvNum", fontName="Helvetica-Bold", fontSize=11,
        textColor=DARK, alignment=meta_align, leading=18, spaceAfter=4
    )

    inv_number = data.get("invoice_number", "0001")
    inv_date = data.get("date", "")
    inv_due = data.get("due_date", "")

    inv_block = [
        Paragraph("INVOICE", invoice_title_style),
        Paragraph(f"# {inv_number}", invoice_num_style),
        Spacer(1, 4),
        Paragraph(f"Date: {inv_date}", invoice_meta_style),
        Paragraph(f"Due: {inv_due}", invoice_meta_style),
    ]

    if has_logo:
        header_table = Table(
            [[logo_cell, inv_block]],
            colWidths=[(PAGE_W - 2 * MARGIN) * 0.55, (PAGE_W - 2 * MARGIN) * 0.45],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        for item in inv_block:
            story.append(item)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Spacer(1, 6 * mm))

    # ── From / Bill To ────────────────────────────────────────────────────────
    label_style = ParagraphStyle(
        "Label", fontName="Helvetica-Bold", fontSize=8,
        textColor=ACCENT, spaceAfter=3, leading=12
    )
    body_style = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=10,
        textColor=DARK, leading=15
    )

    def contact_block(title, name, address, email):
        lines = [Paragraph(title, label_style)]
        if name:
            lines.append(Paragraph(f"<b>{name}</b>", body_style))
        if address:
            lines.append(Paragraph(address.replace("\n", "<br/>"), body_style))
        if email:
            lines.append(Paragraph(email, body_style))
        return lines

    from_block = contact_block(
        "FROM",
        data.get("from_name", ""),
        data.get("from_address", ""),
        data.get("from_email", ""),
    )
    to_block = contact_block(
        "BILL TO",
        data.get("to_name", ""),
        data.get("to_address", ""),
        data.get("to_email", ""),
    )

    contacts_table = Table(
        [[from_block, to_block]],
        colWidths=[(PAGE_W - 2 * MARGIN) * 0.5, (PAGE_W - 2 * MARGIN) * 0.5],
    )
    contacts_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(contacts_table)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Spacer(1, 6 * mm))

    # ── Line Items Table ──────────────────────────────────────────────────────
    col_header_style = ParagraphStyle(
        "ColHdr", fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE
    )
    cell_style = ParagraphStyle(
        "Cell", fontName="Helvetica", fontSize=10, textColor=DARK
    )
    total_cell_style = ParagraphStyle(
        "TotalCell", fontName="Helvetica", fontSize=10, textColor=DARK, alignment=2
    )

    avail = PAGE_W - 2 * MARGIN
    col_widths = [avail * 0.48, avail * 0.12, avail * 0.2, avail * 0.2]

    table_data = [[
        Paragraph("DESCRIPTION", col_header_style),
        Paragraph("QTY", col_header_style),
        Paragraph("UNIT PRICE", col_header_style),
        Paragraph("TOTAL", col_header_style),
    ]]

    line_items = [
        i for i in data.get("line_items", [])
        if str(i.get("description", "")).strip()
        or float(i.get("unit_price") or 0) != 0
    ]
    for item in line_items:
        desc = item.get("description", "")
        qty = item.get("qty", 0)
        unit = item.get("unit_price", 0.0)
        try:
            total = float(qty) * float(unit)
        except (ValueError, TypeError):
            total = 0.0
        table_data.append([
            Paragraph(desc.replace("\n", "<br/>"), cell_style),
            Paragraph(str(qty), cell_style),
            Paragraph(f"${float(unit):,.2f}", total_cell_style),
            Paragraph(f"${total:,.2f}", total_cell_style),
        ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_count = len(table_data)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, row_count - 1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    # ── Totals ────────────────────────────────────────────────────────────────
    subtotal = sum(
        float(i.get("qty", 0)) * float(i.get("unit_price", 0))
        for i in line_items
    )
    tax_pct = float(data.get("tax_percent", 0) or 0)

    totals_style = ParagraphStyle(
        "Totals", fontName="Helvetica", fontSize=10, textColor=DARK, alignment=2
    )
    totals_label_style = ParagraphStyle(
        "TotalsLbl", fontName="Helvetica", fontSize=10, textColor=MID_GRAY, alignment=2
    )
    grand_style = ParagraphStyle(
        "Grand", fontName="Helvetica-Bold", fontSize=12, textColor=ACCENT, alignment=2
    )
    discount_style = ParagraphStyle(
        "Discount", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#5CDB95"), alignment=2
    )

    totals_data = [
        [Paragraph("Subtotal", totals_label_style), Paragraph(f"${subtotal:,.2f}", totals_style)],
    ]

    discount_total = 0.0
    for disc in data.get("discounts", []):
        mode = disc.get("mode", "pct")
        val = float(disc.get("value", 0) or 0)
        desc = disc.get("description", "") or "Discount"
        amt = subtotal * val / 100 if mode == "pct" else val
        discount_total += amt
        totals_data.append([
            Paragraph(desc, totals_label_style),
            Paragraph(f"-${amt:,.2f}", discount_style),
        ])

    after_discount = subtotal - discount_total
    tax_amt = after_discount * tax_pct / 100
    grand_total = after_discount + tax_amt

    totals_data.append([Paragraph(f"Tax ({tax_pct:.1f}%)", totals_label_style), Paragraph(f"${tax_amt:,.2f}", totals_style)])
    totals_data.append([Paragraph("<b>TOTAL</b>", grand_style), Paragraph(f"<b>${grand_total:,.2f}</b>", grand_style)])
    total_row_idx = len(totals_data) - 1

    totals_table = Table(
        totals_data,
        colWidths=[avail * 0.8, avail * 0.2],
    )
    totals_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1, ACCENT),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))

    # ── Payment Details ───────────────────────────────────────────────────────
    payment_text = data.get("payment_details", "").strip()
    if payment_text:
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("PAYMENT DETAILS", label_style))
        pay_box_data = [[Paragraph(payment_text.replace("\n", "<br/>"), body_style)]]
        pay_box = Table(pay_box_data, colWidths=[avail])
        pay_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CCCCCC")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(pay_box)
        story.append(Spacer(1, 6 * mm))

    # ── Terms & Conditions ────────────────────────────────────────────────────
    terms_text = data.get("terms", "").strip()
    if terms_text:
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("TERMS & CONDITIONS", label_style))
        story.append(Paragraph(terms_text.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 6 * mm))

    # ── Footer via canvas ─────────────────────────────────────────────────────
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(MARGIN, 10 * mm, f"Invoice #{inv_number}")
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
