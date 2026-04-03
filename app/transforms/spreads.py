import pandas as pd


def compute_yield_curve_spreads(series: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Compute 10Y-2Y and 10Y-3M spreads.
    Uses pre-computed FRED spread series when available, falls back to raw components.
    """
    df = pd.DataFrame(series).sort_index()
    out = pd.DataFrame(index=df.index)

    if "T10Y2Y" in df.columns:
        out["spread_10y2y"] = df["T10Y2Y"]
    elif "DGS10" in df.columns and "DGS2" in df.columns:
        out["spread_10y2y"] = df["DGS10"] - df["DGS2"]

    if "T10Y3M" in df.columns:
        out["spread_10y3m"] = df["T10Y3M"]
    elif "DGS10" in df.columns and "DGS3MO" in df.columns:
        out["spread_10y3m"] = df["DGS10"] - df["DGS3MO"]

    return out.dropna(how="all")


def compute_hy_spread(series: dict[str, pd.Series]) -> pd.Series:
    return series["BAMLH0A0HYM2"].rename("hy_spread")
