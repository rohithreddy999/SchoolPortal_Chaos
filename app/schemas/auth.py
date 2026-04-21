from datetime import date

from pydantic import BaseModel, EmailStr, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class ParentAccessRequest(BaseModel):
    roll_number: str
    date_of_birth: date
    aadhaar_number: str

    @field_validator("roll_number")
    @classmethod
    def normalize_roll_number(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Roll number is required")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("Date of birth must be in the past")
        return value

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) != 12:
            raise ValueError("Aadhaar number must be 12 digits")
        return digits

