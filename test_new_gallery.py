#!/usr/bin/env python3
"""
Simple test script for the new gallery functionality.
This script tests the basic gallery operations without complex dependencies.
"""

import json
import os
import requests
import time

def test_gallery_functionality():
    """Test the basic gallery functionality"""
    base_url = 'http://localhost:5000'
    
    print("=== Testing New Gallery Functionality ===\n")
    
    # Test 1: Check if gallery page loads
    print("1. Testing gallery page access...")
    try:
        response = requests.get(f'{base_url}/gallery', timeout=10)
        if response.status_code == 200:
            print("✅ Gallery page loads successfully")
            
            # Check if gallery items are present
            gallery_items = response.text.count('gallery-item')
            print(f"   Gallery items found: {gallery_items}")
        else:
            print(f"❌ Gallery page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing gallery: {e}")
    
    # Test 2: Check if admin page is accessible
    print("\n2. Testing admin page access...")
    try:
        response = requests.get(f'{base_url}/admin/gallery/add', timeout=10)
        if response.status_code == 200:
            print("✅ Admin add page loads successfully")
        else:
            print(f"❌ Admin page returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing admin page: {e}")
    
    # Test 3: Check data files
    print("\n3. Testing data files...")
    
    # Check gallery data file
    if os.path.exists('gallery_data.json'):
        try:
            with open('gallery_data.json', 'r') as f:
                gallery_data = json.load(f)
            print(f"✅ Gallery data file exists with {len(gallery_data)} items")
        except Exception as e:
            print(f"❌ Error reading gallery data: {e}")
    else:
        print("✅ Gallery data file doesn't exist yet (will be created when first item is added)")
    
    # Check users data file
    if os.path.exists('users_data.json'):
        try:
            with open('users_data.json', 'r') as f:
                users_data = json.load(f)
            print(f"✅ Users data file exists with {len(users_data)} users")
        except Exception as e:
            print(f"❌ Error reading users data: {e}")
    else:
        print("✅ Users data file doesn't exist yet (will be created when first user registers)")
    
    # Test 4: Check upload directory
    print("\n4. Testing upload directory...")
    if os.path.exists('static/uploads'):
        print("✅ Upload directory exists")
        files = os.listdir('static/uploads')
        print(f"   Files in upload directory: {len(files)}")
    else:
        print("❌ Upload directory doesn't exist")
    
    print("\n=== Test Complete ===")
    print("\nTo test adding items:")
    print("1. Start the Flask app: python app.py")
    print("2. Register/login as an admin user")
    print("3. Go to the gallery and click 'ADD NEW GALLERY ITEM'")
    print("4. Fill out the form and submit")

if __name__ == '__main__':
    test_gallery_functionality() 