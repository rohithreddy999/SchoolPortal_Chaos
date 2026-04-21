from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.core.constants import FEE_HEADS, OFFLINE_PAYMENT_MODES, ONLINE_PAYMENT_MODES
from app.core.validation import normalize_academic_year, normalize_money


class OfflinePaymentCreate(BaseModel):
    student_id: int
    academic_year: str
    fee_head: str
    amount_paid: Decimal
    payment_mode: str | None = None
    receipt_number: str | None = None
    collected_by: str | None = None
    remarks: str | None = None
    payment_date: date | None = None

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, value: str) -> str:
        return normalize_academic_year(value)

    @field_validator("fee_head")
    @classmethod
    def validate_fee_head(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in FEE_HEADS:
            raise ValueError(f"fee_head must be one of: {', '.join(FEE_HEADS)}")
        return value

    @field_validator("amount_paid")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return normalize_money(value, allow_zero=False)

    @field_validator("payment_mode")
    @classmethod
    def validate_payment_mode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not value:
            return None
        if value not in OFFLINE_PAYMENT_MODES:
            raise ValueError(f"payment_mode must be one of: {', '.join(OFFLINE_PAYMENT_MODES)}")
        return value

    @field_validator("receipt_number")
    @classmethod
    def normalize_receipt_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if not value:
            return None
        if len(value) > 30:
            raise ValueError("receipt_number cannot exceed 30 characters")
        return value

    @field_validator("collected_by", "remarks")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("payment_date cannot be in the future")
        return value


class ParentPaymentCreate(BaseModel):
    academic_year: str
    fee_head: str
    amount_paid: Decimal
    payment_mode: str
    remarks: str | None = None

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, value: str) -> str:
        return normalize_academic_year(value)

    @field_validator("fee_head")
    @classmethod
    def validate_fee_head(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in FEE_HEADS:
            raise ValueError(f"fee_head must be one of: {', '.join(FEE_HEADS)}")
        return value

    @field_validator("amount_paid")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return normalize_money(value, allow_zero=False)

    @field_validator("payment_mode")
    @classmethod
    def validate_payment_mode(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("payment_mode is required")
        if value not in ONLINE_PAYMENT_MODES:
            raise ValueError(f"payment_mode must be one of: {', '.join(ONLINE_PAYMENT_MODES)}")
        return value

    @field_validator("remarks")
    @classmethod
    def normalize_remarks(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class OnlinePaymentConfirm(BaseModel):
    razorpay_payment_id: str
    remarks: str | None = None

    @field_validator("razorpay_payment_id")
    @classmethod
    def validate_gateway_payment_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("razorpay_payment_id is required")
        if len(value) > 50:
            raise ValueError("razorpay_payment_id cannot exceed 50 characters")
        return value

    @field_validator("remarks")
    @classmethod
    def normalize_remarks(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class PaymentOut(BaseModel):
    id: int
    student_id: int
    academic_year: str
    fee_head: str
    amount_paid: Decimal
    payment_date: date
    payment_mode: str | None = None
    payment_status: str
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    receipt_number: str | None = None
    collected_by: str | None = None
    remarks: str | None = None

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    school_name: str
    payment_id: int
    receipt_number: str
    payment_date: date
    academic_year: str
    fee_head: str
    amount_paid: Decimal
    payment_mode: str | None = None
    payment_status: str
    collected_by: str | None = None
    student_id: int
    admission_number: str
    roll_number: str
    student_name: str
    class_name: str
    section: str
    remaining_balance: Decimal

