"""
Tests for the post router.
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockerFixture

from social_api import security
from social_api.tests.helpers import create_comment, create_post, like_post


@pytest.fixture()
def mock_generate_cute_creature_api(mocker: MockerFixture):
    """Mocks the creation of image for the post."""

    return mocker.patch(
        "social_api.tasks._generate_cute_creature_api",
        return_value={"output_url": "http://example.net/image.jpg"},
    )


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    """Fixture for a post created by the time the test runs."""

    return await create_post("Test post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Fixture for a comment created by the time the test runs. Also
    creates a post for it first."""

    return await create_comment(
        "Test Comment", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    """Test post is created successfully."""

    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": "Test Post",
        "user_id": confirmed_user["id"],
        "image_url": None,
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker: MockerFixture
):
    """Test if expied token returns 401 when trying to post. Patched token
    expiration ensures the token is expored by the time test uses it."""

    mocker.patch("social_api.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user["email"])

    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    """Test post failed with missing body."""

    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_post_with_prompt(
    async_client: AsyncClient, logged_in_token: str, mock_generate_cute_creature_api
):
    """Test create post with prompt successfully."""

    response = await async_client.post(
        "/post?prompt=A cat",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "body": "Test Post",
        "image_url": None,
    }.items() <= response.json().items()
    mock_generate_cute_creature_api.assert_called()


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Test if liking the post successfully"""

    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    """Test requesting all the posts successfully."""

    response = await async_client.get("/post")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
        ("most_likes", [2, 1]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    """Test retrieving all posts by sorting orders."""

    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)
    await like_post(2, async_client, logged_in_token)

    response = await async_client.get("/post", params={"sorting": sorting})
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert [post["id"] for post in data] == expected_order


@pytest.mark.anyio
async def test_get_all_post_wrong_sorting(async_client: AsyncClient):
    """Test retrieving all posts by a non existing sorting order."""

    response = await async_client.get("/post", params={"sorting": "wrong"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str,
):
    """Test successful comment creation."""

    body = "Test Comment"

    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Test successfully retrieving comments on post."""

    response = await async_client.get(f"/post/{created_post['id']}/comments")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient, created_post: dict
):
    """Test successfully retrieving comments on empty post successfully."""

    response = await async_client.get(f"/post/{created_post['id']}/comments")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Test retrieving post with its comment successfully."""

    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Test if retrieving missing post returns HTTP 404."""

    response = await async_client.get("/post/2")
    assert response.status_code == status.HTTP_404_NOT_FOUND
