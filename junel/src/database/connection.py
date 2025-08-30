"""
Database Connection Module for Face Mask Detection System
PostgreSQL connection with connection pooling and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from ..config import config
import logging

logger = logging.getLogger(__name__)

# Database engine with connection pooling
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection and session factory"""
    global engine, SessionLocal
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,  # Number of connections to maintain
            max_overflow=20,  # Additional connections when pool is full
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,  # Recycle connections every hour
            echo=config.DEBUG  # Log SQL queries in debug mode
        )
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db_session() -> Session:
    """Get a database session"""
    if SessionLocal is None:
        init_database()
    
    return SessionLocal()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as session:
            session.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def create_tables():
    """Create database tables"""
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def drop_tables():
    """Drop all database tables (use with caution)"""
    try:
        from .models import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise
