from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    """Incoming post data from the user."""

    body: str


class UserPost(UserPostIn):
    """User post with ID.
    From attribute true helps to check database return value attributes.
    Be default it checks return_value['something'], with this it
    also looks for return_value.something as well."""

    model_config = ConfigDict(from_attributes=True)
    id: int


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


class UserPostWithComments(BaseModel):
    """Post with its related comments."""

    post: UserPost
    comments: list[Comment]
