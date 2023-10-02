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

@bp.route("/classreport/overview/<classroom_code>/<organization_code>")
@employee_required
def overviewClassReport(classroom_code, organization_code):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

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
                        "value1": organization_code
                    },
                    {
                        "operator": "contains",
                        "search": "classroom_code",
                        "value1": classroom_code
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
            CREATE TEMP TABLE students(student_code VARCHAR(40), student_name VARCHAR(40))
        """)

        for item in dataStudent:
            cur.execute("""
                INSERT INTO students VALUES (%s, %s)
            """, (item["student_code"], item["student_name"],))

        cur.execute("""
            SELECT
                student_list.student_code,
                student_list.student_name,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as potential_privacy,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as potential_social,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as potential_study,
                (select count(*) from t_counseling bb where category_code='1' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as potential_carrier,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as low_privacy,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as low_social,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as low_study,
                (select count(*) from t_counseling bb where category_code='2' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as low_carrier,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as mid_privacy,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as mid_social,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as mid_study,
                (select count(*) from t_counseling bb where category_code='3' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as mid_carrier,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='1' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as high_privacy,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='2' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as high_social,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='3' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as high_study,
                (select count(*) from t_counseling bb where category_code='4' and scope_code='4' and bb.student_code = student_list.student_code and counseling_date between %s and %s) as high_carrier,
                (select count(*) from t_counseling bb where bb.student_code = student_list.student_code and counseling_date between %s and %s) as counseling_freq_first,
                (select count(*) from t_counseling bb where bb.student_code = student_list.student_code and counseling_date between %s and %s) as counseling_freq_second,
                (select count(*) from t_consultation bb where bb.student_code = student_list.student_code and consultation_date between %s and %s) as consultation_freq_first,
                (select count(*) from t_consultation bb where bb.student_code = student_list.student_code and consultation_date between %s and %s) as consultation_freq_second,
                (select count(*) from t_visit bb where bb.student_code = student_list.student_code and visit_date between %s and %s) as visit_freq_first,
                (select count(*) from t_visit bb where bb.student_code = student_list.student_code and visit_date between %s and %s) as visit_freq_second,
                description_list.description
            FROM
                students as student_list
            INNER JOIN
            (
            SELECT bb.student_code, ARRAY_AGG(conclusion) as description
            FROM 
                students as bb
            LEFT JOIN (
                select student_code, conclusion from t_counseling 
                full join(select student_code, conclusion from t_consultation) as xx using(student_code, conclusion)
                full join(select student_code, "result" as conclusion from t_visit) as yy using(student_code, conclusion)) as uuu on uuu.student_code = bb.student_code 
            GROUP BY bb.student_code) as description_list on student_list.student_code = description_list.student_code
            GROUP BY student_list.student_code, description_list.description, student_list.student_name""", (dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond,dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond,dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond,dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond,dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond, dateStartFirst, dateEndSecond,dateStartFirst, dateEndSecond, dateStartFirst, dateEndFirst, dateStartSecond, dateEndSecond,dateStartFirst, dateEndFirst, dateStartSecond, dateEndSecond,dateStartFirst, dateEndFirst, dateStartSecond, dateEndSecond,))
        dataOverview = cur.fetchall()
        cur.close()
        conn.close()
        listOverview = list()

        for data in dataOverview:
            listOverview.append({
                "student_code": data["student_code"],
                "student_name": data["student_name"],
                "potential_privacy" : data["potential_privacy"],
                "potential_social" : data["potential_social"],
                "potential_study" : data["potential_study"],
                "potential_carrier" : data["potential_carrier"],
                "low_privacy" : data["low_privacy"],
                "low_social" : data["low_social"],
                "low_study" : data["low_study"],
                "low_carrier" : data["low_carrier"],
                "mid_privacy" : data["mid_privacy"],
                "mid_social" : data["mid_social"],
                "mid_study" : data["mid_study"],
                "mid_carrier" : data["mid_carrier"],
                "high_privacy" : data["high_privacy"],
                "high_social" : data["high_social"],
                "high_study" : data["high_study"],
                "high_carrier" : data["high_carrier"],
                "counseling_freq_first" : data["counseling_freq_first"],
                "counseling_freq_second" : data["counseling_freq_second"],
                "consultation_freq_first" : data["consultation_freq_first"],
                "consultation_freq_second" : data["consultation_freq_second"],
                "visit_freq_first" : data["visit_freq_first"],
                "visit_freq_second" : data["visit_freq_second"],
                "description" : data["description"]
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