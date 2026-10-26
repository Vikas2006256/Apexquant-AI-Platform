import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apexquant")

# Bootstrap database schema on startup if not present
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # Seed default demo user if not present
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.email == "trader@apexquant.ai").first()
        if not demo_user:
            logger.info("Seeding default demo user trader@apexquant.ai...")
            demo_user = User(
                email="trader@apexquant.ai",
                hashed_password=get_password_hash("password123"),
                full_name="Apex Trader",
                role="trader"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            portfolio = Portfolio(
                user_id=demo_user.id,
                name="Main Paper Account",
                type="paper",
                balance=100000.0
            )
            db.add(portfolio)
            db.commit()
            logger.info("Demo user trader@apexquant.ai and paper portfolio seeded successfully.")
    except Exception as seed_err:
        logger.error(f"Failed to seed demo user: {seed_err}")
    finally:
        db.close()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Dev friendly settings. In production, configure explicitly.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    """Simple API health check endpoint."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

@app.get("/")
def serve_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }

# Serve frontend static files if dist directory exists
frontend_dist_dir = os.environ.get("FRONTEND_DIST_DIR", "../frontend_dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")

    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        if request.url.path.startswith(settings.API_V1_STR):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

