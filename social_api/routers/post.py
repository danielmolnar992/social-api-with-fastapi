"""
Router to handle posts, comments, likes and image prompt.
"""

import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from social_api.database import comments_table, database, likes_table, posts_table
from social_api.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from social_api.models.user import User
from social_api.security import get_current_user
from social_api.tasks import generate_and_add_to_post


router = APIRouter()
logger = logging.getLogger(__name__)


# Select posts and counts their likes
select_post_and_likes = (
    sqlalchemy.select(
        posts_table, sqlalchemy.func.count(likes_table.c.id).label("likes")
    )
    .select_from(posts_table.outerjoin(likes_table))
    .group_by(posts_table.c.id)
)


async def find_post(post_id: int):
    """Finds a post by ID."""

    logger.info(f"Finding posts with id {post_id}")
    query = posts_table.select().where(posts_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: UserPostIn,  # Pydantic model -> expected as the body
    current_user: Annotated[User, Depends(get_current_user)],
    background_task: BackgroundTasks,
    request: Request,
    prompt: str = None,  # str -> expected in the query string arguments
):
    """Create a new post from user input and auto-incremented ID. Requires a
    logged in user (with the injected dependency of currenc_user)."""

    logger.info("Creating post")
    data = {**post.model_dump(), "user_id": current_user.id}

    query = posts_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)

    if prompt:
        background_task.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            request.url_for("get_post_with_comments", post_id=last_record_id),
            database,
            prompt,
        )

    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    """Post sorting logic. Because it is an Rnum and not a Pydantic model,
    FastAPI will know it is a query string parameter.
    I.e.: /post?sorting=most_likes"""

    NEW = "new"  # most recent first
    OLD = "old"  # least recent first
    MOST_LIKES = "most_likes"  # most liked first


@router.get("/post", response_model=list[UserPostWithLikes])
async def list_posts(sorting: PostSorting = PostSorting.NEW):
    """Lists all the saved posts."""

    logger.info("Getting all posts")

    if sorting == PostSorting.NEW:
        query = select_post_and_likes.order_by(posts_table.c.id.desc())
    elif sorting == PostSorting.OLD:
        query = select_post_and_likes.order_by(posts_table.c.id.asc())
    elif sorting == PostSorting.MOST_LIKES:
        query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    """Create a new post from user input and auto-incremented ID. Requires
    a logged in user (with the injected dependency of current_user)."""

    logger.info("Creating a comment")
    post = await find_post(comment.post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comments_table.insert().values(data)
    last_record_id = await database.execute(query)

    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    """Get all the comments for a given post."""

    logger.info("Getting comments on post")
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    """Get post with all it's comments."""

    logger.info("Getting post and its comments")
    query = select_post_and_likes.where(posts_table.c.id == post_id)
    logger.debug(query)

    post = await database.fetch_one(query)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=status.HTTP_201_CREATED)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    """Records a like to a post by an authenticated user."""

    logger.info("Creating a like")

    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    data = {**like.model_dump(), "user_id": current_user.id}
    query = likes_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)

    return {**data, "id": last_record_id}
