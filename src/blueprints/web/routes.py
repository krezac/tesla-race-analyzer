from flask import Blueprint, jsonify, render_template, redirect, url_for
from flask_login import current_user

from src import config

from flask_jwt_extended import create_access_token
# Blueprint Configuration
web_bp = Blueprint(
    'web_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@web_bp.route('/jwt_token', methods=['GET'])
def jwt_token():
    access_token = create_access_token(identity='test', expires_delta=False)  # TODO make the tokens expire in real life
    return jsonify(access_token=access_token), 200


@web_bp.route('/', methods=['GET'])
def index():
    return redirect(url_for(config.index_page))  # configurable


@web_bp.route('/login', methods=['GET'])
def login():
    return redirect(url_for("security.login"))


@web_bp.route('/logout', methods=['GET'])
def logout():
    return redirect(url_for("security.logout"))


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template("dashboard.html")


@web_bp.route('/map', methods=['GET'])
def map():
    return render_template("map.html")

