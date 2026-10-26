from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID
import redis
import logging

from app.core.config import settings

logger = logging.getLogger("apexquant.database")

Base = declarative_base()

# SQLite UUID compiler adapter
@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

# Check if DATABASE_URL is SQLite or fallback
if settings.DATABASE_URL.startswith("sqlite:///"):
    logger.info(f"Using SQLite database configured in Settings: {settings.DATABASE_URL}")
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL Engine Setup with SQLite Fallback
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info("Successfully connected to PostgreSQL database.")
    except (OperationalError, Exception) as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
        sqlite_url = "sqlite:///./apexquant.db"
        engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False}
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# In-Memory Cache Mock for systems without Redis
class LocalMemoryCache:
    def __init__(self):
        self._data = {}

    def get(self, key: str) -> str:
        return self._data.get(key)

    def set(self, key: str, value: str):
        self._data[key] = value

    def setex(self, key: str, time: int, value: str):
        self._data[key] = value

# Redis Client Setup with Local Fallback
try:
    redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client = redis.Redis(connection_pool=redis_pool)
    redis_client.ping()
    logger.info("Successfully connected to Redis.")
except Exception as e:
    logger.warning(f"Redis is unreachable ({e}). Falling back to local in-memory cache.")
    redis_client = LocalMemoryCache()

def get_db() -> Generator:
    """Dependency generator to retrieve database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Dependency generator to retrieve redis client."""
    return redis_client

