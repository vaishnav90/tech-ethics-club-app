#!/usr/bin/env python3
"""
Simple test to verify the login process works correctly.
"""

import os
import requests
import time

# Set up authentication
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/vaishnavanand/club2/tech-ethics-club-sa-key.json'

def test_login():
    """Test the login process"""
    print("🔐 Testing Login Process")
    print("=" * 50)
    
    # Create a session
    session = requests.Session()
    
    # First, check the login page
    print("=== Checking Login Page ===")
    try:
        response = session.get('http://localhost:5001/login', timeout=10)
        print(f"Login page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error accessing login page: {e}")
        return
    
    # Check if we're already logged in by trying to access admin page
    print("\n=== Checking Current Login Status ===")
    try:
        response = session.get('http://localhost:5001/admin/gallery/add', timeout=10)
        print(f"Admin page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Already logged in as admin")
            return True
        elif response.status_code == 302:
            print("⚠️  Not logged in, redirected to login")
        else:
            print(f"❌ Admin page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking admin access: {e}")
    
    # Try to login
    print("\n=== Attempting Login ===")
    print("Please provide your login credentials:")
    
    email = input("Email (or press Enter to use default): ").strip()
    if not email:
        email = "vaishnavanand90@gmail.com"
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password required")
        return False
    
    login_data = {
        'email': email,
        'password': password
    }
    
    try:
        print("Submitting login...")
        response = session.post('http://localhost:5001/login', data=login_data, timeout=10)
        print(f"Login response status: {response.status_code}")
        print(f"Login response URL: {response.url}")
        
        if 'gallery' in response.url:
            print("✅ Login successful, redirected to gallery")
            
            # Verify we can access admin page
            time.sleep(1)
            admin_response = session.get('http://localhost:5001/admin/gallery/add', timeout=10)
            if admin_response.status_code == 200:
                print("✅ Admin page accessible after login")
                return True
            else:
                print(f"❌ Admin page not accessible after login: {admin_response.status_code}")
                return False
        else:
            print("❌ Login failed, not redirected to gallery")
            print("Response content preview:")
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Login Test")
    print("=" * 50)
    
    success = test_login()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Login test successful!")
        print("You should now be able to add gallery items through the web interface.")
    else:
        print("❌ Login test failed!")
        print("Please check your credentials and try again.")

if __name__ == '__main__':
    main() 