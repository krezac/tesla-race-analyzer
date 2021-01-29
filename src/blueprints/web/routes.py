from flask import Blueprint, jsonify, render_template, render_template_string, redirect, url_for, request, abort
from flask_login import current_user
import pendulum
from datetime import timezone
from dateutil import tz
from src import configuration

from flask_jwt_extended import create_access_token
# Blueprint Configuration
web_bp = Blueprint(
    'web_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


def _get_admin_ui_url():
    return url_for("admin.index") if current_user.is_active and current_user.is_authenticated else None


@web_bp.route('/jwt_token', methods=['GET'])
def jwt_token():
    access_token = create_access_token(identity='test', expires_delta=False)  # TODO make the tokens expire in real life
    return jsonify(access_token=access_token), 200


@web_bp.route('/', methods=['GET'])
def index():
    if current_user.is_active and current_user.is_authenticated and current_user.has_role('admin'):
        return redirect(url_for(configuration.admin_index_page))
    else:
        return redirect(url_for(configuration.anonymous_index_page))


@web_bp.route('/login', methods=['GET'])
def login():
    return redirect(url_for("security.login"))


@web_bp.route('/logout', methods=['GET'])
def logout():
    return redirect(url_for("security.logout"))


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template("dashboard.html",
                           configuration=configuration,
                           get_status_url=url_for("api_bp.get_status"),
                           get_laps_url=url_for("api_bp.get_laps"),
                           get_chargings_url=url_for("api_bp.get_chargings"),
                           admin_ui_url=_get_admin_ui_url())


@web_bp.route('/map', methods=['GET'])
def map():
    return render_template("map.html", get_status_url=url_for("api_bp.get_status"))


@web_bp.route('/laps', methods=['GET'])
def laps():
    return render_template("laps.html",
                           configuration=configuration,
                           get_status_url=url_for("api_bp.get_status"),
                           get_laps_url=url_for("api_bp.get_laps"),
                           get_chargings_url=url_for("api_bp.get_chargings"),
                           admin_ui_url=_get_admin_ui_url())


@web_bp.route('/charts', methods=['GET'])
def charts():
    return render_template("charts.html")


@web_bp.route('/custom/<page_name>', methods=['GET'])
def get_custom_page(page_name):
    from src.db_models import CustomPage
    page = CustomPage.query.filter_by(name=page_name).first()
    if not page:
        abort(404)

    return render_template_string(page.template)  # TODO add all useful variables


@web_bp.route('/custom', methods=['GET'])
def get_custom_page_param():
    page_name = request.args.get('page')
    return get_custom_page(page_name)





@web_bp.route('/time_machine', methods=['GET', 'POST'])
def time_machine():
    """
    this is to display specific point of time
    :return:
    """
    from src.blueprints.web.web_forms import StaticDashboardForm
    from src.data_processor.data_processor import data_processor
    form = StaticDashboardForm()

    dt_end = configuration.start_time.add(hours=configuration.hours)
    dt_now = pendulum.now(tz='utc')
    dt = dt_now if dt_now < dt_end else dt_end  # if analyzing after race end, initialize at end of interval

    if form.dt.data:
        dt = pendulum.from_timestamp(form.dt.data.timestamp()).in_tz('utc')

    if form.validate_on_submit():
        offset_seconds = 0
        # find the button used. It's bit stupid as we need to find the one with value true
        if form.go_to_time.data:
            pass  # keep the date as is
        elif form.go_to_start.data:
            dt = configuration.start_time
        elif form.go_to_minus_10_hours.data:
            offset_seconds = -36000
        elif form.go_to_minus_1_hour.data:
            offset_seconds = -3600
        elif form.go_to_minus_10_minutes.data:
            offset_seconds = -600
        elif form.go_to_minus_1_minute.data:
            offset_seconds = -60
        elif form.go_to_minus_10_seconds.data:
            offset_seconds = -10
        elif form.go_to_minus_1_second.data:
            offset_seconds = -1
        elif form.go_to_plus_1_second.data:
            offset_seconds = 1
        elif form.go_to_plus_10_seconds.data:
            offset_seconds = 10
        elif form.go_to_plus_1_minute.data:
            offset_seconds = 60
        elif form.go_to_plus_10_minutes.data:
            offset_seconds = 600
        elif form.go_to_plus_1_hour.data:
            offset_seconds = 3600
        elif form.go_to_plus_10_hours.data:
            offset_seconds = 36000
        elif form.go_to_end.data:
            dt = configuration.start_time.add(hours=configuration.hours)

        if offset_seconds:
            dt = dt.add(seconds=offset_seconds)

    if dt < configuration.start_time:  # just for sure
        dt = configuration.start_time

    snapshot = data_processor.get_static_snapshot(dt)
    if not form.dt.data or (snapshot.car_positions_raw and dt > dt_end):
        form.dt.raw_data = None
        form.dt.data = dt_end.in_tz('local') if snapshot.car_positions_raw else dt.in_tz('local')
    else:
        form.dt.raw_data = None
        form.dt.data = dt.in_tz('local')

    return render_template('time_machine.html', form=form, snapshot=snapshot, configuration=configuration,
                           map_labels=snapshot.current_status_formatted.mapLabels.dict(),
                           status_labels=snapshot.current_status_formatted.statusLabels.dict(),
                           total_labels=snapshot.current_status_formatted.totalLabels.dict(),
                           forecast_labels=snapshot.forecast_formatted.dict(),
                           recent_lap=snapshot.lap_list_formatted.recent.dict() if snapshot.lap_list_formatted.recent else None,
                           previous_laps=snapshot.lap_list_formatted.previous.dict(),
                           charging_processes=snapshot.charging_process_list_formatted.dict(),
                           post_url=url_for('web_bp.time_machine'),
                           admin_ui_url=_get_admin_ui_url())
