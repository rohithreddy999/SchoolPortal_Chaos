import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Load variables from .env if present (local dev convenience).
# override=True so the .env value wins over a stale terminal env var.
load_dotenv(override=True)

def _database_url() -> str:
    # Example: postgresql+psycopg://user:password@localhost:5432/school_fee
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Example: postgresql+psycopg://user:password@localhost:5432/school_fee"
        )
    # If user sets "postgresql://", SQLAlchemy defaults to psycopg2; normalize to psycopg.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


database_url = _database_url()
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _) -> None:
    if engine.dialect.name != "sqlite":
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
