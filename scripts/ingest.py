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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("Starting ingestion run")
    await ingest_all_series()
    log.info("Ingestion run complete")


if __name__ == "__main__":
    asyncio.run(main())
