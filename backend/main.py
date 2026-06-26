import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from routes.meeting_routes import router as meeting_router
from routes.task_routes import router as task_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database ready.")

    try:
        from ml_model.extractor import get_nlp
        get_nlp()
        logger.info("Local ML model (spaCy) loaded successfully.")
    except Exception as e:
        logger.warning(f"ML model load warning: {e}")

    try:
        from agents.escalation_agent import escalation_agent
        result = escalation_agent.run()
        logger.info(f"Startup escalation: {result['newly_overdue']} overdue, {result['escalated']} escalated")
    except Exception as e:
        logger.warning(f"Startup escalation failed: {e}")

    yield
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Autonomous Meeting-to-Execution AI Workflow System",
    description="Multi-agent system using local ML — no API key required.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meeting_router)
app.include_router(task_router)


@app.get("/api/health", tags=["system"])
async def health():
    return {
        "status": "healthy",
        "mode": "local_ml",
        "ml_model": "spaCy en_core_web_sm",
        "version": "2.0.0",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")