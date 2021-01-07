from functools import wraps

from flask import jsonify
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_claims
)


def jwt_ex_role_required(role):
    def _inner_jwt_ex_role_required(fn):  # this way is needed to pass a param
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt_claims()
            if 'roles' not in claims or role not in claims['roles']:
                return jsonify(msg=f"'{role}' role needed"), 403
            else:
                return fn(*args, **kwargs)
        return wrapper
    return _inner_jwt_ex_role_required
