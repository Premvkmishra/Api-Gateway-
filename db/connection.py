import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='yamanote.proxy.rlwy.net',
            port=20143,
            database='intel',
            user='root',
            password='OkMAOoUvUwSGUusrqrdYVBSxORzdnqCC'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None 