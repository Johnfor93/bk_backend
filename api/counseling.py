from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

bp = Blueprint("counseling", __name__)

def counselingJson(item):
    return {
        "counseling_code"       : item["counseling_code"],
        "student_code"          : item["student_code"],
        "scope_code"            : item["scope_code"],
        "category_code"         : item["category_code"],
        "employee_code"         : item["employee_code"],
        "counseling_date"       : item["counseling_date"],
        "problem"               : item["problem"],
        "conclusion"            : item["conclusion"],
        "followup"              : item["followup"],
        "counseling_note"       : item["counseling_note"]
    }

@bp.route("/counselings", methods=["POST"])
@token_required
def counselings():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('scope_code' in content.keys()) or len(content['scope_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('category_code' in content.keys()) or len(content['category_code']) == 0):
                error+="Kategori Masalah Tidak Boleh Kosong! "
            if(not('employee_code' in content.keys()) or len(content['employee_code']) == 0):
                error+="Kode Pegawai Tidak Boleh Kosong! "
            if(not('counseling_date' in content.keys()) or len(content['counseling_date']) == 0):
                error+="Tanggal Konseling Tidak Boleh Kosong! "
            if(not('problem' in content.keys()) or len(content['problem']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('conclusion' in content.keys()) or len(content['conclusion']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Nomor Telpon Tidak Boleh Kosong! "
            
            counseling_note = ""
            if('counseling_note' in content.keys()):
                counseling_note = content["counseling_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('CON',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(counseling_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as counseling_code
                FROM
                    t_counseling
                WHERE
                    counseling_code LIKE CONCAT('CON',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            counseling_code = data["counseling_code"]
            
            cur.execute("""
                INSERT INTO
                    t_counseling
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                counseling_code,
                content['student_code'],
                content['scope_code'],
                content['category_code'],
                content['employee_code'],
                content['counseling_date'],
                content['problem'],
                content['conclusion'],
                content['followup'],
                counseling_note,
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

@bp.route("/counseling/<counseling_code>", methods=["GET", "PUT", "DELETE"])
@token_required
def counseling(counseling_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM t_counseling
                WHERE counseling_code = %s
            """, (counseling_code,))

            data = cur.fetchone()

            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            return make_response(jsonify(counselingJson(data)))
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
            if(not('scope_code' in content.keys()) or len(content['scope_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('category_code' in content.keys()) or len(content['category_code']) == 0):
                error+="Kategori Masalah Tidak Boleh Kosong! "
            if(not('employee_code' in content.keys()) or len(content['employee_code']) == 0):
                error+="Kode Pegawai Tidak Boleh Kosong! "
            if(not('counseling_date' in content.keys()) or len(content['counseling_date']) == 0):
                error+="Tanggal Konseling Tidak Boleh Kosong! "
            if(not('problem' in content.keys()) or len(content['problem']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('conclusion' in content.keys()) or len(content['conclusion']) == 0):
                error+="Masalah Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Nomor Telpon Tidak Boleh Kosong! "
            
            counseling_note = ""
            if('counseling_note' in content.keys()):
                counseling_note = content["counseling_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                UPDATE
                    t_counseling
                SET
                    student_code = %s,
                    scope_code = %s,
                    category_code = %s,
                    employee_code = %s,
                    counseling_date = %s,
                    problem = %s,
                    conclusion = %s,
                    followup = %s,
                    counseling_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    counseling_code = %s
                RETURNING *
            """, (
                content['student_code'],
                content['scope_code'],
                content['category_code'],
                content['employee_code'],
                content['counseling_date'],
                content['problem'],
                content['conclusion'],
                content['followup'],
                counseling_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                counseling_code,))
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
                    t_counseling
                WHERE 
                    counseling_code = %s
                RETURNING *
            """, (counseling_code,))
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

@bp.route("/pagination_counseling", methods=["POST"])
@token_required
def pagination_counseling():
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
                    t_counseling
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
                    t_counseling
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
        
        counselings = []
        for data in datas:
            counselings.append(counselingJson(data))

        return util.log_response(
        {
            "data": counselings,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)