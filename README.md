# Social API with FastAPI

Add post, comments to post and get list of post and comments. This is a simple playground to play with FastAPI and other third party services.
- Logtail (for production only)
- Sentry
- Environment management (dev, test, prod) (within `.env` file with an environment selector value)
- Pytest
- Async database management with SQLAlchemy and Databases. Libraries added for SQLite and PostgreSQL.

## Useful commands

Run FastAPI with reload on code change
```bash
uvicorn social_api.main:app --reload
```

Run pytest
```bash
pytest
```