from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Points Pydantic to the env file."""

    ENV_STATE: Optional[str] = None
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


class GlobalConfig(BaseConfig):
    """Define variables collected from env file. It will strip the prefix
    and use the rest to identify the values."""

    DATABASE_URL: str
    DB_FORCE_ROLL_BACK: bool = False
    LOGTAIL_API_KEY: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    SECRET_KEY: Optional[str] = None


class DevConfig(GlobalConfig):
    """Config used for development."""

    model_config = SettingsConfigDict(env_prefix='DEV_', extra='ignore')


class ProdConfig(GlobalConfig):
    """Config used for production."""

    model_config = SettingsConfigDict(env_prefix='PROD_', extra='ignore')


class TestConfig(GlobalConfig):
    """Config used for testing. As test setup should always be the same
    for everyone, the variables are explicitly set here. By adding them
    explicitly to the .env file, you can override them. These are default
    values."""

    DATABASE_URL: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True

    model_config = SettingsConfigDict(env_prefix='TEST_', extra='ignore')


@lru_cache()
def get_config(env_state: str) -> GlobalConfig:
    """Activate the set environment base on env_state value. Value is cached
    since no need to create a new config with every run and also for playing
    with the cache."""

    configs = {
        'dev': DevConfig,
        'prod': ProdConfig,
        'test': TestConfig
    }

    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
