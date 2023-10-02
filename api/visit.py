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

bp = Blueprint("visit", __name__)

def visitJson(item):
    return {
        "visit_code"     : item["visit_code"],
        "student_code"   : item["student_code"],
        "employee_code"  : item["employee_code"],
        "visit_date"     : item["visit_date"],
        "reason"         : item["reason"],
        "result"         : item["result"],
        "followup"       : item["followup"],
        "visit_note"     : item["visit_note"],
    }

def visitReportJson(item):
    return {
        "visit_code"     : item["visit_code"],
        "student_code"   : item["student_code"],
        "student_name"   : item["student_name"],
        "employee_code"  : item["employee_code"],
        "visit_date"     : item["visit_date"],
        "reason"         : item["reason"],
        "result"         : item["result"],
        "followup"       : item["followup"],
        "visit_note"     : item["visit_note"],
    }

def visitPagingFormatJSON(item, nameStudent):
    return {
        "visit_code"     : item["visit_code"],
        "student_code"   : item["student_code"],
        "employee_code"  : item["employee_code"],
        "visit_date"     : item["visit_date"],
        "reason"         : item["reason"],
        "result"         : item["result"],
        "followup"       : item["followup"],
        "visit_note"     : item["visit_note"],
        "student_name"   : nameStudent[item["student_code"]],
    }

