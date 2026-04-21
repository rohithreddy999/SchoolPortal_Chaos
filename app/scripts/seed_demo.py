from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.aadhaar import tokenize_aadhaar
from app.core.security import hash_password
from app.db.models import Concession, FeeStructure, Payment, Student, User
from app.db.session import SessionLocal


def seed(db: Session) -> dict:
    admin_email = "admin@school.com"
    admin_password = "Admin@12345"
    student_aadhaar = "123412341234"
    father_aadhaar = "987654321012"

    # Users
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(email=admin_email, password_hash=hash_password(admin_password), role="admin")
        db.add(admin)

    # Student
    student = db.query(Student).filter(Student.admission_number == "A0001").first()
    if not student:
        student = Student(
            admission_number="A0001",
            student_identifier="S0001",
            date_of_birth=date(2010, 5, 15),
            student_name="Test Student",
            father_name="Test Father",
            mother_name="Test Mother",
            mobile_number="9999999999",
            class_name="10",
            section="A",
            student_aadhaar_token=tokenize_aadhaar(student_aadhaar),
            father_aadhaar_token=tokenize_aadhaar(father_aadhaar),
        )
        db.add(student)
        db.flush()
    else:
        student.student_identifier = "S0001"
        student.date_of_birth = student.date_of_birth or date(2010, 5, 15)
        student.student_aadhaar_token = student.student_aadhaar_token or tokenize_aadhaar(student_aadhaar)
        student.father_aadhaar_token = student.father_aadhaar_token or tokenize_aadhaar(father_aadhaar)
        student.class_name = student.class_name or "10"
        student.section = student.section or "A"

    year = "2024-2025"

    # Fee structure + concession
    fs = db.query(FeeStructure).filter(FeeStructure.student_id == student.id, FeeStructure.academic_year == year).first()
    if not fs:
        fs = FeeStructure(
            student_id=student.id,
            academic_year=year,
            admission_fee=Decimal("1000.00"),
            term1_fee=Decimal("5000.00"),
            term2_fee=Decimal("5000.00"),
            term3_fee=Decimal("5000.00"),
            transport_fee=Decimal("2000.00"),
            books_fee=Decimal("800.00"),
        )
        db.add(fs)

    cc = db.query(Concession).filter(Concession.student_id == student.id, Concession.academic_year == year).first()
    if not cc:
        cc = Concession(student_id=student.id, academic_year=year, transport_concession=Decimal("500.00"), other_concession=Decimal("0.00"))
        db.add(cc)

    # One successful payment
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.student_id == student.id,
            Payment.academic_year == year,
            Payment.fee_head == "term1",
            Payment.payment_status == "success",
        )
        .first()
    )
    if not existing_payment:
        db.add(
            Payment(
                student_id=student.id,
                academic_year=year,
                fee_head="term1",
                amount_paid=Decimal("2500.00"),
                payment_mode="cash",
                payment_status="success",
                receipt_number="R-0001",
                collected_by="System Seed",
            )
        )

    db.commit()

    return {
        "admin": {"email": admin_email, "password": admin_password},
        "parent_access": {
            "roll_number": student.roll_number,
            "date_of_birth": str(student.date_of_birth),
            "aadhaar_number": student_aadhaar,
            "student_id": student.id,
        },
        "academic_year": year,
    }


def main() -> None:
    db = SessionLocal()
    try:
        info = seed(db)
        print(info)
    finally:
        db.close()


if __name__ == "__main__":
    main()

