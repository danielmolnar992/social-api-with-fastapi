"""
Configuration and fixtures for the tests.
"""

import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


os.environ['ENV_STATE'] = 'test'
from social_api.database import database  # noqa E402
from social_api.main import app  # noqa E402


@pytest.fixture(scope='session')
def anyio_backend() -> str:
    """Tells pytest to use asyncio for the async function executions."""
    return 'asyncio'


@pytest.fixture
def client() -> Generator:
    """Yields a test client."""

    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    """Runs for every test case and since roll back is set to true,
    it will clear the changes."""

    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac
