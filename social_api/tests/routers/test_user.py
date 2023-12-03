import pytest
from fastapi import status
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    """Registers a user for test cases."""

    return await async_client.post(
        '/register', json={'email': email, 'password': password}
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    """Test a successful user registration."""

    response = await register_user(async_client, 'test@example.com', '1234')

    assert response.status_code == status.HTTP_201_CREATED
    assert 'User created' in response.json()['detail']


@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient,
    registered_user: dict
):
    """Test a user registration when user already exists."""

    response = await register_user(
        async_client,
        registered_user['email'],
        registered_user['password']
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'already exists' in response.json()['detail']


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    """Tests if non existing user returns 401 error."""

    response = await async_client.post(
        '/token', json={'email': 'test@example.com', 'password': '1234'}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        '/token',
        json={
            'email': registered_user['email'],
            'password': registered_user['password'],
        },
    )
    assert response.status_code == status.HTTP_200_OK
