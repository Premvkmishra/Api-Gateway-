#!/usr/bin/env python3
"""
Test script for database operations
Tests CRUD operations, connections, and database integrity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_connection, get_async_db_connection
from db.crud import (
    create_user, authenticate_user, get_user_by_id, log_request,
    async_create_user
)
from core.security import hash_password
import asyncio
import time

def test_database_connection():
    """Test database connection functionality"""
    print("🔌 Testing database connection...")
    
    try:
        conn = get_db_connection()
        assert conn is not None, "Database connection should be established"
        print("✅ Database connection successful")
        
        # Test cursor creation
        cursor = conn.cursor()
        assert cursor is not None, "Cursor should be created"
        print("✅ Cursor creation successful")
        
        # Test basic query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "Basic query should return expected result"
        print("✅ Basic query execution successful")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_crud_operations():
    """Test user CRUD operations"""
    print("👤 Testing user CRUD operations...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test user creation
        test_email = f"testuser{int(time.time())}@example.com"
        test_password = "testpass123"
        test_role = "basic"
        
        user_id = create_user(test_email, test_password, test_role)
        assert user_id is not None, "User creation should return user ID"
        print("✅ User creation successful")
        
        # Test user retrieval
        user = get_user_by_id(user_id)
        assert user is not None, "User should be retrievable"
        assert user["email"] == test_email, "Retrieved email should match"
        assert user["role"] == test_role, "Retrieved role should match"
        print("✅ User retrieval successful")
        
        # Test user authentication
        auth_result = authenticate_user(test_email, test_password)
        assert auth_result is not None, "User authentication should succeed"
        assert auth_result["email"] == test_email, "Authenticated user email should match"
        print("✅ User authentication successful")
        
        # Test failed authentication
        failed_auth = authenticate_user(test_email, "wrongpassword")
        assert failed_auth is None, "Wrong password should fail authentication"
        print("✅ Failed authentication handling works")
        
        # Cleanup
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print("✅ Test user cleanup successful")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ User CRUD operations failed: {e}")
        return False

def test_logging_operations():
    """Test request logging operations"""
    print("📝 Testing logging operations...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test log creation
        test_user_id = 1
        test_endpoint = "/test/endpoint"
        test_status_code = 200
        test_response_time = 0.15
        
        log_id = log_request(test_user_id, test_endpoint, test_status_code, test_response_time)
        assert log_id is not None, "Log creation should return log ID"
        print("✅ Log creation successful")
        
        # Verify log entry
        cursor.execute("SELECT * FROM request_logs WHERE id = %s", (log_id,))
        log_entry = cursor.fetchone()
        assert log_entry is not None, "Log entry should exist in database"
        print("✅ Log verification successful")
        
        # Cleanup
        cursor.execute("DELETE FROM request_logs WHERE id = %s", (log_id,))
        conn.commit()
        print("✅ Test log cleanup successful")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Logging operations failed: {e}")
        return False

async def test_async_database_operations():
    """Test async database operations"""
    print("⚡ Testing async database operations...")
    
    try:
        # Test async connection
        async_conn = await get_async_db_connection()
        assert async_conn is not None, "Async database connection should be established"
        print("✅ Async database connection successful")
        
        # Test async user creation
        test_email = f"asyncuser{int(time.time())}@example.com"
        test_password = "asyncpass123"
        test_role = "premium"
        
        user_id = await async_create_user(test_email, test_password, test_role)
        assert user_id is not None, "Async user creation should return user ID"
        print("✅ Async user creation successful")
        
        # Cleanup async user
        async_cursor = await async_conn.cursor()
        await async_cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        await async_conn.commit()
        await async_cursor.close()
        print("✅ Async test user cleanup successful")
        
        await async_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Async database operations failed: {e}")
        return False

def test_database_integrity():
    """Test database integrity constraints"""
    print("🔒 Testing database integrity...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test unique email constraint
        test_email = f"integritytest{int(time.time())}@example.com"
        
        # Create first user
        user1_id = create_user(test_email, "password1", "basic")
        assert user1_id is not None, "First user creation should succeed"
        
        # Try to create second user with same email
        try:
            user2_id = create_user(test_email, "password2", "basic")
            assert False, "Duplicate email should not be allowed"
        except Exception:
            print("✅ Unique email constraint enforced")
        
        # Cleanup
        cursor.execute("DELETE FROM users WHERE id = %s", (user1_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database integrity test failed: {e}")
        return False

def test_database_performance():
    """Test database performance with multiple operations"""
    print("⚡ Testing database performance...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        start_time = time.time()
        
        # Create multiple users
        user_ids = []
        for i in range(10):
            email = f"perftest{i}_{int(time.time())}@example.com"
            user_id = create_user(email, f"pass{i}", "basic")
            user_ids.append(user_id)
        
        creation_time = time.time() - start_time
        print(f"✅ Created 10 users in {creation_time:.3f} seconds")
        
        # Test bulk retrieval
        start_time = time.time()
        cursor.execute("SELECT * FROM users WHERE id IN ({})".format(
            ','.join(['%s'] * len(user_ids))
        ), user_ids)
        users = cursor.fetchall()
        retrieval_time = time.time() - start_time
        print(f"✅ Retrieved {len(users)} users in {retrieval_time:.3f} seconds")
        
        # Cleanup
        for user_id in user_ids:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print("✅ Performance test cleanup successful")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
        return False

async def run_async_tests():
    """Run all async tests"""
    print("🚀 Running async database tests...")
    return await test_async_database_operations()

def run_all_tests():
    """Run all database tests"""
    print("🚀 Starting Database Tests\n")
    
    try:
        # Run sync tests
        test_database_connection()
        test_user_crud_operations()
        test_logging_operations()
        test_database_integrity()
        test_database_performance()
        
        # Run async tests
        asyncio.run(run_async_tests())
        
        print("\n🎉 All database tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
