"""enforce student mobile number format

Revision ID: 20260423_0004
Revises: 20260422_0003
Create Date: 2026-04-23 11:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260423_0004"
down_revision = "20260422_0003"
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
            r"""
            UPDATE students
            SET mobile_number = regexp_replace(COALESCE(mobile_number, ''), '\D', '', 'g')
            """
        )
    )

    invalid_students = bind.execute(
        sa.text(
            """
            SELECT string_agg(admission_number || ' (' || academic_year || ')', ', ' ORDER BY admission_number, academic_year)
            FROM students
            WHERE mobile_number !~ '^[0-9]{10}$'
            """
        )
    ).scalar()

    if invalid_students:
        raise RuntimeError(
            "Student mobile numbers must be 10 digits before migration 20260423_0004 can run: "
            + invalid_students
        )

    if not has_check_constraint(inspector, "students", "ck_students_mobile_number_format"):
        op.create_check_constraint(
            "ck_students_mobile_number_format",
            "students",
            "mobile_number ~ '^[0-9]{10}$'",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_check_constraint(inspector, "students", "ck_students_mobile_number_format"):
        op.drop_constraint("ck_students_mobile_number_format", "students", type_="check")
