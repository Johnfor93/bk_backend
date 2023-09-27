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
            periodStart = yearnow
            periodEnd = yearnow+1
        else:
            periodStart = yearnow-1
            periodEnd = yearnow

        periodYear = str(periodStart)+"/"+str(periodEnd)

        dateStartFirst = str(periodStart)+"-07-01"
        dateEndFirst = str(periodStart)+"-12-31"
        dateStartSecond = str(periodEnd)+"-01-01"
        dateEndSecond = str(periodEnd)+"-06-30"

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

        cur.execute("""
            SELECT
                student_list.student_code,
                student_list.student_name,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x11,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x12,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x13,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x14,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x21,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x22,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x23,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x24,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x31,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x32,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x33,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x34,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x41,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x42,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x43,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as x44,
                (select count(*) from t_counseling bb where bb.student_code = student_list.student_code and counseling_date between %s and %s) as counseling_freq_first,
                (select count(*) from t_counseling bb where bb.student_code = student_list.student_code and counseling_date between %s and %s) as counseling_freq_second,
                (select count(*) from t_consultation bb where bb.student_code = student_list.student_code and consultation_date between %s and %s) as consultation_freq_first,
                (select count(*) from t_consultation bb where bb.student_code = student_list.student_code and consultation_date between %s and %s) as consultation_freq_second,
                (select count(*) from t_visit bb where bb.student_code = student_list.student_code and visit_date between %s and %s) as visit_freq_first,
                (select count(*) from t_visit bb where bb.student_code = student_list.student_code and visit_date between %s and %s) as visit_freq_second,
                description_list.deskripsi
            FROM
                students as student_list
            INNER JOIN
            (
            SELECT bb.student_code, ARRAY_AGG(conclusion) as deskripsi
            FROM 
                students as bb
            LEFT JOIN (
                select student_code, conclusion from t_counseling 
                full join(select student_code, conclusion from t_consultation) as xx using(student_code, conclusion)
                full join(select student_code, "result" as conclusion from t_visit) as yy using(student_code, conclusion)) as uuu on uuu.student_code = bb.student_code)
            GROUP BY bb.student_code
            ) as description_list on student_list.student_code = description_list.student_code
            where
            GROUP BY student_list.student_code, description_list.deskripsi, student_list.student_name
        """)

        for item in dataStudent:
            cur.execute("""
                INSERT INTO students VALUES (%s, %s)
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
            "data": listOverview
        }), 200)
    except psycopg2.Error as error:
        print("------------------\nERROR: " + str(error))
        return util.log_response({
            "success": False,
            "message": error.pgerror,
        }, 400, request.method)