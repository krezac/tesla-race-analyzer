from flask import Blueprint, redirect, render_template, flash, request, session, url_for
from flask_login import login_required, logout_user, current_user, login_user
from .forms import LoginForm, SignupForm
from src.db_models import db, User

auth_bp = Blueprint('auth_bp', __name__,
                          template_folder='templates',
                          static_folder='static', static_url_path='/assets')


