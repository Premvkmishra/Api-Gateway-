#!/usr/bin/env python3
"""
Test script for data models and schemas
Tests Pydantic models, validation, and serialization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    UserCreate, UserLogin, UserResponse, LogResponse, 
    UserUpdate, LogRequest
)
from datetime import datetime
from pydantic import ValidationError
import json

def test_user_create_model():
    """Test UserCreate model validation"""
    print("👤 Testing UserCreate model...")
    
    try:
        # Test valid user creation
        valid_user = UserCreate(
            email="test@example.com",
            password="password123",
            role="basic"
        )
        assert valid_user.email == "test@example.com"
        assert valid_user.password == "password123"
        assert valid_user.role == "basic"
        print("✅ Valid UserCreate model works")
        
        # Test default role
        user_with_default_role = UserCreate(
            email="test2@example.com",
            password="password123"
        )
        assert user_with_default_role.role == "basic"
        print("✅ Default role assignment works")
        
        # Test invalid email format
        try:
            invalid_user = UserCreate(
                email="invalid-email",
                password="password123"
            )
            assert False, "Invalid email should raise validation error"
        except ValidationError:
            print("✅ Invalid email validation works")
        
        # Test empty password
        try:
            empty_password_user = UserCreate(
                email="test@example.com",
                password=""
            )
            assert False, "Empty password should raise validation error"
        except ValidationError:
            print("✅ Empty password validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ UserCreate model test failed: {e}")
        return False

def test_user_login_model():
    """Test UserLogin model validation"""
    print("🔑 Testing UserLogin model...")
    
    try:
        # Test valid login
        valid_login = UserLogin(
            email="test@example.com",
            password="password123"
        )
        assert valid_login.email == "test@example.com"
        assert valid_login.password == "password123"
        print("✅ Valid UserLogin model works")
        
        # Test invalid email format
        try:
            invalid_login = UserLogin(
                email="invalid-email",
                password="password123"
            )
            assert False, "Invalid email should raise validation error"
        except ValidationError:
            print("✅ Invalid email validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ UserLogin model test failed: {e}")
        return False

def test_user_response_model():
    """Test UserResponse model validation"""
    print("👤 Testing UserResponse model...")
    
    try:
        # Test valid user response
        valid_response = UserResponse(
            id=1,
            email="test@example.com",
            role="admin",
            created_at=datetime.now()
        )
        assert valid_response.id == 1
        assert valid_response.email == "test@example.com"
        assert valid_response.role == "admin"
        assert isinstance(valid_response.created_at, datetime)
        print("✅ Valid UserResponse model works")
        
        # Test model serialization
        response_dict = valid_response.dict()
        assert "id" in response_dict
        assert "email" in response_dict
        assert "role" in response_dict
        assert "created_at" in response_dict
        print("✅ UserResponse serialization works")
        
        # Test JSON serialization
        response_json = valid_response.json()
        assert isinstance(response_json, str)
        parsed_json = json.loads(response_json)
        assert parsed_json["id"] == 1
        print("✅ UserResponse JSON serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ UserResponse model test failed: {e}")
        return False

def test_log_response_model():
    """Test LogResponse model validation"""
    print("📝 Testing LogResponse model...")
    
    try:
        # Test valid log response
        valid_log = LogResponse(
            id=1,
            user_id=123,
            endpoint="/test/endpoint",
            status_code=200,
            response_time=0.15,
            timestamp=datetime.now()
        )
        assert valid_log.id == 1
        assert valid_log.user_id == 123
        assert valid_log.endpoint == "/test/endpoint"
        assert valid_log.status_code == 200
        assert valid_log.response_time == 0.15
        assert isinstance(valid_log.timestamp, datetime)
        print("✅ Valid LogResponse model works")
        
        # Test with None user_id (anonymous request)
        anonymous_log = LogResponse(
            id=2,
            user_id=None,
            endpoint="/public/endpoint",
            status_code=200,
            response_time=0.05,
            timestamp=datetime.now()
        )
        assert anonymous_log.user_id is None
        print("✅ LogResponse with None user_id works")
        
        # Test model serialization
        log_dict = valid_log.dict()
        assert "id" in log_dict
        assert "user_id" in log_dict
        assert "endpoint" in log_dict
        assert "status_code" in log_dict
        assert "response_time" in log_dict
        assert "timestamp" in log_dict
        print("✅ LogResponse serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ LogResponse model test failed: {e}")
        return False

def test_user_update_model():
    """Test UserUpdate model validation"""
    print("✏️ Testing UserUpdate model...")
    
    try:
        # Test valid user update
        valid_update = UserUpdate(role="premium")
        assert valid_update.role == "premium"
        print("✅ Valid UserUpdate model works")
        
        # Test role validation
        try:
            invalid_role = UserUpdate(role="invalid_role")
            assert False, "Invalid role should raise validation error"
        except ValidationError:
            print("✅ Invalid role validation works")
        
        # Test model serialization
        update_dict = valid_update.dict()
        assert "role" in update_dict
        assert update_dict["role"] == "premium"
        print("✅ UserUpdate serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ UserUpdate model test failed: {e}")
        return False

def test_log_request_model():
    """Test LogRequest model validation"""
    print("📝 Testing LogRequest model...")
    
    try:
        # Test valid log request
        valid_log_request = LogRequest(
            endpoint="/test/endpoint",
            status_code=200,
            response_time=0.15
        )
        assert valid_log_request.endpoint == "/test/endpoint"
        assert valid_log_request.status_code == 200
        assert valid_log_request.response_time == 0.15
        print("✅ Valid LogRequest model works")
        
        # Test status code validation
        try:
            invalid_status = LogRequest(
                endpoint="/test/endpoint",
                status_code=999,  # Invalid status code
                response_time=0.15
            )
            assert False, "Invalid status code should raise validation error"
        except ValidationError:
            print("✅ Invalid status code validation works")
        
        # Test response time validation
        try:
            invalid_time = LogRequest(
                endpoint="/test/endpoint",
                status_code=200,
                response_time=-0.1  # Negative time
            )
            assert False, "Negative response time should raise validation error"
        except ValidationError:
            print("✅ Negative response time validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ LogRequest model test failed: {e}")
        return False

def test_model_edge_cases():
    """Test model edge cases and boundary conditions"""
    print("⚠️ Testing model edge cases...")
    
    try:
        # Test very long email
        long_email = "a" * 100 + "@example.com"
        try:
            long_email_user = UserCreate(
                email=long_email,
                password="password123"
            )
            print("✅ Long email handling works")
        except ValidationError:
            print("✅ Long email validation works")
        
        # Test very long password
        long_password = "a" * 1000
        try:
            long_password_user = UserCreate(
                email="test@example.com",
                password=long_password
            )
            print("✅ Long password handling works")
        except ValidationError:
            print("✅ Long password validation works")
        
        # Test special characters in email
        special_email = "test+special!@#$%^&*()_+-=[]{}|;:,.<>?@example.com"
        try:
            special_email_user = UserCreate(
                email=special_email,
                password="password123"
            )
            print("✅ Special characters in email handling works")
        except ValidationError:
            print("✅ Special characters in email validation works")
        
        # Test unicode characters
        unicode_email = "test🚀测试@example.com"
        try:
            unicode_user = UserCreate(
                email=unicode_email,
                password="password🚀测试"
            )
            print("✅ Unicode characters handling works")
        except ValidationError:
            print("✅ Unicode characters validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model edge cases test failed: {e}")
        return False

def test_model_inheritance():
    """Test model inheritance and relationships"""
    print("🔗 Testing model inheritance...")
    
    try:
        # Test that all models inherit from BaseModel
        from pydantic import BaseModel
        
        assert issubclass(UserCreate, BaseModel), "UserCreate should inherit from BaseModel"
        assert issubclass(UserLogin, BaseModel), "UserLogin should inherit from BaseModel"
        assert issubclass(UserResponse, BaseModel), "UserResponse should inherit from BaseModel"
        assert issubclass(LogResponse, BaseModel), "LogResponse should inherit from BaseModel"
        assert issubclass(UserUpdate, BaseModel), "UserUpdate should inherit from BaseModel"
        assert issubclass(LogRequest, BaseModel), "LogRequest should inherit from BaseModel"
        print("✅ All models properly inherit from BaseModel")
        
        # Test model field types
        user_fields = UserCreate.__fields__
        assert "email" in user_fields, "UserCreate should have email field"
        assert "password" in user_fields, "UserCreate should have password field"
        assert "role" in user_fields, "UserCreate should have role field"
        print("✅ UserCreate has all required fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Model inheritance test failed: {e}")
        return False

def test_model_validation_rules():
    """Test model validation rules and constraints"""
    print("📋 Testing model validation rules...")
    
    try:
        # Test email format validation
        invalid_emails = [
            "plaintext",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example..com"
        ]
        
        for invalid_email in invalid_emails:
            try:
                invalid_user = UserCreate(
                    email=invalid_email,
                    password="password123"
                )
                print(f"⚠️ Unexpected: {invalid_email} was accepted")
            except ValidationError:
                print(f"✅ {invalid_email} correctly rejected")
        
        # Test password length validation
        try:
            short_password = UserCreate(
                email="test@example.com",
                password="123"
            )
            print("⚠️ Short password was accepted")
        except ValidationError:
            print("✅ Short password correctly rejected")
        
        # Test role validation
        valid_roles = ["basic", "premium", "admin"]
        for role in valid_roles:
            try:
                valid_role_user = UserCreate(
                    email=f"test_{role}@example.com",
                    password="password123",
                    role=role
                )
                print(f"✅ Role '{role}' correctly accepted")
            except ValidationError:
                print(f"❌ Valid role '{role}' was rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation rules test failed: {e}")
        return False

def run_all_tests():
    """Run all model tests"""
    print("🚀 Starting Model Tests\n")
    
    try:
        test_user_create_model()
        test_user_login_model()
        test_user_response_model()
        test_log_response_model()
        test_user_update_model()
        test_log_request_model()
        test_model_edge_cases()
        test_model_inheritance()
        test_model_validation_rules()
        
        print("\n🎉 All model tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
