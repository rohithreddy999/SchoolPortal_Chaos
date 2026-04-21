from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import AuditLog, User


SENSITIVE_KEY_PARTS = ("aadhaar", "password", "token", "secret")


def client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, nested_value in value.items():
            key_text = str(key)
            if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS):
                sanitized[key_text] = "[REDACTED]"
            else:
                sanitized[key_text] = _sanitize(nested_value)
        return sanitized

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize(item) for item in value]

    return value


def log_audit_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    actor: User | None = None,
    actor_email: str | None = None,
    status: str = "success",
    ip_address: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> AuditLog:
    safe_details = _sanitize(details) if details else None
    audit_log = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_email=actor.email if actor else actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        status=status,
        ip_address=ip_address,
        details=json.dumps(safe_details, sort_keys=True, default=_json_default) if safe_details else None,
    )
    db.add(audit_log)
    return audit_log
