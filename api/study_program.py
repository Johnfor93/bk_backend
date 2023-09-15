from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

bp = Blueprint("study_program", __name__)

def study_programJson(item):
    return {
        "study_program_code": item["study_program_code"],
        "faculty_code": item["faculty_code"],
        "study_program_name": item["study_program_name"],
        "study_program_note": item["study_program_note"]
    }

@bp.route("/study_programs", methods=["POST"])
@token_required
def study_programs():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('study_program_name' in content.keys()) or len(content['study_program_name']) == 0):
                error+="Nama Program Studi Kosong! "
            if(not('faculty_code' in content.keys()) or len(content['faculty_code']) == 0):
                error+="Nama Fakultas Tidak Boleh Kosong! "
            
            study_program_note = ""
            if('study_program_note' in content.keys()):
                study_program_note = content["study_program_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('SP',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(study_program_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as study_program_code
                FROM
                    m_study_program
                WHERE
                    study_program_code LIKE CONCAT('SP',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            study_program_code = data["study_program_code"]
            
            cur.execute("""
                INSERT INTO
                    m_study_program
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                study_program_code, 
                content['faculty_code'],
                content['study_program_name'], 
                study_program_note, 
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

@bp.route("/study_program/<study_program_code>", methods=["GET", "PUT", "DELETE"])
@token_required
def study_program(study_program_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM m_study_program
                WHERE study_program_code = %s
            """, (study_program_code,))

            data = cur.fetchone()

            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            return make_response(jsonify(study_programJson(data)))
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
            if(not('study_program_name' in content.keys()) or len(content['study_program_name']) == 0):
                error+="Nama Program Studi Kosong! "
            if(not('faculty_code' in content.keys()) or len(content['faculty_code']) == 0):
                error+="Nama Fakultas Tidak Boleh Kosong! "
            
            study_program_note = ""
            if('study_program_note' in content.keys()):
                study_program_note = content["study_program_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                UPDATE
                    m_study_program
                SET
                    study_program_name = %s,
                    faculty_code = %s,
                    study_program_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    study_program_code = %s
                RETURNING *
            """, (
                content['study_program_name'],
                content['faculty_code'], 
                study_program_note, 
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                study_program_code,))
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
                    m_study_program
                WHERE 
                    study_program_code = %s
                RETURNING *
            """, (study_program_code,))
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

@bp.route("/pagination_study_program", methods=["POST"])
@token_required
def pagination_study_program():
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
                    m_study_program
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
                    m_study_program
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
        
        study_programs = []
        for data in datas:
            study_programs.append(study_programJson(data))

        return util.log_response(
        {
            "data": study_programs,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)