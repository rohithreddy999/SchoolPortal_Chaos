from __future__ import annotations

from app.db.migrations import apply_migrations
from app.db.session import engine


def init_db() -> None:
    apply_migrations(engine)


if __name__ == "__main__":
    init_db()
    print("Database migrations applied.")
