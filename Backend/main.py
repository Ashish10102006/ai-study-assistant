import sys
import os
from pathlib import Path

# Ensure root of backend directory is in sys.path for serverless runtimes
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config.settings import get_settings
from app.routes.api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_study_assistant")

settings = get_settings()

app = FastAPI(
    title="AI STUDY ASSISTANT",
    description="Ask. Understand. Learn. Master. - Your Personal AI Study Companion Backend API.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://ai-study-assistant-five-tau.vercel.app",
]
if settings.APP_URL and settings.APP_URL not in origins:
    origins.append(settings.APP_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits flexible local dev and staging access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def handle_private_network_access(request: Request, call_next):
    response = await call_next(request)
    if request.headers.get("access-control-request-private-network") == "true":
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# Mount Uploads Directory
if settings.UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Include API Router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "platform": "AI STUDY ASSISTANT",
        "tagline": "Ask. Understand. Learn. Master.",
        "supporting": "Your Personal AI Study Companion.",
        "status": "online",
        "api_docs": "/docs",
        "health": "/api/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again or contact support."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
