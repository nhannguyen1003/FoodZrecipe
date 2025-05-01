#!/usr/bin/env python3
"""
Integration test for JWT authentication system API endpoints
"""
import os
import sys
import json
import requests
from pprint import pprint

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import project settings
from config import settings

# API base URL
API_URL = f"http://localhost:8000{settings.API_PREFIX}"

def test_auth():
    """Test the authentication endpoints"""
    print("\n=== Testing Authentication System ===\n")
    
    # Test registration with a new user
    print("1. Testing registration endpoint...")
    new_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=new_user)
        if response.status_code == 201:
            print(f"✅ Registration successful: {response.status_code}")
            print(f"User data: {response.json()}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
    
    # Test login with admin user
    print("\n2. Testing admin login...")
    admin_login = {
        "username": "admin",
        "password": "admin"
    }
    
    admin_token = None
    try:
        response = requests.post(
            f"{API_URL}/auth/login", 
            data={"username": admin_login["username"], "password": admin_login["password"]}
        )
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print(f"✅ Admin login successful: {response.status_code}")
            print(f"Token: {admin_token[:20]}...")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"❌ Admin login request failed: {e}")
    
    # Test login with regular user
    print("\n3. Testing regular user login...")
    user_login = {
        "username": "user",
        "password": "password"
    }
    
    user_token = None
    try:
        response = requests.post(
            f"{API_URL}/auth/login", 
            data={"username": user_login["username"], "password": user_login["password"]}
        )
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            print(f"✅ User login successful: {response.status_code}")
            print(f"Token: {user_token[:20]}...")
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"❌ User login request failed: {e}")
    
    # Test user info endpoint with admin token
    if admin_token:
        print("\n4. Testing admin access to /me endpoint...")
        try:
            response = requests.get(
                f"{API_URL}/auth/me",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            if response.status_code == 200:
                print(f"✅ Admin access to /me successful: {response.status_code}")
                print("Admin user info:")
                pprint(response.json())
            else:
                print(f"❌ Admin access to /me failed: {response.status_code}")
                print(f"Error: {response.json()}")
        except Exception as e:
            print(f"❌ Admin access request failed: {e}")
    
    # Test admin-only endpoint with admin token
    if admin_token:
        print("\n5. Testing admin access to admin-only endpoint...")
        try:
            response = requests.post(
                f"{API_URL}/auth/test-admin",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            if response.status_code == 200:
                print(f"✅ Admin access successful: {response.status_code}")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Admin access failed: {response.status_code}")
                print(f"Error: {response.json()}")
        except Exception as e:
            print(f"❌ Admin access request failed: {e}")
    
    # Test admin-only endpoint with regular user token
    if user_token:
        print("\n6. Testing regular user access to admin-only endpoint (should fail)...")
        try:
            response = requests.post(
                f"{API_URL}/auth/test-admin",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            if response.status_code == 403:
                print(f"✅ Regular user correctly denied access: {response.status_code}")
                print(f"Error: {response.json()}")
            else:
                print(f"❌ Test failed: Regular user was not denied access: {response.status_code}")
                print(f"Response: {response.json()}")
        except Exception as e:
            print(f"❌ User access request failed: {e}")

if __name__ == "__main__":
    test_auth() 