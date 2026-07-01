import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import auth as auth_router
from app.routers import ebay as ebay_router
from app.routers import products as products_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")

app = FastAPI(title="Amazon → eBay 自動出品システム", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(ebay_router.router)


@app.get("/")
def root():
    return {"message": "backend is running", "test_mode": settings.test_mode}


@app.get("/api/health")
def health():
    """アプリとDB接続の疎通確認。"""
    db_ok = False
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:  # noqa: BLE001
        db_error = str(e)
        logger.error("DB health check failed: %s", e)

    return {
        "status": "ok",
        "test_mode": settings.test_mode,
        "database": {"connected": db_ok, "error": db_error},
    }
