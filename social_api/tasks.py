"""
Tasks to send emails and generate images with DeepAI. They are used in
background tasks to reduce response time of the API.
"""

import logging
from json import JSONDecodeError

import httpx
from databases import Database

from social_api.config import config
from social_api.database import posts_table


logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    """Custom exception for errors in Mailgun API call."""

    pass


async def send_simple_email(to: str, subject: str, body: str):
    """Send a simple emial with a subject and a body defined."""

    logger.debug(f"Sending email to {to[:3]} with subject {subject[:20]}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"John Doe <mailgun@{config.MAILGUN_DOMAIN}>",
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug(f"Email OK ({subject}): {response.content.decode()}")

        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                (
                    f"API request failed with status code {err.response.status_code}."
                    f"{err.response.content.decode()}"
                )
            ) from err

        return response


async def send_user_registration_email(username: str, email: str, confirmation_url: str):
    """Sends a precompile email for registration"""

    return await send_simple_email(
        email,
        "Successfully signed up",
        (
            f"Hi {username}!\n\n"
            "You have successfully signed up to the Social REST API.\n"
            "Please confirm your email by clicking on the following link:\n"
            f"{confirmation_url}"
        ),
    )


async def _generate_cute_creature_api(prompt: str):
    """Calls the DeepAI API to return a URL from th cute-creature-generator
    endpoint based on the given prompt."""

    logger.debug(f"Generating cute creature ({prompt})")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.deepai.org/api/cute-creature-generator",
                data={"text": prompt},
                headers={"api-key": config.DEEPAI_API_KEY},
                timeout=60,
            )
            logger.debug(response)
            response.raise_for_status()
            response_data = response.json()

        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                f"API request failed with status code: {err.response.status_code}"
            ) from err
        except (JSONDecodeError, TypeError) as err:
            raise APIResponseError("API response parsing failed.") from err

        return response_data


async def generate_and_add_to_post(
    username: str, email: str, post_id: int, post_url: str, database: Database, prompt: str
):
    """Generates an image to the post and sends an email to the usre with
    the URL."""

    try:
        response_data = await _generate_cute_creature_api(prompt)
    except APIResponseError:
        return await send_simple_email(
            to=email,
            subject="Error Generating Image",
            body=(
                f"Hi {username}!\n\n",
                "Unfortunately there was an error while generating your image.",
            ),
        )

    logger.debug("Connecting to database to update post")
    query = (
        posts_table.update()
        .where(posts_table.c.id == post_id)
        .values(image_url=response_data["output_url"])
    )
    await database.execute(query)
    logger.debug("Database connection closed")

    await send_simple_email(
        to=email,
        subject="Image Generation Completed",
        body=(
            f"Hi {username}!\n\n"
            "Your image has been generated and added to your post.\n\n"
            "Please click on the following link to view it:\n"
            f"{post_url}\n\n"
            "Here is the image generated for the post:\n"
            f"{response_data['output_url']}"
        ),
    )

    return response_data
