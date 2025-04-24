import psycopg2
import logging
from psycopg2 import sql
DB_CONFIG = {
    'dbname': 'DNR_MAYME',
    'user': 'flask_user',
    'password': 'password123',
    'host': '185.229.232.131',
    'port': '5432',
    'client_encoding': 'utf-8'
}

def safe_decode(text):
    try:
        return str(text)  # Если текст уже в Unicode
    except UnicodeError:
        return text.encode('latin1').decode('utf-8', errors='replace')

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def get_info():
    conn = get_db_connection()
    cursor = conn.cursor()


    table_name = 'users'

    cursor.execute(sql.SQL("SELECT * FROM {} LIMIT0").format(sql.Identifier(table_name)))
    column_names = [desc[0] for desc in cursor.description]

    selected_columns = [column_names[1], column_names[8]]

    return selected_columns