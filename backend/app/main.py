from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.api.routes_auth import router as auth_router
from app.api.routes_students import router as students_router
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


settings = get_settings()


def ensure_default_admin() -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.default_admin_username).first()
        if user:
            return
        admin = User(
            username=settings.default_admin_username,
            hashed_password=get_password_hash(settings.default_admin_password),
            is_active=True,
        )
        db.add(admin)
        db.commit()
    except (OperationalError, ProgrammingError) as exc:
        raise RuntimeError("Database schema is not ready. Run 'alembic upgrade head'.") from exc
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_default_admin()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(students_router, prefix=settings.api_prefix)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    db: Session = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    finally:
        db.close()
