from __future__ import annotations

import hashlib
import hmac

from app.core.config import settings


def normalize_aadhaar_digits(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits or None


def tokenize_aadhaar(value: str) -> str:
    digits = normalize_aadhaar_digits(value)
    if digits is None or len(digits) != 12:
        raise ValueError("Aadhaar number must be 12 digits")

    return hmac.new(
        settings.aadhaar_token_key.encode("utf-8"),
        digits.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def tokenize_legacy_aadhaar(value: str | None) -> str | None:
    digits = normalize_aadhaar_digits(value)
    if digits is None or len(digits) != 12:
        return None
    return tokenize_aadhaar(digits)
