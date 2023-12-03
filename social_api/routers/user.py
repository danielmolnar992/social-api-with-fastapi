import logging

from fastapi import APIRouter, HTTPException, status

from social_api.database import database, users_table
from social_api.models.user import UserIn
from social_api.security import (authenticate_user, create_access_token,
                                 get_password_hash, get_user)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register(user: UserIn):
    """Registering a new user."""

    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='A user with that email already exists.'
        )

    hashed_password = get_password_hash(user.password)
    query = users_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(query)
    await database.execute(query)

    return {'detail': 'User created'}


@router.post('/token')
async def login(user: UserIn):
    """Login with an existing user."""

    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)

    return {'access_token': access_token, 'token_type': 'bearer'}
