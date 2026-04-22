from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.student import Student
from app.services.student_balances import build_fee_summary


PRIMARY = colors.HexColor("#6B4226")
SECONDARY = colors.HexColor("#D9A066")
BACKGROUND = colors.HexColor("#FAF3E0")
TEXT = colors.HexColor("#1F1F1F")
ACCENT = colors.HexColor("#B85C38")
MUTED = colors.HexColor("#685849")
BORDER = colors.HexColor("#D8C3A5")


def format_currency(value: Decimal) -> str:
    return f"INR {Decimal(value):,.2f}"


def build_student_statement_pdf(student: Student, school_name: str) -> bytes:
    summary = build_fee_summary(student)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{school_name} Fee Statement",
        author=school_name,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "StatementTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "StatementSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "StatementSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=PRIMARY,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "StatementBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=TEXT,
    )

    story = [
        Paragraph(school_name, title_style),
        Paragraph(
            (
                f"Fee statement generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')} "
                "showing current paid amounts and outstanding balances."
            ),
            subtitle_style,
        ),
    ]

    student_info = Table(
        [
            ["Student Name", student.student_name, "Admission No.", student.admission_number],
            ["Academic Year", student.academic_year, "Class / Section", f"{student.class_name} / {student.section}"],
            ["Father's Name", student.father_name, "Mobile", student.mobile_number],
            ["Student ID", student.student_identifier or "-", "PEN Number", student.pen_number or "-"],
        ],
        colWidths=[28 * mm, 58 * mm, 28 * mm, 58 * mm],
        hAlign="LEFT",
    )
    student_info.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([Paragraph("Student Record", section_style), student_info, Spacer(1, 10)])

    component_rows = [["Component", "Assessed", "Paid", "Balance"]]
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

    fee_table = Table(component_rows, colWidths=[75 * mm, 34 * mm, 34 * mm, 34 * mm], repeatRows=1, hAlign="LEFT")
    fee_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -6), [colors.white, BACKGROUND]),
                ("BACKGROUND", (0, -5), (-1, -1), colors.HexColor("#FFF8EC")),
                ("FONTNAME", (0, -5), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([Paragraph("Current Component Status", section_style), fee_table, Spacer(1, 10)])

    payment_rows = [["Receipt", "Date", "Recorded By", "Amount Received"]]
    if student.payment_transactions:
        for transaction in sorted(
            student.payment_transactions,
            key=lambda item: (item.received_on, item.id),
            reverse=True,
        ):
            payment_total = sum((Decimal(allocation.amount) for allocation in transaction.allocations), Decimal("0.00"))
            payment_rows.append(
                [
                    transaction.receipt_number,
                    transaction.received_on.strftime("%d %b %Y"),
                    transaction.created_by_username or "Administrator",
                    format_currency(payment_total),
                ]
            )
    else:
        payment_rows.append(["No payments recorded", "-", "-", format_currency(Decimal("0.00"))])

    payment_table = Table(payment_rows, colWidths=[45 * mm, 32 * mm, 52 * mm, 48 * mm], repeatRows=1, hAlign="LEFT")
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
            ]
        )
    )
    story.extend([Paragraph("Recorded Payments", section_style), payment_table, Spacer(1, 8)])

    story.append(
        Paragraph(
            "This statement reflects the current ledger balance for the selected student record.",
            body_style,
        )
    )

    document.build(story)
    return buffer.getvalue()
