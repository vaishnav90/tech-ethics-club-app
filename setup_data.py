#!/usr/bin/env python3
"""
Setup script to initialize Cloud Storage data files
This creates the initial JSON files for users and gallery items in your Cloud Storage bucket.
"""

import json
import os
from google.cloud import storage

def setup_cloud_storage_data():
    """Initialize Cloud Storage data files"""
    print("Setting up Cloud Storage data files...")
    
    # Bucket name
    bucket_name = 'tech-ethics-club-uploads'
    
    try:
        # Initialize Cloud Storage client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            print(f"❌ Bucket {bucket_name} does not exist. Please run setup_gcs.py first.")
            return False
        
        print(f"✅ Using bucket: {bucket_name}")
        
        # Initialize users.json
        users_file = 'data/users.json'
        users_blob = bucket.blob(users_file)
        
        if not users_blob.exists():
            initial_users = []
            users_blob.upload_from_string(
                json.dumps(initial_users, indent=2),
                content_type='application/json'
            )
            print(f"✅ Created {users_file}")
        else:
            print(f"✅ {users_file} already exists")
        
        # Initialize gallery.json
        gallery_file = 'data/gallery.json'
        gallery_blob = bucket.blob(gallery_file)
        
        if not gallery_blob.exists():
            initial_gallery = []
            gallery_blob.upload_from_string(
                json.dumps(initial_gallery, indent=2),
                content_type='application/json'
            )
            print(f"✅ Created {gallery_file}")
        else:
            print(f"✅ {gallery_file} already exists")
        
        print("\n🎉 Cloud Storage data files setup complete!")
        print(f"\nYour data will be stored in:")
        print(f"- Users: gs://{bucket_name}/{users_file}")
        print(f"- Gallery: gs://{bucket_name}/{gallery_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Cloud Storage data: {e}")
        return False

if __name__ == "__main__":
    if setup_cloud_storage_data():
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed!")
        exit(1) 