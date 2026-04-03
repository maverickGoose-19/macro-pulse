import pandas as pd
import pytest

from app.transforms.spreads import compute_yield_curve_spreads
from app.transforms.rolling import rolling_zscore, rolling_delta, cpi_yoy


def test_spread_uses_precomputed_t10y2y():
    series = {
        "T10Y2Y": pd.Series([0.5, 0.3, -0.1], dtype=float),
        "DGS10": pd.Series([4.0, 3.9, 3.8], dtype=float),
        "DGS2": pd.Series([3.5, 3.6, 3.9], dtype=float),
    }
    result = compute_yield_curve_spreads(series)
    pd.testing.assert_series_equal(
        result["spread_10y2y"].reset_index(drop=True),
        series["T10Y2Y"].reset_index(drop=True),
        check_names=False,
    )


def test_spread_falls_back_to_components_when_no_precomputed():
    series = {
        "DGS10": pd.Series([4.0, 3.9], dtype=float),
        "DGS2": pd.Series([3.5, 3.6], dtype=float),
        "DGS3MO": pd.Series([3.8, 3.85], dtype=float),
    }
    result = compute_yield_curve_spreads(series)
    expected_10y2y = pd.Series([0.5, 0.3], dtype=float)
    pd.testing.assert_series_equal(
        result["spread_10y2y"].reset_index(drop=True),
        expected_10y2y,
        check_names=False,
    )


def test_rolling_zscore_returns_correct_shape():
    s = pd.Series(range(300), dtype=float, name="test")
    z = rolling_zscore(s, window=252)
    assert len(z) == len(s)
    assert z.dropna().abs().max() < 5  # no extreme z-scores on linear series


def test_rolling_delta_diff():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], dtype=float, name="x")
    delta = rolling_delta(s, periods=1)
    assert delta.iloc[1] == pytest.approx(1.0)
    assert delta.iloc[2] == pytest.approx(1.0)


def test_cpi_yoy_computes_percent_change():
    # CPI goes from 100 → 102 over 12 months → 2% YoY
    values = [100.0] * 12 + [102.0]
    s = pd.Series(values, dtype=float, name="CPIAUCSL")
    yoy = cpi_yoy(s)
    assert yoy.iloc[-1] == pytest.approx(2.0, rel=1e-3)
