# Social API with FastAPI

An API with FastAPI to register users, create posts with comments, likes and AI generated images based on a prompt. Images can be uploaded to a cloud bucket.

This is a simple playground to play with FastAPI and other third party services.
- Python 3.12
- Logtail for production logging
- Sentry for crash reporting
- Environment management (dev, test, prod) within `.env` file with an environment selector value
- Pytest for testing
- Flake8 for linting
- Black and isort for formatting
- Async database management with SQLAlchemy and Databases. Libraries added for SQLite and PostgreSQL.
- Github Actions for continuous integrations
- Dev Container for development
- Mailgun for registration confirmation emails
- DeepAI to generate images for posts based on prompt text
- Google Cloud Storage to store uploaded images

## Endpoints

- Register a user and get a confirmation email: `POST /register`
- Login and get an access token: `POST /token`
- Email confirmation: `GET /confirm/{token}`
- Trigger email reconfirmation: `POST /reconfirm`
- Create a post (with optional prompt): `POST /post`
- Create a comment: `POST /comment`
- Like a post: `POST /like`
- Get a list of post with likes (with specified order): `GET /post`
- Get comments of a post: `GET /post/{post_id}/comments`
- Get post with it's comments: `GET /post/{post_id}`
- Upload files to storage bucket: `POST /upload`

Fast API documenation endpoint: `/docs`

## User data

Registration:
- username: must be unique
- email: must be unique (used in JWT `sub`)
- password

Login (with `OAuth2PasswordBearer`):
- username
- password

## Useful commands

Install packages from requirement files:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for development and testing
```

Run FastAPI with reload on code change
```bash
uvicorn social_api.main:app --reload
```

Run pytest
```bash
pytest -W ignore::DeprecationWarning && flake8
```