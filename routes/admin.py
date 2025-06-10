from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from db.connection import get_db_connection
from core.dependencies import require_role, get_current_user
from models.schemas import UserUpdate, LogRequest
from mysql.connector import Error

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(current_user: dict = Depends(require_role(["admin"]))):
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_role(["admin"]))):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()["total"]
        
        # Get total requests
        cursor.execute("SELECT COUNT(*) as total FROM logs")
        total_requests = cursor.fetchone()["total"]
        
        # Get average response time
        cursor.execute("SELECT AVG(response_time) as avg FROM logs")
        avg_response_time = cursor.fetchone()["avg"] or 0
        
        return {
            "total_users": total_users,
            "total_requests": total_requests,
            "avg_response_time": avg_response_time
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()

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

@router.post("/log-request")
async def log_request(
    log_data: LogRequest,
    current_user: dict = Depends(get_current_user)
):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO logs (user_id, endpoint, status_code, response_time)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            current_user["id"],
            log_data.endpoint,
            log_data.status_code,
            log_data.response_time
        ))
        connection.commit()
        return {"status": "success"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close() 