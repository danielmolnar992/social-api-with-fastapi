import pytest
from jose import jwt

from social_api import security


def test_access_token_expire_minutes():
    """Test if expiration time is 30 mins."""
    assert security.access_token_expire_minutes() == 30


def test_create_access_token():
    """Test email is in decoded token."""

    token = security.create_access_token('123')

    assert {'sub': '123'}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_password_hashes():
    """Tests if created hash can be verified against original text."""

    password = 'password'
    hashed_password = security.get_password_hash(password)

    assert security.verify_password(password, hashed_password)


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user['email'])

    assert user.email == registered_user['email']


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user('test@example.com')

    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    user = await security.authenticate_user(
        registered_user['email'], registered_user['password']
    )
    assert user.email == registered_user['email']


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    """Test if HTTPException is thrown when user is not found."""

    with pytest.raises(security.HTTPException):
        await security.authenticate_user('test@example.com', '1234')


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    """Test if HTTPException is thrown when user password is incorrect."""

    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user['email'], 'wrong password')


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    """Test registered user is authenticated from token successfully."""

    token = security.create_access_token(registered_user['email'])
    user = await security.get_current_user(token)

    assert user.email == registered_user['email']


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    """Tests invalid JWT authentication raises and error."""

    with pytest.raises(security.HTTPException):
        await security.get_current_user('invalid token')
