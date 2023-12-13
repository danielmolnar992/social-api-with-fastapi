"""
Router to handle user registration and authentication.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from social_api import tasks
from social_api.database import database, users_table
from social_api.models.user import UserIn
from social_api.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user_by_email,
    get_user_by_username,
    verify_password,
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, background_task: BackgroundTasks, request: Request):
    """Registering a new user."""

    if await get_user_by_username(user.username) or await get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that username or email already exists.",
        )

    hashed_password = get_password_hash(user.password)
    query = users_table.insert().values(
        username=user.username, email=user.email, password=hashed_password
    )
    logger.debug(query)
    await database.execute(query)

    # Using background task not to minimize registration response time
    background_task.add_task(
        tasks.send_user_registration_email,
        user.username,
        user.email,
        confirmation_url=request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    )

    return {"detail": "User created. Please confirm your email."}


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login with an existing user."""

    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.email)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/reconfirm")
async def trigger_registration_reconfirmation(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    background_task: BackgroundTasks,
    request: Request,
):
    """Triggers an email user confirmation when user is registered but not confirmed."""

    user = await get_user_by_username(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    # Sets confirmation to False, even if it was confirmed before
    query = (
        users_table.update()
        .where(users_table.c.username == user.username)
        .values(confirmed=False)
    )
    logger.debug(query)
    await database.execute(query)

    background_task.add_task(
        tasks.send_user_registration_email,
        user.username,
        user.email,
        confirmation_url=request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    )

    return {"detail": "Reconfirmation initiated. Please check your emails."}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    """Confirm user registration."""

    email = get_subject_for_token_type(token, "confirmation")
    query = (
        users_table.update().where(users_table.c.email == email).values(confirmed=True)
    )

    logger.debug(query)
    await database.execute(query)

    return {"detail": "User confirmed"}
