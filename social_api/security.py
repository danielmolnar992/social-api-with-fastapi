import logging

from social_api.database import database, users_table


logger = logging.getLogger(__name__)


async def get_user(email: str):
    """Returns the user if exists, else None."""

    logger.debug('Fetching user from database', extra={'email': email})
    query = users_table.select().where(users_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        return result
