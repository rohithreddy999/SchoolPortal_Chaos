from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.api.deps import get_db
from app.core.aadhaar import tokenize_aadhaar
from app.core.validation import normalize_academic_year
from app.db.models import Concession, FeeStructure, Payment, User, Student
from app.schemas.fees import ConcessionOut, ConcessionUpsert, FeeStructureOut, FeeStructureUpsert, FeeSummary
from app.schemas.payments import InvoiceOut, OfflinePaymentCreate, OnlinePaymentConfirm, PaymentOut
from app.schemas.students import StudentCreate, StudentOut
from app.services.audit import client_ip, log_audit_event
from app.services.portal import (
    build_fee_summary,
    build_invoice,
    confirm_pending_online_payment,
    create_success_payment,
    ensure_student_exists,
    validate_concession_change,
    validate_fee_structure_change,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
def me(_: User = Depends(require_admin)) -> dict:
    return {"role": "admin"}


@router.get("/students", response_model=list[StudentOut])
def list_students(
    search: str | None = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[Student]:
    query = db.query(Student)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.admission_number.ilike(pattern),
                Student.student_identifier.ilike(pattern),
                Student.student_name.ilike(pattern),
                Student.class_name.ilike(pattern),
                Student.mobile_number.ilike(pattern),
            )
        )
    return query.order_by(Student.created_at.desc(), Student.id.desc()).limit(limit).all()


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Student:
    return ensure_student_exists(db, student_id)


