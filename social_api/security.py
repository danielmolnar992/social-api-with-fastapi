import datetime
import logging
from typing import Annotated

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


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials.',
    headers={'WWW-Authenticate': 'Bearer'}
)


def access_token_expire_minutes() -> int:
    """Number of minutes until JWT expires."""
    return 30


def create_access_token(email: str):
    """Create JWT token based on the email address."""

    logger.debug('Creating access token', extra={'email': email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {'sub': email, 'exp': expire}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


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
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """Returns the current user based on the token or raises an error.
    OAuth2PasswordBearer dependency is injected."""

    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')

        if not email:
            raise credentials_exception

    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired.',
            headers={'WWW-Authenticate': 'Bearer'}
        ) from e

    except JWTError as e:
        raise credentials_exception from e

    user = await get_user(email=email)
    if not user:
        raise credentials_exception

    return user
