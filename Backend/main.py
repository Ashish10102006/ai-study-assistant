import sys
import os
from pathlib import Path

# Ensure root of backend directory is in sys.path for serverless runtimes
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
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

class VercelPathRewriteMiddleware:
    """
    Pure ASGI middleware that intercepts requests where Vercel serverless rewrites
    mapped the incoming path to '/main.py' or 'main.py' and restores the true requested
    path from edge proxy headers (x-matched-path, x-invoke-path, x-forwarded-uri, etc.)
    or __path query parameter.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            current_path = scope.get("path", "")
            if current_path in ("/main.py", "main.py"):
                headers = dict(scope.get("headers", []))
                target_path = None

                # 1. Check Vercel edge proxy path headers
                for header_name in [b"x-matched-path", b"x-invoke-path", b"x-forwarded-uri", b"x-original-uri"]:
                    val = headers.get(header_name)
                    if val:
                        decoded = val.decode("utf-8", errors="ignore").split("?")[0].strip()
                        if decoded and decoded not in ("/main.py", "main.py"):
                            target_path = decoded
                            break

                # 2. Check query string for __path parameter
                if not target_path and "query_string" in scope:
                    qs = scope["query_string"].decode("utf-8", errors="ignore")
                    for param in qs.split("&"):
                        if param.startswith("__path="):
                            from urllib.parse import unquote
                            target_path = unquote(param.split("=", 1)[1].split("?")[0].strip())
                            break

                if target_path:
                    scope["path"] = target_path
                    scope["raw_path"] = target_path.encode("utf-8")
                else:
                    # Fallback to root route if direct invocation of /main.py
                    scope["path"] = "/"
                    scope["raw_path"] = b"/"

        await self.app(scope, receive, send)


app = FastAPI(
    title="AI STUDY ASSISTANT",
    description="Ask. Understand. Learn. Master. - Your Personal AI Study Companion Backend API.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False
)

# Register Vercel ASGI path restoration middleware
app.add_middleware(VercelPathRewriteMiddleware)

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
    allow_origins=origins,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


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


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/")
@app.get("/api", include_in_schema=False)
@app.get("/main.py", include_in_schema=False)
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
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[Req {req_id}] Global unhandled error at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again or contact support.",
            "request_id": req_id
        },
        headers={"X-Request-Id": req_id}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
