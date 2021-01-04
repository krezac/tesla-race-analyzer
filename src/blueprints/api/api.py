from flask import Blueprint, jsonify, render_template
import pendulum

from src.data_processor.data_processor import get_car_status_formatted

api_bp = Blueprint('api_bp', __name__,
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='/assets')


@api_bp.route('/')
def index():
    resp = get_car_status_formatted(2, pendulum.now(tz='utc'))
    return resp.json()

@api_bp.route('/version')
def version():
    return render_template("version.txt")

