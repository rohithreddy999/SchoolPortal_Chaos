from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.payment import PaymentAllocation, PaymentTransaction
from app.models.student import Student
from app.models.user import User
from app.schemas.student import (
    PaymentTransactionCreate,
    StudentCreate,
    StudentListItem,
    StudentRead,
    StudentUpdate,
)
from app.services.student_balances import (
    COMPONENT_LABELS,
    build_fee_summary,
    get_component_assessed,
    get_component_assessed_values,
    get_component_paid,
)
from app.services.student_reports import build_student_statement_pdf


router = APIRouter(prefix="/students", tags=["students"])
settings = get_settings()


def get_integrity_error_detail(exc: IntegrityError, fallback: str) -> str:
    diag = getattr(getattr(exc, "orig", None), "diag", None)
    constraint_name = getattr(diag, "constraint_name", None)
    constraint_messages = {
        "uq_student_admission_year": "A student with this admission number already exists for the selected academic year",
        "uq_students_student_aadhaar": "A student with this Aadhaar number already exists",
        "ck_students_student_aadhaar_format": "Student Aadhaar must contain exactly 12 digits",
        "ck_students_father_aadhaar_format": "Father Aadhaar must contain exactly 12 digits",
    }
    return constraint_messages.get(constraint_name, fallback)


def get_student_or_404(db: Session, student_id: int, *, for_update: bool = False) -> Student:
    query = (
        db.query(Student)
        .populate_existing()
        .options(
            selectinload(Student.payment_transactions).selectinload(PaymentTransaction.allocations),
            selectinload(Student.payment_transactions).selectinload(PaymentTransaction.created_by),
        )
        .filter(Student.id == student_id)
    )
    if for_update:
        query = query.with_for_update()
    student = query.first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def to_student_list_item(student: Student) -> StudentListItem:
    return StudentListItem(
        id=student.id,
        academic_year=student.academic_year,
        admission_number=student.admission_number,
        student_name=student.student_name,
        class_name=student.class_name,
        section=student.section,
        mobile_number=student.mobile_number,
        updated_at=student.updated_at,
    )


def to_student_read(student: Student) -> StudentRead:
    payment_transactions = sorted(
        student.payment_transactions,
        key=lambda transaction: (transaction.received_on, transaction.id),
        reverse=True,
    )
    return StudentRead(
        id=student.id,
        academic_year=student.academic_year,
        admission_number=student.admission_number,
        student_name=student.student_name,
        father_name=student.father_name,
        mother_name=student.mother_name,
        mobile_number=student.mobile_number,
        class_name=student.class_name,
        section=student.section,
        student_aadhaar=student.student_aadhaar,
        father_aadhaar=student.father_aadhaar,
        student_identifier=student.student_identifier,
        pen_number=student.pen_number,
        admission_fee=student.admission_fee,
        first_term_fee=student.first_term_fee,
        second_term_fee=student.second_term_fee,
        third_term_fee=student.third_term_fee,
        transport_fee=student.transport_fee,
        books_fee=student.books_fee,
        concession_transport=student.concession_transport,
        created_at=student.created_at,
        updated_at=student.updated_at,
        fee_summary=build_fee_summary(student),
        payment_transactions=payment_transactions,
    )


def validate_fee_schedule_against_paid_amounts(student: Student, payload: StudentUpdate) -> None:
    assessed_map = get_component_assessed_values(
        admission_fee=payload.admission_fee,
        first_term_fee=payload.first_term_fee,
        second_term_fee=payload.second_term_fee,
        third_term_fee=payload.third_term_fee,
        transport_fee=payload.transport_fee,
        books_fee=payload.books_fee,
        concession_transport=payload.concession_transport,
    )
    paid_map = get_component_paid(student)

    for component, assessed_amount in assessed_map.items():
        paid_amount = paid_map[component]
        if assessed_amount < paid_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{COMPONENT_LABELS[component]} cannot be reduced below the already received amount "
                    f"of {paid_amount:.2f}"
                ),
            )


