"""normalize and enforce student aadhaar uniqueness

Revision ID: 20260422_0003
Revises: 20260422_0002
Create Date: 2026-04-22 22:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0003"
down_revision = "20260422_0002"
branch_labels = None
depends_on = None


def has_unique_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


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
            r"""
            UPDATE students
            SET
                student_aadhaar = NULLIF(regexp_replace(COALESCE(student_aadhaar, ''), '\D', '', 'g'), ''),
                father_aadhaar = NULLIF(regexp_replace(COALESCE(father_aadhaar, ''), '\D', '', 'g'), '')
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE students
            SET student_aadhaar = NULL
            WHERE student_aadhaar IS NOT NULL
              AND student_aadhaar !~ '^[0-9]{12}$'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE students
            SET father_aadhaar = NULL
            WHERE father_aadhaar IS NOT NULL
              AND father_aadhaar !~ '^[0-9]{12}$'
            """
        )
    )

    duplicates = bind.execute(
        sa.text(
            """
            SELECT
                student_aadhaar,
                string_agg(admission_number || ' (' || academic_year || ')', ', ' ORDER BY admission_number, academic_year) AS student_refs
            FROM students
            WHERE student_aadhaar IS NOT NULL
            GROUP BY student_aadhaar
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicates:
        duplicate_lines = [
            f"{row.student_aadhaar}: {row.student_refs}"
            for row in duplicates
        ]
        raise RuntimeError(
            "Duplicate student Aadhaar numbers must be resolved before migration 20260422_0003 can run: "
            + "; ".join(duplicate_lines)
        )

    if not has_unique_constraint(inspector, "students", "uq_students_student_aadhaar"):
        op.create_unique_constraint("uq_students_student_aadhaar", "students", ["student_aadhaar"])

    if not has_check_constraint(inspector, "students", "ck_students_student_aadhaar_format"):
        op.create_check_constraint(
            "ck_students_student_aadhaar_format",
            "students",
            "student_aadhaar IS NULL OR student_aadhaar ~ '^[0-9]{12}$'",
        )

    if not has_check_constraint(inspector, "students", "ck_students_father_aadhaar_format"):
        op.create_check_constraint(
            "ck_students_father_aadhaar_format",
            "students",
            "father_aadhaar IS NULL OR father_aadhaar ~ '^[0-9]{12}$'",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_check_constraint(inspector, "students", "ck_students_father_aadhaar_format"):
        op.drop_constraint("ck_students_father_aadhaar_format", "students", type_="check")

    if has_check_constraint(inspector, "students", "ck_students_student_aadhaar_format"):
        op.drop_constraint("ck_students_student_aadhaar_format", "students", type_="check")

    if has_unique_constraint(inspector, "students", "uq_students_student_aadhaar"):
        op.drop_constraint("uq_students_student_aadhaar", "students", type_="unique")
