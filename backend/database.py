"""
SQLAlchemy Engine and Database Session Management for PolitiAds
"""
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
try:
    from config import DATABASE_URL
    from entities import Base
except ImportError:
    from backend.config import DATABASE_URL
    from backend.entities import Base

# Engine configuration with SQLite thread handling and foreign keys
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Enforce foreign key constraints on SQLite connections
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency that provides a scoped database session per request.
    Automatically closes session on completion and rolls back on unhandled exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Creates tables if they don't already exist.
    """
    Base.metadata.create_all(bind=engine)
