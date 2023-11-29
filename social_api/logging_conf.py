"""
Logging configuration. Logs to console, rotating file in JSON format and
logtail (only in production). When in dev environment it logs from DEBUG,
otherwise only from INFO.
"""

import logging
from logging.config import dictConfig

from social_api.config import DevConfig, config


def obfuscated(email: str, unobfuscated_length: int) -> str:
    """Obfuscates the email based on the requested lenght with asterixes."""

    characters = email[:unobfuscated_length]
    first, last = email.split('@')

    return f'{characters}{'*' * (len(first) - unobfuscated_length)}@{last}'


class EmailObfuscationFilter(logging.Filter):
    """Obfuscates email addresses in log records."""

    def __init__(self, name: str = "", unobfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.unobfuscated_length = unobfuscated_length

    # If returns false, log record is filtered, when true, it is passed on
    def filter(self, record: logging.LogRecord) -> bool:
        """Checks if the record contains an email address."""

        if 'email' in record.__dict__:
            record.email = obfuscated(record.email, self.unobfuscated_length)

        return True


# Only log to Logtail, if environment is prod
handlers = ['default', 'rotating_file', 'logtail']
if config.ENV_STATE == 'prod':
    handlers.append('logtail')


def configure_logging() -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
                'correlation_id': {
                    '()': 'asgi_correlation_id.CorrelationIdFilter',
                    'uuid_length': 8 if isinstance(config, DevConfig) else 32,
                    'default_value': '-',
                },
                'email_obfuscation': {
                    '()': EmailObfuscationFilter,
                    'unobfuscated_length': 2 if isinstance(config, DevConfig) else 0,
                },
            },
            'formatters': {
                'console': {
                    'class': 'logging.Formatter',
                    'datefmt': '%Y-%m-%dT%H:%M:%S',
                    'format': '(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s'
                },
                'file': {
                    'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'datefmt': '%Y-%m-%dT%H:%M:%S',
                    'format': '%(asctime)s %(msecs)03d %(levelname)s %(correlation_id)s %(name)s %(lineno)d %(message)s',
                }
            },
            'handlers': {
                'default': {
                    'class': 'rich.logging.RichHandler',
                    'level': 'DEBUG',
                    'formatter': 'console',
                    'filters': ['correlation_id', 'email_obfuscation'],
                },
                'rotating_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'file',
                    'filename': 'social_api.log',
                    'maxBytes': 1024 * 1024,  # 1 MB
                    'backupCount': 2,
                    'encoding': 'utf8',
                    'filters': ['correlation_id', 'email_obfuscation'],
                },
                'logtail': {
                    'class': 'logtail.LogtailHandler',
                    'level': 'DEBUG',
                    'formatter': 'console',
                    'filters': ['correlation_id', 'email_obfuscation'],
                    'source_token': config.LOGTAIL_API_KEY
                }
            },
            'loggers': {
                'uvicorn': {'handlers': ['default', 'rotating_file'], 'level': 'INFO'},
                'social_api': {
                    'handlers': handlers,
                    # Only log from DEBUG level if in dev, otherwise from INFO
                    'level': 'DEBUG' if isinstance(config, DevConfig) else 'INFO',
                    'propagate': False
                },
                'databases': {'handlers': ['default'], 'level': 'WARNING'},
                'aiosqlite': {'handlers': ['default'], 'level': 'WARNING'},
            }
        }
    )
