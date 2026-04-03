from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


FEATURE_WEIGHTS: dict[str, float] = {
    "spread_10y2y":          0.25,
    "spread_10y3m":          0.20,
    "spread_10y2y_1m_delta": 0.15,
    "hy_spread":             0.20,
    "hy_spread_zscore_1y":   0.10,
    "cpi_yoy":               0.05,
    "fedfunds":              0.05,
}


@dataclass
class FeatureVector:
    observation_date: date
    spread_10y2y: float | None
    spread_10y3m: float | None
    spread_10y2y_1m_delta: float | None
    hy_spread: float | None
    hy_spread_zscore_1y: float | None
    cpi_yoy: float | None
    fedfunds: float | None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_weighted_array(self) -> list[float]:
        """Return a weighted feature array for cosine similarity. Missing values → 0."""
        vec = self.to_dict()
        vec.pop("observation_date")
        return [(vec.get(k) or 0.0) * w for k, w in FEATURE_WEIGHTS.items()]

    def feature_names(self) -> list[str]:
        return list(FEATURE_WEIGHTS.keys())
