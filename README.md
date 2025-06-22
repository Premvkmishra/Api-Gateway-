# IntelliRoute - Intelligent API Gateway

<!-- Screenshots -->

<p align="center">
  <img src="assets/homepage.png" alt="Homepage" width="700"/>
  <br><b>Homepage</b>
  <br><br>
  <img src="assets/dashbaord.png" alt="Main Dashboard" width="700"/>
  <br><b>Main Dashboard</b>
  <br><br>
  <img src="assets/admindashboard.png" alt="Admin Dashboard" width="700"/>
  <br><b>Admin Dashboard</b>
  <br><br>
  <img src="assets/response.png" alt="API Response Example" width="700"/>
  <br><b>API Response Example</b>
</p>

A comprehensive API gateway built with FastAPI featuring authentication, rate limiting, role-based access control, and request logging.

## Features

### ✅ Core Features
- **Dynamic Routing**: Route requests to different microservices based on user roles
- **JWT Authentication**: Secure token-based authentication system
- **Role-Based Access Control (RBAC)**: Three user roles - Admin, Premium, Basic
- **Rate Limiting**: Redis-based rate limiting (100 requests/minute per user/IP)
- **Request Logging**: All requests logged to MySQL database
- **Admin Panel**: Protected admin routes for user management and log viewing
- **Swagger Documentation**: Auto-generated API documentation

### 🔧 Tech Stack
- **Backend**: FastAPI
- **Database**: MySQL (using provided Railway credentials)
- **Cache**: Redis (for rate limiting)
- **Authentication**: JWT tokens
- **Frontend**: HTML/CSS/JavaScript
- **Password Hashing**: bcrypt

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Redis Setup (Optional but Recommended)
Install Redis for rate limiting:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

**Note**: If Redis is not available, the application will work but rate limiting will be disabled.

### 3. Database Setup
Your MySQL database is already configured with the provided credentials. The required tables (`users` and `logs`) are already created.

### 4. Create Static Directory
```bash
mkdir static
# Copy the frontend HTML file to static/index.html
```

### 5. Run the Application
```bash
python main.py
```

The application will start on `http://localhost:8000`

## Project Structure

```
IntelliRoute/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── static/
│   └── index.html      # Frontend dashboard
└── README.md           # This file
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Protected Services (Role-based)
- `GET /service-a/data` - Accessible to all authenticated users
- `GET /service-b/premium-data` - Premium and Admin users only
- `GET /service-c/admin-data` - Admin users only

### Microservices
- `GET /data` - Data service
- `GET /notifications` - Notifications service (Premium+)
- `GET /user-profile` - User profile service

### Admin Panel
- `GET /admin/logs` - View request logs (paginated)
- `GET /admin/users` - View all users
- `PUT /admin/users/{id}/role` - Update user role

### Utility
- `GET /health` - Health check endpoint
- `GET /` - Dashboard (HTML)
- `GET /docs` - Swagger documentation

## User Roles & Permissions

### Basic Users
- Access to basic services (`/service-a/data`, `/data`, `/user-profile`)
- Standard rate limiting

### Premium Users
- All Basic user permissions
- Access to premium services (`/service-b/premium-data`, `/notifications`)

### Admin Users
- All Premium user permissions
- Access to admin-only services (`/service-c/admin-data`)
- Admin panel access (`/admin/*`)
- User management capabilities

## Rate Limiting

- **Limit**: 100 requests per minute per user/IP
- **Implementation**: Redis-based sliding window
- **Response**: 429 Too Many Requests when limit exceeded
- **Fallback**: If Redis unavailable, rate limiting is disabled

## Request Logging

All requests are logged to MySQL with:
- User ID (if authenticated)
- Endpoint accessed
- HTTP status code
- Response time
- Timestamp

## Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: 30-minute expiration
- **CORS**: Configured for cross-origin requests
- **Input Validation**: Pydantic models for request validation

## Usage Examples

### 1. Register a new user
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "role": "basic"}'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### 3. Access protected endpoint
```bash
curl -X GET "http://localhost:8000/service-a/data" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. View logs (Admin only)
```bash
curl -X GET "http://localhost:8000/admin/logs?page=1&size=10" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

## Frontend Dashboard

Access the interactive dashboard at `http://localhost:8000/`

Features:
- User registration and login
- Real-time API testing
- Role-based endpoint access
- Response visualization
- Rate limiting demonstration

## Configuration

### Environment Variables (Optional)
Create a `.env` file for custom configuration:
```env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=mysql://root:OkMAOoUvUwSGUusrqrdYVBSxORzdnqCC@yamanote.proxy.rlwy.net:20143/intel
REDIS_URL=redis://localhost:6379
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_PER_MINUTE=100
```

## Testing

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger documentation

### 3. Rate Limiting Test
Use the frontend dashboard's "Test Rate Limiting" button or make rapid API calls

## Production Considerations

1. **Change Secret Key**: Use a secure, random secret key in production
2. **Redis Setup**: Configure Redis with authentication and persistence
3. **Database Security**: Use connection pooling and prepared statements
4. **HTTPS**: Enable HTTPS with proper SSL certificates
5. **Monitoring**: Add logging and monitoring tools
6. **Load Balancing**: Use reverse proxy (nginx) for production deployment

## Troubleshooting

### Common Issues

1. **Redis Connection Error**: Rate limiting will be disabled if Redis is unavailable
2. **Database Connection Error**: Check your MySQL credentials and network connectivity
3. **JWT Token Expired**: Tokens expire after 30 minutes, re-login required
4. **CORS Issues**: Ensure CORS middleware is properly configured

### Logs
- Application logs are printed to console
- Request logs are stored in MySQL `logs` table
- Database errors are logged with detailed messages

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend      │───▶│   FastAPI    │───▶│   MySQL     │
│   Dashboard     │    │   Gateway    │    │  Database   │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Redis     │
                       │ Rate Limiting│
                       └──────────────┘
```

The gateway acts as a central point for:
- Authentication and authorization
- Rate limiting and throttling
- Request logging and monitoring
- Routing to microservices
- Admin panel functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.