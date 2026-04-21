from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routers import admin as admin_router
from app.api.routers import auth as auth_router
from app.api.routers import parent as parent_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_security()
    init_db()
    yield


app = FastAPI(title="School Fee Portal", lifespan=lifespan)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(parent_router.router)


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    index_file = static_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend not found")
    return FileResponse(index_file)


@app.get("/health")
def health() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "ok", "database": "ok"}


