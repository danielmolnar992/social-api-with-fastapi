"""
Define the user related models.
"""

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model without sensitive information."""

    id: int | None = None
    email: EmailStr
    username: str


class UserIn(User):
    """User with sensitive information."""

    password: str


class UserConfirmed(UserIn):
    """User with confirmation info."""

    confirmed: bool
