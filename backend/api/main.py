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

@app.get("/api/debug/info")
async def debug_info():
    """Debug endpoint to check paths and files."""
    import os
    from pathlib import Path
    
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent
    static_dir = backend_root / "static"
    uploads_dir = static_dir / "uploads"
    
    files = []
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        
    return {
        "current_file": str(current_file),
        "backend_root": str(backend_root),
        "static_dir": str(static_dir),
        "uploads_dir": str(uploads_dir),
        "uploads_exists": os.path.exists(uploads_dir),
        "files_count": len(files),
        "files_sample": files[:10],
        "cwd": os.getcwd()
    }

# Serve Static Files (Frontend)
# Use absolute path to ensure consistency
from pathlib import Path

# Determine if running in Docker
is_docker = os.path.exists("/app/static")

if is_docker:
    static_dir = Path("/app/static")
    uploads_dir = Path("/app/static/uploads")
else:
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent
    static_dir = backend_root / "static"
    uploads_dir = static_dir / "uploads"

# Ensure both directories exist on startup
os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
print(f"Verified static directories: {static_dir}, {uploads_dir}")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static_assets") 

@app.get("/")
async def serve_index():
    return FileResponse(static_dir / "index.html")

@app.get("/index.html")
async def serve_index_explicit():
    return FileResponse(static_dir / "index.html")

@app.get("/admin.html")
async def serve_admin():
    return FileResponse(static_dir / "admin.html")

# Keep this as fallback for assets, but remove html=True to avoid conflicts
# REMOVED conflicting mount
# app.mount("/", StaticFiles(directory=str(static_dir), html=False), name="static")





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=DEBUG
    )
