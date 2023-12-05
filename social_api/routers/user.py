import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from social_api import tasks
from social_api.database import database, users_table
from social_api.models.user import UserIn
from social_api.security import (authenticate_user, create_access_token,
                                 create_confirmation_token, get_password_hash,
                                 get_subject_for_token_type, get_user)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, background_task: BackgroundTasks, request: Request):
    """Registering a new user."""

    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='A user with that email already exists.'
        )

    hashed_password = get_password_hash(user.password)
    query = users_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(query)

    # Using background task not to minimize registration response time
    background_task.add_task(
        tasks.send_user_registration_email,
        user.email,
        confirmation_url=request.url_for(
            'confirm_email', token=create_confirmation_token(user.email)
        )
    )
    await database.execute(query)

    return {'detail': 'User created. Please confirm your email.'}


@router.post('/token')
async def login(user: UserIn):
    """Login with an existing user."""

    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/confirm/{token}')
async def confirm_email(token: str):
    """Confirm user registration."""

    email = get_subject_for_token_type(token, 'confirmation')
    query = (
        users_table.update()
        .where(users_table.c.email == email)
        .values(confirmed=True)
    )

    logger.debug(query)
    await database.execute(query)

    return {'detail': 'User confirmed'}