@bp.route("/visits", methods=["POST"])
@employee_required
def visits():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.form

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('visit_date' in content.keys()) or len(content['visit_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('reason' in content.keys()) or len(content['reason']) == 0):
                error+="Alasan Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Hasil Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            visit_note = ""
            if('visit_note' in content.keys()):
                visit_note = content["visit_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('VST',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(visit_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as visit_code
                FROM
                    t_visit
                WHERE
                    visit_code LIKE CONCAT('VST',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            visit_code = data["visit_code"]

            date_format = "%Y-%m-%d"
            now = datetime.now()
            dateNow = now.strftime("%Y-%m-%d")
            date1 = time.mktime(time.strptime(content['visit_date'], date_format))
            date2 = time.mktime(time.strptime(dateNow, date_format))

            delta = date2 - date1
            if int(delta / 86400) > 14:
                return util.log_response({
                    "success": False,
                    "message": "Sudah lebih dari 14 hari untuk melakukan input",
                }, 400, request.method)
            
            cur.execute("""
                INSERT INTO
                    t_visit
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                visit_code,
                content['student_code'],
                current_app.config['USER_CODE'], 
                content['visit_date'],
                content['reason'],
                content['result'],
                content['followup'],
                visit_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                current_app.config['USER_CODE'], 
                datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
            return util.log_response({
                "success": True,
                "message": "Data sudah dimasukkan"
            }, 200, request.method)
        except psycopg2.Error as error:
            return util.log_response({
                "success": False,
                "message": error.pgerror,
            }, 400, request.method)

@bp.route("/visit/<visit_code>", methods=["GET", "PUT", "DELETE"])
@employee_required
def visit(visit_code):
    if(request.method == "GET"):
        try:
            # get visit data
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM t_visit
                WHERE visit_code = %s
            """, (visit_code,))

            data = cur.fetchone()

            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            
            # get student name
            payload = {
                "limit": "1000",
                "page": "1",
                "filters": [
                    {
                        "operator": "contains",
                        "search": "subject_code",
                        "value1": "bimbingan_konseling"
                    },
                    {
                        "operator": "contains",
                        "search": "student_code",
                        "value1": data["student_code"]
                    }
                ],
                "filter_type": "AND"
            }
        
            headers = {
                    'token': request.headers.get('token'),
                    'Content-Type': 'application/json',
                    'accept': 'application/json',
                    'Proxy-Authorization': 'http://192.168.100.104:7001',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
                }
            
            url = ("http://192.168.100.104:7001/employee_education_detail_paging")

            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=3)

            success = response.ok
            if(not success):
                return make_response({
                    "message": "Data tidak ditemukan"
                }, 401)
            datas = response.json()
            dataStundent = datas["data"]

            if(len(dataStundent) == 0):
                return make_response({
                    "success": False,
                    "message": "Data siswa tidak ditemukan"
                }, 404) 
            
            dataJSON = visitJson(data)
            dataJSON.update({"student_name": dataStundent[0]["student_name"]})

            return make_response(jsonify({
                "data":dataJSON,
                "success": True}), 200)
        except psycopg2.Error as error:
            return make_response(jsonify({
                "success": False,
                "message": error.pgerror,
            }), 400)


    elif request.method == "PUT":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.form

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('visit_date' in content.keys()) or len(content['visit_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('reason' in content.keys()) or len(content['reason']) == 0):
                error+="Alasan Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Hasil Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            visit_note = ""
            if('visit_note' in content.keys()):
                visit_note = content["visit_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            date_format = "%Y-%m-%d"
            now = datetime.now()
            dateNow = now.strftime("%Y-%m-%d")
            date1 = time.mktime(time.strptime(content['created_at'], date_format))
            date2 = time.mktime(time.strptime(dateNow, date_format))

            delta = date2 - date1
            if int(delta / 86400) > 14:
                return util.log_response({
                    "success": False,
                    "message": "Sudah lebih dari 14 hari untuk melakukan update",
                }, 400, request.method)


            cur.execute("""
                UPDATE
                    t_visit
                SET
                    student_code = %s,
                    employee_code = %s,
                    visit_date = %s,
                    reason = %s,
                    result = %s,
                    followup = %s,
                    visit_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    visit_code = %s
                RETURNING *
            """, (
                content['student_code'],
                current_app.config['USER_CODE'], 
                content['visit_date'],
                content['reason'],
                content['result'],
                content['followup'],
                visit_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                visit_code,))
            conn.commit()

            dataUpdated = cur.fetchone()
            cur.close()
            conn.close()
            if(dataUpdated == None):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404, request.method) 

            return util.log_response({
                "success": True,
                "message": "Data sudah diupate"
            }, 200, request.method)
        except psycopg2.Error as error:
            return make_response(jsonify({
                "success": False,
                "message": error.pgerror,
            }), 400)

    elif request.method == "DELETE":
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                DELETE FROM
                    t_visit
                WHERE 
                    visit_code = %s
                RETURNING *
            """, (visit_code,))
            conn.commit()

            dataDeleted = cur.fetchone()
            cur.close()
            conn.close()
            if(dataDeleted == None):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404, request.method) 

            return util.log_response({
                "success": True,
                "message": "Data sudah didelete"
            }, 200, request.method) 
        except psycopg2.Error as error:
            return make_response(jsonify({
                "success": False,
                "message": error.pgerror,
            }), 400)

@bp.route("/pagination_visit", methods=["POST"])
@employee_required
def pagination_visit():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        filter= util.filter(content)

        if(filter==''):
            sql = """
                SELECT
                    *
                FROM
                    t_visit
                ORDER BY
                    visit_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        else:
            sql = """
                SELECT
                    *
                FROM
                    t_visit
                WHERE
                    (""" + util.filter(content) + """
                ORDER BY
                    visit_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        cur.execute(sql)
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        visits = []
        for data in datas:
            visits.append(visitJson(data))

        return util.log_response(
        {
            "data": visits,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)

# showing attachment file
@bp.route("/visit/attachment/<visit_code>")
def visitAttachment(visit_code):
    filename_attachment = visit_code + ".pdf"
    path_file_attachment = os.path.join(current_app.config['UPLOAD_FOLDER_VISIT'], filename_attachment)
    if(os.path.isfile(path_file_attachment)):
        return send_file(path_file_attachment)
    else:
        return make_response({
            "success": False
        }, 404)
    
@bp.route("/employee_pagination_visit", methods=["POST"])
@employee_required
def employee_pagination_visit():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        student_search = ""

        if('filter' in content.keys()):
            student_search = content["filter"]

        payload = {
                "limit": "1000",
                "page": "1",
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
                'accept': 'application/json',
                'Proxy-Authorization': 'http://192.168.100.104:7001',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
            }
        
        url = ("http://192.168.100.104:7001/employee_education_detail_paging")

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=3)

        success = response.ok
        if(not success):
            return make_response({
                "message": "Data tidak ditemukan"
            }, 401)
        datas = response.json()
        dataStundent = datas["data"]
        nameStudent = dict()
        listStundent = list()

        for data in dataStundent: 
            nameStudent.update({data["student_code"]: data["student_name"]})
            listStundent.append(data["student_code"])

        sql = """
            SELECT
                *
            FROM
                t_visit
            WHERE
                student_code = ANY(%s)
            ORDER BY
                visit_date DESC
            LIMIT
                """ + str(content['limit']) + """
            OFFSET
                """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
            """
        
        cur.execute(sql, (list(listStundent),))
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        visits = []
        for data in datas:
            visits.append(visitPagingFormatJSON(data, nameStudent))

        return make_response(
        {
            "data": visits,
            "message": "success"
        }, 
        200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)
    
@bp.route("/visit/history/<student_code>", methods=["GET"])
@employee_required
def historyStudent(student_code):
    try:
        # Get Employee Data
        headers = {
            'token': request.headers.get('token'),
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'Proxy-Authorization': 'https://jpayroll.pppkpetra.sch.id',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
        }

        url = ("https://jpayroll.pppkpetra.sch.id/thirdparty/API_Get_Employee_Profile.php")

        response = requests.get(url, headers=headers)

        datas = response.json()
        dataEmployees = datas["data"]
        employeeDictName = dict()

        for employee in dataEmployees:
            employeeDictName.update({employee["NIK"]: employee["Name"]})

        # get visit data
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                *
            FROM
                t_visit
            WHERE 
                student_code = %s
        """, (student_code,))

        datas = cur.fetchall()

        if(datas == None):
            return make_response({
                "success": False,
                "message": "Data tidak ditemukan"
            }, 404) 
        dataJSON = []
        for data in datas:
            JSONResponseFormat = visitJson(data)
            JSONResponseFormat.update({"employee_name": employeeDictName[data["employee_code"]]})
            dataJSON.append(JSONResponseFormat)

        return make_response(jsonify({
            "data":dataJSON,
            "success": True}), 200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)
    
@bp.route("/classreport/visit/<classroom_code>/<organization_code>")
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
                visit_code,
                students.student_code,
                students.student_name,
                employee_code,
                visit_date,
                reason,
                result,
                followup,
                visit_note
            FROM
                t_visit
                INNER JOIN students ON t_visit.student_code = students.student_code
            WHERE
                visit_date BETWEEN %s AND %s
        """, (dateStartFirst, dateEndSecond,))

        classReportDatas = cur.fetchall()
        cur.close()
        conn.close()

        classReportJSON = list()

        for data in classReportDatas:
            classReportJSON.append(visitReportJson(data))

        return make_response(jsonify({
            "data":classReportJSON,
            "success": True}), 200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)