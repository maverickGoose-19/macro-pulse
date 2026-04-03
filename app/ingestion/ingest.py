"""
Core ingestion logic — upsert FRED series data into series_points.
Called by scripts/ingest.py (Render Cron Job) and the backfill script.
"""

import logging
from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.ingestion.catalog import SERIES_CATALOG, SeriesDef
from app.ingestion.fred_client import fetch_series

log = logging.getLogger(__name__)


async def _upsert_series(db: AsyncSession, fred_id: str, data: pd.Series) -> int:
    """Upsert observations into series_points. Returns number of rows upserted."""
    rows = []
    for obs_date, value in data.items():
        if pd.isna(value):
            continue
        rows.append(
            {
                "fred_id": fred_id,
                "observation_date": obs_date.date() if isinstance(obs_date, datetime) else obs_date,
                "value": float(value),
                "ingest_timestamp": datetime.now(timezone.utc),
            }
        )

    if not rows:
        return 0

    await db.execute(
        text("""
            INSERT INTO series_points (fred_id, observation_date, value, ingest_timestamp, is_revised)
            VALUES (:fred_id, :observation_date, :value, :ingest_timestamp, false)
            ON CONFLICT (fred_id, observation_date)
            DO UPDATE SET
                value = EXCLUDED.value,
                ingest_timestamp = EXCLUDED.ingest_timestamp,
                is_revised = (series_points.value IS DISTINCT FROM EXCLUDED.value)
        """),
        rows,
    )
    return len(rows)


async def _update_catalog_ingest_time(db: AsyncSession, fred_id: str) -> None:
    await db.execute(
        text("UPDATE series_catalog SET last_ingest_at = now() WHERE fred_id = :fred_id"),
        {"fred_id": fred_id},
    )


async def ensure_catalog(db: AsyncSession) -> None:
    """Upsert series definitions into series_catalog from the static catalog."""
    for s in SERIES_CATALOG:
        await db.execute(
            text("""
                INSERT INTO series_catalog
                    (fred_id, name, units, frequency, category, typical_lag_days, source_url)
                VALUES
                    (:fred_id, :name, :units, :frequency, :category, :typical_lag_days, :source_url)
                ON CONFLICT (fred_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    units = EXCLUDED.units,
                    frequency = EXCLUDED.frequency,
                    category = EXCLUDED.category,
                    typical_lag_days = EXCLUDED.typical_lag_days,
                    source_url = EXCLUDED.source_url
            """),
            {
                "fred_id": s.fred_id,
                "name": s.name,
                "units": s.units,
                "frequency": s.frequency,
                "category": s.category,
                "typical_lag_days": s.typical_lag_days,
                "source_url": s.source_url,
            },
        )
    await db.commit()


async def ingest_all_series(start_date: str = "1990-01-01") -> None:
    """Fetch and upsert all series from the catalog. Entry point for cron job."""
    async with AsyncSessionLocal() as db:
        await ensure_catalog(db)
        for series_def in SERIES_CATALOG:
            try:
                data = await fetch_series(series_def.fred_id, start_date=start_date)
                n = await _upsert_series(db, series_def.fred_id, data)
                await _update_catalog_ingest_time(db, series_def.fred_id)
                await db.commit()
                log.info("Ingested %d points for %s", n, series_def.fred_id)
            except Exception as e:
                log.error("Failed to ingest %s: %s", series_def.fred_id, e)
                await db.rollback()
