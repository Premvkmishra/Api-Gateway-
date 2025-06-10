from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "basic"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

class LogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    endpoint: str
    status_code: int
    response_time: float
    timestamp: datetime

class UserUpdate(BaseModel):
    role: str

class LogRequest(BaseModel):
    endpoint: str
    status_code: int
    response_time: float 