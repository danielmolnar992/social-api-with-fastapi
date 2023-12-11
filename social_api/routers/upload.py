"""
Router to handle file uploads.
Flow:
    1. Clinet uploads the file -> Temp file on server
    2. File is uploaded to storage -> Temp file is deleted.
"""

import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status

from social_api.libs.bucket import upload_file_to_bucket


logger = logging.getLogger(__name__)
router = APIRouter()
CHUNK_SIZE = 1024 * 1024  # 1MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    """Uploads a file to the storage in chunks and returns the URL."""

    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info(f"Saving uploaded file temporarly to {filename}")

            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = upload_file_to_bucket(
                local_file=filename, file_name=file.filename
            )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )

    return {"detail": f"Successfully uploaded {file.filename}", "file_url": file_url}
