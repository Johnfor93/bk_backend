from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime
import time

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

bp = Blueprint("continuing_study", __name__)

def continuing_studyJson(item):
    return {
        "continuing_study_code"     : item["continuing_study_code"],
        "student_code"          : item["student_code"],
        "study_program_code"            : item["study_program_code"],
        "employee_code"         : item["employee_code"],
        "continuing_study_date"     : item["continuing_study_date"],
        "result"            : item["result"],
        "continuing_study_note"     : item["continuing_study_note"]
    }

@bp.route("/continuing_studys", methods=["POST"])
@token_required
def continuing_studys():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

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
            """, (
                continuing_study_code,
                content['student_code'],
                content['study_program_code'],
                content['employee_code'],
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

@bp.route("/continuing_study/<continuing_study_code>", methods=["GET", "PUT", "DELETE"])
@token_required
def continuing_study(continuing_study_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM t_continuing_study
                WHERE continuing_study_code = %s
            """, (continuing_study_code,))

            data = cur.fetchone()
            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            return make_response(jsonify(continuing_studyJson(data)))
        except psycopg2.Error as error:
            return make_response(jsonify({
                "success": False,
                "message": error.pgerror,
            }), 400)

    elif request.method == "PUT":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

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
                content['employee_code'],
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
@token_required
def pagination_continuing_study():
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
                    t_continuing_study
                """ + util.sort(content) + """
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
                    t_continuing_study
                WHERE
                    (""" + util.filter(content) + """) """ + util.sort(content) + """
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
            continuing_studys.append(continuing_studyJson(data))

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