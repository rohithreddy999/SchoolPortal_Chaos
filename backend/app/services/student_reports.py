from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.payment import FeeComponent, PaymentTransaction
from app.models.student import Student
from app.services.student_balances import COMPONENT_LABELS, build_fee_summary, get_component_assessed


PRIMARY = colors.HexColor("#1F3A5F")
SECONDARY = colors.HexColor("#D8E3F0")
BACKGROUND = colors.HexColor("#F7F9FC")
TEXT = colors.HexColor("#1F2933")
ACCENT = colors.HexColor("#C0392B")
MUTED = colors.HexColor("#52606D")
BORDER = colors.HexColor("#CBD2D9")


def quantize_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def format_currency(value: Decimal) -> str:
    return f"INR {quantize_money(value):,.2f}"


def format_date(value: date | None) -> str:
    if not value:
        return "-"
    return value.strftime("%d %b %Y")


def format_datetime(value: datetime | None) -> str:
    if not value:
        return "-"
    return value.strftime("%d %b %Y, %I:%M %p")


def get_transaction_total(transaction: PaymentTransaction) -> Decimal:
    return quantize_money(
        sum((Decimal(allocation.amount) for allocation in transaction.allocations), Decimal("0.00"))
    )


def sorted_transactions(student: Student) -> list[PaymentTransaction]:
    return sorted(
        student.payment_transactions,
        key=lambda item: (item.received_on, item.id),
    )


def create_report_assets(report_title: str, report_note: str, school_name: str):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{school_name} {report_title}",
        author=school_name,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=TEXT,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=TEXT,
    )
    muted_style = ParagraphStyle(
        "ReportMuted",
        parent=body_style,
        textColor=MUTED,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        textColor=PRIMARY,
        spaceAfter=6,
    )

    story = [
        Paragraph(school_name, title_style),
        Paragraph(report_title, subtitle_style),
        Paragraph(report_note, muted_style),
    ]

    style_pack = {
        "body": body_style,
        "muted": muted_style,
        "section": section_style,
    }
    return buffer, document, story, style_pack


def build_info_table(rows: list[list[object]], col_widths: list[float]) -> Table:
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_student_record_table(student: Student) -> Table:
    return build_info_table(
        [
            ["Student Name", student.student_name, "Admission No.", student.admission_number],
            ["Academic Year", student.academic_year, "Class / Section", f"{student.class_name} / {student.section}"],
            ["Father's Name", student.father_name, "Mobile", student.mobile_number],
            ["Student ID", student.student_identifier or "-", "PEN Number", student.pen_number or "-"],
        ],
        [28 * mm, 58 * mm, 28 * mm, 58 * mm],
    )


def build_money_table(rows: list[list[object]], *, repeat_rows: int = 1) -> Table:
    table = Table(rows, colWidths=[72 * mm, 34 * mm, 34 * mm, 36 * mm], repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BACKGROUND]),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def build_receipt_snapshot(student: Student, transaction: PaymentTransaction) -> dict[str, object]:
    assessed_map = get_component_assessed(student)
    cumulative_paid = {component: Decimal("0.00") for component in COMPONENT_LABELS}
    receipt_paid = {component: Decimal("0.00") for component in COMPONENT_LABELS}

    target_found = False
    for item in sorted_transactions(student):
        for allocation in item.allocations:
            component = FeeComponent(allocation.component)
            amount = quantize_money(allocation.amount)
            cumulative_paid[component] += amount
            if item.id == transaction.id:
                receipt_paid[component] += amount
        if item.id == transaction.id:
            target_found = True
            break

    if not target_found:
        raise ValueError(f"Transaction {transaction.id} does not belong to student {student.id}")

    summary = build_fee_summary(student)
    component_rows: list[dict[str, object]] = []
    for component, label in COMPONENT_LABELS.items():
        assessed = quantize_money(assessed_map[component])
        paid_till_receipt = quantize_money(cumulative_paid[component])
        balance_left = quantize_money(max(Decimal("0.00"), assessed - paid_till_receipt))
        component_rows.append(
            {
                "label": label,
                "assessed": assessed,
                "paid_in_receipt": quantize_money(receipt_paid[component]),
                "paid_till_receipt": paid_till_receipt,
                "balance_left": balance_left,
            }
        )

    total_paid_till_receipt = quantize_money(sum(cumulative_paid.values(), Decimal("0.00")))
    total_pending_after_receipt = quantize_money(max(Decimal("0.00"), summary.adjusted_total - total_paid_till_receipt))
    return {
        "components": component_rows,
        "total_fee": quantize_money(summary.total_fee),
        "concession_transport": quantize_money(summary.concession_transport),
        "adjusted_total": quantize_money(summary.adjusted_total),
        "total_paid_till_receipt": total_paid_till_receipt,
        "total_pending_after_receipt": total_pending_after_receipt,
    }


