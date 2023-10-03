from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required, employee_required

import json
import requests

bp = Blueprint("service", __name__)

@bp.route("/getemployee/student", methods=["POST"])
@employee_required
def studentList():
    content = request.get_json()
    student_search = ""
    limit = '10'
    if 'student_name' in content.keys():
        student_search = content.get('student_name')

    if 'page' in content.keys():
        page = str(content.get('page'))
    else:
        return make_response({
            "message": "Halaman tidak dimasukkan"
        }, 401)

    if 'limit' in content.keys():
        limit = str(content.get('limit'))

    payload = {
            "limit": limit,
            "page": page,
            "filters": [
                {
                    "operator": "contains",
                    "search": "subject_code",
                    "value1": "bimbingan_konseling"
                },
                {
                    "operator": "contains",
                    "search": "student_name",
                    "value1": student_search
                }
            ],
            "filter_type": "AND"
        }
    
    headers = {
            'token': request.headers.get('token'),
            'Content-Type': 'application/json',
            'Accept': '*',
            'Proxy-Authorization': current_app.config['STUDENT_SERVICES'],
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
        }
    
    url = (current_app.config['STUDENT_SERVICES']+"/employee_education_detail_paging")

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    success = response.ok
    if(not success):
        return make_response({
            "message": "Data tidak ditemukan"
        }, 401)
    stats = response.json()
    status_code = response.status_code
    return make_response(jsonify(stats),status_code)

