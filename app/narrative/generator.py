from __future__ import annotations

"""
Rule-based descriptive narrative generator.

Language rules:
  ALLOWED  — describe changes, levels, divergences, historical comparisons
  FORBIDDEN — recession calls, direction predictions, investment advice
"""

from dataclasses import dataclass
from datetime import date

TEMPLATE_VERSION = "1.0"


@dataclass
class NarrativeInputs:
    snapshot_date: date
    spread_10y2y: float
    spread_10y2y_1m_delta: float
    spread_10y3m: float
    hy_spread: float
    hy_spread_zscore_1y: float
    cpi_yoy: float
    fedfunds: float
    top_matches: list[dict]
    freshness_notes: list[str]


def generate_summary(inputs: NarrativeInputs) -> str:
    parts: list[str] = []

    # — Yield curve
    direction = "widened" if inputs.spread_10y2y_1m_delta > 0 else "narrowed"
    bps = abs(round(inputs.spread_10y2y_1m_delta * 100))
    curve_sign = "positive" if inputs.spread_10y2y >= 0 else "negative"
    parts.append(
        f"The 10Y–2Y spread {direction} {bps} bps over the last month "
        f"to {round(inputs.spread_10y2y, 2)}%, a {curve_sign} reading."
    )

    # — Credit stress
    z = inputs.hy_spread_zscore_1y
    if z > 2.0:
        credit_desc = "significantly elevated relative to the past year"
    elif z > 1.0:
        credit_desc = "elevated relative to the past year"
    elif z < -1.0:
        credit_desc = "compressed below recent norms"
    else:
        credit_desc = "near recent norms"

    parts.append(
        f"High-yield spreads are {credit_desc} at {round(inputs.hy_spread, 2)}%."
    )

    # — Divergence between rates and credit
    curve_inverted = inputs.spread_10y2y < 0
    credit_stressed = z > 1.0

    if curve_inverted and not credit_stressed:
        parts.append(
            "Credit conditions are calmer than rate volatility alone would suggest."
        )
    elif credit_stressed and not curve_inverted:
        parts.append(
            "Credit stress is elevated while the curve has not inverted."
        )
    elif curve_inverted and credit_stressed:
        parts.append(
            "Both curve inversion and elevated credit spreads are present simultaneously."
        )

    # — Inflation context
    if inputs.cpi_yoy > 5.0:
        parts.append(
            f"Headline CPI is running at {round(inputs.cpi_yoy, 1)}% year-over-year, well above the Fed's 2% target."
        )
    elif inputs.cpi_yoy > 3.0:
        parts.append(
            f"Headline CPI is at {round(inputs.cpi_yoy, 1)}% year-over-year, above the Fed's 2% target."
        )
    elif inputs.cpi_yoy < 1.5:
        parts.append(
            f"Headline CPI is at {round(inputs.cpi_yoy, 1)}% year-over-year, below the Fed's 2% target."
        )

    # — Historical comparison
    if inputs.top_matches:
        best = inputs.top_matches[0]
        match_date = best["date"]
        if isinstance(match_date, str):
            match_date = date.fromisoformat(match_date)
        parts.append(
            f"The current configuration most closely resembles conditions around "
            f"{match_date.strftime('%B %Y')} "
            f"(similarity score: {best['similarity_score']})."
        )

    # — Freshness notes
    for note in inputs.freshness_notes:
        parts.append(note)

    return " ".join(parts)