def build_student_statement_pdf(student: Student, school_name: str) -> bytes:
    summary = build_fee_summary(student)
    buffer, document, story, styles = create_report_assets(
        "Student Fee Statement",
        (
            f"Generated on {format_datetime(datetime.now())}. "
            "This statement shows the current assessed, paid, and pending balances for the selected student."
        ),
        school_name,
    )

    story.extend(
        [
            Paragraph("Student Record", styles["section"]),
            build_student_record_table(student),
            Spacer(1, 10),
        ]
    )

    component_rows: list[list[object]] = [["Component", "Assessed", "Paid", "Balance"]]
    for component in summary.components:
        component_rows.append(
            [
                component.label,
                format_currency(component.assessed),
                format_currency(component.paid),
                format_currency(component.balance),
            ]
        )
    component_rows.extend(
        [
            ["Total Fee", format_currency(summary.total_fee), "", ""],
            ["Transport Concession", format_currency(summary.concession_transport), "", ""],
            ["Adjusted Total", format_currency(summary.adjusted_total), "", ""],
            ["Total Paid", "", format_currency(summary.total_paid), ""],
            ["Total Pending", "", "", format_currency(summary.total_pending)],
        ]
    )

    fee_table = build_money_table(component_rows)
    fee_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, -5), (-1, -1), colors.HexColor("#EEF4FB")),
                ("FONTNAME", (0, -5), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
            ]
        )
    )
    story.extend([Paragraph("Current Component Status", styles["section"]), fee_table, Spacer(1, 10)])

    payment_rows: list[list[object]] = [["Receipt", "Date", "Recorded By", "Amount Received"]]
    transactions = sorted_transactions(student)
    if transactions:
        for transaction in reversed(transactions):
            payment_rows.append(
                [
                    transaction.receipt_number,
                    format_date(transaction.received_on),
                    transaction.created_by_username or "Administrator",
                    format_currency(get_transaction_total(transaction)),
                ]
            )
    else:
        payment_rows.append(["No payments recorded", "-", "-", format_currency(Decimal("0.00"))])

    payment_table = Table(
        payment_rows,
        colWidths=[46 * mm, 30 * mm, 54 * mm, 38 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    payment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BACKGROUND]),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([Paragraph("Recorded Payments", styles["section"]), payment_table, Spacer(1, 8)])
    story.append(
        Paragraph(
            "This statement reflects the current ledger balance for the selected student record.",
            styles["body"],
        )
    )

    document.build(story)
    return buffer.getvalue()


