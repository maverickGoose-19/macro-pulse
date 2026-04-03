import pandas as pd


def rolling_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """Z-score relative to a rolling window (default: 1 trading year)."""
    rolling = series.rolling(window=window, min_periods=window // 2)
    z = (series - rolling.mean()) / rolling.std()
    return z.rename(f"{series.name}_zscore_{window}d")


def rolling_delta(series: pd.Series, periods: int = 21) -> pd.Series:
    """Change over N periods (default: ~1 month of trading days)."""
    return series.diff(periods).rename(f"{series.name}_{periods}d_delta")


def cpi_yoy(series: pd.Series) -> pd.Series:
    """Year-over-year percent change for monthly CPI series."""
    return series.pct_change(12).mul(100).rename("cpi_yoy")


def rolling_mean(series: pd.Series, window: int = 252) -> pd.Series:
    """Simple rolling mean — used as a reference line on credit panel."""
    return series.rolling(window=window, min_periods=window // 2).mean().rename(
        f"{series.name}_ma{window}d"
    )
