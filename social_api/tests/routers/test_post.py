import pytest
from fastapi import status
from httpx import AsyncClient

from social_api import security


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    """Creates a post with the given body."""

    response = await async_client.post(
        '/post',
        json={'body': body},
        headers={'Authorization': f'Bearer {logged_in_token}'}
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    """Creates a comment with the given body and post ID. Requires a post
    to be present."""

    response = await async_client.post(
        '/comment',
        json={'body': body, 'post_id': post_id},
        headers={'Authorization': f'Bearer {logged_in_token}'}
    )
    return response.json()


async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    """Likes a post. Requires the post to be present."""

    response = await async_client.post(
        '/like',
        json={'post_id': post_id},
        headers={'Authorization': f'Bearer {logged_in_token}'}
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    """Fixture for a post created by the time the test runs."""

    return await create_post('Test post', async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Fixture for a comment created by the time the test runs. Also
    creates a post for it first."""

    return await create_comment(
        'Test Comment', created_post['id'], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, registered_user: dict, logged_in_token: str
):
    """Test post is created successfully."""

    body = 'Test Post'
    response = await async_client.post(
        '/post',
        json={'body': body},
        headers={'Authorization': f'Bearer {logged_in_token}'},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        'id': 1,
        'body': 'Test Post',
        'user_id': registered_user['id']
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    """Tests if expied token returns 401 when trying to post. Patched token
    expiration ensures the token is expored by the time test uses it."""

    mocker.patch('social_api.security.access_token_expire_minutes', return_value=-1)
    token = security.create_access_token(registered_user['email'])

    response = await async_client.post(
        '/post',
        json={'body': 'Test Post'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'Token has expired' in response.json()['detail']


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    """Test post failed with missing body."""

    response = await async_client.post(
        '/post',
        json={},
        headers={'Authorization': f'Bearer {logged_in_token}'},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Tests if liking the post successfully"""

    response = await async_client.post(
        '/like',
        json={'post_id': created_post['id']},
        headers={'Authorization': f'Bearer {logged_in_token}'},
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    """Test requesting all the posts successfully."""

    response = await async_client.get('/post')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{**created_post, 'likes': 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    'sorting, expected_order',
    [
        ('new', [2, 1]),
        ('old', [1, 2]),
        ('most_likes', [2, 1]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    """Tests retrieving all posts by sorting orders."""

    await create_post('Test Post 1', async_client, logged_in_token)
    await create_post('Test Post 2', async_client, logged_in_token)
    await like_post(2, async_client, logged_in_token)

    response = await async_client.get('/post', params={'sorting': sorting})
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert [post['id'] for post in data] == expected_order


@pytest.mark.anyio
async def test_get_all_post_wrong_sorting(async_client: AsyncClient):
    """Tests retrieving all posts by a non existing sorting order."""

    response = await async_client.get('/post', params={'sorting': 'wrong'})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient, created_post: dict, registered_user: dict, logged_in_token: str
):
    """Tests successful comment creation."""

    body = 'Test Comment'

    response = await async_client.post(
        '/comment',
        json={'body': body, 'post_id': created_post['id']},
        headers={'Authorization': f'Bearer {logged_in_token}'},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        'id': 1,
        'body': body,
        'post_id': created_post['id'],
        'user_id': registered_user['id']
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Tests successfully retrieving comments on post."""

    response = await async_client.get(f'/post/{created_post['id']}/comments')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient, created_post: dict
):
    """Tests successfully retrieving comments on empty post successfully."""

    response = await async_client.get(f'/post/{created_post['id']}/comments')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []



@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Tests retrieving post with its comment successfully."""

    response = await async_client.get(f'/post/{created_post['id']}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'post': {**created_post, 'likes': 0},
        'comments': [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Tests if retrieving missing post returns HTTP 404."""

    response = await async_client.get('/post/2')
    assert response.status_code == status.HTTP_404_NOT_FOUND
