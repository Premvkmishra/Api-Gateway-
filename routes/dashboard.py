from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from db.connection import get_db_connection
from core.rate_limit import redis_client
from datetime import datetime

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard", response_class=HTMLResponse)
async def frontend_dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IntelliRoute API Gateway</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
            .container { max-width: 800px; background: rgba(255, 255, 255, 0.95); padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }
            .header { color: #333; margin-bottom: 30px; }
            .header h1 { font-size: 3em; margin-bottom: 10px; background: linear-gradient(45deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .nav-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
            .nav-link { background: white; padding: 20px; border-radius: 10px; text-decoration: none; color: #333; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.3s; border: 2px solid transparent; }
            .nav-link:hover { transform: translateY(-5px); border-color: #667eea; }
            .nav-link h3 { margin: 0 0 10px 0; color: #667eea; }
            .nav-link p { margin: 0; color: #666; font-size: 14px; }
            .features { margin-top: 40px; text-align: left; }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
            .feature { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; }
            .feature h4 { margin: 0 0 8px 0; color: #333; }
            .feature p { margin: 0; color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Api Gateway</h1>
                <p>Intelligent API Gateway with Authentication, Rate Limiting, and Logging</p>
            </div>
            <div class="nav-links">
                <a href="/dashboard" class="nav-link"><h3>📊 Dashboard</h3><p>Interactive frontend for testing APIs</p></a>
                <a href="/docs" class="nav-link"><h3>📚 API Docs</h3><p>Swagger documentation</p></a>
                <a href="/health" class="nav-link"><h3>🏥 Health Check</h3><p>System status and health</p></a>
            </div>
            <div class="features">
                <h2>Features</h2>
                <div class="feature-grid">
                    <div class="feature"><h4>🔐 JWT Authentication</h4><p>Secure token-based authentication system</p></div>
                    <div class="feature"><h4>👥 Role-Based Access</h4><p>Admin, Premium, and Basic user roles</p></div>
                    <div class="feature"><h4>⚡ Rate Limiting</h4><p>Redis-based request throttling</p></div>
                    <div class="feature"><h4>📝 Request Logging</h4><p>Comprehensive request tracking</p></div>
                    <div class="feature"><h4>🔀 Dynamic Routing</h4><p>Intelligent request routing</p></div>
                    <div class="feature"><h4>🛡️ Admin Panel</h4><p>User management and analytics</p></div>
                </div>
            </div>
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Start by registering a new user or login with existing credentials</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "database": "connected" if get_db_connection() else "disconnected",
            "redis": "connected" if redis_client else "disconnected"
        }
    } 