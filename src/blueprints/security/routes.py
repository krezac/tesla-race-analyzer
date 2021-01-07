from flask import Blueprint, redirect, render_template, flash, request, session, url_for

security_bp = Blueprint('security', __name__, template_folder='templates')

# if you want to be able to load templates from flask_security, then you'll need a second (there can only be one template folder per blueprint):
flask_security_bp = Blueprint('flask_security', 'flask_security', template_folder='templates')



