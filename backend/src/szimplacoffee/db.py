from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DB_PATH


DATABASE_URL = f"sqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _apply_lightweight_migrations() -> None:
    """Run idempotent ALTER TABLE migrations at startup.

    Kept here (rather than bootstrap.py) to avoid circular imports:
    db.py must not import from bootstrap.py at module level.
    bootstrap.py re-exports this function for backward compatibility.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    product_columns = {col["name"] for col in inspector.get_columns("products")}
    override_columns = (
        {col["name"] for col in inspector.get_columns("product_metadata_overrides")}
        if inspector.has_table("product_metadata_overrides")
        else set()
    )
    with engine.begin() as connection:
        _add_col_if_missing = lambda tbl, col, ddl: connection.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {ddl}")) if col not in (product_columns if tbl == "products" else override_columns) else None  # noqa: E731

        for col, ddl in [
            ("image_url", "image_url VARCHAR(1000) NOT NULL DEFAULT ''"),
            ("origin_country", "origin_country VARCHAR(128)"),
            ("origin_country_confidence", "origin_country_confidence FLOAT NOT NULL DEFAULT 0"),
            ("origin_country_source", "origin_country_source VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
            ("origin_region", "origin_region VARCHAR(128)"),
            ("process_family", "process_family VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
            ("process_family_confidence", "process_family_confidence FLOAT NOT NULL DEFAULT 0"),
            ("process_family_source", "process_family_source VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
            ("roast_level", "roast_level VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
            ("roast_level_confidence", "roast_level_confidence FLOAT NOT NULL DEFAULT 0"),
            ("roast_level_source", "roast_level_source VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
            ("metadata_confidence", "metadata_confidence FLOAT NOT NULL DEFAULT 0"),
            ("metadata_source", "metadata_source VARCHAR(32) NOT NULL DEFAULT 'unknown'"),
        ]:
            if col not in product_columns:
                connection.execute(text(f"ALTER TABLE products ADD COLUMN {ddl}"))

        if override_columns:
            for col, ddl in [
                ("origin_country_confidence", "origin_country_confidence FLOAT"),
                ("origin_country_source", "origin_country_source VARCHAR(32)"),
                ("process_family_confidence", "process_family_confidence FLOAT"),
                ("process_family_source", "process_family_source VARCHAR(32)"),
                ("roast_level_confidence", "roast_level_confidence FLOAT"),
                ("roast_level_source", "roast_level_source VARCHAR(32)"),
            ]:
                if col not in override_columns:
                    connection.execute(text(f"ALTER TABLE product_metadata_overrides ADD COLUMN {ddl}"))


def ensure_schema() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
    _apply_lightweight_migrations()


ensure_schema()

