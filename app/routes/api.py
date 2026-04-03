"""
JSON API routes — consumed by HTMX panel updates and chart JS.
All responses use the consistent envelope: {data: ..., meta: {...}}.
"""

from datetime import date, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.comparison.engine import score_historical_matches
from app.comparison.features import FeatureVector
from app.content.panel_copy import GLOSSARY, PANEL_COPY
from app.database import get_db
from app.ingestion.catalog import SERIES_BY_ID, SERIES_CATALOG

router = APIRouter(prefix="/api")


def _meta(sources: list[str], freshness: dict) -> dict:
    return {
        "as_of": date.today().isoformat(),
        "sources": sources,
        "freshness": freshness,
    }


async def _fetch_series_df(
    db: AsyncSession, fred_ids: list[str], days: int = 730
) -> pd.DataFrame:
    """Pull series_points rows into a date-indexed DataFrame."""
    cutoff = date.today() - timedelta(days=days)
    rows = await db.execute(
        text("""
            SELECT fred_id, observation_date, value
            FROM series_points
            WHERE fred_id = ANY(:ids) AND observation_date >= :cutoff
            ORDER BY observation_date
        """),
        {"ids": fred_ids, "cutoff": cutoff},
    )
    records = rows.fetchall()
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records, columns=["fred_id", "date", "value"])
    return df.pivot(index="date", columns="fred_id", values="value")


async def _freshness(db: AsyncSession, fred_ids: list[str]) -> dict:
    rows = await db.execute(
        text("""
            SELECT sp.fred_id,
                   MAX(sp.observation_date) AS last_observation,
                   sc.typical_lag_days
            FROM series_points sp
            JOIN series_catalog sc ON sc.fred_id = sp.fred_id
            WHERE sp.fred_id = ANY(:ids)
            GROUP BY sp.fred_id, sc.typical_lag_days
        """),
        {"ids": fred_ids},
    )
    result = {}
    for row in rows.fetchall():
        lag = (date.today() - row.last_observation).days
        result[row.fred_id] = {
            "last_observation": row.last_observation.isoformat(),
            "lag_days": lag,
            "typical_lag_days": row.typical_lag_days,
            "is_stale": lag > row.typical_lag_days + 2,
        }
    return result


@router.get("/curve")
async def get_curve(db: AsyncSession = Depends(get_db)):
    ids = ["T10Y2Y", "T10Y3M"]
    df = await _fetch_series_df(db, ids, days=730)
    fresh = await _freshness(db, ids)

    if df.empty:
        return {"data": [], "meta": _meta(ids, fresh)}

    records = []
    for obs_date, row in df.iterrows():
        records.append({
            "date": obs_date.isoformat() if hasattr(obs_date, "isoformat") else str(obs_date),
            "spread_10y2y": round(row.get("T10Y2Y", None), 3) if pd.notna(row.get("T10Y2Y")) else None,
            "spread_10y3m": round(row.get("T10Y3M", None), 3) if pd.notna(row.get("T10Y3M")) else None,
        })

    return {"data": records, "meta": _meta(ids, fresh)}


@router.get("/credit")
async def get_credit(db: AsyncSession = Depends(get_db)):
    ids = ["BAMLH0A0HYM2"]
    df = await _fetch_series_df(db, ids, days=730)
    fresh = await _freshness(db, ids)

    if df.empty:
        return {"data": [], "meta": _meta(ids, fresh)}

    series = df["BAMLH0A0HYM2"].dropna()
    ma = series.rolling(252, min_periods=126).mean()

    records = [
        {
            "date": str(d),
            "hy_spread": round(v, 3),
            "hy_spread_ma252": round(ma.get(d, float("nan")), 3) if pd.notna(ma.get(d)) else None,
        }
        for d, v in series.items()
    ]
    return {"data": records, "meta": _meta(ids, fresh)}


