#!/usr/bin/env python3
"""
Integration test for Recipe API endpoints
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

# Test results tracking
test_results = {
    "success": 0,
    "failure": 0,
    "endpoints": {}
}

def track_result(endpoint, success, message=""):
    """Track the result of a test"""
    if endpoint not in test_results["endpoints"]:
        test_results["endpoints"][endpoint] = {"success": 0, "failure": 0}
    
    if success:
        test_results["success"] += 1
        test_results["endpoints"][endpoint]["success"] += 1
    else:
        test_results["failure"] += 1
        test_results["endpoints"][endpoint]["failure"] += 1
        
    if message:
        if "messages" not in test_results["endpoints"][endpoint]:
            test_results["endpoints"][endpoint]["messages"] = []
        test_results["endpoints"][endpoint]["messages"].append(message)

def print_summary():
    """Print a summary of test results"""
    print("\n=== Recipe API Test Summary ===")
    print(f"Total success: {test_results['success']}")
    print(f"Total failure: {test_results['failure']}")
    
    print("\nEndpoint breakdown:")
    for endpoint, results in test_results["endpoints"].items():
        print(f"  {endpoint}: ✅ {results['success']} / ❌ {results['failure']}")
        if "messages" in results and results["messages"]:
            print("    Failure messages:")
            for msg in results["messages"]:
                print(f"      - {msg}")

def test_recipe_api():
    """Test the Recipe API endpoints"""
    print("\n=== Testing Recipe API ===\n")
    
    # Get admin token for authenticated endpoints
    print("1. Logging in as admin...")
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
            track_result("POST /auth/login (admin)", True)
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("POST /auth/login (admin)", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ Admin login request failed: {e}")
        track_result("POST /auth/login (admin)", False, str(e))
    
    # Get a non-admin user token
    print("\n2. Logging in as regular user...")
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
            track_result("POST /auth/login (user)", True)
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("POST /auth/login (user)", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ User login request failed: {e}")
        track_result("POST /auth/login (user)", False, str(e))
    
    # Test getting all recipes
    print("\n3. Testing GET /recipes/ endpoint...")
    try:
        response = requests.get(f"{API_URL}/recipes/")
        if response.status_code == 200:
            recipes = response.json()
            print(f"✅ GET recipes successful: {response.status_code}")
            print(f"Found {len(recipes)} recipes")
            if recipes:
                print("First recipe:")
                for key, value in recipes[0].items():
                    if key != "raw_data" and key != "text_feature_vector" and key != "image_feature_vector":
                        print(f"  {key}: {value}")
            track_result("GET /recipes/", True)
        else:
            print(f"❌ GET recipes failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("GET /recipes/", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ GET recipes request failed: {e}")
        track_result("GET /recipes/", False, str(e))
    
    # Test getting recipes with pagination
    print("\n4. Testing GET /recipes/ with pagination...")
    try:
        response = requests.get(f"{API_URL}/recipes/?skip=5&limit=5")
        if response.status_code == 200:
            recipes = response.json()
            print(f"✅ GET recipes with pagination successful: {response.status_code}")
            print(f"Found {len(recipes)} recipes")
            track_result("GET /recipes/ (pagination)", True)
        else:
            print(f"❌ GET recipes with pagination failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("GET /recipes/ (pagination)", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ GET recipes with pagination request failed: {e}")
        track_result("GET /recipes/ (pagination)", False, str(e))
    
    # Test getting a specific recipe
    print("\n5. Testing GET /recipes/{id} endpoint...")
    recipe_id = 1  # Assuming recipe with ID 1 exists
    try:
        response = requests.get(f"{API_URL}/recipes/{recipe_id}")
        if response.status_code == 200:
            recipe = response.json()
            print(f"✅ GET recipe by ID successful: {response.status_code}")
            print(f"Recipe title: {recipe['title']}")
            track_result("GET /recipes/{id}", True)
        else:
            print(f"❌ GET recipe by ID failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("GET /recipes/{id}", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ GET recipe by ID request failed: {e}")
        track_result("GET /recipes/{id}", False, str(e))
    
    # Test searching for recipes
    print("\n6. Testing GET /recipes/search endpoint...")
    search_term = "chicken"
    try:
        response = requests.get(f"{API_URL}/recipes/search?query={search_term}")
        if response.status_code == 200:
            search_results = response.json()
            print(f"✅ Search recipes successful: {response.status_code}")
            print(f"Found {len(search_results)} matching recipes for '{search_term}'")
            if search_results:
                print("First result title:", search_results[0]["title"])
            track_result("GET /recipes/search", True)
        else:
            print(f"❌ Search recipes failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("GET /recipes/search", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ Search recipes request failed: {e}")
        track_result("GET /recipes/search", False, str(e))
    
    # Test filtering recipes by category
    print("\n7. Testing GET /recipes/ with category filter...")
    category = "dinner"
    try:
        response = requests.get(f"{API_URL}/recipes/?category={category}")
        if response.status_code == 200:
            category_results = response.json()
            print(f"✅ Filter recipes by category successful: {response.status_code}")
            print(f"Found {len(category_results)} recipes in category '{category}'")
            if category_results:
                print("First result title:", category_results[0]["title"])
            track_result("GET /recipes/ (category filter)", True)
        else:
            print(f"❌ Filter recipes by category failed: {response.status_code}")
            print(f"Error: {response.json()}")
            track_result("GET /recipes/ (category filter)", False, f"Status: {response.status_code}, Error: {response.json()}")
    except Exception as e:
        print(f"❌ Filter recipes by category request failed: {e}")
        track_result("GET /recipes/ (category filter)", False, str(e))
    
    # Test getting user's own recipes
    if user_token:
        print("\n8. Testing GET /recipes/mine endpoint...")
        try:
            response = requests.get(
                f"{API_URL}/recipes/mine",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            if response.status_code == 200:
                my_recipes = response.json()
                print(f"✅ GET my recipes successful: {response.status_code}")
                print(f"Found {len(my_recipes)} user recipes")
                if my_recipes:
                    print("First recipe title:", my_recipes[0]["title"])
                track_result("GET /recipes/mine", True)
            else:
                print(f"❌ GET my recipes failed: {response.status_code}")
                print(f"Error: {response.json()}")
                track_result("GET /recipes/mine", False, f"Status: {response.status_code}, Error: {response.json()}")
        except Exception as e:
            print(f"❌ GET my recipes request failed: {e}")
            track_result("GET /recipes/mine", False, str(e))
    
    # Test creating a new recipe
    if user_token:
        print("\n9. Testing POST /recipes/ endpoint...")
        recipe_data = {
            "title": "Integration Test Recipe",
            "description": "Recipe created in integration test",
            "ingredients": "ingredient1,ingredient2,ingredient3",
            "instructions": "Step 1. Do this. Step 2. Do that."
        }
        
        try:
            response = requests.post(
                f"{API_URL}/recipes/",
                headers={"Authorization": f"Bearer {user_token}"},
                data=recipe_data
            )
            
            if response.status_code == 200:
                new_recipe = response.json()
                new_recipe_id = new_recipe["id"]
                print(f"✅ Create recipe successful: {response.status_code}")
                print(f"New recipe ID: {new_recipe_id}")
                print(f"Title: {new_recipe['title']}")
                track_result("POST /recipes/", True)
                
                # Test updating the recipe we just created
                print("\n10. Testing PUT /recipes/{id} endpoint...")
                update_data = {
                    "title": "Updated Integration Test Recipe",
                    "description": "Updated in integration test"
                }
                
                update_response = requests.put(
                    f"{API_URL}/recipes/{new_recipe_id}",
                    headers={"Authorization": f"Bearer {user_token}"},
                    data=update_data
                )
                
                if update_response.status_code == 200:
                    updated_recipe = update_response.json()
                    print(f"✅ Update recipe successful: {update_response.status_code}")
                    print(f"Updated title: {updated_recipe['title']}")
                    track_result("PUT /recipes/{id}", True)
                else:
                    print(f"❌ Update recipe failed: {update_response.status_code}")
                    print(f"Error: {update_response.json()}")
                    track_result("PUT /recipes/{id}", False, f"Status: {update_response.status_code}, Error: {update_response.json()}")
                
                # Test deleting the recipe we created
                print("\n11. Testing DELETE /recipes/{id} endpoint...")
                delete_response = requests.delete(
                    f"{API_URL}/recipes/{new_recipe_id}",
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                
                if delete_response.status_code == 200:
                    print(f"✅ Delete recipe successful: {delete_response.status_code}")
                    track_result("DELETE /recipes/{id}", True)
                else:
                    print(f"❌ Delete recipe failed: {delete_response.status_code}")
                    print(f"Error: {delete_response.json()}")
                    track_result("DELETE /recipes/{id}", False, f"Status: {delete_response.status_code}, Error: {delete_response.json()}")
            else:
                print(f"❌ Create recipe failed: {response.status_code}")
                print(f"Error: {response.json()}")
                track_result("POST /recipes/", False, f"Status: {response.status_code}, Error: {response.json()}")
        except Exception as e:
            print(f"❌ Create recipe request failed: {e}")
            track_result("POST /recipes/", False, str(e))
    
    print("\n=== Recipe API Tests Complete ===")
    print_summary()

if __name__ == "__main__":
    test_recipe_api() 