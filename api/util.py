from flask import (
    make_response, jsonify, request, current_app
)
import inspect
from datetime import datetime
from .database import get_db_connection

# def log_response(data, status = 200):
#     return make_response(jsonify(data), status)

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