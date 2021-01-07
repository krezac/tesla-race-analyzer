from flask import Blueprint, jsonify, render_template, Response
import pendulum
from flask_jwt_extended import jwt_required

from src import config
from src.jwt_roles import jwt_ex_role_required

from src.data_processor.data_processor import get_car_status_formatted, get_car_status, describe_status_fields, get_car_laps

api_bp = Blueprint('api_bp', __name__,
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='/assets')


@api_bp.route('/car/status/raw')
# @jwt_ex_role_required('admin')  # @jwt_required
def get_status_raw():
    resp = get_car_status(pendulum.now(tz='utc'))
    return jsonify(resp._asdict())


@api_bp.route('/car/status')
def get_status():
    resp = get_car_status_formatted(pendulum.now(tz='utc'))
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/status/fields')
def get_status_fields():
    resp = describe_status_fields()
    return Response(resp.json(), mimetype='application/json')


@api_bp.route('/car/laps/raw')
# @jwt_ex_role_required('admin')  # @jwt_required
def get_laps_raw():
    resp = get_car_laps(config.car_id, pendulum.now(tz='utc'))
    return jsonify(resp)


@api_bp.route('/version')
def version():
    return Response(render_template("version.txt"), mimetype='application/json')

