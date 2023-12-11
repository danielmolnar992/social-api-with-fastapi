import pytest
from jose import jwt

from social_api import security


def test_access_token_expire_minutes():
    """Test if expiration time is 30 mins."""
    assert security.access_token_expire_minutes() == 30


def test_confirm__token_expire_minutes():
    """Test if expiration time is 1440 mins."""
    assert security.confirm_token_expire_minutes() == 1440


def test_create_access_token():
    """Test email is in decoded access token."""

    token = security.create_access_token("123")

    assert {"sub": "123", "type": "access"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_create_confirmation_token():
    """Test email is in decoded confirmation token."""

    token = security.create_confirmation_token("123")

    assert {"sub": "123", "type": "confirmation"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_get_subject_for_token_type_valid_confirmation():
    """Test valid confimration token."""

    email = "test@example.com"
    token = security.create_confirmation_token(email)
    assert email == security.get_subject_for_token_type(token, "confirmation")


def test_get_subject_for_token_type_valid_access():
    """Test valid access token."""

    email = "test@example.com"
    token = security.create_access_token(email)
    assert email == security.get_subject_for_token_type(token, "access")


def test_get_subject_for_token_type_expired(mocker):
    """Test expored token."""

    mocker.patch("social_api.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has expired" == exc_info.value.detail


def test_get_subject_for_token_type_invalid_token():
    """Test invalid token."""

    token = "invalid token"
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Invalid token" == exc_info.value.detail


def test_get_subject_for_token_type_missing_sub():
    """Test token with missing sub field."""

    email = "test@example.com"
    token = security.create_access_token(email)
    payload = jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    del payload["sub"]
    token = jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert 'Token is missing "sub" field' == exc_info.value.detail


def test_get_subject_for_token_type_wrong_type():
    """Test incorrect token type."""

    email = "test@example.com"
    token = security.create_confirmation_token(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has incorrect type, expected access" == exc_info.value.detail


def test_password_hashes():
    """Test if created hash can be verified against original text."""

    password = "password"
    hashed_password = security.get_password_hash(password)

    assert security.verify_password(password, hashed_password)


@pytest.mark.anyio
async def test_get_user_by_email(registered_user: dict):
    """Test getting existing user."""

    user = await security.get_user_by_email(registered_user["email"])

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_by_email_not_found():
    """Test getting non existing user."""
    user = await security.get_user_by_email("test@example.com")

    assert user is None


@pytest.mark.anyio
async def test_get_user_by_username(registered_user: dict):
    """Test getting existing user."""

    user = await security.get_user_by_username(registered_user["username"])

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_by_username_not_found():
    """Test getting non existing user."""
    user = await security.get_user_by_username("testuser")

    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    """Test successful user authentication."""

    user = await security.authenticate_user(
        confirmed_user["username"], confirmed_user["password"]
    )
    assert user.username == confirmed_user["username"]
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    """Test if HTTPException is thrown when user is not found."""

    with pytest.raises(security.HTTPException):
        await security.authenticate_user("testuser", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    """Test if HTTPException is thrown when user password is incorrect."""

    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["username"], "wrong password")


@pytest.mark.anyio
async def test_authenticate_user_not_confirmed(registered_user: dict):
    """Test registered but not confirmed user authentication raises
    HTTPException."""

    with pytest.raises(security.HTTPException):
        await security.authenticate_user(
            registered_user["username"], registered_user["password"]
        )


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    """Test registered user is authenticated from token successfully."""

    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    """Test invalid JWT authentication raises and error."""

    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_get_current_user_wrong_token_type(registered_user: dict):
    """Test invalid token type for user authentication."""

    token = security.create_confirmation_token(registered_user["email"])

    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
