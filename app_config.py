"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class AppConfig:
    """ application specific values """
    CONFIG_DIR = 'etc'
    CONFIG_FILE = 'config.json'
    BACKGROUND_JOB_BASE = environ.get("TRAN_BACKGROUND_JOB_BASE", 'http://127.0.0.1:80/api/_internal')

    """Set Flask config variables."""

    FLASK_APP = 'tran.py'
    FLASK_ENV = 'development'
    TESTING = True
    # Generate a nice key using secrets.token_urlsafe()
    SECRET_KEY = environ.get("SECRET_KEY", 'test_key')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    DEBUG = True

    # Database
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{environ.get('TRAN_DB_USER')}:{environ.get('TRAN_DB_PASS')}@{environ.get('TRAN_DB_HOST')}:{environ.get('TRAN_DB_PORT', 5432)}/{environ.get('TRAN_DB_NAME')}"
    SQLALCHEMY_BINDS = {
        "teslamate": f"postgresql+psycopg2://{environ.get('TM_DB_USER')}:{environ.get('TM_DB_PASS')}@{environ.get('TM_DB_HOST')}:{environ.get('TM_DB_PORT', 5432)}/{environ.get('TM_DB_NAME')}"
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # As of Flask-SQLAlchemy 2.4.0 it is easy to pass in options directly to the
    # underlying engine. This option makes sure that DB connections from the
    # pool are still valid. Important for entire application since
    # many DBaaS options automatically close idle connections.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Flask-Security-Too settings

    # Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
    # Generate a good salt using: secrets.SystemRandom().getrandbits(128)
    SECURITY_PASSWORD_SALT = environ.get("SECURITY_PASSWORD_SALT", '245566430388240650680293166088556633912')

    # Specifies the URL prefix for the Flask-Security blueprint.
    SECURITY_URL_PREFIX = '/security'

    # Specifies if Flask-Security should create a user registration endpoint. (creates /register endpoint)
    # TODO remember to disable on prod once users are configured
    SECURITY_REGISTERABLE = environ.get("SECURITY_REGISTERABLE", False)

    # allow change password (/change)
    SECURITY_CHANGEABLE = environ.get("SECURITY_CHANGEABLE", False)

    SECURITY_POST_LOGIN_VIEW = '../admin/'

    # Specifies whether registration email is sent.
    SECURITY_SEND_REGISTER_EMAIL = False

    # Flask-admin
    # set optional bootswatch theme
    FLASK_ADMIN_SWATCH = 'cerulean'
