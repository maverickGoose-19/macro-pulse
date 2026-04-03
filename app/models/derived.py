from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DerivedMetric(Base):
    """Spreads, deltas, rolling windows, z-scores, and composites."""

    __tablename__ = "derived_metrics"
    __table_args__ = (UniqueConstraint("metric_id", "observation_date", name="uq_derived_metric"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_series: Mapped[str] = mapped_column(String(256), nullable=False)
    window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
