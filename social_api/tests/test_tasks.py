import httpx
import pytest

from social_api.tasks import APIResponseError, send_simple_email


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