@router.get("/inflation")
async def get_inflation(db: AsyncSession = Depends(get_db)):
    ids = ["CPIAUCSL", "CPILFESL", "FEDFUNDS"]
    df = await _fetch_series_df(db, ids, days=365 * 7)
    fresh = await _freshness(db, ids)

    if df.empty:
        return {"data": [], "meta": _meta(ids, fresh)}

    cpi_yoy = df["CPIAUCSL"].pct_change(12).mul(100) if "CPIAUCSL" in df.columns else pd.Series(dtype=float)
    core_yoy = df["CPILFESL"].pct_change(12).mul(100) if "CPILFESL" in df.columns else pd.Series(dtype=float)
    fedfunds = df["FEDFUNDS"] if "FEDFUNDS" in df.columns else pd.Series(dtype=float)

    idx = cpi_yoy.dropna().index.union(fedfunds.dropna().index)
    cutoff = date.today().replace(year=date.today().year - 5)
    idx = idx[idx >= pd.Timestamp(cutoff)]

    records = []
    for d in idx:
        records.append({
            "date": str(d.date() if hasattr(d, "date") else d),
            "cpi_yoy": round(cpi_yoy.get(d, float("nan")), 2) if pd.notna(cpi_yoy.get(d, float("nan"))) else None,
            "core_cpi_yoy": round(core_yoy.get(d, float("nan")), 2) if pd.notna(core_yoy.get(d, float("nan"))) else None,
            "fedfunds": round(fedfunds.get(d, float("nan")), 2) if pd.notna(fedfunds.get(d, float("nan"))) else None,
        })

    return {"data": records, "meta": _meta(ids, fresh)}


@router.get("/comparison")
async def get_comparison(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("""
            SELECT observation_date, spread_10y2y, spread_10y3m, spread_10y2y_1m_delta,
                   hy_spread, hy_spread_zscore_1y, cpi_yoy, fedfunds, feature_vector
            FROM comparison_snapshots
            ORDER BY observation_date DESC
            LIMIT 1825
        """)
    )
    records = rows.fetchall()

    if not records:
        return {"data": [], "meta": _meta([], {})}

    current_row = records[0]
    current = FeatureVector(
        observation_date=current_row.observation_date,
        spread_10y2y=current_row.spread_10y2y,
        spread_10y3m=current_row.spread_10y3m,
        spread_10y2y_1m_delta=current_row.spread_10y2y_1m_delta,
        hy_spread=current_row.hy_spread,
        hy_spread_zscore_1y=current_row.hy_spread_zscore_1y,
        cpi_yoy=current_row.cpi_yoy,
        fedfunds=current_row.fedfunds,
    )
    historical = [
        FeatureVector(
            observation_date=r.observation_date,
            spread_10y2y=r.spread_10y2y,
            spread_10y3m=r.spread_10y3m,
            spread_10y2y_1m_delta=r.spread_10y2y_1m_delta,
            hy_spread=r.hy_spread,
            hy_spread_zscore_1y=r.hy_spread_zscore_1y,
            cpi_yoy=r.cpi_yoy,
            fedfunds=r.fedfunds,
        )
        for r in records[1:]
    ]

    matches = score_historical_matches(current, historical, top_n=5)
    for m in matches:
        if isinstance(m["date"], date):
            m["date"] = m["date"].isoformat()

    return {
        "data": {
            "current_date": current_row.observation_date.isoformat(),
            "matches": matches,
        },
        "meta": _meta(["comparison_snapshots"], {}),
    }


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT summary_text, snapshot_date, generated_at FROM summary_runs ORDER BY generated_at DESC LIMIT 1")
    )
    result = row.fetchone()
    if not result:
        return {"data": None, "meta": _meta([], {})}
    return {
        "data": {
            "text": result.summary_text,
            "snapshot_date": result.snapshot_date.isoformat(),
            "generated_at": result.generated_at.isoformat(),
        },
        "meta": _meta([], {}),
    }


@router.get("/freshness")
async def get_freshness(db: AsyncSession = Depends(get_db)):
    ids = [s.fred_id for s in SERIES_CATALOG]
    fresh = await _freshness(db, ids)
    return {"data": fresh, "meta": _meta(ids, {})}


@router.get("/series/{fred_id}")
async def get_series(fred_id: str, db: AsyncSession = Depends(get_db)):
    if fred_id not in SERIES_BY_ID:
        raise HTTPException(status_code=404, detail=f"Series {fred_id} not in catalog")
    df = await _fetch_series_df(db, [fred_id], days=365 * 10)
    fresh = await _freshness(db, [fred_id])
    if df.empty or fred_id not in df.columns:
        return {"data": [], "meta": _meta([fred_id], fresh)}
    series = df[fred_id].dropna()
    records = [{"date": str(d), "value": round(v, 4)} for d, v in series.items()]
    return {"data": records, "meta": _meta([fred_id], fresh)}


@router.get("/explanations")
async def get_explanations():
    return {"data": {"panels": PANEL_COPY, "glossary": GLOSSARY}, "meta": {}}


@router.get("/explanations/{panel}")
async def get_panel_explanation(panel: str):
    if panel not in PANEL_COPY:
        raise HTTPException(status_code=404, detail=f"Panel '{panel}' not found")
    return {"data": PANEL_COPY[panel], "meta": {}}
