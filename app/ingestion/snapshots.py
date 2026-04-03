"""
Compute and upsert feature vectors into comparison_snapshots.
Called after ingestion so the comparison table stays current.
"""

import json
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.transforms.rolling import rolling_delta, rolling_zscore, cpi_yoy
from app.transforms.spreads import compute_yield_curve_spreads, compute_hy_spread

log = logging.getLogger(__name__)

_REQUIRED_IDS = ["T10Y2Y", "T10Y3M", "BAMLH0A0HYM2", "CPIAUCSL", "FEDFUNDS"]


async def _load_series(db: AsyncSession) -> pd.DataFrame:
    """Load all required series from series_points into a date-indexed DataFrame."""
    rows = await db.execute(
        text("""
            SELECT fred_id, observation_date, value
            FROM series_points
            WHERE fred_id = ANY(:ids)
            ORDER BY observation_date
        """),
        {"ids": _REQUIRED_IDS},
    )
    records = rows.fetchall()
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records, columns=["fred_id", "date", "value"])
    pivoted = df.pivot(index="date", columns="fred_id", values="value")
    pivoted.index = pd.to_datetime(pivoted.index)
    return pivoted


def _build_snapshot_df(raw: pd.DataFrame) -> pd.DataFrame:
    """
    From raw series DataFrame compute all feature vector columns.
    Returns a monthly-frequency DataFrame aligned on month-end dates.
    """
    # --- Daily-resolution derived metrics (computed before downsampling) ---
    spreads = compute_yield_curve_spreads({col: raw[col] for col in raw.columns if col in raw.columns})
    s10y2y = spreads["spread_10y2y"] if "spread_10y2y" in spreads.columns else pd.Series(dtype=float)
    s10y3m = spreads["spread_10y3m"] if "spread_10y3m" in spreads.columns else pd.Series(dtype=float)

    hy = compute_hy_spread({"BAMLH0A0HYM2": raw["BAMLH0A0HYM2"]}) if "BAMLH0A0HYM2" in raw.columns else pd.Series(dtype=float)

    # Rolling metrics on daily series
    s10y2y_delta = rolling_delta(s10y2y.rename("spread_10y2y"), periods=21)
    hy_zscore = rolling_zscore(hy.rename("hy_spread"), window=252)

    daily = pd.DataFrame({
        "spread_10y2y": s10y2y,
        "spread_10y3m": s10y3m,
        "spread_10y2y_1m_delta": s10y2y_delta,
        "hy_spread": hy,
        "hy_spread_zscore_1y": hy_zscore,
    })

    # Resample daily → month-end (last value of each month)
    daily_monthly = daily.resample("ME").last()

    # --- Monthly-frequency series ---
    # dropna() gives a dense monthly series so pct_change(12) = 12 months back, not 12 days
    cpi_dense = raw["CPIAUCSL"].dropna() if "CPIAUCSL" in raw.columns else pd.Series(dtype=float)
    fedfunds_dense = raw["FEDFUNDS"].dropna() if "FEDFUNDS" in raw.columns else pd.Series(dtype=float)

    cpi_yoy_series = cpi_yoy(cpi_dense.rename("CPIAUCSL"))

    # Both series have first-of-month dates; resample to month-end to align with daily_monthly
    monthly = pd.DataFrame({
        "cpi_yoy": cpi_yoy_series,
        "fedfunds": fedfunds_dense,
    }).resample("ME").last()

    # Merge daily (resampled) with monthly
    merged = daily_monthly.join(monthly, how="outer").sort_index()
    merged = merged.ffill(limit=3)  # forward-fill up to 3 months for monthly series alignment

    # Drop rows where all key features are null
    key_cols = ["spread_10y2y", "hy_spread", "cpi_yoy"]
    merged = merged.dropna(subset=key_cols, how="all")

    return merged


async def compute_and_upsert_snapshots() -> None:
    """Entry point: load series, compute feature vectors, upsert into comparison_snapshots."""
    async with AsyncSessionLocal() as db:
        raw = await _load_series(db)
        if raw.empty:
            log.warning("No series data found — skipping snapshot computation")
            return

        df = _build_snapshot_df(raw)
        if df.empty:
            log.warning("Snapshot DataFrame is empty after transforms — nothing to upsert")
            return

        now = datetime.now(timezone.utc)
        rows = []
        for obs_date, row in df.iterrows():
            def _val(col):
                v = row.get(col)
                return round(float(v), 4) if v is not None and pd.notna(v) else None

            feature_vector = {
                "spread_10y2y": _val("spread_10y2y"),
                "spread_10y3m": _val("spread_10y3m"),
                "spread_10y2y_1m_delta": _val("spread_10y2y_1m_delta"),
                "hy_spread": _val("hy_spread"),
                "hy_spread_zscore_1y": _val("hy_spread_zscore_1y"),
                "cpi_yoy": _val("cpi_yoy"),
                "fedfunds": _val("fedfunds"),
            }

            rows.append({
                "observation_date": obs_date.date() if hasattr(obs_date, "date") else obs_date,
                "spread_10y2y": _val("spread_10y2y"),
                "spread_10y3m": _val("spread_10y3m"),
                "spread_10y2y_1m_delta": _val("spread_10y2y_1m_delta"),
                "hy_spread": _val("hy_spread"),
                "hy_spread_zscore_1y": _val("hy_spread_zscore_1y"),
                "cpi_yoy": _val("cpi_yoy"),
                "fedfunds": _val("fedfunds"),
                "fedfunds_3m_delta": None,  # not computed here; reserved for future use
                "feature_vector": json.dumps(feature_vector),
                "computed_at": now,
            })

        await db.execute(
            text("""
                INSERT INTO comparison_snapshots
                    (observation_date, spread_10y2y, spread_10y3m, spread_10y2y_1m_delta,
                     hy_spread, hy_spread_zscore_1y, cpi_yoy, fedfunds, fedfunds_3m_delta,
                     feature_vector, computed_at)
                VALUES
                    (:observation_date, :spread_10y2y, :spread_10y3m, :spread_10y2y_1m_delta,
                     :hy_spread, :hy_spread_zscore_1y, :cpi_yoy, :fedfunds, :fedfunds_3m_delta,
                     :feature_vector, :computed_at)
                ON CONFLICT (observation_date) DO UPDATE SET
                    spread_10y2y          = EXCLUDED.spread_10y2y,
                    spread_10y3m          = EXCLUDED.spread_10y3m,
                    spread_10y2y_1m_delta = EXCLUDED.spread_10y2y_1m_delta,
                    hy_spread             = EXCLUDED.hy_spread,
                    hy_spread_zscore_1y   = EXCLUDED.hy_spread_zscore_1y,
                    cpi_yoy               = EXCLUDED.cpi_yoy,
                    fedfunds              = EXCLUDED.fedfunds,
                    fedfunds_3m_delta     = EXCLUDED.fedfunds_3m_delta,
                    feature_vector        = EXCLUDED.feature_vector,
                    computed_at           = EXCLUDED.computed_at
            """),
            rows,
        )
        await db.commit()
        log.info("Upserted %d comparison snapshots", len(rows))