def build_payment_receipt_pdf(student: Student, transaction: PaymentTransaction, school_name: str) -> bytes:
    snapshot = build_receipt_snapshot(student, transaction)
    buffer, document, story, styles = create_report_assets(
        "Offline Payment Receipt",
        (
            f"Generated on {format_datetime(datetime.now())}. "
            "This receipt shows the recorded payment and the balance left immediately after that payment."
        ),
        school_name,
    )

    receipt_info = build_info_table(
        [
            ["Receipt Number", transaction.receipt_number, "Received On", format_date(transaction.received_on)],
            ["Recorded At", format_datetime(transaction.created_at), "Recorded By", transaction.created_by_username or "Administrator"],
            ["Student Name", student.student_name, "Admission No.", student.admission_number],
            ["Class / Section", f"{student.class_name} / {student.section}", "Payment Total", format_currency(get_transaction_total(transaction))],
        ],
        [32 * mm, 54 * mm, 32 * mm, 54 * mm],
    )
    story.extend([Paragraph("Receipt Details", styles["section"]), receipt_info, Spacer(1, 10)])

    allocation_rows: list[list[object]] = [["Component", "Amount Received", "", ""]]
    for allocation in transaction.allocations:
        allocation_rows.append(
            [
                COMPONENT_LABELS[FeeComponent(allocation.component)],
                format_currency(allocation.amount),
                "",
                "",
            ]
        )

    allocation_table = build_money_table(allocation_rows)
    story.extend([Paragraph("Recorded Allocation", styles["section"]), allocation_table, Spacer(1, 10)])

    balance_rows: list[list[object]] = [["Component", "Assessed", "Paid Till Receipt", "Balance Left"]]
    for component in snapshot["components"]:
        balance_rows.append(
            [
                component["label"],
                format_currency(component["assessed"]),
                format_currency(component["paid_till_receipt"]),
                format_currency(component["balance_left"]),
            ]
        )
    balance_rows.extend(
        [
            ["Total Fee", format_currency(snapshot["total_fee"]), "", ""],
            ["Transport Concession", format_currency(snapshot["concession_transport"]), "", ""],
            ["Adjusted Total", format_currency(snapshot["adjusted_total"]), "", ""],
            ["Total Paid Till Receipt", "", format_currency(snapshot["total_paid_till_receipt"]), ""],
            ["Total Pending After Receipt", "", "", format_currency(snapshot["total_pending_after_receipt"])],
        ]
    )

    balance_table = build_money_table(balance_rows)
    balance_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, -5), (-1, -1), colors.HexColor("#EEF4FB")),
                ("FONTNAME", (0, -5), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
            ]
        )
    )
    story.extend([Paragraph("Balances After This Receipt", styles["section"]), balance_table, Spacer(1, 8)])

    story.append(
        Paragraph(
            f"Note: {transaction.note or 'No note added for this payment.'}",
            styles["body"],
        )
    )

    document.build(story)
    return buffer.getvalue()


def build_payment_history_pdf(student: Student, school_name: str) -> bytes:
    summary = build_fee_summary(student)
    transactions = list(reversed(sorted_transactions(student)))
    buffer, document, story, styles = create_report_assets(
        "Student Payment History",
        (
            f"Generated on {format_datetime(datetime.now())}. "
            "This report contains the full recorded payment history for the selected student, including receipt numbers."
        ),
        school_name,
    )

    story.extend(
        [
            Paragraph("Student Record", styles["section"]),
            build_student_record_table(student),
            Spacer(1, 10),
        ]
    )

    summary_rows = [["Summary", "Amount", "", ""]]
    summary_rows.extend(
        [
            ["Adjusted Total", format_currency(summary.adjusted_total), "", ""],
            ["Total Paid", format_currency(summary.total_paid), "", ""],
            ["Total Pending", format_currency(summary.total_pending), "", ""],
        ]
    )
    summary_table = build_money_table(summary_rows)
    story.extend([Paragraph("Current Ledger Summary", styles["section"]), summary_table, Spacer(1, 10)])

    transaction_rows: list[list[object]] = [
        [
            "Receipt Number",
            "Date",
            "Recorded By",
            "Note",
            "Total",
        ]
    ]
    if transactions:
        for transaction in transactions:
            transaction_rows.append(
                [
                    transaction.receipt_number,
                    format_date(transaction.received_on),
                    transaction.created_by_username or "Administrator",
                    Paragraph(transaction.note or "-", styles["body"]),
                    format_currency(get_transaction_total(transaction)),
                ]
            )
    else:
        transaction_rows.append(["No payments recorded", "-", "-", Paragraph("-", styles["body"]), format_currency(Decimal("0.00"))])

    transaction_table = Table(
        transaction_rows,
        colWidths=[36 * mm, 22 * mm, 30 * mm, 62 * mm, 26 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    transaction_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BACKGROUND]),
                ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([Paragraph("Transaction History", styles["section"]), transaction_table, Spacer(1, 10)])

    allocation_rows: list[list[object]] = [["Receipt Number", "Fee Head", "Amount", "Received On"]]
    if transactions:
        for transaction in transactions:
            for allocation in transaction.allocations:
                allocation_rows.append(
                    [
                        transaction.receipt_number,
                        COMPONENT_LABELS[FeeComponent(allocation.component)],
                        format_currency(allocation.amount),
                        format_date(transaction.received_on),
                    ]
                )
    else:
        allocation_rows.append(["-", "-", format_currency(Decimal("0.00")), "-"])

    allocation_table = Table(
        allocation_rows,
        colWidths=[38 * mm, 64 * mm, 32 * mm, 30 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    allocation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BACKGROUND]),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([Paragraph("Allocation Breakdown", styles["section"]), allocation_table])

    document.build(story)
    return buffer.getvalue()
