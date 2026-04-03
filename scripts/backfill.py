"""
One-time backfill script — loads historical data from 1990 into series_points.
Run once after first deploy: python -m scripts.backfill
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.ingest import ingest_all_series

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("Starting historical backfill from 1990-01-01")
    await ingest_all_series(start_date="1990-01-01")
    log.info("Backfill complete")


if __name__ == "__main__":
    asyncio.run(main())
