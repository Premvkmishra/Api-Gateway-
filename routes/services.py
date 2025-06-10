from fastapi import APIRouter, Depends
from core.dependencies import require_role, get_current_user
from datetime import datetime

router = APIRouter(tags=["services"])

@router.get("/service-a/data")
async def service_a_data(current_user: dict = Depends(require_role(["admin", "premium", "basic"]))):
    return {
        "service": "Service A",
        "data": "Public data accessible to all authenticated users",
        "user_role": current_user["role"]
    }

@router.get("/service-b/premium-data")
async def service_b_premium(current_user: dict = Depends(require_role(["admin", "premium"]))):
    return {
        "service": "Service B",
        "data": "Premium data accessible to premium and admin users only",
        "user_role": current_user["role"]
    }

@router.get("/service-c/admin-data")
async def service_c_admin(current_user: dict = Depends(require_role(["admin"]))):
    return {
        "service": "Service C",
        "data": "Admin-only data with sensitive information",
        "user_role": current_user["role"]
    }

@router.get("/data")
async def data_service(current_user: dict = Depends(get_current_user)):
    return {"service": "Data Service", "message": "Data retrieved successfully", "timestamp": datetime.now()}

@router.get("/notifications")
async def notifications_service(current_user: dict = Depends(require_role(["admin", "premium"]))):
    return {"service": "Notifications Service", "notifications": ["Welcome!", "New feature available"], "timestamp": datetime.now()}

@router.get("/user-profile")
async def user_profile_service(current_user: dict = Depends(get_current_user)):
    return {
        "service": "User Profile Service",
        "profile": {
            "id": current_user["id"],
            "email": current_user["email"],
            "role": current_user["role"]
        },
        "timestamp": datetime.now()
    } 