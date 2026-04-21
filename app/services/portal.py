from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import FEE_HEADS
from app.db.models import Concession, FeeStructure, Payment, Student, User
from app.schemas.fees import FeeSummary
from app.schemas.payments import InvoiceOut
from app.services.audit import log_audit_event


ZERO = Decimal("0.00")


def ensure_student_exists(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def _assigned_from_structure(structure: FeeStructure | None) -> dict[str, Decimal]:
    return {
        "admission": structure.admission_fee if structure else ZERO,
        "term1": structure.term1_fee if structure else ZERO,
        "term2": structure.term2_fee if structure else ZERO,
        "term3": structure.term3_fee if structure else ZERO,
        "transport": structure.transport_fee if structure else ZERO,
        "books": structure.books_fee if structure else ZERO,
    }


def _successful_payments_by_head(db: Session, student_id: int, academic_year: str) -> dict[str, Decimal]:
    paid_rows = (
        db.query(Payment.fee_head, func.coalesce(func.sum(Payment.amount_paid), 0))
        .filter(
            Payment.student_id == student_id,
            Payment.academic_year == academic_year,
            Payment.payment_status == "success",
        )
        .group_by(Payment.fee_head)
        .all()
    )
    paid: dict[str, Decimal] = {fee_head: Decimal(str(amount)) for fee_head, amount in paid_rows}
    for fee_head in FEE_HEADS:
        paid.setdefault(fee_head, ZERO)
    return paid


def validate_fee_structure_change(
    db: Session,
    *,
    student_id: int,
    academic_year: str,
    assigned: dict[str, Decimal],
) -> None:
    _lock_student_for_payment(db, student_id)
    paid = _successful_payments_by_head(db, student_id, academic_year)
    concession = (
        db.query(Concession)
        .filter(Concession.student_id == student_id, Concession.academic_year == academic_year)
        .first()
    )
    transport_concession = concession.transport_concession if concession else ZERO
    other_concession = concession.other_concession if concession else ZERO

    if assigned["transport"] < paid["transport"] + transport_concession:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transport fee cannot be less than paid transport amount plus concession",
        )

    for fee_head in FEE_HEADS:
        if fee_head == "transport":
            continue
        if assigned[fee_head] < paid[fee_head]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{fee_head} fee cannot be less than already paid amount",
            )

    total_assigned = sum(assigned.values(), ZERO)
    total_credits = sum(paid.values(), ZERO) + transport_concession + other_concession
    if total_assigned < total_credits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total fee cannot be less than existing payments plus concessions",
        )


def validate_concession_change(
    db: Session,
    *,
    student_id: int,
    academic_year: str,
    transport_concession: Decimal,
    other_concession: Decimal,
) -> None:
    _lock_student_for_payment(db, student_id)
    structure = (
        db.query(FeeStructure)
        .filter(FeeStructure.student_id == student_id, FeeStructure.academic_year == academic_year)
        .first()
    )
    if not structure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fee structure must be assigned before concessions",
        )

    assigned = _assigned_from_structure(structure)
    paid = _successful_payments_by_head(db, student_id, academic_year)

    if transport_concession + paid["transport"] > assigned["transport"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transport concession cannot exceed unpaid transport fee",
        )

    total_credits = sum(paid.values(), ZERO) + transport_concession + other_concession
    if total_credits > sum(assigned.values(), ZERO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total concessions plus payments cannot exceed assigned fees",
        )


def build_fee_summary(db: Session, student_id: int, academic_year: str) -> FeeSummary:
    structure = (
        db.query(FeeStructure)
        .filter(FeeStructure.student_id == student_id, FeeStructure.academic_year == academic_year)
        .first()
    )
    concession = (
        db.query(Concession)
        .filter(Concession.student_id == student_id, Concession.academic_year == academic_year)
        .first()
    )

    assigned = _assigned_from_structure(structure)
    concessions = {
        "transport": concession.transport_concession if concession else ZERO,
        "other": concession.other_concession if concession else ZERO,
    }

    paid = _successful_payments_by_head(db, student_id, academic_year)

    total_assigned = sum(assigned.values(), ZERO)
    total_concessions = sum(concessions.values(), ZERO)
    total_paid = sum(paid.values(), ZERO)
    balance = max(total_assigned - total_concessions - total_paid, ZERO)

    return FeeSummary(
        student_id=student_id,
        academic_year=academic_year,
        assigned=assigned,
        concessions=concessions,
        paid=paid,
        total_assigned=total_assigned,
        total_concessions=total_concessions,
        total_paid=total_paid,
        balance=balance,
    )


