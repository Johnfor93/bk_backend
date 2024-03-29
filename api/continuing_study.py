from flask import (
    request, Blueprint, current_app, make_response, jsonify, send_file
    )
from datetime import datetime
import time
import os.path

import requests
import json

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required, employee_required

bp = Blueprint("continuing_study", __name__)

def continuing_studyJson(item):
    return {
        "continuing_study_code"     : item["continuing_study_code"],
        "student_code"              : item["student_code"],
        "study_program_code"        : item["study_program_code"],
        "study_program_name"        : item["study_program_name"],
        "faculty_code"              : item["faculty_code"],
        "faculty_name"              : item["faculty_name"],
        "university_code"           : item["university_code"],
        "university_name"           : item["university_name"],
        "employee_code"             : item["employee_code"],
        "continuing_study_date"     : item["continuing_study_date"],
        "result"                    : item["result"],
        "create_date"               : item["create_date"],
        "continuing_study_note"     : item["continuing_study_note"]
    }

def continuing_studyReportJson(item):
    return {
        "continuing_study_code"     : item["continuing_study_code"],
        "student_code"              : item["student_code"],
        "student_name"              : item["student_name"],
        "study_program_code"        : item["study_program_code"],
        "study_program_name"        : item["study_program_name"],
        "faculty_code"              : item["faculty_code"],
        "faculty_name"              : item["faculty_name"],
        "university_code"           : item["university_code"],
        "university_name"           : item["university_name"],
        "employee_code"             : item["employee_code"],
        "continuing_study_date"     : item["continuing_study_date"],
        "result"                    : item["result"],
        "continuing_study_note"     : item["continuing_study_note"]
    }
    
def continuing_studyPagingFormatJSON(item, nameStudent):
    return {
        "continuing_study_code"         : item["continuing_study_code"],
        "student_code"                  : item["student_code"],
        "university_name"               : item["university_name"],
        "study_program_name"            : item["study_program_name"],
        "continuing_study_date"         : item["continuing_study_date"],
        "result"                        : item["result"],
        "student_name"                  : nameStudent[item["student_code"]],
    }
    
