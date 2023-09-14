from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

bp = Blueprint("faculty", __name__)

def facultyJson(item):
    return {
        "faculty_code": item["faculty_code"],
        "university_code": item["university_code"],
        "faculty_name": item["faculty_name"],
        "faculty_note": item["faculty_note"]
    }

@bp.route("/facultys", methods=["POST"])
@token_required
def facultys():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('faculty_name' in content.keys()) or len(content['faculty_name']) == 0):
                error+="Nama Fakultas Kosong! "
            if(not('university_code' in content.keys()) or len(content['university_code']) == 0):
                error+="Nama Universitas Tidak Boleh Kosong! "
            
            faculty_note = ""
            if('faculty_note' in content.keys()):
                faculty_note = content["faculty_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('FAL',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(faculty_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as faculty_code
                FROM
                    m_faculty
                WHERE
                    faculty_code LIKE CONCAT('FAL',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            faculty_code = data["faculty_code"]
            
            cur.execute("""
                INSERT INTO
                    m_faculty
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                faculty_code, 
                content['university_code'],
                content['faculty_name'], 
                faculty_note, 
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

@bp.route("/faculty/<faculty_code>", methods=["GET", "PUT", "DELETE"])
@token_required
def faculty(faculty_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM m_faculty
                WHERE faculty_code = %s
            """, (faculty_code,))

            data = cur.fetchone()
            return make_response(jsonify(facultyJson(data)))
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
            if(not('faculty_name' in content.keys()) or len(content['faculty_name']) == 0):
                error+="Nama Fakultas Kosong! "
            
            faculty_note = ""
            if('faculty_note' in content.keys()):
                faculty_note = content["faculty_note"]
            if(not('university_code' in content.keys()) or len(content['university_code']) == 0):
                error+="Nama Universitas Tidak Boleh Kosong! "

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                UPDATE
                    m_faculty
                SET
                    faculty_name = %s,
                    university_code = %s
                    faculty_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    faculty_code = %s
            """, (
                content['faculty_name'],
                content['university_code'], 
                faculty_note, 
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                faculty_code,))
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
                    m_faculty
                WHERE 
                    faculty_code = %s
                RETURNING *
            """, (faculty_code,))
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

@bp.route("/pagination_faculty", methods=["POST"])
@token_required
def pagination_faculty():
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
                    m_faculty
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
                    m_faculty
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
        
        facultys = []
        for data in datas:
            facultys.append(facultyJson(data))

        return util.log_response(
        {
            "data": facultys,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)