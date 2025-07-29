#!/usr/bin/env python3
"""
Diagnostic script to check Cloud Storage data and identify issues between local and deployed environments.
"""

import os
import json
from google.cloud import storage

# Configuration - should match app.py
GCS_BUCKET_NAME = 'tech-ethics-club-uploads'
GCS_DATA_USERS = 'data/users.json'
GCS_DATA_GALLERY = 'data/gallery.json'

def get_gcs_bucket():
    """Get the GCS bucket"""
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        return bucket
    except Exception as e:
        print(f"Error accessing GCS: {e}")
        return None

def check_bucket_access():
    """Check if we can access the bucket"""
    print("=== Checking Bucket Access ===")
    bucket = get_gcs_bucket()
    if not bucket:
        print("❌ Cannot access GCS bucket")
        return False
    
    print(f"✅ Successfully connected to bucket: {GCS_BUCKET_NAME}")
    print(f"Bucket exists: {bucket.exists()}")
    return True

def list_bucket_contents():
    """List all files in the bucket"""
    print("\n=== Bucket Contents ===")
    bucket = get_gcs_bucket()
    if not bucket:
        return
    
    blobs = list(bucket.list_blobs())
    print(f"Total files in bucket: {len(blobs)}")
    
    for blob in blobs:
        print(f"  - {blob.name} ({blob.size} bytes)")
        if blob.name.startswith('data/'):
            print(f"    Last modified: {blob.updated}")

def check_data_files():
    """Check the specific data files"""
    print("\n=== Checking Data Files ===")
    bucket = get_gcs_bucket()
    if not bucket:
        return
    
    # Check users.json
    users_blob = bucket.blob(GCS_DATA_USERS)
    print(f"Users file ({GCS_DATA_USERS}):")
    if users_blob.exists():
        try:
            content = users_blob.download_as_text()
            users_data = json.loads(content)
            print(f"  ✅ Exists - {len(users_data)} users")
            for user in users_data:
                print(f"    - {user.get('email')} (admin: {user.get('is_admin', False)})")
        except Exception as e:
            print(f"  ❌ Error reading: {e}")
    else:
        print("  ❌ Does not exist")
    
    # Check gallery.json
    gallery_blob = bucket.blob(GCS_DATA_GALLERY)
    print(f"\nGallery file ({GCS_DATA_GALLERY}):")
    if gallery_blob.exists():
        try:
            content = gallery_blob.download_as_text()
            gallery_data = json.loads(content)
            print(f"  ✅ Exists - {len(gallery_data)} items")
            for item in gallery_data:
                print(f"    - {item.get('title')} (ID: {item.get('id')})")
                print(f"      Image: {item.get('image_filename')}")
        except Exception as e:
            print(f"  ❌ Error reading: {e}")
    else:
        print("  ❌ Does not exist")

def check_authentication():
    """Check current authentication context"""
    print("\n=== Authentication Context ===")
    try:
        client = storage.Client()
        project = client.project
        print(f"Current project: {project}")
        
        # Try to get credentials info
        credentials = client._credentials
        if hasattr(credentials, 'service_account_email'):
            print(f"Service account: {credentials.service_account_email}")
        else:
            print("Using user credentials (not service account)")
            
    except Exception as e:
        print(f"Error checking authentication: {e}")

def create_test_data():
    """Create test data to verify write access"""
    print("\n=== Testing Write Access ===")
    bucket = get_gcs_bucket()
    if not bucket:
        return
    
    test_data = {
        'test_timestamp': '2024-01-01T00:00:00Z',
        'test_message': 'This is a test from the diagnostic script'
    }
    
    test_blob = bucket.blob('test_diagnostic.json')
    try:
        test_blob.upload_from_string(json.dumps(test_data), content_type='application/json')
        print("✅ Successfully wrote test file")
        
        # Verify we can read it back
        content = test_blob.download_as_text()
        read_data = json.loads(content)
        print(f"✅ Successfully read back test file: {read_data}")
        
        # Clean up
        test_blob.delete()
        print("✅ Successfully deleted test file")
        
    except Exception as e:
        print(f"❌ Error testing write access: {e}")

def main():
    """Main diagnostic function"""
    print("🔍 Cloud Storage Diagnostic Tool")
    print("=" * 50)
    
    # Check authentication
    check_authentication()
    
    # Check bucket access
    if not check_bucket_access():
        print("\n❌ Cannot proceed without bucket access")
        return
    
    # List bucket contents
    list_bucket_contents()
    
    # Check data files
    check_data_files()
    
    # Test write access
    create_test_data()
    
    print("\n" + "=" * 50)
    print("🔍 Diagnostic Complete")
    print("\nNext steps:")
    print("1. If you see different data locally vs deployed, check your authentication")
    print("2. Make sure both environments use the same service account")
    print("3. Verify the bucket name is correct in both environments")
    print("4. Check that the service account has proper permissions")

if __name__ == '__main__':
    main() 