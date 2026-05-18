"""Safe database connectivity check for the configured SQLAlchemy engine."""

from sqlalchemy import text

from app.db.database import engine


def main() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("Database connection successful")


if __name__ == "__main__":
    main()
