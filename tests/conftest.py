import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from db.models import Base
from db.session import DatabaseManager
from main import create_app


@pytest.fixture(scope="session")
def test_database_url():
    """Test database URL."""
    return "sqlite:///./test_corelogger.db"


@pytest.fixture(scope="session")
def test_db_manager(test_database_url):
    """Test database manager."""
    manager = DatabaseManager(test_database_url)
    manager.create_tables()
    yield manager
    # Cleanup
    manager.drop_tables()
    # Close all connections to ensure file is not locked
    manager.engine.dispose()
    # Wait a bit and try to remove the file
    import time
    time.sleep(0.1)
    try:
        if os.path.exists("./test_corelogger.db"):
            os.remove("./test_corelogger.db")
    except PermissionError:
        # File is still locked, skip cleanup
        pass


@pytest.fixture
def db_session(test_db_manager):
    """Database session for testing."""
    with test_db_manager.get_session() as session:
        yield session


@pytest.fixture
def client(test_db_manager):
    """Test client for FastAPI app."""
    app = create_app()
    
    # Override database dependency
    def override_get_db():
        with test_db_manager.get_session() as session:
            yield session
    
    from db import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
