from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from db.models import Base


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(
            self.database_url,
            echo=settings.database_echo,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def get_session_direct(self) -> Session:
        """Get a database session (must be closed manually)."""
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency function for FastAPI to get database session."""
    session = db_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    """Initialize the database with tables."""
    db_manager.create_tables()


def reset_database() -> None:
    """Reset the database by dropping and recreating tables."""
    db_manager.drop_tables()
    db_manager.create_tables()
