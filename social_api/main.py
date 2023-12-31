"""
Defines the FastAPI app and it's routers.
"""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler

from social_api.config import config
from social_api.database import database
from social_api.libs.bucket import client_authentication, close_bucket_client
from social_api.logging_conf import configure_logging
from social_api.routers.post import router as post_router
from social_api.routers.upload import router as upload_router
from social_api.routers.user import router as user_router


logger = logging.getLogger(__name__)

# Only enable Sentry if DSN is present in env/config
if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN, traces_sample_rate=1.0, profiles_sample_rate=1.0
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles connection to the database. Will leave the connection open
    until the app is shut down. Also sets up the custom root logger."""

    configure_logging()
    client_authentication()
    await database.connect()
    yield
    await database.disconnect()
    close_bucket_client()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(post_router)
app.include_router(upload_router)
app.include_router(user_router)


@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request: Request, exc: HTTPException):
    """Adds unified logging to HTTP exception handler."""

    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)


@app.get("/sentry-debug")
async def trigger_error():
    """Trigger an error to test Sentry."""

    return 1 / 0
