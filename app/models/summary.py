from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SummaryRun(Base):
    """Generated descriptive summary tied to a specific data snapshot."""

    __tablename__ = "summary_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    data_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    template_version: Mapped[str] = mapped_column(String(16), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
