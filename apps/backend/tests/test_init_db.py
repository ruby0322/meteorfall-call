from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.db.init_db import init_database


def make_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def create_legacy_schema(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE portfolios (
                    id VARCHAR(36) PRIMARY KEY,
                    initial_cash_usd FLOAT NOT NULL,
                    prior_value_usd FLOAT NOT NULL,
                    rates_date VARCHAR(10),
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE rebalance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id VARCHAR(36) NOT NULL,
                    effective_rates_date VARCHAR(10) NOT NULL,
                    total_value_usd FLOAT NOT NULL,
                    holdings_json TEXT NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )


def test_init_database_adds_base_currency_to_legacy_tables() -> None:
    engine = make_engine()
    create_legacy_schema(engine)

    init_database(engine)

    inspector = inspect(engine)
    portfolio_columns = {column["name"] for column in inspector.get_columns("portfolios")}
    rebalance_columns = {column["name"] for column in inspector.get_columns("rebalance_records")}
    assert "base_currency" in portfolio_columns
    assert "base_currency" in rebalance_columns


def test_init_database_column_patch_is_idempotent() -> None:
    engine = make_engine()
    create_legacy_schema(engine)

    init_database(engine)
    init_database(engine)

    inspector = inspect(engine)
    portfolio_columns = [column["name"] for column in inspector.get_columns("portfolios")]
    assert portfolio_columns.count("base_currency") == 1
