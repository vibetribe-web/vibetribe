"""Development-only helper to create database tables from SQLAlchemy models.

For production, prefer Alembic migrations. This script is useful for quickly
bootstrapping a development Supabase PostgreSQL database from the current models.
"""

from app.db.database import engine
from app.db.base import Base
import app.models  # noqa: F401  Import all models so metadata is registered.


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
