import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from social_api.database import comments_table, database, posts_table
from social_api.models.post import (Comment, CommentIn, UserPost, UserPostIn,
                                    UserPostWithComments)
from social_api.security import get_current_user


router = APIRouter()
logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    """Finds a post by ID."""

    logger.info(f'Finding posts with id {post_id}')
    query = posts_table.select().where(posts_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post('/post', response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: UserPostIn, current_user: Annotated[str, Depends(get_current_user)]
):
    """Create a new post from user input and auto-incremented ID. Requires a
    logged in user (with the injected dependency of currenc_user)."""

    logger.info('Creating post')
    data = {**post.model_dump(), 'user_id': current_user.id}

    query = posts_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)

    return {**data, 'id': last_record_id}


@router.get('/post', response_model=list[UserPost])
async def list_posts():
    """Lists all the saved posts."""

    logger.info('Getting all posts')
    query = posts_table.select()
    logger.debug(query)

    return await database.fetch_all(query)


@router.post('/comment', response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentIn, current_user: Annotated[str, Depends(get_current_user)]
):
    """Create a new post from user input and auto-incremented ID. Requires
    a logged in user (with the injected dependency of current_user)."""

    logger.info('Creating a comment')
    post = await find_post(comment.post_id)

    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    data = {**comment.model_dump(), 'user_id': current_user.id}
    query = comments_table.insert().values(data)
    last_record_id = await database.execute(query)

    return {**data, 'id': last_record_id}


@router.get('/post/{post_id}/comments', response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    """Get all the comments for a given post."""

    logger.info('Getting comments on post')
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    logger.debug(query)

    return await database.fetch_all(query)


@router.get('/post/{post_id}', response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    """Get post with all it's comments."""

    logger.info('Getting post and its comments')
    post = await find_post(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Post not found'
        )

    return {
        'post': post,
        'comments': await get_comments_on_post(post_id),
    }
