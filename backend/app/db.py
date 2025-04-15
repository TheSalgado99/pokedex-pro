# backend/app/db.py

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
# from contextlib import asynccontextmanager # No longer needed here if get_session doesn't use it explicitly

from .config import settings # Import settings to get the DATABASE_URL

# ============================================
# Database Engine Creation
# ============================================
print("DB: Creating database engine...")
async_engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False, # Set to False for less verbose logs, True for debugging SQL
    pool_size=5,
    max_overflow=10
)
# CORRECTED Print statement: Cast URL to string directly
# Pydantic V2's DSN types should automatically mask the password on string conversion.
print(f"DB: Database engine created for URL: {str(settings.DATABASE_URL)}")


# ============================================
# Database Session Dependency
# ============================================
async def get_session() -> AsyncSession:
    """
    FastAPI dependency to provide an asynchronous database session per request.
    Uses AsyncSession as an async context manager for reliable handling.
    """
    async with AsyncSession(async_engine) as session:
        try:
            yield session
        except Exception:
            # Rollback on any exception during the request handling using the session
            await session.rollback()
            raise
        # Note: Commit should generally happen within the endpoint logic
        # after successful operations. The session closes automatically.

# ============================================
# Database Initialization Function
# ============================================
async def init_db():
    """
    Initializes the database by creating tables based on SQLModel metadata.
    Called during application startup via lifespan event.
    """
    print("DB: Attempting to check/create database tables...")
    try:
        async with async_engine.begin() as conn:
            # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment for testing to drop tables first
            await conn.run_sync(SQLModel.metadata.create_all)
            print("DB: Database tables checked/created successfully.")
    except Exception as e:
        print(f"[ERROR] DB: An error occurred during table creation: {e}")
        print("[ERROR] DB: Please check DB connection string and ensure PostgreSQL server is running.")
        # Depending on requirements, you might want to raise e to stop startup