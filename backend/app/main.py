"""
LogSentinel — FastAPI Application
AI-Powered Security Log Analyzer
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict

from app.config import settings
from app.database import engine, Base
from app.routers import logs, auth
class RateLimiter:
    """Simple in-memory IP-based rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window

        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        self.requests[client_ip].append(now)
        return True


upload_limiter = RateLimiter(max_requests=10, window_seconds=60)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Import models so they're registered with Base
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
app = FastAPI(
    title="LogSentinel API",
    description="AI-Powered Security Log Analyzer",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
        settings.NEXTAUTH_URL,
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/api/v1/logs/upload" and request.method == "POST":
        # Extract IP, with fallback to proxy headers or 127.0.0.1
        client_ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP")
        if not client_ip:
            client_ip = request.client.host if request.client else "127.0.0.1"
            
        # Handle X-Forwarded-For comma-separated lists
        client_ip = client_ip.split(",")[0].strip()

        if not upload_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Max 10 uploads per minute."},
            )
    response = await call_next(request)
    return response
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "logsentinel-api", "version": "1.0.0"}
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Logs"])
