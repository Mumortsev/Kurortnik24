"""
FastAPI main application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db
from .routes import categories, products, orders, images, admin

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
WEBAPP_URL = os.getenv("WEBAPP_URL", "*")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    
    # Run seeder
    try:
        from .seeder import seed_categories
        await seed_categories()
    except Exception as e:
        print(f"Error seeding categories: {e}")
        
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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# ... existing imports

# After app definition and middleware...

# Include routers
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(images.router)
app.include_router(admin.router)

@app.get("/health")
async def health():
    """Health check for Docker."""
    return {"status": "healthy"}

# Serve Static Files (Frontend)
# Create static directory if it doesn't exist to avoid errors locally
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static_assets") # Mount specific static assets if needed
app.mount("/", StaticFiles(directory="static", html=True), name="static")





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=DEBUG
    )
