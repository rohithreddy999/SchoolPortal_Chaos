from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import decode_token
from app.db.models import Student, User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        return decode_token(token)
    except ValueError:
        raise _unauthorized("Invalid token")


def get_current_user(
    db: Session = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> User:
    user_id = payload.get("user_id")
    if not user_id:
        raise _unauthorized("Invalid token payload")
    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        raise _unauthorized("Invalid token payload")

    user = db.get(User, parsed_user_id)
    if not user:
        raise _unauthorized("User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_parent_student(
    db: Session = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> Student:
    if payload.get("role") != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent access required")

    student_id = payload.get("student_id")
    if not student_id:
        raise _unauthorized("Parent token missing student_id")

    try:
        parsed_student_id = int(student_id)
    except (TypeError, ValueError):
        raise _unauthorized("Parent token missing student_id")

    student = db.get(Student, parsed_student_id)
    if not student:
        raise _unauthorized("Student not found")

    roll_number = payload.get("roll_number")
    if roll_number and student.roll_number != str(roll_number):
        raise _unauthorized("Student session is invalid")

    return student

