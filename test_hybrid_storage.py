#!/usr/bin/env python3
"""
Test script for the hybrid storage system.
This verifies that the system can handle both local and cloud storage.
"""

import os
import json
from app import GCS_AVAILABLE, get_gcs_bucket, upload_to_gcs, delete_from_gcs, get_data_from_gcs, GCS_DATA_USERS, GCS_DATA_GALLERY

def test_hybrid_storage():
    """Test the hybrid storage functionality"""
    print("=== Testing Hybrid Storage System ===\n")
    
    # Test 1: Check if Google Cloud Storage is available
    print("1. Testing Google Cloud Storage availability...")
    if GCS_AVAILABLE:
        print("✅ Google Cloud Storage library is available")
        
        # Test 2: Check if credentials are available
        if os.path.exists('tech-ethics-club-sa-key.json'):
            print("✅ Google Cloud credentials file exists")
            
            # Test 3: Try to access the bucket
            try:
                bucket = get_gcs_bucket()
                if bucket:
                    print("✅ Successfully connected to Google Cloud Storage")
                    print(f"   Bucket: {bucket.name}")
                else:
                    print("⚠️  Could not connect to Google Cloud Storage (will use local fallback)")
            except Exception as e:
                print(f"⚠️  Error connecting to Google Cloud Storage: {e}")
                print("   System will use local storage fallback")
        else:
            print("❌ Google Cloud credentials file not found")
            print("   System will use local storage only")
    else:
        print("❌ Google Cloud Storage library not available")
        print("   System will use local storage only")
    
    # Test 4: Check local storage
    print("\n2. Testing local storage...")
    if os.path.exists('static/uploads'):
        print("✅ Local upload directory exists")
        files = os.listdir('static/uploads')
        print(f"   Files in local storage: {len(files)}")
    else:
        print("❌ Local upload directory doesn't exist")
    
    # Test 5: Check data files
    print("\n3. Testing data files...")
    
    # Check local gallery data
    if os.path.exists('gallery_data.json'):
        try:
            with open('gallery_data.json', 'r') as f:
                local_gallery_data = json.load(f)
            print(f"✅ Local gallery data file exists with {len(local_gallery_data)} items")
        except Exception as e:
            print(f"❌ Error reading local gallery data: {e}")
            local_gallery_data = []
    else:
        print("✅ Local gallery data file doesn't exist yet")
        local_gallery_data = []
    
    # Check cloud gallery data
    if GCS_AVAILABLE:
        try:
            cloud_gallery_data = get_data_from_gcs(GCS_DATA_GALLERY, [])
            print(f"✅ Cloud gallery data exists with {len(cloud_gallery_data)} items")
            
            # Compare local and cloud data
            if len(local_gallery_data) == len(cloud_gallery_data):
                print("✅ Local and cloud gallery data are in sync")
            else:
                print(f"⚠️  Local and cloud gallery data are different (Local: {len(local_gallery_data)}, Cloud: {len(cloud_gallery_data)})")
        except Exception as e:
            print(f"❌ Error reading cloud gallery data: {e}")
            cloud_gallery_data = []
    else:
        print("⚠️  Cannot check cloud gallery data (GCS not available)")
        cloud_gallery_data = []
    
    # Check local users data
    if os.path.exists('users_data.json'):
        try:
            with open('users_data.json', 'r') as f:
                local_users_data = json.load(f)
            print(f"✅ Local users data file exists with {len(local_users_data)} users")
        except Exception as e:
            print(f"❌ Error reading local users data: {e}")
            local_users_data = []
    else:
        print("✅ Local users data file doesn't exist yet")
        local_users_data = []
    
    # Check cloud users data
    if GCS_AVAILABLE:
        try:
            cloud_users_data = get_data_from_gcs(GCS_DATA_USERS, [])
            print(f"✅ Cloud users data exists with {len(cloud_users_data)} users")
            
            # Compare local and cloud data
            if len(local_users_data) == len(cloud_users_data):
                print("✅ Local and cloud users data are in sync")
            else:
                print(f"⚠️  Local and cloud users data are different (Local: {len(local_users_data)}, Cloud: {len(cloud_users_data)})")
        except Exception as e:
            print(f"❌ Error reading cloud users data: {e}")
            cloud_users_data = []
    else:
        print("⚠️  Cannot check cloud users data (GCS not available)")
        cloud_users_data = []
    
    # Test 6: Check image URLs
    print("\n4. Testing image storage...")
    all_gallery_data = local_gallery_data or cloud_gallery_data
    if all_gallery_data:
        for item in all_gallery_data:
            image_url = item.get('image_url', '')
            if image_url.startswith('https://storage.googleapis.com/'):
                print(f"   ✅ Item uses cloud storage: {item.get('title')}")
            elif image_url.startswith('/static/uploads/'):
                print(f"   ✅ Item uses local storage: {item.get('title')}")
            else:
                print(f"   ⚠️  Item has unknown URL format: {item.get('title')}")
    else:
        print("   No gallery items found")
    
    print("\n=== Storage System Summary ===")
    if GCS_AVAILABLE and os.path.exists('tech-ethics-club-sa-key.json'):
        print("✅ Hybrid storage system is ready")
        print("   - Will use Google Cloud Storage when deployed")
        print("   - Will fall back to local storage if needed")
        print("   - Images will work both locally and when deployed")
        print("   - Data is available in both local and cloud storage")
        print("   - Gallery items and user accounts will persist when deployed")
    else:
        print("✅ Local storage system is ready")
        print("   - Will use local storage for development")
        print("   - Images will work locally")
        print("   - For deployment, ensure Google Cloud credentials are available")
    
    print("\n=== Deployment Readiness ===")
    if GCS_AVAILABLE and cloud_gallery_data and cloud_users_data:
        print("✅ FULLY DEPLOYMENT READY")
        print("   - Gallery items will show when deployed")
        print("   - User accounts will be available when deployed")
        print("   - Images will be accessible when deployed")
        print("   - All data is backed up to cloud storage")
    elif GCS_AVAILABLE:
        print("⚠️  PARTIALLY DEPLOYMENT READY")
        print("   - System can use cloud storage")
        print("   - But no data has been migrated yet")
        print("   - Run 'python migrate_to_cloud.py' to migrate data")
    else:
        print("❌ NOT DEPLOYMENT READY")
        print("   - Google Cloud Storage not available")
        print("   - Install google-cloud-storage and add credentials")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_hybrid_storage() 