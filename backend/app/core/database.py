"""
Database configuration and session management
"""
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Database naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Create base class for models
Base = declarative_base(metadata=metadata)


# Async engine for async operations
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Sync engine for migrations and sync operations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Sync session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for backward compatibility
get_db = get_async_session


def get_sync_session() -> Session:
    """
    Get synchronous database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables
    """
    from sqlalchemy import exc

    async with async_engine.begin() as conn:
        try:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        except exc.IntegrityError as e:
            # Ignore errors for existing ENUM types (PostgreSQL specific issue)
            if "duplicate key value violates unique constraint" in str(e) and "pg_type_typname_nsp_index" in str(e):
                # ENUM types already exist, this is fine
                pass
            else:
                # Re-raise if it's a different integrity error
                raise


async def close_db():
    """
    Close database connections
    """
    await async_engine.dispose()