import os


class Config:
    """Base configuration with defaults shared by every environment."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    LOGIN_RATE_LIMIT = '5 per minute'
    RATELIMIT_STORAGE_URI = 'memory://'


class DevelopmentConfig(Config):
    """Configuration for running the app locally."""

    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key-change-me')

    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False


class TestingConfig(Config):
    """Configuration used by the automated test suite."""

    TESTING = True
    DEBUG = False
    SECRET_KEY = 'test-secret-key'

    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False
    WTF_CSRF_ENABLED = False

    LOGIN_RATE_LIMIT = '1000 per minute'


class ProductionConfig(Config):
    """Configuration for a deployed environment."""

    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config(config_name=None):
    """Look up a configuration class by environment name.

    Defaults to development when no name is given. Fails fast if production
    is selected without a SECRET_KEY in the environment, rather than letting
    the app start with a publicly-known default secret.
    """
    config_name = config_name or 'development'
    config_class = config_by_name.get(config_name, DevelopmentConfig)

    if config_class is ProductionConfig and not config_class.SECRET_KEY:
        raise RuntimeError(
            'SECRET_KEY environment variable must be set when FLASK_CONFIG=production.'
        )

    return config_class
