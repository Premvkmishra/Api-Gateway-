from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import time
import redis
import mysql.connector
from mysql.connector import Error
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional, List
import json
from contextlib import asynccontextmanager

# Configuration
DATABASE_URL = "mysql://root:OkMAOoUvUwSGUusrqrdYVBSxORzdnqCC@yamanote.proxy.rlwy.net:20143/intel"
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis configuration (you'll need to set this up)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("Redis connected successfully")
except:
    print("Redis not available - rate limiting will be disabled")
    redis_client = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Pydantic models
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

# Database connection
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

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Database operations
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

def log_request(user_id: Optional[int], endpoint: str, status_code: int, response_time: float):
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

# Rate limiting
def check_rate_limit(identifier: str, limit: int = 60, window: int = 60) -> bool:
    if not redis_client:
        return True
    
    current_time = int(time.time())
    window_start = current_time - window
    
    # Remove old entries
    redis_client.zremrangebyscore(f"rate_limit:{identifier}", 0, window_start)
    
    # Count current requests
    current_count = redis_client.zcard(f"rate_limit:{identifier}")
    
    if current_count >= limit:
        return False
    
    # Add current request
    redis_client.zadd(f"rate_limit:{identifier}", {str(current_time): current_time})
    redis_client.expire(f"rate_limit:{identifier}", window)
    
    return True

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Role-based access control
def require_role(required_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return current_user
    return role_checker

# Middleware for request logging and rate limiting
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("IntelliRoute API Gateway starting up...")
    yield
    # Shutdown
    print("IntelliRoute API Gateway shutting down...")

app = FastAPI(
    title="IntelliRoute API Gateway",
    description="Intelligent API Router with authentication, rate limiting, and logging",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Get user ID if authenticated
    user_id = None
    try:
        if "authorization" in request.headers:
            token = request.headers["authorization"].replace("Bearer ", "")
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
    except:
        pass
    
    # Rate limiting
    client_ip = request.client.host
    rate_limit_key = f"ip:{client_ip}" if not user_id else f"user:{user_id}"
    
    if not check_rate_limit(rate_limit_key, limit=100):  # 100 requests per minute
        log_request(user_id, str(request.url.path), 429, 0)
        raise HTTPException(status_code=429, detail="Too many requests")
    
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Log the request
    log_request(user_id, str(request.url.path), response.status_code, process_time)
    
    return response

# Static files for frontend
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    print("Static directory not found - creating it...")
    import os
    os.makedirs("static", exist_ok=True)

# Authentication routes
@app.post("/auth/register")
async def register(user: UserCreate):
    user_id = create_user(user.email, user.password, user.role)
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/auth/login")
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

# Protected route to get current user info
@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "created_at": current_user["created_at"]
    }

# Simulated microservices with role-based access
@app.get("/service-a/data")
async def service_a_data(current_user: dict = Depends(require_role(["admin", "premium", "basic"]))):
    return {
        "service": "Service A",
        "data": "Public data accessible to all authenticated users",
        "user_role": current_user["role"]
    }

@app.get("/service-b/premium-data")
async def service_b_premium(current_user: dict = Depends(require_role(["admin", "premium"]))):
    return {
        "service": "Service B",
        "data": "Premium data accessible to premium and admin users only",
        "user_role": current_user["role"]
    }

@app.get("/service-c/admin-data")
async def service_c_admin(current_user: dict = Depends(require_role(["admin"]))):
    return {
        "service": "Service C",
        "data": "Admin-only data with sensitive information",
        "user_role": current_user["role"]
    }

# Dummy microservices endpoints
@app.get("/data")
async def data_service(current_user: dict = Depends(get_current_user)):
    return {"service": "Data Service", "message": "Data retrieved successfully", "timestamp": datetime.now()}

@app.get("/notifications")
async def notifications_service(current_user: dict = Depends(require_role(["admin", "premium"]))):
    return {"service": "Notifications Service", "notifications": ["Welcome!", "New feature available"], "timestamp": datetime.now()}

@app.get("/user-profile")
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

# Admin panel routes
@app.get("/admin/logs")
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
        
        # Get total count
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

@app.get("/admin/users")
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

@app.put("/admin/users/{user_id}/role")
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

# Dashboard endpoint (serves HTML)
@app.get("/dashboard", response_class=HTMLResponse)
async def frontend_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IntelliRoute Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .auth-section {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 40px;
            }
            
            .auth-card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                border: 1px solid #e0e0e0;
            }
            
            .auth-card h3 {
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            
            .form-group input, .form-group select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
            }
            
            .api-section {
                margin-top: 30px;
            }
            
            .api-endpoints {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .endpoint-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #667eea;
            }
            
            .endpoint-card h4 {
                color: #333;
                margin-bottom: 10px;
            }
            
            .endpoint-card p {
                color: #666;
                margin-bottom: 15px;
                font-size: 14px;
            }
            
            .role-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .role-admin { background: #ffe6e6; color: #dc3545; }
            .role-premium { background: #fff3cd; color: #856404; }
            .role-basic { background: #d4edda; color: #155724; }
            
            .test-btn {
                padding: 8px 16px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .user-info {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: none;
            }
            
            .response-area {
                background: #1e1e1e;
                color: #fff;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                max-height: 200px;
                overflow-y: auto;
                white-space: pre-wrap;
            }
            
            .alert {
                padding: 10px 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            
            @media (max-width: 768px) {
                .auth-section {
                    grid-template-columns: 1fr;
                }
                
                .api-endpoints {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 IntelliRoute Dashboard</h1>
                <p>Intelligent API Gateway with Authentication & Rate Limiting</p>
            </div>
            
            <div id="userInfo" class="user-info">
                <h4>Welcome back!</h4>
                <p id="userDetails"></p>
                <button onclick="logout()" class="btn" style="width: auto; padding: 8px 16px;">Logout</button>
            </div>
            
            <div class="auth-section">
                <div class="auth-card">
                    <h3>Register</h3>
                    <form id="registerForm">
                        <div class="form-group">
                            <label>Email:</label>
                            <input type="email" id="regEmail" required>
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="regPassword" required>
                        </div>
                        <div class="form-group">
                            <label>Role:</label>
                            <select id="regRole">
                                <option value="basic">Basic</option>
                                <option value="premium">Premium</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">Register</button>
                    </form>
                </div>
                
                <div class="auth-card">
                    <h3>Login</h3>
                    <form id="loginForm">
                        <div class="form-group">
                            <label>Email:</label>
                            <input type="email" id="loginEmail" required>
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="loginPassword" required>
                        </div>
                        <button type="submit" class="btn">Login</button>
                    </form>
                </div>
            </div>
            
            <div class="api-section">
                <h2>API Endpoints</h2>
                <div class="api-endpoints">
                    <div class="endpoint-card">
                        <h4>GET /service-a/data</h4>
                        <p>Public data accessible to all authenticated users</p>
                        <span class="role-badge role-basic">All Users</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/service-a/data')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /service-b/premium-data</h4>
                        <p>Premium data accessible to premium and admin users only</p>
                        <span class="role-badge role-premium">Premium + Admin</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/service-b/premium-data')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /service-c/admin-data</h4>
                        <p>Admin-only data with sensitive information</p>
                        <span class="role-badge role-admin">Admin Only</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/service-c/admin-data')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /data</h4>
                        <p>Data microservice endpoint</p>
                        <span class="role-badge role-basic">All Users</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/data')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /notifications</h4>
                        <p>Notifications microservice</p>
                        <span class="role-badge role-premium">Premium + Admin</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/notifications')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /user-profile</h4>
                        <p>User profile microservice</p>
                        <span class="role-badge role-basic">All Users</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/user-profile')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /admin/logs</h4>
                        <p>View request logs (paginated)</p>
                        <span class="role-badge role-admin">Admin Only</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/admin/logs')">Test</button>
                    </div>
                    
                    <div class="endpoint-card">
                        <h4>GET /admin/users</h4>
                        <p>View all users</p>
                        <span class="role-badge role-admin">Admin Only</span>
                        <br><br>
                        <button class="test-btn" onclick="testEndpoint('/admin/users')">Test</button>
                    </div>
                </div>
                
                <button onclick="testRateLimit()" class="btn" style="width: auto; padding: 10px 20px; margin: 20px auto; display: block;">
                    Test Rate Limiting
                </button>
            </div>
            
            <div id="responseArea" class="response-area" style="display: none;"></div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/docs" target="_blank" style="color: #667eea; text-decoration: none; font-weight: bold;">
                    📚 View Swagger API Documentation
                </a>
            </div>
        </div>

        <script>
            const API_BASE = '';
            let authToken = localStorage.getItem('authToken');
            let currentUser = null;

            // Check if user is logged in on page load
            if (authToken) {
                checkAuthStatus();
            }

            // Register form handler
            document.getElementById('registerForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('regEmail').value;
                const password = document.getElementById('regPassword').value;
                const role = document.getElementById('regRole').value;
                
                try {
                    const response = await fetch(`${API_BASE}/auth/register`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password, role })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showAlert('Registration successful! Please login.', 'success');
                        document.getElementById('registerForm').reset();
                    } else {
                        showAlert(data.detail || 'Registration failed', 'error');
                    }
                } catch (error) {
                    showAlert('Network error: ' + error.message, 'error');
                }
            });

            // Login form handler
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                
                try {
                    const response = await fetch(`${API_BASE}/auth/login`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        authToken = data.access_token;
                        localStorage.setItem('authToken', authToken);
                        currentUser = data.user;
                        showUserInfo();
                        showAlert('Login successful!', 'success');
                        document.getElementById('loginForm').reset();
                    } else {
                        showAlert(data.detail || 'Login failed', 'error');
                    }
                } catch (error) {
                    showAlert('Network error: ' + error.message, 'error');
                }
            });

            // Check authentication status
            async function checkAuthStatus() {
                try {
                    const response = await fetch(`${API_BASE}/auth/me`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    if (response.ok) {
                        currentUser = await response.json();
                        showUserInfo();
                    } else {
                        logout();
                    }
                } catch (error) {
                    logout();
                }
            }

            // Show user info
            function showUserInfo() {
                if (currentUser) {
                    document.getElementById('userInfo').style.display = 'block';
                    document.getElementById('userDetails').innerHTML = `
                        <strong>Email:</strong> ${currentUser.email}<br>
                        <strong>Role:</strong> <span class="role-badge role-${currentUser.role}">${currentUser.role.toUpperCase()}</span><br>
                        <strong>ID:</strong> ${currentUser.id}
                    `;
                }
            }

            // Logout function
            function logout() {
                authToken = null;
                currentUser = null;
                localStorage.removeItem('authToken');
                document.getElementById('userInfo').style.display = 'none';
                showAlert('Logged out successfully', 'success');
            }

            // Test endpoint function
            async function testEndpoint(endpoint) {
                if (!authToken) {
                    showAlert('Please login first to test endpoints', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`${API_BASE}${endpoint}`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    const data = await response.json();
                    
                    const responseArea = document.getElementById('responseArea');
                    responseArea.style.display = 'block';
                    responseArea.innerHTML = `
Endpoint: ${endpoint}
Status: ${response.status} ${response.statusText}
Response:
${JSON.stringify(data, null, 2)}
                    `;
                    
                    if (!response.ok) {
                        showAlert(`Error ${response.status}: ${data.detail || 'Request failed'}`, 'error');
                    } else {
                        showAlert(`Success! Check response below.`, 'success');
                    }
                    
                } catch (error) {
                    showAlert('Network error: ' + error.message, 'error');
                    const responseArea = document.getElementById('responseArea');
                    responseArea.style.display = 'block';
                    responseArea.innerHTML = `Error: ${error.message}`;
                }
            }

            // Show alert function
            function showAlert(message, type) {
                // Remove existing alerts
                const existingAlerts = document.querySelectorAll('.alert');
                existingAlerts.forEach(alert => alert.remove());
                
                const alert = document.createElement('div');
                alert.className = `alert alert-${type}`;
                alert.textContent = message;
                
                document.querySelector('.container').insertBefore(alert, document.querySelector('.auth-section'));
                
                // Auto remove after 5 seconds
                setTimeout(() => alert.remove(), 5000);
            }

            // Test rate limiting
            function testRateLimit() {
                if (!authToken) {
                    showAlert('Please login first', 'error');
                    return;
                }
                
                showAlert('Testing rate limiting with 10 rapid requests...', 'success');
                
                // Make multiple rapid requests to test rate limiting
                for (let i = 0; i < 10; i++) {
                    setTimeout(() => {
                        testEndpoint('/data');
                    }, i * 100);
                }
            }
        </script>
    </body>
    </html>
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IntelliRoute Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .endpoint { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .role-admin { color: #dc3545; font-weight: bold; }
            .role-premium { color: #ffc107; font-weight: bold; }
            .role-basic { color: #28a745; font-weight: bold; }
            .api-docs { text-align: center; margin: 20px 0; }
            .api-docs a { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🚀 IntelliRoute API Gateway</h1>
            <p style="text-align: center; color: #666;">Intelligent API Router with Authentication, Rate Limiting, and Logging</p>
            
            <div class="section">
                <h2>Authentication Endpoints</h2>
                <div class="endpoint">POST /auth/register - Register new user</div>
                <div class="endpoint">POST /auth/login - Login user</div>
                <div class="endpoint">GET /auth/me - Get current user info</div>
            </div>
            
            <div class="section">
                <h2>Protected Services</h2>
                <div class="endpoint">GET /service-a/data - <span class="role-basic">All authenticated users</span></div>
                <div class="endpoint">GET /service-b/premium-data - <span class="role-premium">Premium & Admin only</span></div>
                <div class="endpoint">GET /service-c/admin-data - <span class="role-admin">Admin only</span></div>
            </div>
            
            <div class="section">
                <h2>Microservices</h2>
                <div class="endpoint">GET /data - Data Service</div>
                <div class="endpoint">GET /notifications - Notifications Service (Premium+)</div>
                <div class="endpoint">GET /user-profile - User Profile Service</div>
            </div>
            
            <div class="section">
                <h2>Admin Panel</h2>
                <div class="endpoint">GET /admin/logs - View request logs <span class="role-admin">(Admin only)</span></div>
                <div class="endpoint">GET /admin/users - View all users <span class="role-admin">(Admin only)</span></div>
                <div class="endpoint">PUT /admin/users/{id}/role - Update user role <span class="role-admin">(Admin only)</span></div>
            </div>
            
            <div class="api-docs">
                <a href="/docs" target="_blank">📚 View API Documentation</a>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #666;">
                <p>Features: JWT Authentication | Role-Based Access Control | Rate Limiting | Request Logging</p>
            </div>
        </div>
    </body>
    </html>
    """
# Root endpoint - Simple navigation page
@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IntelliRoute API Gateway</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container { 
                max-width: 800px; 
                background: rgba(255, 255, 255, 0.95);
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
            }
            .header { 
                color: #333; 
                margin-bottom: 30px; 
            }
            .header h1 {
                font-size: 3em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .nav-links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .nav-link {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-decoration: none;
                color: #333;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s;
                border: 2px solid transparent;
            }
            .nav-link:hover {
                transform: translateY(-5px);
                border-color: #667eea;
            }
            .nav-link h3 {
                margin: 0 0 10px 0;
                color: #667eea;
            }
            .nav-link p {
                margin: 0;
                color: #666;
                font-size: 14px;
            }
            .features {
                margin-top: 40px;
                text-align: left;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .feature {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .feature h4 {
                margin: 0 0 8px 0;
                color: #333;
            }
            .feature p {
                margin: 0;
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Api Gateway</h1>
                <p>Intelligent API Gateway with Authentication, Rate Limiting, and Logging</p>
            </div>
            
            <div class="nav-links">
                <a href="/dashboard" class="nav-link">
                    <h3>📊 Dashboard</h3>
                    <p>Interactive frontend for testing APIs</p>
                </a>
                
                <a href="/docs" class="nav-link">
                    <h3>📚 API Docs</h3>
                    <p>Swagger documentation</p>
                </a>
                
                <a href="/health" class="nav-link">
                    <h3>🏥 Health Check</h3>
                    <p>System status and health</p>
                </a>
            </div>
            
            <div class="features">
                <h2>Features</h2>
                <div class="feature-grid">
                    <div class="feature">
                        <h4>🔐 JWT Authentication</h4>
                        <p>Secure token-based authentication system</p>
                    </div>
                    <div class="feature">
                        <h4>👥 Role-Based Access</h4>
                        <p>Admin, Premium, and Basic user roles</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ Rate Limiting</h4>
                        <p>Redis-based request throttling</p>
                    </div>
                    <div class="feature">
                        <h4>📝 Request Logging</h4>
                        <p>Comprehensive request tracking</p>
                    </div>
                    <div class="feature">
                        <h4>🔀 Dynamic Routing</h4>
                        <p>Intelligent request routing</p>
                    </div>
                    <div class="feature">
                        <h4>🛡️ Admin Panel</h4>
                        <p>User management and analytics</p>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Start by registering a new user or login with existing credentials</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "database": "connected" if get_db_connection() else "disconnected",
            "redis": "connected" if redis_client else "disconnected"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)