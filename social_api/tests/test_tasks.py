import httpx
import pytest
from databases import Database
from fastapi import status

from social_api.database import posts_table
from social_api.tasks import (APIResponseError, _generate_cute_creature_api,
                              generate_and_add_to_post, send_simple_email)


@pytest.mark.anyio
async def test_send_simple_message(mock_httpx_client):
    """Test client's post method was called successfully."""

    await send_simple_email("test@example.net", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_message_api_error(mock_httpx_client):
    """Test 500 response raises and APIResponseError."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError, match="API request failed with status code"):
        await send_simple_email("test@example.com", "Test Subject", "Test Body")


@pytest.mark.anyio
async def test_generate_cute_creature_api_success(mock_httpx_client):
    """Test successfully call to genearate an image."""

    json_data = {'output_url': 'https://example.com/image.jpg'}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        json=json_data,
        request=httpx.Request('POST', '//')
    )

    result = await _generate_cute_creature_api('A cat')

    assert result == json_data


@pytest.mark.anyio
async def test_generate_cute_creature_api_server_error(mock_httpx_client):
    """Test unsuccessfull image generation with HTTP 500."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content='',
        request=httpx.Request('POST', '//')
    )

    with pytest.raises(
        APIResponseError, match='API request failed with status code: 500'
    ):
        await _generate_cute_creature_api('A cat')


@pytest.mark.anyio
async def test_generate_cute_creature_api_json_error(mock_httpx_client):
    """Test unsuccessfull image generation with non JSON response."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        content='Not JSON',
        request=httpx.Request('POST', '//')
    )

    with pytest.raises(APIResponseError, match='API response parsing failed'):
        await _generate_cute_creature_api('A cat')


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    mock_httpx_client, created_post: dict, confirmed_user: dict, db: Database
):
    """Test successfully saving image to post."""

    json_data = {'output_url': 'https://example.com/image.jpg'}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        json=json_data,
        request=httpx.Request('POST', '//')
    )

    await generate_and_add_to_post(
        confirmed_user['email'], created_post['id'], '/post/1', db, 'A cat'
    )

    # Check that the post has been updated
    query = posts_table.select().where(posts_table.c.id == created_post['id'])
    updated_post = await db.fetch_one(query)

    assert updated_post.image_url == json_data['output_url']
