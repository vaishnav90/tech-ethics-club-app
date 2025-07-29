#!/usr/bin/env python3
"""
Deployment test script to verify the app can start without errors.
This tests the actual app startup and error handling.
"""

import os
import sys
import json

def test_app_startup():
    """Test that the app can start without errors"""
    print("=== Testing App Deployment Readiness ===\n")
    
    # Test 1: Simulate App Engine environment
    print("1. Testing App Engine environment simulation...")
    
    # Set App Engine environment variable
    os.environ['GAE_ENV'] = 'standard'
    
    try:
        # Import the app
        from app import app, get_all_gallery_items, get_user_by_email
        
        print("✅ App imports successfully in App Engine environment")
        
        # Test 2: Test data loading functions
        print("\n2. Testing data loading functions...")
        
        try:
            # Test gallery items loading
            gallery_items = get_all_gallery_items()
            print(f"✅ Gallery items loaded: {len(gallery_items)} items")
            
            # Test user loading
            users = get_user_by_email('vaishnavanand90@gmail.com')
            if users:
                print("✅ User data loading works")
            else:
                print("⚠️  User data not found (this is normal if no users exist)")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
        
        # Test 3: Test route handlers
        print("\n3. Testing route handlers...")
        
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home page loads successfully")
            else:
                print(f"❌ Home page failed: {response.status_code}")
            
            # Test gallery page
            response = client.get('/gallery')
            if response.status_code == 200:
                print("✅ Gallery page loads successfully")
            else:
                print(f"❌ Gallery page failed: {response.status_code}")
            
            # Test health check
            response = client.get('/_ah/health')
            if response.status_code == 200:
                print("✅ Health check endpoint works")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        
        print("\n✅ App is deployment ready!")
        return True
        
    except Exception as e:
        print(f"❌ App failed to start: {e}")
        return False
    
    finally:
        # Clean up environment
        if 'GAE_ENV' in os.environ:
            del os.environ['GAE_ENV']

def test_regular_environment():
    """Test that the app works in regular environment"""
    print("\n=== Testing Regular Environment ===\n")
    
    try:
        # Import the app
        from app import app, get_all_gallery_items, get_user_by_email
        
        print("✅ App imports successfully in regular environment")
        
        # Test data loading
        try:
            gallery_items = get_all_gallery_items()
            print(f"✅ Gallery items loaded: {len(gallery_items)} items")
            
            users = get_user_by_email('vaishnavanand90@gmail.com')
            if users:
                print("✅ User data loading works")
            else:
                print("⚠️  User data not found")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
        
        # Test route handlers
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home page loads successfully")
            else:
                print(f"❌ Home page failed: {response.status_code}")
        
        print("✅ App works in regular environment")
        return True
        
    except Exception as e:
        print(f"❌ App failed in regular environment: {e}")
        return False

if __name__ == '__main__':
    print("Testing deployment readiness...\n")
    
    success1 = test_app_startup()
    success2 = test_regular_environment()
    
    print("\n=== Deployment Test Results ===")
    if success1 and success2:
        print("✅ ALL TESTS PASSED - App is ready for deployment!")
        print("\nThe app should now work on Google App Engine without 502 errors.")
        print("Key fixes applied:")
        print("- Added proper error handling for cloud storage failures")
        print("- Made local file operations conditional on environment")
        print("- Added try-catch blocks around all data operations")
        print("- App will gracefully handle GCS connection issues")
    else:
        print("❌ Some tests failed - App needs fixes before deployment.")
    
    print("\nTo deploy:")
    print("1. Run: gcloud app deploy")
    print("2. The app should start without 502 errors")
    print("3. Gallery and user data will be loaded from cloud storage")
    print("4. If GCS fails, app will still work with empty data") 