from sqlalchemy import Engine, inspect, text

from app.db.models import Base

COLUMN_PATCHES: tuple[tuple[str, str, str], ...] = (
    ("portfolios", "base_currency", "VARCHAR(3) NOT NULL DEFAULT 'USD'"),
    ("rebalance_records", "base_currency", "VARCHAR(3) NOT NULL DEFAULT 'USD'"),
)


def _apply_column_patches(engine: Engine) -> None:
    inspector = inspect(engine)
    dialect = engine.dialect.name
    with engine.begin() as connection:
        for table_name, column_name, column_def in COLUMN_PATCHES:
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            if column_name in existing:
                continue
            if dialect == "postgresql":
                statement = (
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN IF NOT EXISTS {column_name} {column_def}"
                )
            else:
                statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
            connection.execute(text(statement))


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    _apply_column_patches(engine)
