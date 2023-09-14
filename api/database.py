import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    conn = psycopg2.connect(
        host = os.environ.get("DB_HOST"), 
        database = os.environ.get("DB_NAME"), 
        user = os.environ.get("DB_USERNAME"), 
        password = os.environ.get("DB_PASS"),
        cursor_factory=RealDictCursor
    )
    return conn
