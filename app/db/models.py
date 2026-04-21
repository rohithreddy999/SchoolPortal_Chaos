from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin','parent')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    parent_links: Mapped[list[Parent]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_student_aadhaar_token", "student_aadhaar_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admission_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    student_identifier: Mapped[str] = mapped_column("student_id", String(20), unique=True, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    student_name: Mapped[str] = mapped_column(String(100), nullable=False)
    father_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(15), nullable=True)

    class_name: Mapped[str] = mapped_column(String(10), nullable=False)
    section: Mapped[str] = mapped_column(String(5), nullable=False)

    student_aadhaar_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    father_aadhaar_token: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    parent_links: Mapped[list[Parent]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    fee_structures: Mapped[list[FeeStructure]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    concessions: Mapped[list[Concession]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    payments: Mapped[list[Payment]] = relationship(back_populates="student")

    @property
    def roll_number(self) -> str:
        return self.student_identifier


class Parent(Base):
    __tablename__ = "parents"
    __table_args__ = (
        UniqueConstraint("user_id", "student_id", name="uq_parents_user_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    is_primary: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="parent_links")
    student: Mapped[Student] = relationship(back_populates="parent_links")


class FeeStructure(Base):
    __tablename__ = "fee_structure"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year", name="uq_fee_structure_student_year"),
        CheckConstraint(
            "admission_fee >= 0 AND term1_fee >= 0 AND term2_fee >= 0 AND "
            "term3_fee >= 0 AND transport_fee >= 0 AND books_fee >= 0",
            name="ck_fee_structure_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)

    admission_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    term1_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    term2_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    term3_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    transport_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    books_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")

    student: Mapped[Student] = relationship(back_populates="fee_structures")


class Concession(Base):
    __tablename__ = "concessions"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year", name="uq_concessions_student_year"),
        CheckConstraint(
            "transport_concession >= 0 AND other_concession >= 0",
            name="ck_concessions_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)

    transport_concession: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    other_concession: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")

    student: Mapped[Student] = relationship(back_populates="concessions")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "fee_head IN ('term1','term2','term3','transport','books','admission')",
            name="ck_payments_fee_head",
        ),
        CheckConstraint(
            "payment_status IN ('pending','success','failed')",
            name="ck_payments_status",
        ),
        CheckConstraint("amount_paid > 0", name="ck_payments_amount_positive"),
        Index("ix_payments_student_year_status", "student_id", "academic_year", "payment_status"),
        Index("ix_payments_student_year_head_status", "student_id", "academic_year", "fee_head", "payment_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)

    fee_head: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    payment_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    razorpay_order_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    collected_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped[Student] = relationship(back_populates="payments")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="success")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

