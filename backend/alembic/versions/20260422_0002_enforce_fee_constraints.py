"""enforce fee constraints and receipt requirements

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22 21:35:00
"""

from datetime import date

from alembic import op
import sqlalchemy as sa


revision = "20260422_0002"
down_revision = "20260422_0001"
branch_labels = None
depends_on = None


CHECK_CONSTRAINTS = {
    "ck_students_admission_fee_non_negative": "admission_fee >= 0",
    "ck_students_first_term_fee_non_negative": "first_term_fee >= 0",
    "ck_students_second_term_fee_non_negative": "second_term_fee >= 0",
    "ck_students_third_term_fee_non_negative": "third_term_fee >= 0",
    "ck_students_transport_fee_non_negative": "transport_fee >= 0",
    "ck_students_books_fee_non_negative": "books_fee >= 0",
    "ck_students_concession_transport_non_negative": "concession_transport >= 0",
    "ck_students_concession_within_transport": "concession_transport <= transport_fee",
}


def has_check_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(constraint["name"] == constraint_name for constraint in inspector.get_check_constraints(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    rows = bind.execute(
        sa.text(
            """
            SELECT id, received_on
            FROM payment_transactions
            WHERE receipt_number IS NULL
            ORDER BY id
            """
        )
    ).fetchall()
    for row in rows:
        received_on = row.received_on
        if not isinstance(received_on, date):
            received_on = date.fromisoformat(str(received_on))
        bind.execute(
            sa.text(
                """
                UPDATE payment_transactions
                SET receipt_number = :receipt_number
                WHERE id = :transaction_id
                """
            ),
            {
                "receipt_number": f"SSHS-{received_on.year}-{row.id:06d}",
                "transaction_id": row.id,
            },
        )

    nullable_columns = {column["name"]: column["nullable"] for column in inspector.get_columns("payment_transactions")}
    if nullable_columns.get("receipt_number", True):
        op.alter_column(
            "payment_transactions",
            "receipt_number",
            existing_type=sa.String(length=32),
            nullable=False,
        )

    for constraint_name, sqltext in CHECK_CONSTRAINTS.items():
        if not has_check_constraint(inspector, "students", constraint_name):
            op.create_check_constraint(constraint_name, "students", sqltext)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for constraint_name in CHECK_CONSTRAINTS:
        if has_check_constraint(inspector, "students", constraint_name):
            op.drop_constraint(constraint_name, "students", type_="check")

    nullable_columns = {column["name"]: column["nullable"] for column in inspector.get_columns("payment_transactions")}
    if not nullable_columns.get("receipt_number", True):
        op.alter_column(
            "payment_transactions",
            "receipt_number",
            existing_type=sa.String(length=32),
            nullable=True,
        )
