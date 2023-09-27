from flask import (
    request, Blueprint, current_app, make_response, jsonify, send_file
    )
from datetime import datetime
import time

import os
import os.path

import requests
import json

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required, employee_required

bp = Blueprint("report", __name__)

@bp.route("/classreport")
@employee_required
def classreport():
    try:
        # Get Employee Data
        headers = {
            'token': request.headers.get('token'),
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'Proxy-Authorization': 'http://192.168.100.104:7001',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
        }

        url = ("http://192.168.100.104:7001/employee_classroom_schedule")

        response = requests.get(url, headers=headers)

        datas = response.json()

        if(response.status_code != 200):
            return util.log_response({
                "success": False,
                "message": "Laman tidak dapat diakses",
            }, 400, request.method)
        
        dataClasses = datas["data"]

        timenow = datetime.now()

        yearnow = timenow.year
        monthnow = timenow.month

        if(monthnow >= 7):
            periodYear = str(yearnow)+"/"+str(yearnow+1)
        else:
            periodYear = str(yearnow-1)+"/"+str(yearnow)

        counselingClass = list()

        for data in dataClasses:
            if(data["subject_code"] == "bimbingan_konseling" and data["period_code"] == periodYear):
                counselingClass.append(data)

        return make_response(jsonify({"data": counselingClass}), 200)
    except psycopg2.Error as error:
        return util.log_response({
            "success": False,
            "message": error.pgerror,
        }, 400, request.method)

@bp.route("/classreport/overview", methods=["POST"])
@employee_required
def overviewClassReport():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        timenow = datetime.now()

        yearnow = timenow.year
        monthnow = timenow.month

        if(monthnow >= 7):
            periodYear = str(yearnow)+"/"+str(yearnow+1)
        else:
            periodYear = str(yearnow-1)+"/"+str(yearnow)
        limit = '1000'

        payload = {
                "limit": limit,
                "page": 1,
                "filters": [
                    {
                        "operator": "contains",
                        "search": "subject_code",
                        "value1": "bimbingan_konseling"
                    },
                    {
                        "operator": "contains",
                        "search": "period_code",
                        "value1": periodYear
                    },
                    {
                        "operator": "contains",
                        "search": "organization_code",
                        "value1": content["organization_code"]
                    },
                    {
                        "operator": "contains",
                        "search": "classroom_code",
                        "value1": content["classroom_code"]
                    }
                ],
                "filter_type": "AND"
            }
        
        headers = {
                'token': request.headers.get('token'),
                'Content-Type': 'application/json',
                'Accept': '*',
                'Proxy-Authorization': 'http://192.168.100.104:7001',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
            }
        
        url = ("http://192.168.100.104:7001/employee_education_detail_paging")

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if(response.status_code != 200):
            return util.log_response({
                "success": False,
                "message": "Laman tidak dapat diakses",
            }, 400, request.method)
            
        datas = response.json()
        dataStudent = datas["data"]

        cur.execute("CREATE TEMP TABLE students(student_code VARCHAR(40), student_name VARCHAR(40))")

        for item in dataStudent:
            cur.execute("""
                INSERT INTO student VALUES (%s %s)
            """, (item["student_code"], item["student_name"],))

        cur.execute("SELECT * FROM students")
        dataOverview = cur.fetchall()
        cur.close()
        conn.close()
        listOverview = list()

        for data in dataOverview:
            listOverview.append({
                "student_code": data["student_code"],
                "student_name": data["student_name"]
            })
        return make_response(jsonify({
            "data": "listOverview"
        }), 200)
    except psycopg2.Error as error:
        print(error)
        return util.log_response({
            "success": False,
            "message": error.pgerror,
        }, 400, request.method)