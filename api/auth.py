from functools import wraps
from flask import (
    request, make_response, jsonify, Blueprint, current_app, render_template
)
from  werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db_connection
import jwt
import requests
from datetime import datetime, timedelta
import psycopg2
import json
import hashlib

bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return make_response(jsonify({"message": "Missing token"}), 401)
        try:
            login = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db_connection()
            print(token)
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    *
                FROM
                    (
                        SELECT
                            user_code,route_name,route_method
                        FROM
                            m_user_route
                        UNION ALL
                        SELECT
                            'administrator' user_code,route_name,route_method
                        FROM
                            b_route
                    ) x
                WHERE
                    user_code = %s AND route_name = %s AND route_method = %s
            """, (login['user_code'], f.__name__, request.method))
            datas = cur.fetchall()
            cur.close()
            conn.close()
            if datas:
                current_app.config['USER_CODE'] = login['user_code']
            else:
                return make_response(jsonify({"message": "Not authorized"}), 401)
        except:
            return make_response(jsonify({"message": "Invalid ENV"}), 401)
        return f(*args, **kwargs)
    return decorator

def employee_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return make_response(jsonify({"message": "Missing token"}), 400)
        try:
            login = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_app.config['USER_CODE'] = login['employee_code']
        except:
            return make_response(jsonify({"message": "Invalid ENV"}), 400)
        return f(*args, **kwargs)
    return decorator

@bp.route('login', methods=('GET', 'POST'))
def login():
    try:
        content = request.get_json()

        headers = {
            'Content-Type': 'application/json',
            'Accept': '*',
            'Proxy-Authorization': 'http://192.168.100.106:7002',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
        }
        url = ("http://192.168.100.106:7002/user_login/")
        hashed_key = hashlib.md5(content["user_key"].encode()).hexdigest()
        payload = {
            "user_code" : content["user_code"],
            "user_key" : hashed_key
        }

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        success = response.ok
        if(not success):
            return make_response({
                "message": "Data tidak ditemukan"
            }, 401)
        stats = response.json()
        status_code = response.status_code
        return make_response(jsonify(stats),status_code)
    except requests.exceptions.HTTPError as err:
        return make_response(err, 401)
    
@bp.route('/employee_login', methods=['POST'])
def employee_login():
    content = request.get_json()
    # hashed_key = hashlib.md5(employee_key.encode()).hexdigest()
    payload = {
        "employee_code" :  content["employee_code"],
        "employee_key" : content["employee_key"]
    }
    response = requests.post("http://192.168.100.106:7002/employee_login", headers = {'Content-Type' : 'application/json'}, json = payload)
    
    if 'token' not in response.json():
        return make_response({
                "message": "Data tidak ditemukan"
            }, 401)
    else:
        stats = response.json()
        status_code = response.status_code
        return make_response(jsonify(stats),status_code)