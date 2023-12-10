"""
Define the user related models.
"""

from pydantic import BaseModel


class User(BaseModel):
    """User model without sensitive information."""

    id: int | None = None
    email: str


class UserIn(User):
    """User with sensitive information."""

    password: str
