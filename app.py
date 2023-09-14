import os
from flask import (
    Flask,
)
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

import api

app.register_blueprint(api.bp)