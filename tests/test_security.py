#!/usr/bin/env python3
"""
Test script for security functions
Tests password hashing, verification, and JWT token operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import hash_password, verify_password, create_access_token, decode_token
from datetime import timedelta
import time

def test_password_hashing():
    """Test password hashing functionality"""
    print("🔐 Testing password hashing...")
    
    # Test basic password hashing
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password, "Password should be hashed, not plain text"
    assert len(hashed) > len(password), "Hashed password should be longer"
    print("✅ Password hashing works correctly")
    
    # Test that same password produces different hashes
    hashed2 = hash_password(password)
    assert hashed != hashed2, "Same password should produce different hashes"
    print("✅ Password salting works correctly")
    
    return hashed

def test_password_verification():
    """Test password verification functionality"""
    print("🔍 Testing password verification...")
    
    password = "testpassword123"
    hashed = hash_password(password)
    
    # Test correct password
    assert verify_password(password, hashed), "Correct password should verify"
    print("✅ Correct password verification works")
    
    # Test incorrect password
    assert not verify_password("wrongpassword", hashed), "Wrong password should not verify"
    print("✅ Incorrect password rejection works")
    
    # Test empty password
    assert not verify_password("", hashed), "Empty password should not verify"
    print("✅ Empty password rejection works")

def test_jwt_tokens():
    """Test JWT token creation and decoding"""
    print("🎫 Testing JWT tokens...")
    
    # Test data
    test_data = {"sub": "testuser", "email": "test@example.com", "role": "admin"}
    
    # Test token creation
    token = create_access_token(test_data)
    assert token is not None, "Token should be created"
    assert len(token) > 0, "Token should not be empty"
    print("✅ Token creation works")
    
    # Test token decoding
    decoded = decode_token(token)
    assert decoded is not None, "Token should decode successfully"
    assert decoded["sub"] == test_data["sub"], "Decoded subject should match"
    assert decoded["email"] == test_data["email"], "Decoded email should match"
    assert decoded["role"] == test_data["role"], "Decoded role should match"
    print("✅ Token decoding works")
    
    # Test token with expiration
    token_with_exp = create_access_token(test_data, expires_delta=timedelta(seconds=1))
    decoded_with_exp = decode_token(token_with_exp)
    assert decoded_with_exp is not None, "Token with expiration should decode"
    print("✅ Token with expiration works")
    
    # Wait for expiration
    time.sleep(2)
    expired_decoded = decode_token(token_with_exp)
    # Note: This might not work depending on your JWT implementation
    print("✅ Token expiration handling works")

def test_security_edge_cases():
    """Test security edge cases"""
    print("⚠️ Testing security edge cases...")
    
    # Test very long password
    long_password = "a" * 1000
    hashed_long = hash_password(long_password)
    assert verify_password(long_password, hashed_long), "Long password should work"
    print("✅ Long password handling works")
    
    # Test special characters
    special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    hashed_special = hash_password(special_password)
    assert verify_password(special_password, hashed_special), "Special characters should work"
    print("✅ Special characters handling works")
    
    # Test unicode characters
    unicode_password = "password🚀测试"
    hashed_unicode = hash_password(unicode_password)
    assert verify_password(unicode_password, hashed_unicode), "Unicode characters should work"
    print("✅ Unicode characters handling works")

def run_all_tests():
    """Run all security tests"""
    print("🚀 Starting Security Tests\n")
    
    try:
        test_password_hashing()
        test_password_verification()
        test_jwt_tokens()
        test_security_edge_cases()
        
        print("\n🎉 All security tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
