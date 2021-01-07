"""Initialize Flask app."""
from os import path
from flask import Flask, render_template_string, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password, roles_required
from flask_security.models import fsqla_v2 as fsqla
from src.data_models import Config
from flask_jwt_extended import JWTManager
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_admin.menu import MenuLink
import logging
import sys

from src.admin_views.admin_views import MyAdminView, MyAuthView, MyLogoutView, LabelFormatView, CalculatedFieldView

# global config (meant to be read only besides the admin doing POST case) !!!

# Globally accessible libraries
config: Config = None

db = SQLAlchemy()
jwt = JWTManager()
admin = Admin(name='TRAn Admin', template_mode='bootstrap4')

def load_config(app: Flask):
    global config
    p = path.join(app.config["CONFIG_DIR"], app.config["CONFIG_FILE"])
    config = Config.parse_file(p)
    config.load_sub_files(app.config["CONFIG_DIR"])


def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('app_config.AppConfig')

    # Initialize Plugins
    db.init_app(app)
    jwt.init_app(app)
    admin.init_app(app)

    with app.app_context():
        handler = logging.StreamHandler(sys.stdout)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)

        _migrate = Migrate(app, db)  # ?? Create Database Models using db.create_all()

        # load local config
        load_config(app)

        # flask-security-too
        # Define models
        fsqla.FsModels.set_db_info(db)  # once 4.0 in place, this is how to change table names , user_table_name="fs_users", role_table_name="fs_roles"

        from src.db_models import Role, User, Driver, DriverChange, LabelGroup, LabelFormat, FieldScope, CalculatedField

        # Setup Flask-Security
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        security = Security(app, user_datastore, register_blueprint=True)





        # Import parts of our application
        from src.blueprints.api.api import api_bp
        from src.blueprints.security.routes import security_bp, flask_security_bp
        from src.blueprints.web.routes import web_bp

        # Register Blueprints
        # app.register_blueprint(security_bp, url_prefix='/security')
        #app.register_blueprint(flask_security_bp, url_prefix='/flask_security')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(web_bp)

        # configure flask-admin
        #admin.add_link(MenuLink(name='Login', url='/security/login', category='Login'))
        #admin.add_link(MenuLink(name='Logout', url='/security/logout', category='Login'))

        admin.add_view(MyAdminView(User, db.session, category="Access"))
        admin.add_view(MyAdminView(Role, db.session, category="Access"))
        admin.add_view(MyAdminView(Driver, db.session, category="Drivers"))
        admin.add_view(MyAdminView(DriverChange, db.session, category="Drivers"))
        admin.add_view(MyAdminView(FieldScope, db.session, category="Fields"))
        admin.add_view(CalculatedFieldView(CalculatedField, db.session, category="Fields"))
        admin.add_view(MyAdminView(LabelGroup, db.session, category="Labels"))
        admin.add_view(LabelFormatView(LabelFormat, db.session, category="Labels"))

        admin.add_view(MyLogoutView(name="Logout", endpoint="logout"))


        # Using the user_claims_loader, we can specify a method that will be
        # called when creating access tokens, and add these claims to the said
        # token. This method is passed the identity of who the token is being
        # created for, and must return data that is json serializable
        @jwt.user_claims_loader
        def add_claims_to_access_token(identity):
            return {
                'roles': ['admin', 'loser']
            }

        @security.context_processor
        def security_context_processor():
            return dict(
                admin_base_template=admin.base_template,
                admin_view=admin.index_view,
                h=admin_helpers,
                get_url=url_for
            )

        return app
