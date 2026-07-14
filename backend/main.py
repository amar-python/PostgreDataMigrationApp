"""FastAPI application entrypoint for the Migration Evaluation Platform (MEP).

This is the foundation-only skeleton: it wires up CORS, the health router, a
root route, and a startup hook that logs and tests the database connection.
Business logic (migration orchestration, evaluation, reporting) is added in
later steps.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health
from config import settings
from database.connection import check_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mep")

VERSION = "0.1.0"

app = FastAPI(title="Migration Evaluation Platform", version=VERSION)

# CORS — allow all origins during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under the /api prefix.
app.include_router(health.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    """Log startup and test the database connection."""
    logger.info("MEP Backend starting...")
    logger.info("Environment: %s | Debug: %s", settings.APP_ENV, settings.DEBUG)
    if check_db_connection():
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: UNAVAILABLE")


@app.get("/")
def root() -> dict:
    """Root route confirming the API is running."""
    return {"message": "MEP API is running", "version": VERSION}
