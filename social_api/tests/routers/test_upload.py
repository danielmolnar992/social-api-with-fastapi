"""
Tests for the upload router.
"""

import contextlib
import os
import pathlib
import tempfile

import pytest
from fastapi import status
from httpx import AsyncClient
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture


@pytest.fixture()
def sample_image(fs: FakeFilesystem) -> pathlib.Path:
    """Add a sample image to the fake filesystem"""

    path = (pathlib.Path(__file__).parent / 'assets' / 'myfile.png').resolve()
    fs.create_file(path)

    return path


@pytest.fixture(autouse=True)
def mock_upload_file_to_bucket(mocker: MockerFixture):
    """Mock the upload_file_to_bucket function so that it returns a fake URL.
    Applied automatically."""

    return mocker.patch(
        'social_api.routers.upload.upload_file_to_bucket',
        return_value='https://fakeurl.com'
    )


# Mock the aiofiles.open function so that it
# returns a fake file object from the fake filesystem
@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker: MockerFixture, fs: FakeFilesystem):
    """Mock the aiofiles.open function so that it returns a fake file object
    from the fake filesystem. The built-in 'open' is patched by pyfakedfs
    already."""

    mock_open = mocker.patch("aiofiles.open")

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = 'r'):

        out_fs_mock = mocker.AsyncMock(name=f'async_file_open:{fname!r}/{mode!r}')
        with open(fname, mode) as fin:
            out_fs_mock.read.side_effect = fin.read
            out_fs_mock.write.side_effect = fin.write

            yield out_fs_mock

    mock_open.side_effect = async_file_open

    return mock_open


async def call_upload_endpoint(
    async_client: AsyncClient, token: str, sample_image: pathlib.Path
):
    """Sends a request to the /upload endpoint with a token and sample
    image."""

    return await async_client.post(
        '/upload',
        files={'file': open(sample_image, 'rb')},
        headers={'Authorization': f'Bearer {token}'}
    )


@pytest.mark.anyio
async def test_upload_image(
    async_client: AsyncClient, logged_in_token: str, sample_image: pathlib.Path
):
    """Test file is uploaded successfully."""

    response = await call_upload_endpoint(async_client, logged_in_token, sample_image)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['file_url'] == 'https://fakeurl.com'


@pytest.mark.anyio
async def test_temp_file_removed_after_upload(
    async_client: AsyncClient,
    logged_in_token: str,
    sample_image: pathlib.Path,
    mocker: MockerFixture
):
    """Test if the temp file is deleted after upload finished."""

    # Spy on the NamedTemporaryFile function
    named_temp_file_spy = mocker.spy(tempfile, 'NamedTemporaryFile')

    response = await call_upload_endpoint(async_client, logged_in_token, sample_image)
    assert response.status_code == status.HTTP_201_CREATED

    # Get the filename of the temporary file created by the upload endpoint
    created_temp_file = named_temp_file_spy.spy_return

    # Check if the temp_file is removed after the file is uploaded
    assert not os.path.exists(created_temp_file.name)
