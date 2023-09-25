from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime

import psycopg2

from .database import get_db_connection
from . import util
from .auth import employee_required

bp = Blueprint("provider", __name__)

def providerJson(item):
    return {
        "provider_code": item["provider_code"],
        "phone": item["phone"],
        "provider_name": item["provider_name"],
        "provider_note": item["provider_note"]
    }

@bp.route("/providers", methods=["POST"])
@employee_required
def providers():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.get_json()

            error = ""
            if(not('provider_name' in content.keys()) or len(content['provider_name']) == 0):
                error+="Nama Provider Kosong! "
            if(not('phone' in content.keys()) or len(content['phone']) == 0):
                error+="Nomor Telpon Tidak Boleh Kosong! "
            
            provider_note = ""
            if('provider_note' in content.keys()):
                provider_note = content["provider_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('P',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(provider_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as provider_code
                FROM
                    m_provider
                WHERE
                    provider_code LIKE CONCAT('P',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            provider_code = data["provider_code"]
            
            cur.execute("""
                INSERT INTO
                    m_provider
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                provider_code, 
                content['provider_name'], 
                content['phone'],
                provider_note, 
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

@bp.route("/provider/<provider_code>", methods=["GET", "PUT", "DELETE"])
@employee_required
def provider(provider_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT *
                FROM m_provider
                WHERE provider_code = %s
            """, (provider_code,))

            data = cur.fetchone()

            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            return make_response(jsonify(providerJson(data)))
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
            if(not('provider_name' in content.keys()) or len(content['provider_name']) == 0):
                error+="Nama Provider Kosong! "
            if(not('phone' in content.keys()) or len(content['phone']) == 0):
                error+="Nomor Telpon Tidak Boleh Kosong! "
            
            provider_note = ""
            if('provider_note' in content.keys()):
                provider_note = content["provider_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                UPDATE
                    m_provider
                SET
                    provider_name = %s,
                    phone = %s,
                    provider_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    provider_code = %s
                RETURNING *
            """, (
                content['provider_name'],
                content['phone'], 
                provider_note, 
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                provider_code,))
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
                    m_provider
                WHERE 
                    provider_code = %s
                RETURNING *
            """, (provider_code,))
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

@bp.route("/pagination_provider", methods=["POST"])
@employee_required
def pagination_provider():
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
                    m_provider
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
                    m_provider
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
        
        providers = []
        for data in datas:
            providers.append(providerJson(data))

        return util.log_response(
        {
            "data": providers,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)