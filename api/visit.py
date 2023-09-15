from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

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
        "visit_note"     : item["visit_note"]
    }

@bp.route("/visits", methods=["POST"])
@token_required
def visits():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('employee_code' in content.keys()) or len(content['employee_code']) == 0):
                error+="Kode Pegawai Tidak Boleh Kosong! "
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
            
            cur.execute("""
                INSERT INTO
                    t_visit
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                visit_code,
                content['student_code'],
                content['employee_code'],
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
@token_required
def visit(visit_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM t_visit
                WHERE visit_code = %s
            """, (visit_code,))

            data = cur.fetchone()
            return make_response(jsonify(visitJson(data)))
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
            if(not('employee_code' in content.keys()) or len(content['employee_code']) == 0):
                error+="Kode Pegawai Tidak Boleh Kosong! "
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
                content['employee_code'],
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
                }, 200, request.method) 

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
                }, 200, request.method) 

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
@token_required
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
                    t_visit
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