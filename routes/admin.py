from fastapi import APIRouter, Depends, HTTPException
from db.connection import get_db_connection
from core.dependencies import require_role
from models.schemas import UserUpdate
from mysql.connector import Error

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/logs")
async def get_logs(
    page: int = 1,
    size: int = 50,
    current_user: dict = Depends(require_role(["admin"]))
):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        offset = (page - 1) * size
        query = """
        SELECT l.*, u.email as user_email, u.role as user_role
        FROM logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.timestamp DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (size, offset))
        logs = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) as total FROM logs")
        total = cursor.fetchone()["total"]
        return {
            "logs": logs,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size
            }
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

@router.get("/users")
async def get_users(current_user: dict = Depends(require_role(["admin"]))):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC"
        cursor.execute(query)
        users = cursor.fetchall()
        return {"users": users}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role(["admin"]))
):
    if user_update.role not in ["admin", "premium", "basic"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        query = "UPDATE users SET role = %s WHERE id = %s"
        cursor.execute(query, (user_update.role, user_id))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User role updated to {user_update.role}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close() 