@bp.route("/continuing_studys", methods=["POST"])
@employee_required
def continuing_studys():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.form
            uploaded_file = request.files

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('study_program_code' in content.keys()) or len(content['study_program_code']) == 0):
                error+="Program Studi Tidak Boleh Kosong! "
            if(not('continuing_study_date' in content.keys()) or len(content['continuing_study_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Hasil Tidak Boleh Kosong! "
            
            continuing_study_note = ""
            if('continuing_study_note' in content.keys()):
                continuing_study_note = content["continuing_study_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('CST',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(continuing_study_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as continuing_study_code
                FROM
                    t_continuing_study
                WHERE
                    continuing_study_code LIKE CONCAT('CST',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            continuing_study_code = data["continuing_study_code"]

            date_format = "%Y-%m-%d"
            now = datetime.now()
            dateNow = now.strftime("%Y-%m-%d")
            date1 = time.mktime(time.strptime(content['continuing_study_date'], date_format))
            date2 = time.mktime(time.strptime(dateNow, date_format))

            delta = date2 - date1
            if int(delta / 86400) > 14:
                return util.log_response({
                    "success": False,
                    "message": "Sudah lebih dari 14 hari untuk melakukan input",
                }, 400, request.method)

            
            cur.execute("""
                INSERT INTO
                    t_continuing_study
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                continuing_study_code,
                content['student_code'],
                content['study_program_code'],
                current_app.config['USER_CODE'], 
                content['continuing_study_date'],
                content['result'],
                continuing_study_note,
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
                uploaded_filename = inserted_id["continuing_study_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CONTINUING_STUDY'], uploaded_filename))

            return util.log_response({
                "success": True,
                "message": "Data sudah dimasukkan"
            }, 200, request.method)
        except psycopg2.Error as error:
            return util.log_response({
                "success": False,
                "message": error.pgerror,
            }, 400, request.method)

@bp.route("/continuing_study/<continuing_study_code>", methods=["GET", "PUT", "DELETE"])
@employee_required
def continuing_study(continuing_study_code):
    if(request.method == "GET"):
        try:
            # get continuing_study data
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
            SELECT
                continuing_study_code,
                student_code,
                m_study_program.study_program_code,
                m_study_program.study_program_name,
                m_faculty.faculty_code,
                m_faculty.faculty_name,
                m_university.university_code,
                m_university.university_name,
                employee_code,
                continuing_study_date,
                result,
                continuing_study_note,
                t_continuing_study.create_date
            FROM
                t_continuing_study
                INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                INNER JOIN m_university ON m_university.university_code = m_faculty.university_code
            WHERE
                continuing_study_code = %s
            """, (continuing_study_code,))

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
                    'Proxy-Authorization': current_app.config['STUDENT_SERVICES'],
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
                }
            
            url = (current_app.config['STUDENT_SERVICES']+"/employee_education_detail_paging")

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
            
            dataJSON = continuing_studyJson(data)
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
            if(not('study_program_code' in content.keys()) or len(content['study_program_code']) == 0):
                error+="Program Studi Tidak Boleh Kosong! "
            if(not('employee_code' in content.keys()) or len(content['employee_code']) == 0):
                error+="Kode Pegawai Tidak Boleh Kosong! "
            if(not('continuing_study_date' in content.keys()) or len(content['continuing_study_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Konklusi Tidak Boleh Kosong! "
            
            continuing_study_note = ""
            if('continuing_study_note' in content.keys()):
                continuing_study_note = content["continuing_study_note"]

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
                    t_continuing_study
                SET
                    student_code = %s,
                    study_program_code = %s,
                    employee_code = %s,
                    continuing_study_date = %s,
                    result = %s,
                    continuing_study_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    continuing_study_code = %s
                RETURNING *
            """, (
                content['student_code'],
                content['study_program_code'],
                current_app.config['USER_CODE'], 
                content['continuing_study_date'],
                content['result'],
                continuing_study_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                continuing_study_code,))
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
                uploaded_filename = dataUpdated["continuing_study_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                if(os.path.exists((os.path.join(current_app.config['UPLOAD_FOLDER_CONTINUING_STUDY'], uploaded_filename)))):
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_CONTINUING_STUDY'], uploaded_filename))
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CONTINUING_STUDY'], uploaded_filename))

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
                    t_continuing_study
                WHERE 
                    continuing_study_code = %s
                RETURNING *
            """, (continuing_study_code,))
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

@bp.route("/pagination_continuing_study", methods=["POST"])
@employee_required
def pagination_continuing_study():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        filter= util.filter(content)

        if(filter==''):
            sql = """
                SELECT
                    continuing_study_code,
                    student_code,
                    university_name,
                    study_program_name,
                    continuing_study_date,
                    result
                FROM
                    t_continuing_study
                    INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                    INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                    INNER JOIN m_university ON m_university.university_code = m_faculty.university_code
                ORDER BY
                    continuing_study_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        else:
            sql = """
                SELECT
                    continuing_study_code,
                    student_code,
                    university_name,
                    study_program_name,
                    continuing_study_date,
                    result
                FROM
                    t_continuing_study
                    INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                    INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                    INNER JOIN m_university ON m_university.university_code = m_faculty.university_code
                WHERE
                    (""" + util.filter(content) + """
                ORDER BY
                    continuing_study_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        cur.execute(sql)
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        continuing_studys = []
        for data in datas:
            continuing_studys.append(continuing_studyPagingFormatJSON(data))

        return util.log_response(
        {
            "data": continuing_studys,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)

@bp.route("/employee_pagination_continuing_study", methods=["POST"])
@employee_required
def employee_pagination_continuing_study():
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
                    }
                ],
                "filter_type": "AND"
            }
        
        headers = {
                'token': request.headers.get('token'),
                'Content-Type': 'application/json',
                'accept': 'application/json',
                'Proxy-Authorization': current_app.config['STUDENT_SERVICES'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
            }
        
        url = (current_app.config['STUDENT_SERVICES']+"/employee_education_detail_paging")

        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=3)

        success = response.ok
        if(not success):
            return make_response({
                "message": "Data tidak ditemukan"
            }, 401)
        datas = response.json()
        dataStudent = datas["data"]
        nameStudent = dict()
        listStudent = list()
        listFilteredStudent = list()

        for data in dataStudent: 
            nameStudent.update({data["student_code"]: data["student_name"]})
            if (student_search in data["student_code"]) or (student_search in data["student_name"]):
                listFilteredStudent.append(data["student_code"])
            listStudent.append(data["student_code"])

        like_pattern = '%{}%'.format(student_search)

        sql = """
            SELECT
                continuing_study_code,
                student_code,
                university_name,
                study_program_name,
                continuing_study_date,
                result
            FROM
                t_continuing_study
                INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                INNER JOIN univ_to_faculty ON m_faculty.faculty_code = univ_to_faculty.faculty_code
                INNER JOIN m_university ON m_university.university_code = univ_to_faculty.university_code
            WHERE
                student_code = ANY(%s) OR (continuing_study_code LIKE %s AND student_code = ANY(%s))
            ORDER BY
                continuing_study_date DESC
            LIMIT
                """ + str(content['limit']) + """
            OFFSET
                """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
            """
        
        cur.execute(sql, (list(listFilteredStudent), like_pattern, list(listStudent)))
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        continuing_studys = []
        for data in datas:
            continuing_studys.append(continuing_studyPagingFormatJSON(data, nameStudent))

        return make_response(
        {
            "data": continuing_studys,
            "message": "success"
        }, 
        200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)
    
@bp.route("/continuingstudy/history/<student_code>", methods=["GET"])
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
            
        # get continuing_study data
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                continuing_study_code,
                student_code,
                m_study_program.study_program_code,
                m_study_program.study_program_name,
                m_faculty.faculty_code,
                m_faculty.faculty_name,
                m_university.university_code,
                m_university.university_name,
                employee_code,
                continuing_study_date,
                result,
                continuing_study_note,
                t_continuing_study.create_date
            FROM
                t_continuing_study
                INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                INNER JOIN univ_to_faculty ON m_faculty.faculty_code = univ_to_faculty.faculty_code
                INNER JOIN m_university ON m_university.university_code = univ_to_faculty.university_code
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
            JSONResponseFormat = continuing_studyJson(data)
            JSONResponseFormat.update({"employee_name": employeeDictName[data["employee_code"]]})
            dataJSON.append(JSONResponseFormat)

        return make_response(jsonify({
            "data":dataJSON,
            "success": True}), 200)
    except psycopg2.Error as error:
        print(error)
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)
    
@bp.route("/classreport/continuing_study/<classroom_code>/<organization_code>")
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
                'Proxy-Authorization': current_app.config['STUDENT_SERVICES'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
            }
        
        url = (current_app.config['STUDENT_SERVICES']+"/employee_education_detail_paging")

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
                continuing_study_code,
                students.student_code,
                students.student_name,
                m_study_program.study_program_code,
                m_study_program.study_program_name,
                m_faculty.faculty_code,
                m_faculty.faculty_name,
                m_university.university_code,
                m_university.university_name,
                employee_code,
                continuing_study_date,
                result,
                continuing_study_note
            FROM
                t_continuing_study
                INNER JOIN m_study_program ON m_study_program.study_program_code = t_continuing_study.study_program_code
                INNER JOIN m_faculty ON m_study_program.faculty_code = m_faculty.faculty_code
                INNER JOIN univ_to_faculty ON m_faculty.faculty_code = univ_to_faculty.faculty_code
                INNER JOIN m_university ON m_university.university_code = univ_to_faculty.university_code
                INNER JOIN students ON t_continuing_study.student_code = students.student_code
            WHERE
                continuing_study_date BETWEEN %s AND %s
        """, (dateStartFirst, dateEndSecond,))

        classReportDatas = cur.fetchall()
        cur.close()
        conn.close()

        classReportJSON = list()

        for data in classReportDatas:
            classReportJSON.append(continuing_studyReportJson(data))

        return make_response(jsonify({
            "data":classReportJSON,
            "success": True}), 200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)