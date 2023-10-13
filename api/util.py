from flask import (
    make_response, jsonify, request, current_app
)
import inspect
from datetime import datetime
from .database import get_db_connection
import requests
import json

# def log_response(data, status = 200):
#     return make_response(jsonify(data), status)

def getPeriod():
    timenow = datetime.now()

    yearnow = timenow.year
    monthnow = timenow.month

    if(monthnow > 6):
        periodStart = yearnow
        periodEnd = yearnow+1
    else:
        periodStart = yearnow-1
        periodEnd = yearnow

    periodYear = str(periodStart)+"/"+str(periodEnd)

    dateStartFirst = str(periodStart)+"-07-01"
    dateEndFirst = str(periodStart)+"-12-31"

    dateStartSecond = str(periodEnd)+"-01-01"
    dateEndSecond = str(periodEnd)+"-06-30"

    return {
        "periodYear"        : periodYear,
        "dateStartFirst"    : dateStartFirst,
        "dateEndSecond"     : dateEndSecond,
        "dateEndFirst"      : dateEndFirst,
        "dateStartSecond"   : dateStartSecond,
    }

def admin_getStudent(classroom_code, organization_code):
    period = getPeriod()
    payload = {
        "limit": "10000",
        "page": "1",
        "filters": [
            {
                "operator": "contains",
                "search": "period_code",
                "value1": period["periodYear"]
            },
            {
                "operator": "contains",
                "search": "classroom_code",
                "value1": classroom_code
            },
            {
                "operator": "contains",
                "search": "organization_code",
                "value1": organization_code
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

    url = (current_app.config['STUDENT_SERVICES']+"/education_detail_paging")

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    success = response.ok
    if(not success):
        return make_response({
            "message": "Data tidak ditemukan"
        }, 401)
    
    stats = response.json()    
    status_code = response.status_code

    student_code_list = []
    student_name_dict = dict()

    for data in stats["data"]:
        temp = dict()
        temp.update({"student_code": data["student_code"]})
        temp.update({"student_name": data["student_code"]+"NAMA"})
        student_code_list.append(temp)
        student_name_dict.update({data["student_code"]: 1})

    return (student_code_list, student_name_dict)

def log_response(data, status, method):
    if "message" in data:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO
                l_user_response(user_code, route_name, route_method, request_time, response_code, response_message)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """, (current_app.config['USER_CODE'], calframe[1][3], request.method, datetime.now(), status, data["message"]))
        conn.commit()
        cur.close()
        conn.close()
    return make_response(jsonify(data), status)

def filter(content):
    filters = []
    if 'filters' in content:
        filters=content['filters']
    filter_type = ""
    if 'filter_type' in content:
        filter_type=content['filter_type']
    temp = ''
    for filter in filters:
        if(temp != ''):
            temp+=filter_type
        temp = temp + " " + filter['search'] + " ILIKE '%" + filter['value'] + "%' "
    return temp

def sort(content):
    sorts = []
    if 'sorts' in content:
        sorts=content['sorts']
    temp = ''
    for sort in sorts:
        if temp == '':
            temp = """
                ORDER BY
                    """ + sort['field'] + """ """ + sort['order']
        else:
            temp = temp + ", " + sort['field'] + " " + sort['order']
    return temp