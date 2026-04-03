from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComparisonSnapshot(Base):
    """Feature vector for a given date, used for regime matching."""

    __tablename__ = "comparison_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observation_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)

    spread_10y2y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spread_10y3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spread_10y2y_1m_delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hy_spread: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hy_spread_zscore_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpi_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fedfunds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fedfunds_3m_delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
