from fastapi import APIRouter, Depends, HTTPException
from db.crud import create_user, authenticate_user
from models.schemas import UserCreate, UserLogin
from core.security import create_access_token
from core.dependencies import get_current_user
from datetime import timedelta
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user: UserCreate):
    user_id = create_user(user.email, user.password, user.role)
    return {"message": "User created successfully", "user_id": user_id}

@router.post("/login")
async def login(user: UserLogin):
    authenticated_user = authenticate_user(user.email, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(authenticated_user["id"])},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": authenticated_user["id"],
            "email": authenticated_user["email"],
            "role": authenticated_user["role"]
        }
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "created_at": current_user["created_at"]
    } 