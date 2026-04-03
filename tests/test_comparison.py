from datetime import date

import pytest

from app.comparison.engine import cosine_similarity, score_historical_matches
from app.comparison.features import FeatureVector


def _vec(d: str, **kwargs) -> FeatureVector:
    defaults = dict(
        spread_10y2y=0.0, spread_10y3m=0.0, spread_10y2y_1m_delta=0.0,
        hy_spread=0.0, hy_spread_zscore_1y=0.0, cpi_yoy=0.0, fedfunds=0.0,
    )
    defaults.update(kwargs)
    return FeatureVector(observation_date=date.fromisoformat(d), **defaults)


def test_identical_vectors_score_1():
    v = _vec("2020-01-01", spread_10y2y=-0.5, hy_spread=5.0)
    assert cosine_similarity(v.to_weighted_array(), v.to_weighted_array()) == pytest.approx(1.0)


def test_opposite_vectors_score_negative():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(-1.0)


def test_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_matches_exclude_recent_window():
    current = _vec("2024-01-01", spread_10y2y=-0.5)
    recent = _vec("2023-06-15", spread_10y2y=-0.48)   # within 365 days
    old = _vec("2019-03-01", spread_10y2y=-0.5)
    matches = score_historical_matches(current, [recent, old], exclude_window_days=365)
    dates = [m["date"] for m in matches]
    assert old.observation_date in dates
    assert recent.observation_date not in dates


def test_matches_returns_top_n():
    current = _vec("2024-01-01", spread_10y2y=-0.5, hy_spread=4.0)
    historical = [_vec(f"200{i}-01-01", spread_10y2y=-0.5, hy_spread=4.0) for i in range(5)]
    matches = score_historical_matches(current, historical, top_n=3)
    assert len(matches) == 3


def test_feature_deltas_present_in_results():
    current = _vec("2024-01-01", spread_10y2y=-0.5)
    hist = _vec("2010-01-01", spread_10y2y=-0.3)
    matches = score_historical_matches(current, [hist], top_n=1)
    assert "feature_deltas" in matches[0]
    assert "spread_10y2y" in matches[0]["feature_deltas"]
