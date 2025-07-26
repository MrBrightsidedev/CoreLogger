"""Test configuration for CoreLogger."""

import pytest
import asyncio


def pytest_configure(config):
    """Configure pytest."""
    # Silence some warnings
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
