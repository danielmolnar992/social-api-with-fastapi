"""
Configuration and fixtures for the tests.
"""

import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, Request, Response
from pytest_mock import MockerFixture


os.environ['ENV_STATE'] = 'test'
from social_api.database import database, users_table
from social_api.main import app
from social_api.tests.helpers import create_post


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

    # Without connecting, the force rollback True setting won't take effect.
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    """Registers a user and returns the data."""

    user_details = {'email': 'test@example.com', 'password': '1234'}
    await async_client.post('/register', json=user_details)

    query = users_table.select().where(users_table.c.email == user_details['email'])
    user = await database.fetch_one(query)
    user_details['id'] = user.id
    return user_details


@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    """Confirms the registered user fixture and returns the user."""

    query = (
        users_table.update()
        .where(users_table.c.email == registered_user['email'])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict):
    """Returns a valid access token for a registered and logged in user."""

    response = await async_client.post('/token', json=confirmed_user)
    return response.json()['access_token']


@pytest.fixture(autouse=True)
def mock_httpx_client(mocker: MockerFixture):
    """Mocks the call to a third party API automatically for testing.
    Returns the mocked async client for optional direct use."""

    mocked_client = mocker.patch('social_api.tasks.httpx.AsyncClient')
    mocked_async_client = Mock()
    response = Response(status_code=200, content='', request=Request('POST', '//'))
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client

    return mocked_async_client


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    """Fixture for a post created by the time the test runs."""

    return await create_post('Test post', async_client, logged_in_token)
