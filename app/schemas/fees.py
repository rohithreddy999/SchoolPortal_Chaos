from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.core.validation import normalize_academic_year, normalize_money


class FeeStructureUpsert(BaseModel):
    student_id: int
    academic_year: str
    admission_fee: Decimal = Decimal("0.00")
    term1_fee: Decimal = Decimal("0.00")
    term2_fee: Decimal = Decimal("0.00")
    term3_fee: Decimal = Decimal("0.00")
    transport_fee: Decimal = Decimal("0.00")
    books_fee: Decimal = Decimal("0.00")

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, value: str) -> str:
        return normalize_academic_year(value)

    @field_validator(
        "admission_fee",
        "term1_fee",
        "term2_fee",
        "term3_fee",
        "transport_fee",
        "books_fee",
    )
    @classmethod
    def validate_amounts(cls, value: Decimal) -> Decimal:
        return normalize_money(value, allow_zero=True)


class FeeStructureOut(FeeStructureUpsert):
    id: int

    class Config:
        from_attributes = True


class ConcessionUpsert(BaseModel):
    student_id: int
    academic_year: str
    transport_concession: Decimal = Decimal("0.00")
    other_concession: Decimal = Decimal("0.00")

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, value: str) -> str:
        return normalize_academic_year(value)

    @field_validator("transport_concession", "other_concession")
    @classmethod
    def validate_amounts(cls, value: Decimal) -> Decimal:
        return normalize_money(value, allow_zero=True)


class ConcessionOut(ConcessionUpsert):
    id: int

    class Config:
        from_attributes = True


class FeeSummary(BaseModel):
    student_id: int
    academic_year: str

    assigned: dict[str, Decimal]
    concessions: dict[str, Decimal]
    paid: dict[str, Decimal]

    total_assigned: Decimal
    total_concessions: Decimal
    total_paid: Decimal
    balance: Decimal

