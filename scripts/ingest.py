"""
Entry point for the Render Cron Job.
Schedule: 0 18 * * 1-5  (weekdays at 6pm ET)
Command:  python -m scripts.ingest
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure app is importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.ingest import ingest_all_series
from app.ingestion.snapshots import compute_and_upsert_snapshots
from app.narrative.runner import generate_and_save_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("Starting ingestion run")
    await ingest_all_series()
    log.info("Ingestion run complete")
    log.info("Computing comparison snapshots")
    await compute_and_upsert_snapshots()
    log.info("Snapshot computation complete")
    log.info("Generating narrative summary")
    await generate_and_save_summary()
    log.info("Summary generation complete")


if __name__ == "__main__":
    asyncio.run(main())
