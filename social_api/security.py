"""
Security setup to handle password encryption and decreption, user
authentication, token creation and information retrieval.
"""

import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from social_api.config import config
from social_api.database import database, users_table


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=['bcrypt'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
SECRET_KEY = config.SECRET_KEY
ALGORITHM = 'HS256'


def create_credentials_exception(detail: str):
    """Returns a 401 HTTP exception with the supplied detail."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={'WWW-Authenticate': 'Bearer'}
    )


def access_token_expire_minutes() -> int:
    """Number of minutes until JWT expires."""
    return 30


def confirm_token_expire_minutes() -> int:
    """Number of minutes until JWT expires."""
    return 1440


def create_access_token(email: str):
    """Create JWT token based on the email address."""

    logger.debug('Creating access token', extra={'email': email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {'sub': email, 'exp': expire, 'type': 'access'}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_confirmation_token(email: str):
    """Create JWT token based on the email address."""

    logger.debug('Creating confirmation token', extra={'email': email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {'sub': email, 'exp': expire, 'type': 'confirmation'}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_subject_for_token_type(
    token: str, exp_type: Literal['access', 'confirmation']
):
    """Gets the subject value from the given token type or raises an error."""

    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except ExpiredSignatureError as e:
        raise create_credentials_exception('Token has expired') from e

    except JWTError as e:
        raise create_credentials_exception('Invalid token') from e

    email = payload.get('sub')
    if not email:
        raise create_credentials_exception('Token is missing "sub" field')

    token_type = payload.get('type')
    if token_type != exp_type:
        raise create_credentials_exception(
            f'Token has incorrect type, expected {exp_type}'
        )

    return email


def get_password_hash(password: str) -> str:
    """Hashes the given password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validates the password againsted the hashed value."""
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    """Returns the user if exists, else None."""

    logger.debug('Fetching user from database', extra={'email': email})
    query = users_table.select().where(users_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        return result


async def authenticate_user(email: str, password: str):
    """Checks if user exists, password is correct and returns the user.
    Raises an HTTPException when user doesn't exists or password is
    incorrect."""

    logger.debug('Authenticating user', extra={'email': email})
    user = await get_user(email)

    if not user:
        raise create_credentials_exception('Invalid emial or password')
    if not verify_password(password, user.password):
        raise create_credentials_exception('Invalid emial or password')
    if not user.confirmed:
        raise create_credentials_exception('User has not confirmed email')

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Returns the current user based on the token or raises an error.
    OAuth2PasswordBearer dependency is injected."""

    email = get_subject_for_token_type(token, 'access')
    user = await get_user(email=email)
    if not user:
        raise create_credentials_exception('Could not find user for this token')

    return user
