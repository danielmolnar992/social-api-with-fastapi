import logging
from contextlib import asynccontextmanager

import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler

from social_api.config import config
from social_api.database import database
from social_api.logging_conf import configure_logging
from social_api.routers.post import router as post_router


sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles connection to the database. Will leave the connection open
    until the app is shut down. Also sets up the custom root logger."""

    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(post_router)


@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request: Request, exc: HTTPException):
    """Adds unified logging to HTTP exception handler."""

    logger.error(f'HTTPException: {exc.status_code} {exc.detail}')
    return await http_exception_handler(request, exc)


@app.get('/sentry-debug')
async def trigger_error():
    """Trigger an error to test Sentry."""

    return 1 / 0
