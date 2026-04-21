from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.aadhaar import tokenize_aadhaar
from app.core.security import create_access_token, verify_password
from app.db.models import Student, User
from app.schemas.auth import ParentAccessRequest, Token
from app.services.rate_limit import RateLimitUnavailable, auth_rate_limiter


router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_attempt_key(request: Request, scope: str, subject: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{scope}:{client_host}:{subject.strip().lower()}"


def _raise_rate_limited() -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many failed attempts. Try again later.",
    )


def _handle_rate_limit_unavailable(exc: RateLimitUnavailable) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication rate limiter unavailable",
    ) from exc


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    attempt_key = _auth_attempt_key(request, "admin-login", form_data.username)
    try:
        if auth_rate_limiter.is_limited(attempt_key):
            _raise_rate_limited()

        user = db.query(User).filter(User.email == form_data.username).first()
        if not user or not verify_password(form_data.password, user.password_hash):
            auth_rate_limiter.record_failure(attempt_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if user.role != "admin":
            auth_rate_limiter.record_failure(attempt_key)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only school administrators can use this login endpoint",
            )

        auth_rate_limiter.reset(attempt_key)
    except RateLimitUnavailable as exc:
        _handle_rate_limit_unavailable(exc)

    payload: dict[str, object] = {"user_id": user.id, "email": user.email, "role": user.role}

    token = create_access_token(payload)
    return Token(access_token=token)


@router.post("/parent-access", response_model=Token)
def parent_access(
    request: Request,
    body: ParentAccessRequest,
    db: Session = Depends(get_db),
) -> Token:
    attempt_key = _auth_attempt_key(request, "parent-access", body.roll_number)
    try:
        if auth_rate_limiter.is_limited(attempt_key):
            _raise_rate_limited()

        aadhaar_token = tokenize_aadhaar(body.aadhaar_number)
        student = (
            db.query(Student)
            .filter(
                Student.student_identifier == body.roll_number,
                Student.date_of_birth == body.date_of_birth,
                Student.student_aadhaar_token == aadhaar_token,
            )
            .first()
        )
        if not student:
            auth_rate_limiter.record_failure(attempt_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid roll number, date of birth, or Aadhaar number",
            )

        auth_rate_limiter.reset(attempt_key)
    except RateLimitUnavailable as exc:
        _handle_rate_limit_unavailable(exc)

    token = create_access_token(
        {"role": "parent", "student_id": student.id, "roll_number": student.roll_number}
    )
    return Token(access_token=token)

