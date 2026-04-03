from __future__ import annotations

from datetime import date

import numpy as np

from app.comparison.features import FeatureVector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def score_historical_matches(
    current: FeatureVector,
    historical: list[FeatureVector],
    top_n: int = 5,
    exclude_window_days: int = 365,
) -> list[dict]:
    """
    Return top_n historical dates ranked by cosine similarity to current.
    Each result includes the score AND per-feature delta breakdown for inspectability.
    Dates within exclude_window_days of current are excluded.
    """
    current_vec = current.to_weighted_array()
    current_dict = current.to_dict()
    feature_keys = current.feature_names()
    results = []

    for hist in historical:
        days_apart = abs((hist.observation_date - current.observation_date).days)
        if days_apart < exclude_window_days:
            continue

        hist_vec = hist.to_weighted_array()
        score = cosine_similarity(current_vec, hist_vec)
        hist_dict = hist.to_dict()

        feature_deltas = {
            k: round((hist_dict.get(k) or 0.0) - (current_dict.get(k) or 0.0), 3)
            for k in feature_keys
        }

        results.append(
            {
                "date": hist.observation_date,
                "similarity_score": round(score, 4),
                "feature_deltas": feature_deltas,
                "historical_values": {k: hist_dict.get(k) for k in feature_keys},
                "current_values": {k: current_dict.get(k) for k in feature_keys},
            }
        )

    return sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:top_n]
