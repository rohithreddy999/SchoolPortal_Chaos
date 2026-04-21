from datetime import date

from pydantic import BaseModel, field_validator


def _normalize_digits(value: str | None, field_name: str, expected_lengths: set[int]) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) not in expected_lengths:
        raise ValueError(f"{field_name} must contain {', '.join(str(length) for length in sorted(expected_lengths))} digits")
    return digits


class StudentCreate(BaseModel):
    admission_number: str
    roll_number: str
    student_name: str
    father_name: str | None = None
    mother_name: str | None = None
    mobile_number: str | None = None
    class_name: str
    section: str
    date_of_birth: date
    student_aadhaar: str
    father_aadhaar: str | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("Date of birth must be in the past")
        return value

    @field_validator("admission_number", "roll_number")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("This field is required")
        return value

    @field_validator("student_name", "father_name", "mother_name", "class_name", "section")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str | None) -> str | None:
        return _normalize_digits(value, "Mobile number", {10, 11, 12, 13, 14, 15})

    @field_validator("student_aadhaar")
    @classmethod
    def validate_student_aadhaar(cls, value: str) -> str:
        normalized = _normalize_digits(value, "Student Aadhaar", {12})
        if normalized is None:
            raise ValueError("Student Aadhaar is required")
        return normalized

    @field_validator("father_aadhaar")
    @classmethod
    def validate_father_aadhaar(cls, value: str | None) -> str | None:
        return _normalize_digits(value, "Father Aadhaar", {12})


class StudentOut(BaseModel):
    id: int
    admission_number: str
    roll_number: str
    student_name: str
    father_name: str | None = None
    mother_name: str | None = None
    mobile_number: str | None = None
    class_name: str
    section: str
    date_of_birth: date | None = None

    class Config:
        from_attributes = True
