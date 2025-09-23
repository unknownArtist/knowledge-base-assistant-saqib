from db import db
from config.settings import settings


# Database connection configuration
DATABASE_CONFIG = {
    "host": settings.POSTGRES_HOST,
    "port": settings.POSTGRES_PORT,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "database": settings.POSTGRES_DB,
}


# Database dependency for FastAPI
async def get_db():
    """Database dependency for FastAPI"""
    return db
