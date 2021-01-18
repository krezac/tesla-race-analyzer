"""Initialize Flask app."""
from os import path, getenv
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore, hash_password
from flask_security.models import fsqla_v2 as fsqla
from src.data_models import Configuration
from flask_jwt_extended import JWTManager
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
import logging
import sys
import requests
import pendulum
from apscheduler.schedulers.background import BackgroundScheduler


from src.parent_views import MyRedirectView, MyRoleRequiredDataView, MyRoleRequiredCustomView
from src.enums import CalculatedFieldScopeEnum, LabelFormatGroupEnum
from src.utils import function_timer_block

import logging
logger = logging.getLogger(__name__)

# global config (meant to be read only besides the admin doing POST case) !!!

scheduler = BackgroundScheduler()

db = SQLAlchemy()
jwt = JWTManager()
admin = Admin(name='TRAn Admin', template_mode='bootstrap4')

# Globally accessible libraries
configuration: Configuration = None

# note this is ugly hack to trigger background jobs as normal endpoints
# URLs set from app.config later
background_job_update_status_url: str = None
background_job_update_laps_url: str = None


def load_config(app: Flask):
    global configuration
    p = path.join(app.config["CONFIG_DIR"], app.config["CONFIG_FILE"])
    configuration = Configuration.parse_file(p)
    configuration.post_process()


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

        global background_job_update_laps_url, background_job_update_laps_url
        background_job_update_laps_url = app.config["BACKGROUND_JOB_BASE"] + '/update_status'
        background_job_update_laps_url = app.config["BACKGROUND_JOB_BASE"] + '/update_laps'

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

        admin.add_view(MyRedirectView(target_endpoint='web_bp.dashboard', name="Dashboard",
                                      endpoint="ui_dashboard", category="Go to UI"))
        admin.add_view(MyRedirectView(target_endpoint='web_bp.map', name="Map",
                                      endpoint="ui_map", category="Go to UI"))
        admin.add_view(MyRedirectView(target_endpoint='web_bp.laps', name="Laps",
                                      endpoint="ui_laps", category="Go to UI"))
        admin.add_view(MyRedirectView(target_endpoint='web_bp.time_machine', name="Time Machine",
                                      endpoint="ui_time_machine", category="Go to UI"))

        # TODO these are just placeholders
        admin.add_view(MyRoleRequiredDataView('operator', DriverChange, db.session, category="Operator", endpoint="aaa"))
        admin.add_view(MyRoleRequiredDataView('data', DriverChange, db.session, category="Data", endpoint="bbb"))


        from src.admin.admin_views import MyTestLabelFormatTestView, MyTestCalculatedFieldView
        admin.add_view(MyTestCalculatedFieldView('data', name="Calculated Field", endpoint="test_calculated_field",
                                                 category="Test custom"))
        admin.add_view(MyTestLabelFormatTestView('data', name="Formatted Label", endpoint="test_label_format",
                                                 category="Test custom"))

        # pages for built-in db editor
        admin.add_view(MyRoleRequiredDataView('admin', Driver, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', DriverChange, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', FieldScope, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', CalculatedField, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', LabelGroup, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', LabelFormat, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', User, db.session, category="DB Editor"))
        admin.add_view(MyRoleRequiredDataView('admin', Role, db.session, category="DB Editor"))


        admin.add_view(MyRedirectView(target_endpoint='security.login', name="Login",
                                      endpoint="sec_login", category="User"))
        admin.add_view(MyRedirectView(target_endpoint='security.change_password', name="Change password",
                                      endpoint="sec_change_password", category="User"))
        admin.add_view(MyRedirectView(target_endpoint='security.logout', name="Logout",
                                      endpoint="sec_logout", category="User"))

        # register background jobs
        def _update_car_status():
            from src import configuration
            if configuration.update_run_background and background_job_update_status_url:
                logger.info("Updating car status by background job")
                with function_timer_block('bg update status'):
                    resp = requests.get(background_job_update_status_url)
                    logger.info(f"{pendulum.now()}: {resp}")

        def _update_car_laps():
            from src import configuration
            if configuration.update_run_background and background_job_update_laps_url:
                logger.info("Updating car laps... by background job")
                with function_timer_block('bg update laps'):
                    resp = requests.get(background_job_update_laps_url)
                    logger.info(f"{pendulum.now()}: {resp}")

        scheduler.add_job(_update_car_status, 'interval', seconds=configuration.update_status_seconds)
        scheduler.add_job(_update_car_laps, 'interval', seconds=configuration.update_laps_seconds)
        scheduler.start()

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

        @app.before_first_request
        def before_first_request():
            # Create any database tables that don't exist yet.  (? remove on prod ?
            db.create_all()

            # Create the Roles "admin" and "end-user" -- unless they already exist
            user_datastore.find_or_create_role(name='admin', description='Administrator (change configuration)')
            user_datastore.find_or_create_role(name='data', description='Raw and historical data access')
            user_datastore.find_or_create_role(name='operator', description='Store info during race (driver changes)')

            admin_email = getenv('TRAN_ADMIN_EMAIL')
            admin_password = getenv('TRAN_ADMIN_PASSWORD')
            if admin_email and admin_password:
                print("***********************************************")
            if not user_datastore.find_user(email=admin_email):
                user_datastore.create_user(email=admin_email, password=hash_password(admin_password))
            # Commit any database changes; the User and Roles must exist before we can add a Role to the User
            db.session.commit()

            # Assign roles. Again, commit any database changes.
            user_datastore.add_role_to_user(admin_email, 'admin')
            user_datastore.add_role_to_user(admin_email, 'data')
            user_datastore.add_role_to_user(admin_email, 'operator')
            db.session.commit()

            # populate code tables
            # label groups
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.STATUS, 'Car Status')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.MAP, 'Car Status on map')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.TOTAL, 'Total')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.RECENT_LAP, 'Current Lap')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.PREVIOUS_LAPS, 'Previous Laps')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.FORECAST, 'Forecast')
            LabelGroup.add_if_not_exists(LabelFormatGroupEnum.CHARGING, 'Charging')

            # calculated field scopes
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.STATUS, 'Status')
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.POSITION, 'Position')
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.TOTAL, 'Total')
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.LAP, 'Lap')
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.FORECAST, 'Forecast')
            FieldScope.add_if_not_exists(CalculatedFieldScopeEnum.CHARGING, 'Charging')

            db.session.commit()

        return app
