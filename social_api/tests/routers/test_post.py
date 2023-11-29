import pytest
from httpx import AsyncClient


async def create_post(body: str, async_client: AsyncClient) -> dict:
    """Creates a post with the given body."""

    response = await async_client.post('/post', json={'body': body})
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    """Fixture for a post created by the time the test runs."""

    return await create_post('Test post', async_client)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict):
    """Fixture for a comment created by the time the test runs. Also
    creates a post for it first."""

    response = await async_client.post(
        '/comment',
        json={'body': 'Test Comment', 'post_id': created_post['id']},
    )
    return response.json()


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    """Test post is created successfully."""

    body = 'Test Post'
    response = await async_client.post('/post', json={'body': body})

    assert response.status_code == 201
    assert {'id': 1, 'body': 'Test Post'}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_missing_data(async_client: AsyncClient):
    """Test post failed with missing body."""

    response = await async_client.post('/post', json={})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    """Test requesting all the posts successfully."""

    response = await async_client.get('/post')

    assert response.status_code == 200
    assert response.json() == [created_post]


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):

    body = 'Test Comment'

    response = await async_client.post(
        '/comment',
        json={'body': body, 'post_id': created_post['id']},
    )
    assert response.status_code == 201
    assert {
        'id': 1,
        'body': body,
        'post_id': created_post['id'],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f'/post/{created_post['id']}/comments')
    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f'/post/{created_post['id']}')
    assert response.status_code == 200
    assert response.json() == {
        'post': created_post,
        'comments': [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get('/post/2')
    assert response.status_code == 404
