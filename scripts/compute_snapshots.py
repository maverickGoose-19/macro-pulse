"""
Standalone entrypoint to compute and upsert comparison_snapshots.
Run after backfill or whenever series_points data changes:
    python -m scripts.compute_snapshots
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.snapshots import compute_and_upsert_snapshots

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("Starting snapshot computation")
    await compute_and_upsert_snapshots()
    log.info("Snapshot computation complete")


if __name__ == "__main__":
    asyncio.run(main())
