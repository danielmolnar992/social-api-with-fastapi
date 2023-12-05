import logging

import httpx

from social_api.config import config


logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    """Custom exception for errors in Mailgun API call."""
    pass

async def send_simple_email(to: str, subject: str, body: str):
    """Send a simple emial with a subject and a body defined."""

    logger.debug(f'Sending email to {to[:3]} with subject {subject[:20]}')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f'https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages',
                auth=('api', config.MAILGUN_API_KEY),
                data={
                    'from': f'John Doe <mailgun@{config.MAILGUN_DOMAIN}>',
                    'to': [to],
                    'subject': subject,
                    'text': body
                }
            )
            response.raise_for_status()
            logger.debug(response.content)

        except httpx.HTTPStatusError as err:
            raise APIResponseError((
                f'API request failed with status code {err.response.status_code}.'
                f'{err.response.content.decode()}'
            )) from err

        return response


async def send_user_registration_email(email: str, confirmation_url: str):
    """Sends a precompile email for registration"""

    return await send_simple_email(
        email,
        'Successfully signed up',
        (
            f'Hi {email}! You have successfully signed up to the Social REST API.'
            ' Please confirm your email by clicking on the'
            f' following link: {confirmation_url}'
        ),
    )
