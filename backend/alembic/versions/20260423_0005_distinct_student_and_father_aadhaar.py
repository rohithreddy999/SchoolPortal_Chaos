"""enforce distinct student and father aadhaar values

Revision ID: 20260423_0005
Revises: 20260423_0004
Create Date: 2026-04-23 11:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260423_0005"
down_revision = "20260423_0004"
branch_labels = None
depends_on = None


def has_check_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_check_constraints(table_name)
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    bind.execute(
        sa.text(
            """
            UPDATE students
            SET father_aadhaar = NULL
            WHERE student_aadhaar IS NOT NULL
              AND father_aadhaar IS NOT NULL
              AND student_aadhaar = father_aadhaar
            """
        )
    )

    invalid_students = bind.execute(
        sa.text(
            """
            SELECT string_agg(admission_number || ' (' || academic_year || ')', ', ' ORDER BY admission_number, academic_year)
            FROM students
            WHERE student_aadhaar IS NOT NULL
              AND father_aadhaar IS NOT NULL
              AND student_aadhaar = father_aadhaar
            """
        )
    ).scalar()

    if invalid_students:
        raise RuntimeError(
            "Student and father Aadhaar numbers must differ before migration 20260423_0005 can run: "
            + invalid_students
        )

    if not has_check_constraint(inspector, "students", "ck_students_distinct_aadhaar_values"):
        op.create_check_constraint(
            "ck_students_distinct_aadhaar_values",
            "students",
            "student_aadhaar IS NULL OR father_aadhaar IS NULL OR student_aadhaar <> father_aadhaar",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_check_constraint(inspector, "students", "ck_students_distinct_aadhaar_values"):
        op.drop_constraint("ck_students_distinct_aadhaar_values", "students", type_="check")
