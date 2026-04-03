import pandas as pd


def curve_stress_composite(
    spread_10y2y_z: pd.Series,
    spread_10y3m_z: pd.Series,
) -> pd.Series:
    """
    Simple average of z-scored curve spreads.
    Negative = inversion stress. Positive = steepening.
    """
    return ((spread_10y2y_z + spread_10y3m_z) / 2).rename("curve_stress_composite")
