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

bp = Blueprint("consultation", __name__)

def consultationJson(item):
    return {
        "consultation_code"     : item["consultation_code"],
        "student_code"          : item["student_code"],
        "scope_code"            : item["scope_code"],
        "employee_code"         : item["employee_code"],
        "consultation_date"     : item["consultation_date"],
        "problem"               : item["problem"],
        "conclusion"            : item["conclusion"],
        "followup"              : item["followup"],
        "consultation_note"     : item["consultation_note"]
    }

def consultationHistoryJson(item):
    return {
        "consultation_code"     : item["consultation_code"],
        "student_code"          : item["student_code"],
        "scope_code"            : item["scope_code"],
        "scope_name"            : item["scope_name"],
        "employee_code"         : item["employee_code"],
        "consultation_date"     : item["consultation_date"],
        "problem"               : item["problem"],
        "conclusion"            : item["conclusion"],
        "followup"              : item["followup"],
        "consultation_note"     : item["consultation_note"]
    }

def consultationPagingFormatJSON(item, nameStudent):
    return {
        "consultation_code"       : item["consultation_code"],
        "student_code"          : item["student_code"],
        "scope_name"            : item["scope_name"],
        "consultation_date"       : item["consultation_date"],
        "problem"               : item["problem"],
        "student_name"          : nameStudent[item["student_code"]],
    }

