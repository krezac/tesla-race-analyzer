"""Initialize Flask app."""
from os import path
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password, roles_required
from flask_security.models import fsqla_v2 as fsqla
from src.data_models import Config

import datetime

# global config (meant to be read only besides the admin doing POST case) !!!

# Globally accessible libraries
db = SQLAlchemy()
config: Config = None


def load_config(app: Flask):
    global config
    p = path.join(app.config["CONFIG_DIR"], app.config["CONFIG_FILE"])
    config = Config.parse_file(p)
    config.load_sub_files(app.config["CONFIG_DIR"])
    print(config)


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('app_config.AppConfig')

    # Initialize Plugins
    db.init_app(app)

    with app.app_context():
        _migrate = Migrate(app, db)  # ?? Create Database Models using db.create_all()

        # load local config
        load_config(app)

        # flask-security-too
        # Define models
        fsqla.FsModels.set_db_info(db)  # once 4.0 in place, this is how to change table names , user_table_name="fs_users", role_table_name="fs_roles"

        from src.db_models import Role, User, Driver, DriverChange

        # Setup Flask-Security
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        security = Security(app, user_datastore)

        # Import parts of our application
        from src.blueprints.api.api import api_bp
        from src.blueprints.auth.auth import auth_bp
        from src.blueprints.web.routes import web_bp

        # Register Blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(web_bp)

        return app
