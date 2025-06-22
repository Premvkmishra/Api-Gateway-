from db.connection import get_db_connection
from core.security import hash_password
import random
import time

if __name__ == "__main__":
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to the Railway MySQL database.")
        exit(1)
    cursor = conn.cursor()
    try:
        # Insert dummy user
        email = f"dummy{random.randint(1000,9999)}@test.com"
        password = hash_password("testpassword123")
        role = random.choice(["basic", "premium", "admin"])
        cursor.execute(
            "INSERT INTO users (email, hashed_password, role) VALUES (%s, %s, %s)",
            (email, password, role)
        )
        user_id = cursor.lastrowid
        print(f"✅ Inserted dummy user: {email} (id={user_id}, role={role})")

        # Insert dummy log
        endpoint = "/test/endpoint"
        status_code = 200
        response_time = round(random.uniform(0.05, 0.5), 3)
        cursor.execute(
            "INSERT INTO logs (user_id, endpoint, status_code, response_time) VALUES (%s, %s, %s, %s)",
            (user_id, endpoint, status_code, response_time)
        )
        log_id = cursor.lastrowid
        print(f"✅ Inserted dummy log (id={log_id}) for user_id={user_id}")

        conn.commit()
    except Exception as e:
        print(f"❌ Error inserting dummy data: {e}")
    finally:
        cursor.close()
        conn.close() 