@bp.route("/consultations", methods=["POST"])
@employee_required
def consultations():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.form
            uploaded_file = request.files

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('scope_code' in content.keys()) or len(content['scope_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('consultation_date' in content.keys()) or len(content['consultation_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('problem' in content.keys()) or len(content['problem']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('conclusion' in content.keys()) or len(content['conclusion']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            consultation_note = ""
            if('consultation_note' in content.keys()):
                consultation_note = content["consultation_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('CON',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(consultation_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as consultation_code
                FROM
                    t_consultation
                WHERE
                    consultation_code LIKE CONCAT('CON',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            consultation_code = data["consultation_code"]

            date_format = "%Y-%m-%d"
            now = datetime.now()
            dateNow = now.strftime("%Y-%m-%d")
            date1 = time.mktime(time.strptime(content['consultation_date'], date_format))
            date2 = time.mktime(time.strptime(dateNow, date_format))

            delta = date2 - date1
            if int(delta / 86400) > 14:
                return util.log_response({
                    "success": False,
                    "message": "Sudah lebih dari 14 hari untuk melakukan input",
                }, 400, request.method)

            
            cur.execute("""
                INSERT INTO
                    t_consultation
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING consultation_code
            """, (
                consultation_code,
                content['student_code'],
                content['scope_code'],
                current_app.config['USER_CODE'], 
                content['consultation_date'],
                content['problem'],
                content['conclusion'],
                content['followup'],
                consultation_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                current_app.config['USER_CODE'], 
                datetime.now())
            )
            conn.commit()
            inserted_id = cur.fetchone()
            cur.close()
            conn.close()

            if(len(uploaded_file['attachment'].filename) != 0):
                uploaded_file = uploaded_file['attachment']
                uploaded_filename = inserted_id["consultation_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CONSULTATION'], uploaded_filename))

            return util.log_response({
                "success": True,
                "message": "Data sudah dimasukkan"
            }, 200, request.method)
        except psycopg2.Error as error:
            return util.log_response({
                "success": False,
                "message": error.pgerror,
            }, 400, request.method)

@bp.route("/consultation/<consultation_code>", methods=["GET", "PUT", "DELETE"])
@employee_required
def consultation(consultation_code):
    if(request.method == "GET"):
        try:
            # get consultation data
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM t_consultation
                WHERE consultation_code = %s
            """, (consultation_code,))

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
            
            dataJSON = consultationJson(data)
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
            uploaded_file = request.files

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('scope_code' in content.keys()) or len(content['scope_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('consultation_date' in content.keys()) or len(content['consultation_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('problem' in content.keys()) or len(content['problem']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('conclusion' in content.keys()) or len(content['conclusion']) == 0):
                error+="Konklusi Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            consultation_note = ""
            if('consultation_note' in content.keys()):
                consultation_note = content["consultation_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            print(content['created_at'])
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
                    t_consultation
                SET
                    student_code = %s,
                    scope_code = %s,
                    employee_code = %s,
                    consultation_date = %s,
                    problem = %s,
                    conclusion = %s,
                    followup = %s,
                    consultation_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    consultation_code = %s
                RETURNING *
            """, (
                content['student_code'],
                content['scope_code'],
                current_app.config['USER_CODE'], 
                content['consultation_date'],
                content['problem'],
                content['conclusion'],
                content['followup'],
                consultation_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                consultation_code,))
            conn.commit()

            dataUpdated = cur.fetchone()
            cur.close()
            conn.close()
            if(dataUpdated == None):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404, request.method) 

            if(len(uploaded_file['attachment'].filename) != 0):
                uploaded_file = uploaded_file['attachment']
                uploaded_filename = dataUpdated["consultation_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                if(os.path.exists((os.path.join(current_app.config['UPLOAD_FOLDER_CONSULTATION'], uploaded_filename)))):
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_CONSULTATION'], uploaded_filename))
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CONSULTATION'], uploaded_filename))

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
                    t_consultation
                WHERE 
                    consultation_code = %s
                RETURNING *
            """, (consultation_code,))
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

@bp.route("/pagination_consultation", methods=["POST"])
@employee_required
def pagination_consultation():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        filter= util.filter(content)

        if(filter==''):
            sql = """
                SELECT
                    consultation_code,
                    student_code,
                    scope_name,
                    consultation_date,
                    problem
                FROM
                    t_consultation
                    INNER JOIN m_scope ON t_consultation.scope_code = m_scope.scope_code
                """ + util.sort(content) + """
                ORDER BY
                    consultation_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        else:
            sql = """
                SELECT
                    consultation_code,
                    student_code,
                    scope_name,
                    consultation_date,
                    problem
                FROM
                    t_consultation
                    INNER JOIN m_scope ON t_consultation.scope_code = m_scope.scope_code
                WHERE
                    (""" + util.filter(content) + """) 
                ORDER BY
                    consultation_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        cur.execute(sql)
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        consultations = []
        for data in datas:
            consultations.append(consultationPagingFormatJSON(data))

        return make_response(
        {
            "data": consultations,
            "message": "success"
        }, 
        200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)

# showing attachment file
@bp.route("/consultation/attachment/<consultation_code>")
def consultationAttachment(consultation_code):
    filename_attachment = consultation_code + ".pdf"
    path_file_attachment = os.path.join(current_app.config['UPLOAD_FOLDER_CONSULTATION'], filename_attachment)
    not_found = os.path.join(current_app.config['UPLOAD_FOLDER'], '404.png')
    if(os.path.isfile(path_file_attachment)):
        return send_file(path_file_attachment)
    else:
        return make_response({
            "success": False
        }, 404)
    
@bp.route("/employee_pagination_consultation", methods=["POST"])
@employee_required
def employee_pagination_consultation():
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
                consultation_code,
                student_code,
                scope_name,
                consultation_date,
                problem
            FROM
                t_consultation
                INNER JOIN m_scope ON t_consultation.scope_code = m_scope.scope_code
            WHERE
                student_code = ANY(%s)
            ORDER BY
                consultation_date DESC
            LIMIT
                """ + str(content['limit']) + """
            OFFSET
                """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
            """
        
        cur.execute(sql, (list(listStundent),))
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        consultations = []
        for data in datas:
            consultations.append(consultationPagingFormatJSON(data, nameStudent))

        return make_response(
        {
            "data": consultations,
            "message": "success"
        }, 
        200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)
    
@bp.route("/consultation/history/<student_code>", methods=["GET"])
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
            
        # get consultation data
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                consultation_code,
                student_code,
                m_scope.scope_code,
                m_scope.scope_name,
                employee_code,
                consultation_date,
                problem,
                conclusion,
                followup,
                consultation_note
            FROM
                t_consultation
                INNER JOIN m_scope ON t_consultation.scope_code = m_scope.scope_code
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
            JSONResponseFormat = consultationHistoryJson(data)
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