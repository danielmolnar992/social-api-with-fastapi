"""
Define the posts and comments models.
"""

from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    """Incoming post data from the user."""

    body: str


class UserPost(UserPostIn):
    """User post with ID and user ID.
    From attribute true helps to check database return value attributes.
    Be default it checks return_value['something'], with this it
    also looks for return_value.something as well."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class UserPostWithLikes(UserPost):
    """User post with the count of likes assiociated."""

    likes: int


class CommentIn(BaseModel):
    """Incoming comment data from user."""

    body: str
    post_id: int


class Comment(CommentIn):
    """Comment with ID.
    From attribute true helps to check database return value attributes.
    Be default it checks return_value['something'], with this it
    also looks for return_value.something as well."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class UserPostWithComments(BaseModel):
    """Post with its related comments."""

    post: UserPostWithLikes
    comments: list[Comment]


class PostLikeIn(BaseModel):
    """Incoming like data for posts."""

    post_id: int


class PostLike(PostLikeIn):
    """Data of post likes."""

    id: int
    user_id: int
