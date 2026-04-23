"""enforce payment allocation integrity

Revision ID: 20260423_0006
Revises: 20260423_0005
Create Date: 2026-04-23 21:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260423_0006"
down_revision = "20260423_0005"
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

    invalid_amounts = bind.execute(
        sa.text(
            """
            SELECT string_agg(id::text, ', ' ORDER BY id)
            FROM payment_allocations
            WHERE amount <= 0
            """
        )
    ).scalar()

    if invalid_amounts:
        raise RuntimeError(
            "Payment allocations must be greater than zero before migration 20260423_0006 can run: "
            + invalid_amounts
        )

    duplicate_allocations = bind.execute(
        sa.text(
            """
            SELECT string_agg(transaction_id::text || ':' || component, ', ' ORDER BY transaction_id, component)
            FROM (
                SELECT transaction_id, component
                FROM payment_allocations
                GROUP BY transaction_id, component
                HAVING COUNT(*) > 1
            ) duplicates
            """
        )
    ).scalar()

    if duplicate_allocations:
        raise RuntimeError(
            "Duplicate payment allocation components must be resolved before migration 20260423_0006 can run: "
            + duplicate_allocations
        )

    if not has_unique_constraint(inspector, "payment_allocations", "uq_payment_allocations_transaction_component"):
        op.create_unique_constraint(
            "uq_payment_allocations_transaction_component",
            "payment_allocations",
            ["transaction_id", "component"],
        )

    if not has_check_constraint(inspector, "payment_allocations", "ck_payment_allocations_amount_positive"):
        op.create_check_constraint(
            "ck_payment_allocations_amount_positive",
            "payment_allocations",
            "amount > 0",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_check_constraint(inspector, "payment_allocations", "ck_payment_allocations_amount_positive"):
        op.drop_constraint("ck_payment_allocations_amount_positive", "payment_allocations", type_="check")

    if has_unique_constraint(inspector, "payment_allocations", "uq_payment_allocations_transaction_component"):
        op.drop_constraint("uq_payment_allocations_transaction_component", "payment_allocations", type_="unique")
