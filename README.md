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

## Useful commands

Run FastAPI with reload on code change
```bash
uvicorn social_api.main:app --reload
```

Run pytest
```bash
pytest
```