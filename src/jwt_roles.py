from functools import wraps

from flask import jsonify, abort, Response
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_claims
)


def ensure_jwt_has_user_role(role):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if 'roles' not in claims or role not in claims['roles']:
        abort(403, f"'{role}' role needed")


def jwt_ex_role_required(role):
    def _inner_jwt_ex_role_required(fn):  # this way is needed to pass a param
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ensure_jwt_has_user_role(role)
            return fn(*args, **kwargs)
        return wrapper
    return _inner_jwt_ex_role_required

