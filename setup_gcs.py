#!/usr/bin/env python3
"""
Script to set up proper Cloud Storage authentication for both local and deployed environments.
This ensures both environments use the same service account and can access the same data.
"""

import os
import json
from google.cloud import storage
from google.oauth2 import service_account

# Configuration
GCS_BUCKET_NAME = 'tech-ethics-club-uploads'
GCS_DATA_USERS = 'data/users.json'
GCS_DATA_GALLERY = 'data/gallery.json'
SERVICE_ACCOUNT_KEY_FILE = 'tech-ethics-club-sa-key.json'

def setup_service_account_auth():
    """Set up authentication using the service account key file"""
    print("=== Setting up Service Account Authentication ===")
    
    if not os.path.exists(SERVICE_ACCOUNT_KEY_FILE):
        print(f"❌ Service account key file not found: {SERVICE_ACCOUNT_KEY_FILE}")
        return False
    
    try:
        # Set the environment variable to use the service account
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(SERVICE_ACCOUNT_KEY_FILE)
        print(f"✅ Set GOOGLE_APPLICATION_CREDENTIALS to: {os.path.abspath(SERVICE_ACCOUNT_KEY_FILE)}")
        
        # Test the authentication
        client = storage.Client()
        project = client.project
        print(f"✅ Successfully authenticated with project: {project}")
        
        # Check if we're using the service account
        credentials = client._credentials
        if hasattr(credentials, 'service_account_email'):
            print(f"✅ Using service account: {credentials.service_account_email}")
        else:
            print("⚠️  Not using service account credentials")
            
        return True
        
    except Exception as e:
        print(f"❌ Error setting up service account authentication: {e}")
        return False

def verify_bucket_access():
    """Verify we can access the bucket with service account"""
    print("\n=== Verifying Bucket Access ===")
    
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        if not bucket.exists():
            print(f"❌ Bucket {GCS_BUCKET_NAME} does not exist")
            return False
        
        print(f"✅ Successfully accessed bucket: {GCS_BUCKET_NAME}")
        
        # Test read access
        blobs = list(bucket.list_blobs(max_results=5))
        print(f"✅ Can list bucket contents ({len(blobs)} items visible)")
        
        # Test write access
        test_blob = bucket.blob('test_auth.json')
        test_data = {'test': 'authentication'}
        test_blob.upload_from_string(json.dumps(test_data), content_type='application/json')
        print("✅ Can write to bucket")
        
        # Clean up test file
        test_blob.delete()
        print("✅ Can delete from bucket")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing bucket: {e}")
        return False

def check_data_consistency():
    """Check if data files exist and are accessible"""
    print("\n=== Checking Data Consistency ===")
    
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Check users.json
        users_blob = bucket.blob(GCS_DATA_USERS)
        if users_blob.exists():
            content = users_blob.download_as_text()
            users_data = json.loads(content)
            print(f"✅ Users file exists with {len(users_data)} users")
        else:
            print("⚠️  Users file does not exist")
        
        # Check gallery.json
        gallery_blob = bucket.blob(GCS_DATA_GALLERY)
        if gallery_blob.exists():
            content = gallery_blob.download_as_text()
            gallery_data = json.loads(content)
            print(f"✅ Gallery file exists with {len(gallery_data)} items")
        else:
            print("⚠️  Gallery file does not exist")
            
    except Exception as e:
        print(f"❌ Error checking data consistency: {e}")

def create_initial_data():
    """Create initial data files if they don't exist"""
    print("\n=== Creating Initial Data (if needed) ===")
    
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Create users.json if it doesn't exist
        users_blob = bucket.blob(GCS_DATA_USERS)
        if not users_blob.exists():
            initial_users = []
            users_blob.upload_from_string(json.dumps(initial_users), content_type='application/json')
            print("✅ Created initial users.json")
        else:
            print("ℹ️  users.json already exists")
        
        # Create gallery.json if it doesn't exist
        gallery_blob = bucket.blob(GCS_DATA_GALLERY)
        if not gallery_blob.exists():
            initial_gallery = []
            gallery_blob.upload_from_string(json.dumps(initial_gallery), content_type='application/json')
            print("✅ Created initial gallery.json")
        else:
            print("ℹ️  gallery.json already exists")
            
    except Exception as e:
        print(f"❌ Error creating initial data: {e}")

def main():
    """Main setup function"""
    print("🔧 Cloud Storage Setup Tool")
    print("=" * 50)
    
    # Set up service account authentication
    if not setup_service_account_auth():
        print("\n❌ Failed to set up authentication")
        return
    
    # Verify bucket access
    if not verify_bucket_access():
        print("\n❌ Failed to verify bucket access")
        return
    
    # Check data consistency
    check_data_consistency()
    
    # Create initial data if needed
    create_initial_data()
    
    print("\n" + "=" * 50)
    print("🔧 Setup Complete")
    print("\nNext steps:")
    print("1. Your local environment is now configured to use the service account")
    print("2. Both local and deployed environments should now see the same data")
    print("3. Test by adding a gallery item locally and checking if it appears in the deployed app")
    print("4. If issues persist, check the service account permissions in Google Cloud Console")

if __name__ == '__main__':
    main() 