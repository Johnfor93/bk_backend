from flask import (
    make_response, jsonify, Blueprint
)

from . import auth
from . import scope
from . import category
from . import university
from . import faculty
from . import study_program
from . import provider

bp = Blueprint('api', __name__, url_prefix='/api')

bp.register_blueprint(auth.bp)
bp.register_blueprint(scope.bp)
bp.register_blueprint(category.bp)
bp.register_blueprint(university.bp)
bp.register_blueprint(faculty.bp)
bp.register_blueprint(study_program.bp)
bp.register_blueprint(provider.bp)

@bp.route("/")
@auth.token_required
def helloword():
    return "Hello World"