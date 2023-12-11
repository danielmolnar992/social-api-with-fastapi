"""
Communication with the selected storage bucket provider.
Currently this is GCS.
"""

import logging
from functools import lru_cache

from google.cloud import storage

from social_api.config import config


logger = logging.getLogger(__name__)


@lru_cache()
def client_authentication():
    """Authenticate the service account. Not expected to change during
    runtime, thus the value is cached."""

    logger.debug("Authorizing Service Account to GCP GCS")
    client = storage.Client.from_service_account_json(config.GCP_SA_KEY_PATH)

    return client


@lru_cache()
def get_storage_bucket(client: storage.Client):
    """Returns the storage bucket. Not expected to change during runtime,
    thus the value is cached. In a more complex setup, this should contain
    the logic which bucket to return."""

    return client.bucket(config.GCP_BUCKET_NAME)


def upload_file_to_bucket(local_file: str, file_name: str):
    """Uploads file from given path with given name to the pre-set bucket.
    Returns the URL of the file object."""

    client = client_authentication()
    bucket = get_storage_bucket(client)

    logger.debug(f"Uploading {local_file} to GCS as {file_name}")
    blob = bucket.blob(file_name)
    blob.upload_from_filename(local_file)

    download_url = blob.public_url
    logger.debug(f"Uploaded {local_file} and got download URL: {download_url}")

    return download_url


def close_bucket_client():
    """Closes the storage bucket client."""

    logger.debug("Closing transport to GCS.")
    client = client_authentication()
    client.close()
