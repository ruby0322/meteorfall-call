import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    initial_cash_usd: Mapped[float] = mapped_column(Float, default=10000.0)
    prior_value_usd: Mapped[float] = mapped_column(Float, default=10000.0)
    rates_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    currency_code: Mapped[str] = mapped_column(String(3))
    quantity: Mapped[float] = mapped_column(Float)
    weight_percent: Mapped[float] = mapped_column(Float)
    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
