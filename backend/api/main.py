"""
FastAPI main application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db
from .routes import categories, products, orders, images

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
WEBAPP_URL = os.getenv("WEBAPP_URL", "*")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Telegram Shop API",
    description="Backend API for Telegram Mini App Store",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEBAPP_URL] if WEBAPP_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(images.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Telegram Shop API is running"}


@app.get("/health")
async def health():
    """Health check for Docker."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=DEBUG
    )