@router.get("/fee-summary", response_model=FeeSummary)
def admin_fee_summary(
    student_id: int,
    academic_year: str = Query(..., examples=["2024-2025"]),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FeeSummary:
    ensure_student_exists(db, student_id)
    try:
        normalized_year = normalize_academic_year(academic_year)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_fee_summary(db, student_id, normalized_year)


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    student_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[Payment]:
    query = db.query(Payment)
    if student_id is not None:
        ensure_student_exists(db, student_id)
        query = query.filter(Payment.student_id == student_id)
    if status_filter and status_filter.strip():
        status_value = status_filter.strip().lower()
        if status_value not in {"pending", "success", "failed"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status must be one of: pending, success, failed",
            )
        query = query.filter(Payment.payment_status == status_value)
    return query.order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(limit).all()


@router.get("/payments/{payment_id}/invoice", response_model=InvoiceOut)
def admin_invoice(
    payment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> InvoiceOut:
    payment = db.get(Payment, payment_id)
    if not payment or payment.payment_status != "success":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    student = ensure_student_exists(db, payment.student_id)
    return build_invoice(db, student, payment)


@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def register_student(
    body: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Student:
    existing_student = (
        db.query(Student)
        .filter(
            or_(
                Student.admission_number == body.admission_number,
                Student.student_identifier == body.roll_number,
            )
        )
        .first()
    )
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this admission number or roll number already exists",
        )

    student = Student(
        admission_number=body.admission_number,
        student_identifier=body.roll_number,
        student_name=body.student_name,
        father_name=body.father_name,
        mother_name=body.mother_name,
        mobile_number=body.mobile_number,
        class_name=body.class_name,
        section=body.section,
        date_of_birth=body.date_of_birth,
        student_aadhaar_token=tokenize_aadhaar(body.student_aadhaar),
        father_aadhaar_token=tokenize_aadhaar(body.father_aadhaar) if body.father_aadhaar else None,
    )
    db.add(student)
    try:
        db.flush()
        log_audit_event(
            db,
            actor=admin,
            action="admin.student.create",
            entity_type="student",
            entity_id=student.id,
            ip_address=client_ip(request),
            details={
                "admission_number": student.admission_number,
                "roll_number": student.roll_number,
                "class_name": student.class_name,
                "section": student.section,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this admission number or roll number already exists",
        ) from exc
    db.refresh(student)
    return student


@router.post("/parents/link")
def link_parent(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    _ = db
    return {
        "message": "Parent accounts are not required. Use /auth/parent-access with roll number, date of birth, and Aadhaar."
    }


@router.post("/fee-structure", response_model=FeeStructureOut)
def assign_fee_structure(
    body: FeeStructureUpsert,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> FeeStructure:
    ensure_student_exists(db, body.student_id)
    validate_fee_structure_change(
        db,
        student_id=body.student_id,
        academic_year=body.academic_year,
        assigned={
            "admission": body.admission_fee,
            "term1": body.term1_fee,
            "term2": body.term2_fee,
            "term3": body.term3_fee,
            "transport": body.transport_fee,
            "books": body.books_fee,
        },
    )

    fee_structure = (
        db.query(FeeStructure)
        .filter(
            FeeStructure.student_id == body.student_id,
            FeeStructure.academic_year == body.academic_year,
        )
        .first()
    )

    if not fee_structure:
        fee_structure = FeeStructure(student_id=body.student_id, academic_year=body.academic_year)
        db.add(fee_structure)

    fee_structure.admission_fee = body.admission_fee
    fee_structure.term1_fee = body.term1_fee
    fee_structure.term2_fee = body.term2_fee
    fee_structure.term3_fee = body.term3_fee
    fee_structure.transport_fee = body.transport_fee
    fee_structure.books_fee = body.books_fee

    try:
        db.flush()
        log_audit_event(
            db,
            actor=admin,
            action="admin.fee_structure.upsert",
            entity_type="fee_structure",
            entity_id=fee_structure.id,
            ip_address=client_ip(request),
            details={
                "student_id": body.student_id,
                "academic_year": body.academic_year,
                "fees": {
                    "admission": body.admission_fee,
                    "term1": body.term1_fee,
                    "term2": body.term2_fee,
                    "term3": body.term3_fee,
                    "transport": body.transport_fee,
                    "books": body.books_fee,
                },
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fee structure was changed concurrently. Refresh and retry.",
        ) from exc
    db.refresh(fee_structure)
    return fee_structure


@router.post("/concessions", response_model=ConcessionOut)
def apply_concession(
    body: ConcessionUpsert,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Concession:
    ensure_student_exists(db, body.student_id)
    validate_concession_change(
        db,
        student_id=body.student_id,
        academic_year=body.academic_year,
        transport_concession=body.transport_concession,
        other_concession=body.other_concession,
    )

    concession = (
        db.query(Concession)
        .filter(
            Concession.student_id == body.student_id,
            Concession.academic_year == body.academic_year,
        )
        .first()
    )

    if not concession:
        concession = Concession(student_id=body.student_id, academic_year=body.academic_year)
        db.add(concession)

    concession.transport_concession = body.transport_concession
    concession.other_concession = body.other_concession

    try:
        db.flush()
        log_audit_event(
            db,
            actor=admin,
            action="admin.concession.upsert",
            entity_type="concession",
            entity_id=concession.id,
            ip_address=client_ip(request),
            details={
                "student_id": body.student_id,
                "academic_year": body.academic_year,
                "transport_concession": body.transport_concession,
                "other_concession": body.other_concession,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concession was changed concurrently. Refresh and retry.",
        ) from exc
    db.refresh(concession)
    return concession


@router.post("/payments/online/{payment_id}/confirm", response_model=InvoiceOut)
def confirm_online_payment(
    payment_id: int,
    body: OnlinePaymentConfirm,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> InvoiceOut:
    payment = confirm_pending_online_payment(
        db,
        payment_id=payment_id,
        razorpay_payment_id=body.razorpay_payment_id,
        collected_by=admin.email,
        remarks=body.remarks,
        audit_actor=admin,
        audit_ip=client_ip(request),
    )
    student = ensure_student_exists(db, payment.student_id)
    return build_invoice(db, student, payment)


@router.post("/payments/offline", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def record_offline_payment(
    body: OfflinePaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> InvoiceOut:
    student = ensure_student_exists(db, body.student_id)
    payment = create_success_payment(
        db,
        student=student,
        academic_year=body.academic_year,
        fee_head=body.fee_head,
        amount_paid=body.amount_paid,
        payment_mode=body.payment_mode or "offline",
        collected_by=body.collected_by or "School Administration",
        receipt_number=body.receipt_number,
        remarks=body.remarks,
        payment_date=body.payment_date,
        audit_actor=admin,
        audit_ip=client_ip(request),
    )
    return build_invoice(db, student, payment)

