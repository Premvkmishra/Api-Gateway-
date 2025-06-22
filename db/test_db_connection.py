from connection import get_db_connection

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("✅ Successfully connected to the Railway MySQL database!")
        conn.close()
    else:
        print("❌ Failed to connect to the Railway MySQL database.") 