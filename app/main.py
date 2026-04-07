import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.routes.api import router as api_router
from app.routes.dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def _bootstrap_if_empty() -> None:
    """Run the full data pipeline on first boot if the database has no data."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM series_points"))
        count = result.scalar()

    if count and count > 0:
        log.info("Database already seeded (%d rows) — skipping bootstrap", count)
        return

    log.info("Database is empty — running first-time bootstrap (this may take ~30s)")
    from app.ingestion.ingest import ingest_all_series
    from app.ingestion.snapshots import compute_and_upsert_snapshots
    from app.narrative.runner import generate_and_save_summary

    await ingest_all_series(start_date="1990-01-01")
    await compute_and_upsert_snapshots()
    await generate_and_save_summary()
    log.info("Bootstrap complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _bootstrap_if_empty()
    yield


app = FastAPI(title="MacroPulse", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router)
app.include_router(dashboard_router)
