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
    db_status = "🟢 Connected" if get_db_connection() else "🔴 Disconnected"
    redis_status = "🟢 Connected" if redis_client else "🔴 Disconnected"
    html_content = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>IntelliRoute API Gateway</title>
        <link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap' rel='stylesheet'>
        <style>
            body {{
                font-family: 'Inter', Arial, sans-serif;
                margin: 0;
                padding: 0;
                min-height: 100vh;
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
                color: #e1e5e9;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(15, 15, 25, 0.95);
                border-radius: 24px;
                padding: 40px;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 50px;
                position: relative;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -20px;
                left: 50%;
                transform: translateX(-50%);
                width: 100px;
                height: 4px;
                background: linear-gradient(90deg, #4f46e5, #7c3aed, #ec4899);
                border-radius: 2px;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 3.5em;
                margin-bottom: 15px;
                font-weight: 800;
                background: linear-gradient(45deg, #4f46e5, #7c3aed, #ec4899);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -0.02em;
            }}
            .header p {{
                color: #9ca3af;
                font-size: 1.2em;
                font-weight: 400;
            }}
            .status-bar {{
                display: flex;
                justify-content: center;
                gap: 30px;
                margin: 30px 0 0 0;
                font-size: 1.1em;
            }}
            .status-item {{
                background: rgba(30,34,44,0.85);
                color: #e5e7ef;
                border-radius: 16px;
                padding: 10px 28px;
                box-shadow: 0 2px 8px rgba(99,102,241,0.08);
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                border: 1px solid #23273a;
            }}
            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 32px;
                margin-top: 40px;
            }}
            .feature-card {{
                background: rgba(49, 51, 82, 0.98);
                border-radius: 18px;
                padding: 32px 22px;
                box-shadow: 0 2px 16px rgba(99,102,241,0.07);
                text-align: left;
                border: 1.5px solid rgba(99,102,241,0.13);
                position: relative;
                overflow: hidden;
                transition: box-shadow 0.2s, border 0.2s, transform 0.2s;
            }}
            .feature-card:hover {{
                box-shadow: 0 8px 32px rgba(99,102,241,0.18);
                border: 1.5px solid #a78bfa;
                transform: translateY(-4px) scale(1.03);
            }}
            .feature-card h3 {{
                margin: 0 0 10px 0;
                font-size: 1.25em;
                color: #a78bfa;
                font-weight: 700;
            }}
            .feature-card p {{
                margin: 0;
                color: #c7d2fe;
                font-size: 1.05em;
            }}
            .quick-links {{
                display: flex;
                justify-content: center;
                gap: 28px;
                margin: 50px 0 0 0;
            }}
            .quick-link {{
                background: linear-gradient(90deg, #6366f1 0%, #a78bfa 100%);
                color: #fff;
                padding: 16px 38px;
                border-radius: 16px;
                font-weight: 700;
                text-decoration: none;
                font-size: 1.15em;
                box-shadow: 0 2px 8px rgba(99,102,241,0.10);
                border: none;
                transition: background 0.2s, color 0.2s, transform 0.2s;
            }}
            .quick-link:hover {{
                background: linear-gradient(90deg, #a78bfa 0%, #6366f1 100%);
                color: #fff;
                transform: translateY(-2px) scale(1.04);
            }}
            .footer {{
                margin: 60px 0 0 0;
                text-align: center;
                color: #a5b4fc;
                font-size: 1.05em;
                padding-bottom: 20px;
            }}
            .footer a {{
                color: #a78bfa;
                text-decoration: none;
                font-weight: 600;
            }}
            @media (max-width: 900px) {{
                .container {{ padding: 15px 2vw; }}
                .header h1 {{ font-size: 2.2em; }}
                .features-grid {{ grid-template-columns: 1fr; }}
                .quick-links {{ flex-direction: column; gap: 16px; }}
            }}
        </style>
    </head>
    <body>
        <div class='container'>
            <div class='header'>
                <h1>🚀 IntelliRoute API Gateway</h1>
                <p>Modern, Secure & Intelligent API Management for your microservices</p>
            </div>
            <div class='status-bar'>
                <div class='status-item'>MySQL: <span>{db_status}</span></div>
                <div class='status-item'>Redis: <span>{redis_status}</span></div>
            </div>
            <div class='features-grid'>
                <div class='feature-card'>
                    <h3>🔐 JWT Authentication</h3>
                    <p>Secure, stateless authentication for all API requests using industry-standard JWT tokens.</p>
                </div>
                <div class='feature-card'>
                    <h3>👥 Role-Based Access</h3>
                    <p>Fine-grained access control for Admin, Premium, and Basic users.</p>
                </div>
                <div class='feature-card'>
                    <h3>⚡ Rate Limiting</h3>
                    <p>Protect your APIs from abuse with Redis-powered, per-user/IP rate limiting.</p>
                </div>
                <div class='feature-card'>
                    <h3>📝 Request Logging</h3>
                    <p>All API requests are logged to MySQL for analytics, monitoring, and auditing.</p>
                </div>
                <div class='feature-card'>
                    <h3>🔀 Dynamic Routing</h3>
                    <p>Route requests to different microservices based on user roles and endpoint.</p>
                </div>
                <div class='feature-card'>
                    <h3>🛡️ Admin Panel</h3>
                    <p>Manage users, view logs, and monitor system health from a secure admin interface.</p>
                </div>
            </div>
            <div class='quick-links'>
                <a href='/dashboard' class='quick-link'>🖥️ Dashboard</a>
                <a href='/docs' class='quick-link'>📚 API Docs</a>
                <a href='/health' class='quick-link'>🏥 Health</a>
                <a href='https://github.com/' class='quick-link' target='_blank'>🌐 GitHub</a>
            </div>
            <div class='footer'>
                IntelliRoute v1.0.0 &mdash; Built with <a href='https://fastapi.tiangolo.com/' target='_blank'>FastAPI</a>.<br>
                &copy; {datetime.now().year} depak. All rights reserved.
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