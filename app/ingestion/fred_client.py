import asyncio
import logging
from functools import lru_cache

import pandas as pd
from fredapi import Fred

from app.config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def _fred() -> Fred:
    return Fred(api_key=get_settings().fred_api_key)


async def fetch_series(fred_id: str, start_date: str = "1990-01-01") -> pd.Series:
    """Fetch a FRED series asynchronously (fredapi is sync — run in executor)."""
    loop = asyncio.get_event_loop()
    series = await loop.run_in_executor(
        None,
        lambda: _fred().get_series(fred_id, observation_start=start_date),
    )
    log.debug("Fetched %d observations for %s", len(series), fred_id)
    return series


async def fetch_series_info(fred_id: str) -> dict:
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(
        None,
        lambda: _fred().get_series_info(fred_id),
    )
    return info.to_dict()
