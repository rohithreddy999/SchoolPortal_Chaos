from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("admission_number", "academic_year", name="uq_student_admission_year"),
        UniqueConstraint("student_aadhaar", name="uq_students_student_aadhaar"),
        CheckConstraint("admission_fee >= 0", name="ck_students_admission_fee_non_negative"),
        CheckConstraint("first_term_fee >= 0", name="ck_students_first_term_fee_non_negative"),
        CheckConstraint("second_term_fee >= 0", name="ck_students_second_term_fee_non_negative"),
        CheckConstraint("third_term_fee >= 0", name="ck_students_third_term_fee_non_negative"),
        CheckConstraint("transport_fee >= 0", name="ck_students_transport_fee_non_negative"),
        CheckConstraint("books_fee >= 0", name="ck_students_books_fee_non_negative"),
        CheckConstraint("concession_transport >= 0", name="ck_students_concession_transport_non_negative"),
        CheckConstraint("concession_transport <= transport_fee", name="ck_students_concession_within_transport"),
        CheckConstraint(
            "student_aadhaar IS NULL OR char_length(student_aadhaar) = 12",
            name="ck_students_student_aadhaar_format",
        ),
        CheckConstraint(
            "father_aadhaar IS NULL OR char_length(father_aadhaar) = 12",
            name="ck_students_father_aadhaar_format",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    academic_year: Mapped[str] = mapped_column(String(20), index=True)
    admission_number: Mapped[str] = mapped_column(String(50), index=True)
    student_name: Mapped[str] = mapped_column(String(120), index=True)
    father_name: Mapped[str] = mapped_column(String(120))
    mother_name: Mapped[str] = mapped_column(String(120), nullable=True)
    mobile_number: Mapped[str] = mapped_column(String(20))
    class_name: Mapped[str] = mapped_column(String(30), index=True)
    section: Mapped[str] = mapped_column(String(10))
    student_aadhaar: Mapped[str] = mapped_column(String(20), nullable=True)
    father_aadhaar: Mapped[str] = mapped_column(String(20), nullable=True)
    student_identifier: Mapped[str] = mapped_column(String(50), nullable=True)
    pen_number: Mapped[str] = mapped_column(String(50), nullable=True)

    admission_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    first_term_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    second_term_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    third_term_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    transport_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    books_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    concession_transport: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment_transactions = relationship(
        "PaymentTransaction",
        back_populates="student",
        cascade="all, delete-orphan",
    )
