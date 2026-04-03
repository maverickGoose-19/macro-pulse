from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SeriesCatalog(Base):
    """Metadata for each base FRED series."""

    __tablename__ = "series_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fred_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    units: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    typical_lag_days: Mapped[int] = mapped_column(Integer, default=1)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    last_ingest_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class SeriesPoint(Base):
    """Normalized time-series observations with full timing provenance."""

    __tablename__ = "series_points"
    __table_args__ = (UniqueConstraint("fred_id", "observation_date", name="uq_series_point"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fred_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    release_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ingest_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    is_revised: Mapped[bool] = mapped_column(Boolean, default=False)
