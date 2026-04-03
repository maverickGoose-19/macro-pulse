from datetime import date

from app.narrative.generator import NarrativeInputs, generate_summary

FORBIDDEN = [
    "recession", "imminent", "will pivot", "bullish", "bearish",
    "investors should", "position for", "about to", "is likely",
    "will happen", "predicts", "forecast",
]


def _inputs(**kwargs) -> NarrativeInputs:
    defaults = dict(
        snapshot_date=date(2024, 1, 15),
        spread_10y2y=-0.3,
        spread_10y2y_1m_delta=0.15,
        spread_10y3m=0.1,
        hy_spread=4.5,
        hy_spread_zscore_1y=1.2,
        cpi_yoy=3.1,
        fedfunds=5.33,
        top_matches=[{"date": date(2007, 8, 1), "similarity_score": 0.93}],
        freshness_notes=[],
    )
    defaults.update(kwargs)
    return NarrativeInputs(**defaults)


def test_no_forbidden_language():
    text = generate_summary(_inputs()).lower()
    for phrase in FORBIDDEN:
        assert phrase not in text, f"Forbidden phrase found: '{phrase}'"


def test_summary_is_nonempty_string():
    result = generate_summary(_inputs())
    assert isinstance(result, str) and len(result) > 20


def test_widening_described_correctly():
    result = generate_summary(_inputs(spread_10y2y_1m_delta=0.20))
    assert "widened" in result


def test_narrowing_described_correctly():
    result = generate_summary(_inputs(spread_10y2y_1m_delta=-0.10))
    assert "narrowed" in result


def test_high_inflation_mentioned():
    result = generate_summary(_inputs(cpi_yoy=6.5))
    assert "6.5%" in result


def test_divergence_credit_calm_curve_inverted():
    result = generate_summary(_inputs(spread_10y2y=-0.4, hy_spread_zscore_1y=0.2))
    assert "calmer" in result.lower()


def test_historical_match_date_in_summary():
    result = generate_summary(_inputs())
    assert "August 2007" in result
