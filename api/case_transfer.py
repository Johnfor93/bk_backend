from flask import (
    request, Blueprint, current_app, make_response, jsonify
    )
from datetime import datetime
import time
import os
import os.path

import psycopg2

from .database import get_db_connection
from . import util
from .auth import token_required, employee_required

bp = Blueprint("case_transfer", __name__)

def case_transferJson(item):
    return {
        "case_transfer_code"     : item["case_transfer_code"],
        "student_code"          : item["student_code"],
        "provider_code"            : item["provider_code"],
        "provider_name"            : item["provider_name"],
        "employee_code"         : item["employee_code"],
        "case_transfer_date"     : item["case_transfer_date"],
        "result"            : item["result"],
        "followup"              : item["followup"],
        "case_transfer_note"     : item["case_transfer_note"]
    }

def case_transferPagingFormatJSON(item, nameStudent):
    return {
        "case_transfer_code"       : item["case_transfer_code"],
        "student_code"          : item["student_code"],
        "provider_name"            : item["provider_name"],
        "case_transfer_date"       : item["case_transfer_date"],
        "result"               : item["result"],
        "student_name"          : nameStudent[item["student_code"]],
    }

@bp.route("/case_transfers", methods=["POST"])
@employee_required
def case_transfers():
    if(request.method == "POST"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            content = request.form
            uploaded_file = request.files

            error = ""
            if(not('student_code' in content.keys()) or len(content['student_code']) == 0):
                error+="Kode Siswa Tidak Boleh Kosong! "
            if(not('provider_code' in content.keys()) or len(content['provider_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('case_transfer_date' in content.keys()) or len(content['case_transfer_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Hasil Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            case_transfer_note = ""
            if('case_transfer_note' in content.keys()):
                case_transfer_note = content["case_transfer_note"]

            if(len(error) > 0):
                return util.log_response({
                    "success": False,
                    "message": "Data tidak lengkap! " + error,
                }, 400, request.method)

            cur.execute("""
                SELECT
                    CONCAT('CTR',TO_CHAR(CURRENT_DATE,'YYMM'),LPAD(CAST(COALESCE(CAST(MAX(RIGHT(case_transfer_code,4)) AS INT)+1,1) AS VARCHAR),4,'0')) as case_transfer_code
                FROM
                    t_case_transfer
                WHERE
                    case_transfer_code LIKE CONCAT('CTR',TO_CHAR(CURRENT_DATE,'YYMM'),'%')
                """)
            data = cur.fetchone()
            case_transfer_code = data["case_transfer_code"]

            date_format = "%Y-%m-%d"
            now = datetime.now()
            dateNow = now.strftime("%Y-%m-%d")
            date1 = time.mktime(time.strptime(content['case_transfer_date'], date_format))
            date2 = time.mktime(time.strptime(dateNow, date_format))

            delta = date2 - date1
            if int(delta / 86400) > 14:
                return util.log_response({
                    "success": False,
                    "message": "Sudah lebih dari 14 hari untuk melakukan input",
                }, 400, request.method)
            
            cur.execute("""
                INSERT INTO
                    t_case_transfer
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING case_transfer_code
            """, (
                case_transfer_code,
                content['student_code'],
                content['provider_code'],
                current_app.config['USER_CODE'], 
                content['case_transfer_date'],
                content['result'],
                content['followup'],
                case_transfer_note,
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
                uploaded_filename = inserted_id["case_transfer_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CASETRANSFER'], uploaded_filename))

            return util.log_response({
                "success": True,
                "message": "Data sudah dimasukkan"
            }, 200, request.method)
        except psycopg2.Error as error:
            return util.log_response({
                "success": False,
                "message": error.pgerror,
            }, 400, request.method)

@bp.route("/case_transfer/<case_transfer_code>", methods=["GET", "PUT", "DELETE"])
@employee_required
def case_transfer(case_transfer_code):
    if(request.method == "GET"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    case_transfer_code,
                    student_code,
                    m_provider.provider_code,
                    provider_name,
                    employee_code,
                    case_transfer_date,
                    result,
                    followup,
                    case_transfer_note
                FROM t_case_transfer
                INNER JOIN m_provider on m_provider.provider_code = t_case_transfer.provider_code
                WHERE case_transfer_code = %s
            """, (case_transfer_code,))

            data = cur.fetchone()

            if(data == None):
                return make_response({
                    "success": False,
                    "message": "Data tidak ditemukan"
                }, 404) 
            return make_response(jsonify({
                "data":case_transferJson(data),
                "success": True}))
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
            if(not('provider_code' in content.keys()) or len(content['provider_code']) == 0):
                error+="Lingkup Masalah Tidak Boleh Kosong! "
            if(not('case_transfer_date' in content.keys()) or len(content['case_transfer_date']) == 0):
                error+="Tanggal Konsultasi Tidak Boleh Kosong! "
            if(not('result' in content.keys()) or len(content['result']) == 0):
                error+="Konklusi Tidak Boleh Kosong! "
            if(not('followup' in content.keys()) or len(content['followup']) == 0):
                error+="Tindakan Lebih Lanjut Tidak Boleh Kosong! "
            
            case_transfer_note = ""
            if('case_transfer_note' in content.keys()):
                case_transfer_note = content["case_transfer_note"]

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
                    t_case_transfer
                SET
                    student_code = %s,
                    provider_code = %s,
                    employee_code = %s,
                    case_transfer_date = %s,
                    result = %s,
                    followup = %s,
                    case_transfer_note = %s,
                    is_active = %s,
                    update_by = %s,
                    update_date = %s
                WHERE 
                    case_transfer_code = %s
                RETURNING *
            """, (
                content['student_code'],
                content['provider_code'],
                current_app.config['USER_CODE'], 
                content['case_transfer_date'],
                content['result'],
                content['followup'],
                case_transfer_note,
                'Y', 
                current_app.config['USER_CODE'], 
                datetime.now(), 
                case_transfer_code,))
            conn.commit()

            dataUpdated = cur.fetchone()

            if(len(uploaded_file['attachment'].filename) != 0):
                uploaded_file = uploaded_file['attachment']
                uploaded_filename = dataUpdated["case_transfer_code"] + '.' + uploaded_file.filename.split('.')[-1] 
                if(os.path.exists((os.path.join(current_app.config['UPLOAD_FOLDER_CASETRANSFER'], uploaded_filename)))):
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_CASETRANSFER'], uploaded_filename))
                uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_CASETRANSFER'], uploaded_filename))
            
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
                    t_case_transfer
                WHERE 
                    case_transfer_code = %s
                RETURNING *
            """, (case_transfer_code,))
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

@bp.route("/pagination_case_transfer", methods=["POST"])
@employee_required
def pagination_case_transfer():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        content = request.get_json()

        filter= util.filter(content)

        if(filter==''):
            sql = """
                SELECT
                    case_transfer_code,
                    student_code,
                    provider_name,
                    case_transfer_date,
                    result
                FROM
                    t_case_transfer
                    INNER JOIN m_provider on m_provider.provider_code = t_case_transfer.provider_code
                ORDER BY
                    case_transfer_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        else:
            sql = """
                SELECT
                    case_transfer_code,
                    student_code,
                    provider_name,
                    case_transfer_date,
                    result
                FROM
                    t_case_transfer
                    INNER JOIN m_provider on m_provider.provider_code = t_case_transfer.provider_code
                WHERE
                    (""" + util.filter(content) + """
                ORDER BY
                    case_transfer_date DESC
                LIMIT
                    """ + str(content['limit']) + """
                OFFSET
                    """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
                """
        cur.execute(sql)
        print("MASUKK")
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        case_transfers = []
        for data in datas:
            case_transfers.append(case_transferPagingFormatJSON(data))

        return util.log_response(
        {
            "data": case_transfers,
            "message": "success"
        }, 
        200, request.method)
    except psycopg2.Error as error:
        print(error)
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)

# showing attachment file
@bp.route("/case_transfer/attachment/<case_transfer_code>")
def case_transferAttachment(case_transfer_code):
    filename_attachment = case_transfer_code + ".pdf"
    path_file_attachment = os.path.join(current_app.config['UPLOAD_FOLDER_CASETRANSFER'], filename_attachment)
    not_found = os.path.join(current_app.config['UPLOAD_FOLDER'], '404.png')
    if(os.path.isfile(path_file_attachment)):
        return send_file(path_file_attachment)
    else:
        return make_response({
            "success": False
        }, 404)
    
@bp.route("/employee_pagination_case_transfer", methods=["POST"])
@employee_required
def employee_pagination_case_transfer():
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
                case_transfer_code,
                student_code,
                provider_name,
                case_transfer_date,
                result
            FROM
                t_case_transfer
                INNER JOIN m_provider on m_provider.provider_code = t_case_transfer.provider_code
            WHERE
                student_code = ANY(%s)
            ORDER BY
                case_transfer_date DESC
            LIMIT
                """ + str(content['limit']) + """
            OFFSET
                """ + str(int(content['limit']) * (int(content['page']) - 1)) + """
            """
        
        cur.execute(sql, (list(listStundent),))
        datas = cur.fetchall()
        cur.close()
        conn.close()
        
        case_transfers = []
        for data in datas:
            case_transfers.append(case_transferPagingFormatJSON(data, nameStudent))

        return make_response(
        {
            "data": case_transfers,
            "message": "success"
        }, 
        200)
    except psycopg2.Error as error:
        return make_response(jsonify({
            "success": False,
            "message": error.pgerror,
        }), 400)