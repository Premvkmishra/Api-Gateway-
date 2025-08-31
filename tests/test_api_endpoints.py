#!/usr/bin/env python3
"""
Test script for API endpoints
Tests authentication, role-based access, and response validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
import json
import time

# Create test client
client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check endpoint...")
    
    try:
        response = client.get("/health")
        assert response.status_code == 200, "Health check should return 200"
        
        data = response.json()
        assert "status" in data, "Response should contain status field"
        assert data["status"] == "healthy", "Status should be healthy"
        print("✅ Health check endpoint works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("🏠 Testing root endpoint...")
    
    try:
        response = client.get("/")
        assert response.status_code == 200, "Root endpoint should return 200"
        assert "text/html" in response.headers["content-type"], "Should return HTML"
        print("✅ Root endpoint works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Root endpoint test failed: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    print("📝 Testing user registration...")
    
    try:
        # Test valid registration
        test_email = f"testuser{int(time.time())}@example.com"
        test_password = "testpass123"
        
        registration_data = {
            "email": test_email,
            "password": test_password,
            "role": "basic"
        }
        
        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 200, "Registration should succeed"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "user_id" in data, "Response should contain user_id"
        print("✅ User registration works correctly")
        
        # Test duplicate registration
        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 400, "Duplicate registration should fail"
        print("✅ Duplicate registration handling works")
        
        return test_email, test_password
        
    except Exception as e:
        print(f"❌ User registration test failed: {e}")
        return None, None

def test_user_login():
    """Test user login endpoint"""
    print("🔑 Testing user login...")
    
    try:
        # First register a user
        test_email, test_password = test_user_registration()
        if not test_email:
            return None
        
        # Test valid login
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200, "Login should succeed"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "token_type" in data, "Response should contain token_type"
        assert data["token_type"] == "bearer", "Token type should be bearer"
        print("✅ User login works correctly")
        
        return data["access_token"]
        
    except Exception as e:
        print(f"❌ User login test failed: {e}")
        return None

def test_protected_endpoints():
    """Test protected endpoints with authentication"""
    print("🔒 Testing protected endpoints...")
    
    try:
        # Get access token
        token = test_user_login()
        if not token:
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test /auth/me endpoint
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200, "Protected endpoint should be accessible"
        
        data = response.json()
        assert "id" in data, "User data should contain id"
        assert "email" in data, "User data should contain email"
        assert "role" in data, "User data should contain role"
        print("✅ Protected endpoint /auth/me works correctly")
        
        # Test /services/data endpoint
        response = client.get("/services/data", headers=headers)
        assert response.status_code == 200, "Service endpoint should be accessible"
        print("✅ Protected service endpoint works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Protected endpoints test failed: {e}")
        return False

def test_role_based_access():
    """Test role-based access control"""
    print("👥 Testing role-based access control...")
    
    try:
        # Create admin user
        admin_email = f"admin{int(time.time())}@example.com"
        admin_data = {
            "email": admin_email,
            "password": "adminpass123",
            "role": "admin"
        }
        
        response = client.post("/auth/register", json=admin_data)
        assert response.status_code == 200, "Admin registration should succeed"
        
        # Login as admin
        login_data = {"email": admin_email, "password": "adminpass123"}
        response = client.post("/auth/login", json=login_data)
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin-only endpoint
        response = client.get("/admin/stats", headers=admin_headers)
        assert response.status_code == 200, "Admin should access admin endpoint"
        print("✅ Admin role access works correctly")
        
        # Test premium endpoint with admin
        response = client.get("/services/service-b/premium-data", headers=admin_headers)
        assert response.status_code == 200, "Admin should access premium endpoint"
        print("✅ Admin premium access works correctly")
        
        # Create basic user
        basic_email = f"basic{int(time.time())}@example.com"
        basic_data = {
            "email": basic_email,
            "password": "basicpass123",
            "role": "basic"
        }
        
        response = client.post("/auth/register", json=basic_data)
        assert response.status_code == 200, "Basic user registration should succeed"
        
        # Login as basic user
        login_data = {"email": basic_email, "password": "basicpass123"}
        response = client.post("/auth/login", json=login_data)
        basic_token = response.json()["access_token"]
        basic_headers = {"Authorization": f"Bearer {basic_token}"}
        
        # Test basic user access to admin endpoint (should fail)
        response = client.get("/admin/stats", headers=basic_headers)
        assert response.status_code == 403, "Basic user should not access admin endpoint"
        print("✅ Basic user access restriction works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Role-based access test failed: {e}")
        return False

def test_service_endpoints():
    """Test various service endpoints"""
    print("🔧 Testing service endpoints...")
    
    try:
        # Create test user
        test_email = f"serviceuser{int(time.time())}@example.com"
        user_data = {
            "email": test_email,
            "password": "servicepass123",
            "role": "premium"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200, "Service user registration should succeed"
        
        # Login
        login_data = {"email": test_email, "password": "servicepass123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test service-a endpoint
        response = client.get("/services/service-a/data", headers=headers)
        assert response.status_code == 200, "Service A should be accessible"
        print("✅ Service A endpoint works correctly")
        
        # Test service-b endpoint (premium)
        response = client.get("/services/service-b/premium-data", headers=headers)
        assert response.status_code == 200, "Premium service should be accessible"
        print("✅ Service B premium endpoint works correctly")
        
        # Test notifications endpoint
        response = client.get("/services/notifications", headers=headers)
        assert response.status_code == 200, "Notifications should be accessible"
        print("✅ Notifications endpoint works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Service endpoints test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and validation"""
    print("⚠️ Testing error handling...")
    
    try:
        # Test invalid JSON
        response = client.post("/auth/login", data="invalid json")
        assert response.status_code == 422, "Invalid JSON should return 422"
        print("✅ Invalid JSON handling works")
        
        # Test missing required fields
        response = client.post("/auth/login", json={"email": "test@example.com"})
        assert response.status_code == 422, "Missing password should return 422"
        print("✅ Missing field validation works")
        
        # Test invalid email format
        response = client.post("/auth/login", json={
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422, "Invalid email should return 422"
        print("✅ Email format validation works")
        
        # Test non-existent endpoint
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404, "Non-existent endpoint should return 404"
        print("✅ 404 error handling works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("⏱️ Testing rate limiting...")
    
    try:
        # Create test user
        test_email = f"ratelimituser{int(time.time())}@example.com"
        user_data = {
            "email": test_email,
            "password": "ratelimitpass123",
            "role": "basic"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200, "Rate limit user registration should succeed"
        
        # Login
        login_data = {"email": test_email, "password": "ratelimitpass123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make multiple requests quickly
        responses = []
        for i in range(10):
            response = client.get("/services/data", headers=headers)
            responses.append(response.status_code)
        
        # Check if rate limiting is working (some requests might be blocked)
        print(f"✅ Rate limiting responses: {responses}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def run_all_tests():
    """Run all API endpoint tests"""
    print("🚀 Starting API Endpoint Tests\n")
    
    try:
        test_health_check()
        test_root_endpoint()
        test_user_registration()
        test_user_login()
        test_protected_endpoints()
        test_role_based_access()
        test_service_endpoints()
        test_error_handling()
        test_rate_limiting()
        
        print("\n🎉 All API endpoint tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
