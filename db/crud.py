from fastapi import HTTPException
from mysql.connector import Error
from db.connection import get_db_connection
from core.security import hash_password, verify_password
import aiomysql
from db.connection import get_async_db_connection

# User CRUD

def create_user(email: str, password: str, role: str = "basic"):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        hashed_password = hash_password(password)
        query = "INSERT INTO users (email, hashed_password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, hashed_password, role))
        connection.commit()
        user_id = cursor.lastrowid
        return user_id
    except Error as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

def authenticate_user(email: str, password: str):
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        if user and verify_password(password, user['hashed_password']):
            return user
        return None
    except Error:
        return None
    finally:
        connection.close()

def get_user_by_id(user_id: int):
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        return user
    except Error:
        return None
    finally:
        connection.close()

def log_request(user_id: int, endpoint: str, status_code: int, response_time: float):
    connection = get_db_connection()
    if not connection:
        return
    try:
        cursor = connection.cursor()
        query = "INSERT INTO logs (user_id, endpoint, status_code, response_time) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, endpoint, status_code, response_time))
        connection.commit()
    except Error as e:
        print(f"Logging error: {e}")
    finally:
        connection.close()

async def async_create_user(email: str, password: str, role: str = "basic"):
    pool = await get_async_db_connection()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                hashed_password = hash_password(password)
                query = "INSERT INTO users (email, hashed_password, role) VALUES (%s, %s, %s)"
                await cursor.execute(query, (email, hashed_password, role))
                await conn.commit()
                user_id = cursor.lastrowid
                return user_id
            except aiomysql.IntegrityError as e:
                if "Duplicate entry" in str(e):
                    raise HTTPException(status_code=400, detail="Email already registered")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 