def fee_head_outstanding(summary: FeeSummary, fee_head: str) -> Decimal:
    head_concession = summary.concessions["transport"] if fee_head == "transport" else ZERO
    return max(summary.assigned[fee_head] - head_concession - summary.paid[fee_head], ZERO)


def _validate_payable(summary: FeeSummary, fee_head: str, amount_paid: Decimal) -> None:
    total_outstanding = max(summary.balance, ZERO)

    if summary.total_assigned <= ZERO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fee structure has not been assigned for this academic year",
        )
    if total_outstanding <= ZERO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No outstanding balance remains")

    head_outstanding = fee_head_outstanding(summary, fee_head)
    if head_outstanding <= ZERO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{fee_head} fee is already fully paid",
        )

    allowed_amount = min(head_outstanding, total_outstanding)
    if amount_paid > allowed_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum payable amount for {fee_head} is {allowed_amount}",
        )


def _generate_receipt_number(payment_id: int) -> str:
    return f"INV-{date.today():%Y%m%d}-{payment_id:05d}"


def _generate_order_id() -> str:
    return f"order_{uuid4().hex}"


def _lock_student_for_payment(db: Session, student_id: int) -> Student:
    locked_student = (
        db.execute(select(Student).where(Student.id == student_id).with_for_update())
        .scalar_one_or_none()
    )
    if not locked_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return locked_student


def create_success_payment(
    db: Session,
    *,
    student: Student,
    academic_year: str,
    fee_head: str,
    amount_paid: Decimal,
    payment_mode: str | None = None,
    collected_by: str | None = None,
    receipt_number: str | None = None,
    remarks: str | None = None,
    payment_date: date | None = None,
    audit_actor: User | None = None,
    audit_actor_email: str | None = None,
    audit_ip: str | None = None,
) -> Payment:
    try:
        locked_student = _lock_student_for_payment(db, student.id)
        summary = build_fee_summary(db, locked_student.id, academic_year)
        _validate_payable(summary, fee_head, amount_paid)

        if receipt_number:
            existing_payment = db.query(Payment.id).filter(Payment.receipt_number == receipt_number).first()
            if existing_payment:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Receipt number already exists")

        payment = Payment(
            student_id=locked_student.id,
            academic_year=academic_year,
            fee_head=fee_head,
            amount_paid=amount_paid,
            payment_mode=payment_mode,
            payment_status="success",
            receipt_number=receipt_number,
            collected_by=collected_by,
            remarks=remarks,
            payment_date=payment_date or date.today(),
        )
        db.add(payment)
        db.flush()

        if not payment.receipt_number:
            payment.receipt_number = _generate_receipt_number(payment.id)

        log_audit_event(
            db,
            actor=audit_actor,
            actor_email=audit_actor_email,
            action="payment.status_changed",
            entity_type="payment",
            entity_id=payment.id,
            ip_address=audit_ip,
            details={
                "student_id": locked_student.id,
                "academic_year": academic_year,
                "fee_head": fee_head,
                "amount_paid": amount_paid,
                "payment_mode": payment_mode,
                "receipt_number": payment.receipt_number,
                "old_status": None,
                "new_status": "success",
            },
        )
        db.commit()
        db.refresh(payment)
        return payment
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be recorded because it conflicts with an existing record",
        ) from exc
    except HTTPException:
        db.rollback()
        raise


