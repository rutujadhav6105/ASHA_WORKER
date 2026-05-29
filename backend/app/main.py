"""
ASHA Seva - Production FastAPI Backend
======================================
Endpoints: Auth, Patients, Pregnancies, ANC, Immunization,
           Home Visits, Medicine Stock, ML, Reports, Dashboard
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from app.database import Base, engine, get_db
from app.routes import (
    auth, patients, pregnancies, anc, immunization,
    home_visits, medicine_stock, ml_routes, reports,
    dashboard, villages, schemes, ai_assistant,
    alerts, training, supervisor_notes, sync
)
from app.services.backup_service import run_daily_backup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created.")

    # Schedule daily CSV backup at 2 AM
    scheduler.add_job(run_daily_backup, "cron", hour=2, minute=0)
    scheduler.start()
    logger.info("Backup scheduler started.")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="ASHA Seva API",
    description="Backend for the ASHA Seva health worker application",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Flutter app domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "ASHA Seva API v2.0 running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "version": "2.0.0"}


# ── Register all routers ──────────────────────────────────────────────────────
PREFIX = "/api"

app.include_router(auth.router,              prefix=PREFIX, tags=["Auth"])
app.include_router(patients.router,          prefix=PREFIX, tags=["Patients"])
app.include_router(pregnancies.router,       prefix=PREFIX, tags=["Pregnancies"])
app.include_router(anc.router,               prefix=PREFIX, tags=["ANC"])
app.include_router(immunization.router,      prefix=PREFIX, tags=["Immunization"])
app.include_router(home_visits.router,       prefix=PREFIX, tags=["Home Visits"])
app.include_router(medicine_stock.router,    prefix=PREFIX, tags=["Medicine"])
app.include_router(ml_routes.router,         prefix=PREFIX, tags=["ML Predictions"])
app.include_router(reports.router,           prefix=PREFIX, tags=["Reports"])
app.include_router(dashboard.router,         prefix=PREFIX, tags=["Dashboard"])
app.include_router(villages.router,          prefix=PREFIX, tags=["Villages"])
app.include_router(schemes.router,           prefix=PREFIX, tags=["Schemes"])
app.include_router(ai_assistant.router,      prefix=PREFIX, tags=["AI Assistant"])
app.include_router(alerts.router,            prefix=PREFIX, tags=["Alerts"])
app.include_router(training.router,          prefix=PREFIX, tags=["Training"])
app.include_router(supervisor_notes.router,  prefix=PREFIX, tags=["Supervisor Notes"])
app.include_router(sync.router,              prefix=PREFIX, tags=["Sync"])


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
