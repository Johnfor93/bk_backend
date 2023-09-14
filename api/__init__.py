from flask import (
    make_response, jsonify, Blueprint
)

from . import auth

bp = Blueprint('api', __name__, url_prefix='/api')

bp.register_blueprint(auth.bp)