def create_pending_online_payment(
    db: Session,
    *,
    student: Student,
    academic_year: str,
    fee_head: str,
    amount_paid: Decimal,
    payment_mode: str,
    remarks: str | None = None,
    audit_actor: User | None = None,
    audit_actor_email: str | None = None,
    audit_ip: str | None = None,
) -> Payment:
    try:
        locked_student = _lock_student_for_payment(db, student.id)
        summary = build_fee_summary(db, locked_student.id, academic_year)
        _validate_payable(summary, fee_head, amount_paid)

        payment = Payment(
            student_id=locked_student.id,
            academic_year=academic_year,
            fee_head=fee_head,
            amount_paid=amount_paid,
            payment_mode=payment_mode,
            payment_status="pending",
            razorpay_order_id=_generate_order_id(),
            collected_by="Parent Portal",
            remarks=remarks,
            payment_date=date.today(),
        )
        db.add(payment)
        db.flush()
        log_audit_event(
            db,
            actor=audit_actor,
            actor_email=audit_actor_email,
            action="payment.status_changed",
            entity_type="payment",
            entity_id=payment.id,
            ip_address=audit_ip,
            details={
                "student_id": locked_student.id,
                "academic_year": academic_year,
                "fee_head": fee_head,
                "amount_paid": amount_paid,
                "payment_mode": payment_mode,
                "razorpay_order_id": payment.razorpay_order_id,
                "old_status": None,
                "new_status": "pending",
            },
        )
        db.commit()
        db.refresh(payment)
        return payment
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment order could not be created because it conflicts with an existing record",
        ) from exc
    except HTTPException:
        db.rollback()
        raise


def confirm_pending_online_payment(
    db: Session,
    *,
    payment_id: int,
    razorpay_payment_id: str,
    collected_by: str,
    remarks: str | None = None,
    audit_actor: User | None = None,
    audit_actor_email: str | None = None,
    audit_ip: str | None = None,
) -> Payment:
    try:
        payment = (
            db.execute(select(Payment).where(Payment.id == payment_id).with_for_update())
            .scalar_one_or_none()
        )
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        if payment.payment_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending online payments can be confirmed",
            )

        _lock_student_for_payment(db, payment.student_id)
        summary = build_fee_summary(db, payment.student_id, payment.academic_year)
        _validate_payable(summary, payment.fee_head, payment.amount_paid)

        existing_gateway_payment = (
            db.query(Payment.id)
            .filter(
                Payment.razorpay_payment_id == razorpay_payment_id,
                Payment.id != payment.id,
            )
            .first()
        )
        if existing_gateway_payment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Gateway payment id has already been used",
            )

        old_status = payment.payment_status
        payment.payment_status = "success"
        payment.razorpay_payment_id = razorpay_payment_id
        payment.receipt_number = payment.receipt_number or _generate_receipt_number(payment.id)
        payment.collected_by = collected_by
        payment.remarks = remarks or payment.remarks
        payment.payment_date = date.today()

        log_audit_event(
            db,
            actor=audit_actor,
            actor_email=audit_actor_email,
            action="payment.status_changed",
            entity_type="payment",
            entity_id=payment.id,
            ip_address=audit_ip,
            details={
                "student_id": payment.student_id,
                "academic_year": payment.academic_year,
                "fee_head": payment.fee_head,
                "amount_paid": payment.amount_paid,
                "payment_mode": payment.payment_mode,
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "receipt_number": payment.receipt_number,
                "old_status": old_status,
                "new_status": payment.payment_status,
            },
        )
        db.commit()
        db.refresh(payment)
        return payment
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment could not be confirmed because it conflicts with an existing record",
        ) from exc
    except HTTPException:
        db.rollback()
        raise


def build_invoice(db: Session, student: Student, payment: Payment) -> InvoiceOut:
    updated_summary = build_fee_summary(db, student.id, payment.academic_year)

    return InvoiceOut(
        school_name=settings.school_name,
        payment_id=payment.id,
        receipt_number=payment.receipt_number or f"PAY-{payment.id}",
        payment_date=payment.payment_date,
        academic_year=payment.academic_year,
        fee_head=payment.fee_head,
        amount_paid=payment.amount_paid,
        payment_mode=payment.payment_mode,
        payment_status=payment.payment_status,
        collected_by=payment.collected_by,
        student_id=student.id,
        admission_number=student.admission_number,
        roll_number=student.roll_number,
        student_name=student.student_name,
        class_name=student.class_name,
        section=student.section,
        remaining_balance=updated_summary.balance,
    )
