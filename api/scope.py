from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required

bp = Blueprint("scope", __name__)

def scopeJson(item):
    return {
        "scope_code": item["scope_code"],
        "scope_name": item["scope_name"],
        "scope_note": item["scope_note"]
    }

@bp.route("/scopes", methods=["POST"])
@token_required
def scopes():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('scope_name' in content.keys()) or len(content['scope_name']) == 0):
                error+="Nama Batasan Kosong! "
            
            scope_note = ""
            if('scope_note' in content.keys()):
                scope_note = content["scope_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('SC',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(scope_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as scope_code
                FROM
                    m_scope
                WHERE
                    scope_code LIKE CONCAT('SC',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            scope_code = data["scope_code"]
            
            cur.execute("""
                INSERT INTO
                    m_scope
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                scope_code, 
                content['scope_name'], 
                scope_note, 
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

@bp.route("/scope/<scope_code>", methods=["GET", "PUT", "DELETE"])
@token_required
def scope(scope_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM m_scope
                WHERE scope_code = %s
            """, (scope_code,))

            data = cur.fetchone()
            return make_response(jsonify(scopeJson(data)))
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
            if(not('scope_name' in content.keys()) or len(content['scope_name']) == 0):
                error+="Nama Batasan Kosong! "
            
            scope_note = ""
            if('scope_note' in content.keys()):
                scope_note = content["scope_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                UPDATE
                    m_scope
                SET
                    scope_name = %s,
                    scope_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    scope_code = %s
                RETURNING *
            """, (
                content['scope_name'], 
                scope_note, 
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                scope_code,))
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
                    m_scope
                WHERE 
                    scope_code = %s
                RETURNING *
            """, (scope_code,))
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

@bp.route("/pagination_scope", methods=["POST"])
@token_required
def pagination_scope():
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
                    m_scope
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
                    m_scope
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
        
        scopes = []
        for data in datas:
            scopes.append(scopeJson(data))

        return util.log_response(
        {
            "data": scopes,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)