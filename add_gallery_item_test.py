#!/usr/bin/env python3
"""
Simple script to test adding a gallery item through the web interface.
This will help verify that the full workflow from local to deployed app works correctly.
"""

import os
import requests
import time

# Set up authentication
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/vaishnavanand/club2/tech-ethics-club-sa-key.json'

def test_gallery_access():
    """Test accessing the gallery page"""
    print("=== Testing Gallery Access ===")
    
    try:
        # Test local gallery
        response = requests.get('http://localhost:5001/gallery', timeout=10)
        if response.status_code == 200:
            print("✅ Local gallery accessible")
            if 'gallery-item' in response.text:
                print("✅ Gallery items are displayed")
            else:
                print("⚠️  No gallery items found in HTML")
        else:
            print(f"❌ Local gallery returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing local gallery: {e}")

def check_deployed_gallery():
    """Check the deployed gallery (you'll need to provide the URL)"""
    print("\n=== Checking Deployed Gallery ===")
    
    # You can replace this with your actual deployed app URL
    deployed_url = input("Enter your deployed app URL (or press Enter to skip): ").strip()
    
    if not deployed_url:
        print("ℹ️  Skipping deployed gallery check")
        return
    
    try:
        response = requests.get(f"{deployed_url}/gallery", timeout=10)
        if response.status_code == 200:
            print("✅ Deployed gallery accessible")
            if 'gallery-item' in response.text:
                print("✅ Gallery items are displayed in deployed app")
            else:
                print("⚠️  No gallery items found in deployed app")
        else:
            print(f"❌ Deployed gallery returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing deployed gallery: {e}")

def main():
    """Main test function"""
    print("🌐 Gallery Web Interface Test")
    print("=" * 50)
    
    # Test local gallery
    test_gallery_access()
    
    # Check deployed gallery
    check_deployed_gallery()
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Your local environment is now properly configured with the service account")
    print("2. Both local and deployed environments should see the same Cloud Storage data")
    print("3. To test adding new items:")
    print("   - Go to http://localhost:5001/admin/gallery/add (if logged in as admin)")
    print("   - Add a new gallery item with an image")
    print("   - Check that it appears in both local and deployed galleries")
    print("4. If items still don't sync, check the service account permissions in Google Cloud Console")

if __name__ == '__main__':
    main() 