from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeeComponent(StrEnum):
    ADMISSION = "admission_fee"
    FIRST_TERM = "first_term_fee"
    SECOND_TERM = "second_term_fee"
    THIRD_TERM = "third_term_fee"
    TRANSPORT = "transport_fee"
    BOOKS = "books_fee"


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    receipt_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    received_on: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="payment_transactions")
    created_by = relationship("User", back_populates="payment_transactions")
    allocations = relationship(
        "PaymentAllocation",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="PaymentAllocation.id",
    )

    @property
    def created_by_username(self) -> str | None:
        if not self.created_by:
            return None
        return self.created_by.username


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("payment_transactions.id", ondelete="CASCADE"), index=True)
    component: Mapped[FeeComponent] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    transaction = relationship("PaymentTransaction", back_populates="allocations")
