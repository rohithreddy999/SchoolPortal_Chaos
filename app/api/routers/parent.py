from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.auth import require_parent_student
from app.api.deps import get_db
from app.core.validation import normalize_academic_year
from app.db.models import Payment, Student
from app.schemas.fees import FeeSummary
from app.schemas.payments import InvoiceOut, ParentPaymentCreate, PaymentOut
from app.services.audit import client_ip
from app.services.portal import build_fee_summary, build_invoice, create_pending_online_payment


router = APIRouter(prefix="/parent", tags=["parent"])


def _academic_year_param(value: str) -> str:
    try:
        return normalize_academic_year(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me")
def me(student: Student = Depends(require_parent_student)) -> dict:
    return {
        "role": "parent",
        "student_id": student.id,
        "admission_number": student.admission_number,
        "roll_number": student.roll_number,
        "student_name": student.student_name,
        "class_name": student.class_name,
        "section": student.section,
    }


@router.get("/fee-summary", response_model=FeeSummary)
def fee_summary(
    academic_year: str = Query(..., examples=["2024-2025"]),
    db: Session = Depends(get_db),
    student: Student = Depends(require_parent_student),
) -> FeeSummary:
    academic_year = _academic_year_param(academic_year)
    return build_fee_summary(db, student.id, academic_year)


@router.post("/pay-online", response_model=PaymentOut, status_code=status.HTTP_202_ACCEPTED)
def pay_online(
    body: ParentPaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    student: Student = Depends(require_parent_student),
) -> Payment:
    return create_pending_online_payment(
        db,
        student=student,
        academic_year=body.academic_year,
        fee_head=body.fee_head,
        amount_paid=body.amount_paid,
        payment_mode=body.payment_mode,
        remarks=body.remarks,
        audit_actor_email="Parent Portal",
        audit_ip=client_ip(request),
    )


@router.get("/payments", response_model=list[PaymentOut])
def payment_history(
    db: Session = Depends(get_db),
    student: Student = Depends(require_parent_student),
) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.student_id == student.id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
        .all()
    )


@router.get("/invoices/{payment_id}", response_model=InvoiceOut)
def get_invoice(
    payment_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(require_parent_student),
) -> InvoiceOut:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.student_id == student.id)
        .first()
    )
    if not payment or payment.payment_status != "success":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    return build_invoice(db, student, payment)

