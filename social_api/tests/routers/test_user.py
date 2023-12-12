"""
Tests for the user router.
"""

import pytest
from databases import Database
from fastapi import BackgroundTasks, status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from social_api.database import users_table


async def register_user(
    async_client: AsyncClient, username: str, email: str, password: str
):
    """Registers a user for test cases."""

    return await async_client.post(
        "/register",
        json={"username": username, "email": email, "password": password},
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    """Test a successful user registration."""

    response = await register_user(async_client, "testuser", "test@example.com", "1234")

    assert response.status_code == status.HTTP_201_CREATED
    assert "User created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_invalid_email(async_client: AsyncClient):
    """Test register user with invalid email fails."""

    response = await register_user(async_client, "testuser", "testexamplecom", "1234")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "not a valid email" in response.json()["detail"][0]["msg"]


@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    """Test a user registration when user (username and email) already exists."""

    response = await register_user(
        async_client,
        registered_user["username"],
        registered_user["email"],
        registered_user["password"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_email_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    """Test a user registration when email already exists."""

    response = await register_user(
        async_client,
        registered_user["username"],
        "test2@example.com",
        "12345",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_username_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    """Test a user registration when username already exists."""

    response = await register_user(
        async_client,
        "testuser2",
        registered_user["email"],
        "12345",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker: MockerFixture):
    """Test successful user confirmation."""

    spy = mocker.spy(BackgroundTasks, "add_task")
    await register_user(async_client, "testuser", "test@example.net", "1234")

    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)

    assert response.status_code == status.HTTP_200_OK
    assert "User confirmed" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    """Test failed user confirmation with invalid token."""

    response = await async_client.get("/confirm/invalid_token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_confirm_user_expired_token(
    async_client: AsyncClient, mocker: MockerFixture
):
    """Test failed user confirmation with expired token."""

    mocker.patch("social_api.security.confirm_token_expire_minutes", return_value=-1)
    spy = mocker.spy(BackgroundTasks, "add_task")
    await register_user(async_client, "testuser", "test@example.net", "1234")

    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    """Test if non existing user returns 401 error."""

    response = await async_client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "1234",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        data={
            "username": confirmed_user["username"],
            "password": confirmed_user["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_login_user_not_confirmed(
    async_client: AsyncClient, registered_user: dict
):
    """Test registered but not confirmed user login fails."""
    response = await async_client.post(
        "/token",
        data={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_reconfirm_user(
    async_client: AsyncClient, confirmed_user: dict, db: Database, mocker: MockerFixture
):
    """Test a successful user reconfirmation."""

    spy = mocker.spy(BackgroundTasks, "add_task")

    query = users_table.select().where(
        users_table.c.username == confirmed_user["username"]
    )
    user = await db.fetch_one(query)

    assert user.confirmed is True

    response = await async_client.post(
        "/reconfirm",
        data={
            "username": confirmed_user["username"],
            "password": confirmed_user["password"],
        },
    )

    query = users_table.select().where(
        users_table.c.username == confirmed_user["username"]
    )
    user = await db.fetch_one(query)

    spy.assert_called_once()
    assert user.confirmed is False
    assert response.status_code == status.HTTP_200_OK
    assert "Reconfirmation initiated" in response.json()["detail"]


@pytest.mark.anyio
async def test_reconfirm_not_confirmed_user(
    async_client: AsyncClient,
    registered_user: dict,
    db: Database,
    mocker: MockerFixture,
):
    """Test a successful user reconfirmation."""

    spy = mocker.spy(BackgroundTasks, "add_task")

    query = users_table.select().where(
        users_table.c.username == registered_user["username"]
    )
    user = await db.fetch_one(query)

    assert user.confirmed is False

    response = await async_client.post(
        "/reconfirm",
        data={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )

    query = users_table.select().where(
        users_table.c.username == registered_user["username"]
    )
    user = await db.fetch_one(query)

    spy.assert_called_once()
    assert user.confirmed is False
    assert response.status_code == status.HTTP_200_OK
    assert "Reconfirmation initiated" in response.json()["detail"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "username, password",
    [
        ("testuser_wrong", "1234"),
        ("testuser", "12345"),
        ("testuser_wrong", "12345"),
    ],
)
async def test_reconfirm_user_wrong_inputs(
    async_client: AsyncClient,
    confirmed_user: dict,
    db: Database,
    mocker: MockerFixture,
    username: str,
    password: str,
):
    """Test a failed user reconfirmation with wrong inputs."""

    spy = mocker.spy(BackgroundTasks, "add_task")

    query = users_table.select().where(
        users_table.c.username == confirmed_user["username"]
    )
    user = await db.fetch_one(query)

    assert user.confirmed is True

    response = await async_client.post(
        "/reconfirm",
        data={
            "username": username,
            "password": password,
        },
    )

    query = users_table.select().where(
        users_table.c.username == confirmed_user["username"]
    )
    user = await db.fetch_one(query)

    spy.assert_not_called()
    assert user.confirmed is True
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect username or password" in response.json()["detail"]