def ensure_unique_student_aadhaar(
    db: Session,
    student_aadhaar: str | None,
    *,
    current_student_id: int | None = None,
) -> None:
    if not student_aadhaar:
        return

    query = db.query(Student).filter(Student.student_aadhaar == student_aadhaar)
    if current_student_id is not None:
        query = query.filter(Student.id != current_student_id)

    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this Aadhaar number already exists",
        )


@router.get("", response_model=list[StudentListItem])
def list_students(
    admission_number: str | None = Query(default=None),
    academic_year: str | None = Query(default=None),
    student_name: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudentListItem]:
    query = db.query(Student)
    if admission_number:
        query = query.filter(Student.admission_number == admission_number)
    if academic_year:
        query = query.filter(Student.academic_year == academic_year)
    if student_name:
        query = query.filter(Student.student_name.ilike(f"%{student_name}%"))
    if class_name:
        query = query.filter(Student.class_name == class_name)

    students = query.order_by(Student.student_name.asc()).limit(100).all()
    return [to_student_list_item(student) for student in students]


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentRead:
    existing = (
        db.query(Student)
        .filter(
            Student.admission_number == payload.admission_number,
            Student.academic_year == payload.academic_year,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this admission number already exists for the selected academic year",
        )
    ensure_unique_student_aadhaar(db, payload.student_aadhaar)

    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_integrity_error_detail(
                exc,
                "The student record could not be saved because it conflicts with existing data",
            ),
        ) from exc
    db.expire_all()
    student = get_student_or_404(db, student.id)
    return to_student_read(student)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentRead:
    student = get_student_or_404(db, student_id)
    return to_student_read(student)


@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentRead:
    student = get_student_or_404(db, student_id)
    validate_fee_schedule_against_paid_amounts(student, payload)
    ensure_unique_student_aadhaar(db, payload.student_aadhaar, current_student_id=student_id)

    duplicate = (
        db.query(Student)
        .filter(
            Student.id != student_id,
            Student.admission_number == payload.admission_number,
            Student.academic_year == payload.academic_year,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another student already uses this admission number for the selected academic year",
        )

    for field, value in payload.model_dump().items():
        setattr(student, field, value)

    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_integrity_error_detail(
                exc,
                "The student record could not be updated because it conflicts with existing data",
            ),
        ) from exc
    db.expire_all()
    student = get_student_or_404(db, student.id)
    return to_student_read(student)


@router.post("/{student_id}/payments", response_model=StudentRead)
def record_payment(
    student_id: int,
    payload: PaymentTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentRead:
    student = get_student_or_404(db, student_id, for_update=True)
    assessed_map = get_component_assessed(student)
    paid_map = get_component_paid(student)

    for allocation in payload.allocations:
        component = allocation.component
        new_paid_total = paid_map[component] + Decimal(allocation.amount)
        if new_paid_total > assessed_map[component]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment for {component} exceeds the remaining balance",
            )

    transaction = PaymentTransaction(
        student_id=student.id,
        receipt_number=f"TMP-{uuid4().hex[:20]}",
        received_on=payload.received_on,
        note=payload.note,
        created_by_user_id=current_user.id,
    )
    for allocation in payload.allocations:
        transaction.allocations.append(
            PaymentAllocation(component=allocation.component, amount=allocation.amount)
        )

    db.add(transaction)
    db.flush()
    transaction.receipt_number = f"SSHS-{payload.received_on.year}-{transaction.id:06d}"
    db.commit()
    db.expire_all()
    student = get_student_or_404(db, student.id)
    return to_student_read(student)


@router.get("/{student_id}/statement.pdf")
def download_student_statement_pdf(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    student = get_student_or_404(db, student_id)
    pdf_bytes = build_student_statement_pdf(student, settings.school_name)
    filename = f"{student.admission_number}_{student.academic_year}_statement.pdf".replace(" ", "_")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
