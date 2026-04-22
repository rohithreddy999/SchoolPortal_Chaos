"""baseline schema with receipt numbers

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 20:40:00
"""

from datetime import date

from alembic import op
import sqlalchemy as sa


revision = "20260422_0001"
down_revision = None
branch_labels = None
depends_on = None


def has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=False)


def create_students_table() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("admission_number", sa.String(length=50), nullable=False),
        sa.Column("student_name", sa.String(length=120), nullable=False),
        sa.Column("father_name", sa.String(length=120), nullable=False),
        sa.Column("mother_name", sa.String(length=120), nullable=True),
        sa.Column("mobile_number", sa.String(length=20), nullable=False),
        sa.Column("class_name", sa.String(length=30), nullable=False),
        sa.Column("section", sa.String(length=10), nullable=False),
        sa.Column("student_aadhaar", sa.String(length=20), nullable=True),
        sa.Column("father_aadhaar", sa.String(length=20), nullable=True),
        sa.Column("student_identifier", sa.String(length=50), nullable=True),
        sa.Column("pen_number", sa.String(length=50), nullable=True),
        sa.Column("admission_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("first_term_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("second_term_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("third_term_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("transport_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("books_fee", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("concession_transport", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("admission_number", "academic_year", name="uq_student_admission_year"),
    )
    op.create_index("ix_students_id", "students", ["id"])
    op.create_index("ix_students_academic_year", "students", ["academic_year"])
    op.create_index("ix_students_admission_number", "students", ["admission_number"])
    op.create_index("ix_students_student_name", "students", ["student_name"])
    op.create_index("ix_students_class_name", "students", ["class_name"])


def create_payment_transactions_table() -> None:
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receipt_number", sa.String(length=32), nullable=True),
        sa.Column("received_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_payment_transactions_id", "payment_transactions", ["id"])
    op.create_index("ix_payment_transactions_student_id", "payment_transactions", ["student_id"])
    op.create_index("ix_payment_transactions_receipt_number", "payment_transactions", ["receipt_number"], unique=True)


def create_payment_allocations_table() -> None:
    op.create_table(
        "payment_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("payment_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("component", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_payment_allocations_id", "payment_allocations", ["id"])
    op.create_index("ix_payment_allocations_transaction_id", "payment_allocations", ["transaction_id"])


def backfill_receipt_numbers(bind: sa.Connection) -> None:
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
        receipt_number = f"SSHS-{received_on.year}-{row.id:06d}"
        bind.execute(
            sa.text(
                """
                UPDATE payment_transactions
                SET receipt_number = :receipt_number
                WHERE id = :transaction_id
                """
            ),
            {"receipt_number": receipt_number, "transaction_id": row.id},
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not has_table(inspector, "users"):
        create_users_table()

    if not has_table(inspector, "students"):
        create_students_table()

    if not has_table(inspector, "payment_transactions"):
        create_payment_transactions_table()
    else:
        if not has_column(inspector, "payment_transactions", "receipt_number"):
            op.add_column("payment_transactions", sa.Column("receipt_number", sa.String(length=32), nullable=True))
        if not has_index(inspector, "payment_transactions", "ix_payment_transactions_receipt_number"):
            op.create_index(
                "ix_payment_transactions_receipt_number",
                "payment_transactions",
                ["receipt_number"],
                unique=True,
            )

    if not has_table(inspector, "payment_allocations"):
        create_payment_allocations_table()

    backfill_receipt_numbers(bind)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_index(inspector, "payment_transactions", "ix_payment_transactions_receipt_number"):
        op.drop_index("ix_payment_transactions_receipt_number", table_name="payment_transactions")
    if has_column(inspector, "payment_transactions", "receipt_number"):
        op.drop_column("payment_transactions", "receipt_number")
