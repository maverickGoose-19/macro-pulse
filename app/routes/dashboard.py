from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.panel_copy import GLOSSARY, PANEL_COPY, curve_state_label, credit_state_label, inflation_state_label
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    r = await db.execute(text("""
        SELECT
            (SELECT value FROM series_points WHERE fred_id='T10Y2Y' AND value IS NOT NULL ORDER BY observation_date DESC LIMIT 1) AS spread_10y2y,
            (SELECT value FROM series_points WHERE fred_id='T10Y3M' AND value IS NOT NULL ORDER BY observation_date DESC LIMIT 1) AS spread_10y3m,
            (SELECT observation_date FROM series_points WHERE fred_id='T10Y2Y' AND value IS NOT NULL ORDER BY observation_date DESC LIMIT 1) AS as_of
    """))
    curve = r.fetchone()

    r = await db.execute(text("""
        SELECT value AS hy_spread, observation_date
        FROM series_points
        WHERE fred_id='BAMLH0A0HYM2' AND value IS NOT NULL
        ORDER BY observation_date DESC LIMIT 1
    """))
    credit = r.fetchone()

    r = await db.execute(text("""
        SELECT value, observation_date FROM series_points
        WHERE fred_id='CPIAUCSL' AND value IS NOT NULL
        ORDER BY observation_date DESC LIMIT 13
    """))
    cpi_data = r.fetchall()

    r = await db.execute(text(
        "SELECT summary_text FROM summary_runs ORDER BY generated_at DESC LIMIT 1"
    ))
    summary = r.fetchone()

    r = await db.execute(text("""
        SELECT hy_spread_zscore_1y FROM comparison_snapshots
        WHERE hy_spread_zscore_1y IS NOT NULL
        ORDER BY observation_date DESC LIMIT 1
    """))
    hy_z_row = r.fetchone()
    hy_z = hy_z_row.hy_spread_zscore_1y if hy_z_row else 0.0

    cpi_yoy = None
    if len(cpi_data) >= 13:
        cpi_yoy = round((cpi_data[0].value / cpi_data[12].value - 1) * 100, 2)

    # State labels
    spread_10y2y = curve.spread_10y2y if curve and curve.spread_10y2y else 0.0
    spread_10y3m = curve.spread_10y3m if curve and curve.spread_10y3m else 0.0
    hy_spread = credit.hy_spread if credit and credit.hy_spread else 0.0

    c_label, c_color = curve_state_label(spread_10y2y, spread_10y3m)
    cr_label, cr_color = credit_state_label(hy_z)
    inf_label, inf_color = inflation_state_label(cpi_yoy or 0.0)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "as_of_date": curve.as_of.isoformat() if curve and curve.as_of else date.today().isoformat(),
            "spread_10y2y": round(spread_10y2y, 2),
            "spread_10y3m": round(spread_10y3m, 2),
            "hy_spread": round(hy_spread, 2),
            "cpi_yoy": cpi_yoy,
            "curve_state_label": c_label,
            "curve_state_color": c_color,
            "credit_state_label": cr_label,
            "credit_state_color": cr_color,
            "inflation_state_label": inf_label,
            "inflation_state_color": inf_color,
            "summary_text": summary.summary_text if summary else "Summary not yet available. Run ingestion first.",
            "hy_z": hy_z,
            "copy": PANEL_COPY,
            "glossary": GLOSSARY,
        },
    )
