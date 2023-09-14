from flask import (
    make_response, jsonify, Blueprint
)

from . import auth
from . import scope

bp = Blueprint('api', __name__, url_prefix='/api')

bp.register_blueprint(auth.bp)
bp.register_blueprint(scope.bp)

@bp.route("/")
@auth.token_required
def helloword():
    return "Hello World"