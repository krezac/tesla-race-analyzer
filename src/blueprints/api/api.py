from flask import Blueprint, jsonify, render_template, Response
import pendulum

from src import config

from src.data_processor.data_processor import get_car_status_formatted

api_bp = Blueprint('api_bp', __name__,
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='/assets')


@api_bp.route('/car/<car_id>/status')
def index(car_id):
    resp = get_car_status_formatted(car_id, pendulum.now(tz='utc'))
    return resp.json()


@api_bp.route('/version')
def version():
    return Response(render_template("version.txt"), mimetype='application/json')

