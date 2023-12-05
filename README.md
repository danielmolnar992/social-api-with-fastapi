# Social API with FastAPI

Add post, comments to their posts and query them.

This is a simple playground to play with FastAPI and other third party services.
- Python 3.12
- Logtail for production logging
- Sentry for crash reporting
- Environment management (dev, test, prod) within `.env` file with an environment selector value
- Pytest for testing
- Flake8 for linting
- Async database management with SQLAlchemy and Databases. Libraries added for SQLite and PostgreSQL.
- Github Actions for continuous integrations
- Dev Container for development
- Mailgun for registration confirmation emails

## Endpoints

- Register a user and get a confirmation email: `POST /register`
- Login and get an access token: `POST /token`
- Email confirmation: `GET /confirm/{token}`
- Create a post: `POST /post`
- Create a comment: `POST /comment`
- Like a post: `POST /like`
- Get a list of post with likes (with specified order): `GET /post`
- Get comments of a post: `GET /post/{post_id}/comments`
- Get post with it's comments: `GET /post/{post_id}`

## Useful commands

Run FastAPI with reload on code change
```bash
uvicorn social_api.main:app --reload
```

Run pytest
```bash
pytest
```