from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.core.constants import MAX_MONEY


ACADEMIC_YEAR_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")
MONEY_QUANT = Decimal("0.01")
MAX_MONEY_VALUE = Decimal(MAX_MONEY)


def normalize_academic_year(value: str) -> str:
    value = value.strip()
    match = ACADEMIC_YEAR_PATTERN.fullmatch(value)
    if not match:
        raise ValueError("Academic year must use YYYY-YYYY format")

    start_year = int(match.group(1))
    end_year = int(match.group(2))
    if end_year != start_year + 1:
        raise ValueError("Academic year must cover exactly one year")

    return value


def normalize_money(value: Decimal, *, allow_zero: bool) -> Decimal:
    try:
        normalized = value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Amount must be a valid currency value") from exc

    if value != normalized:
        raise ValueError("Amount cannot have more than two decimal places")

    if allow_zero:
        if normalized < 0:
            raise ValueError("Amount cannot be negative")
    elif normalized <= 0:
        raise ValueError("Amount must be greater than zero")

    if normalized > MAX_MONEY_VALUE:
        raise ValueError(f"Amount cannot exceed {MAX_MONEY_VALUE}")

    return normalized
