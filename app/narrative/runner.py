"""
Generates a narrative summary from the latest comparison_snapshots data
and upserts it into summary_runs.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.narrative.generator import TEMPLATE_VERSION, NarrativeInputs, generate_summary
from app.comparison.engine import score_historical_matches
from app.comparison.features import FeatureVector

log = logging.getLogger(__name__)


async def generate_and_save_summary() -> None:
    async with AsyncSessionLocal() as db:
        # Load recent snapshots (current + historical for matching)
        rows = await db.execute(
            text("""
                SELECT observation_date, spread_10y2y, spread_10y3m, spread_10y2y_1m_delta,
                       hy_spread, hy_spread_zscore_1y, cpi_yoy, fedfunds
                FROM comparison_snapshots
                ORDER BY observation_date DESC
                LIMIT 1825
            """)
        )
        records = rows.fetchall()

        if not records:
            log.warning("No comparison snapshots found — skipping summary generation")
            return

        current = records[0]
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
        current_fv = FeatureVector(
            observation_date=current.observation_date,
            spread_10y2y=current.spread_10y2y,
            spread_10y3m=current.spread_10y3m,
            spread_10y2y_1m_delta=current.spread_10y2y_1m_delta,
            hy_spread=current.hy_spread,
            hy_spread_zscore_1y=current.hy_spread_zscore_1y,
            cpi_yoy=current.cpi_yoy,
            fedfunds=current.fedfunds,
        )
        top_matches = score_historical_matches(current_fv, historical, top_n=3)
        for m in top_matches:
            if hasattr(m["date"], "isoformat"):
                m["date"] = m["date"].isoformat()

        inputs = NarrativeInputs(
            snapshot_date=current.observation_date,
            spread_10y2y=current.spread_10y2y or 0.0,
            spread_10y2y_1m_delta=current.spread_10y2y_1m_delta or 0.0,
            spread_10y3m=current.spread_10y3m or 0.0,
            hy_spread=current.hy_spread or 0.0,
            hy_spread_zscore_1y=current.hy_spread_zscore_1y or 0.0,
            cpi_yoy=current.cpi_yoy or 0.0,
            fedfunds=current.fedfunds or 0.0,
            top_matches=top_matches,
            freshness_notes=[],
        )

        summary_text = generate_summary(inputs)

        data_snapshot = {
            "spread_10y2y": current.spread_10y2y,
            "spread_10y3m": current.spread_10y3m,
            "spread_10y2y_1m_delta": current.spread_10y2y_1m_delta,
            "hy_spread": current.hy_spread,
            "hy_spread_zscore_1y": current.hy_spread_zscore_1y,
            "cpi_yoy": current.cpi_yoy,
            "fedfunds": current.fedfunds,
        }

        await db.execute(
            text("""
                INSERT INTO summary_runs (snapshot_date, summary_text, data_snapshot, template_version, generated_at)
                VALUES (:snapshot_date, :summary_text, :data_snapshot, :template_version, :generated_at)
            """),
            {
                "snapshot_date": current.observation_date,
                "summary_text": summary_text,
                "data_snapshot": json.dumps(data_snapshot),
                "template_version": TEMPLATE_VERSION,
                "generated_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()
        log.info("Summary saved for %s", current.observation_date)
