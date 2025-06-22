import mysql.connector
from mysql.connector import Error
import aiomysql
import asyncio

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

# Async connection pool (singleton)
_async_pool = None

async def get_async_db_connection():
    global _async_pool
    if _async_pool is None:
        _async_pool = await aiomysql.create_pool(
            host='yamanote.proxy.rlwy.net',
            port=20143,
            db='intel',
            user='root',
            password='OkMAOoUvUwSGUusrqrdYVBSxORzdnqCC',
            autocommit=True,
            minsize=1,
            maxsize=5
        )
    return _async_pool 