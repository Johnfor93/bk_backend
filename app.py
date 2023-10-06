import os
from flask import (
    Flask,
)
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['MAX_SIZE_FILE'] = 1024*1024
app.config['STUDENT_SERVICES'] = os.environ.get("STUDENT_SERVICES")
app.config['LOGIN_SERVICES'] = os.environ.get("LOGIN_SERVICE")

path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
UPLOAD_FOLDER_COUNSELING = os.path.join(path, 'uploads/counseling')
UPLOAD_FOLDER_CONSULTATION = os.path.join(path, 'uploads/consultation')
UPLOAD_FOLDER_STUDY = os.path.join(path, 'uploads/study')
UPLOAD_FOLDER_CASETRANSFER = os.path.join(path, 'uploads/casetransfer')
UPLOAD_FOLDER_VISIT = os.path.join(path, 'uploads/visit')

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if not os.path.isdir(UPLOAD_FOLDER_COUNSELING):
    os.mkdir(UPLOAD_FOLDER_COUNSELING)
if not os.path.isdir(UPLOAD_FOLDER_CONSULTATION):
    os.mkdir(UPLOAD_FOLDER_CONSULTATION)
if not os.path.isdir(UPLOAD_FOLDER_STUDY):
    os.mkdir(UPLOAD_FOLDER_STUDY)
if not os.path.isdir(UPLOAD_FOLDER_CASETRANSFER):
    os.mkdir(UPLOAD_FOLDER_CASETRANSFER)
if not os.path.isdir(UPLOAD_FOLDER_VISIT):
    os.mkdir(UPLOAD_FOLDER_VISIT)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_COUNSELING'] = UPLOAD_FOLDER_COUNSELING
app.config['UPLOAD_FOLDER_CONSULTATION'] = UPLOAD_FOLDER_CONSULTATION
app.config['UPLOAD_FOLDER_STUDY'] = UPLOAD_FOLDER_STUDY
app.config['UPLOAD_FOLDER_CASETRANSFER'] = UPLOAD_FOLDER_CASETRANSFER
app.config['UPLOAD_FOLDER_VISIT'] = UPLOAD_FOLDER_VISIT

import api

app.register_blueprint(api.bp)