#!/usr/bin/env python3
"""
Script to sync cloud data to local storage.
This ensures local development environment has the same data as cloud storage.
"""

import json
import os
from app import get_data_from_gcs, GCS_DATA_USERS, GCS_DATA_GALLERY

def sync_cloud_data():
    """Sync data from cloud storage to local files"""
    print("=== Syncing Cloud Data to Local Storage ===\n")
    
    # Sync gallery data
    print("1. Syncing gallery data...")
    try:
        cloud_gallery_data = get_data_from_gcs(GCS_DATA_GALLERY, [])
        if cloud_gallery_data:
            with open('gallery_data.json', 'w', encoding='utf-8') as f:
                json.dump(cloud_gallery_data, f, indent=2, default=str)
            print(f"✅ Synced {len(cloud_gallery_data)} gallery items to local storage")
            for item in cloud_gallery_data:
                print(f"   - {item.get('title')} (Image: {item.get('image_filename')})")
        else:
            print("⚠️  No gallery data found in cloud storage")
    except Exception as e:
        print(f"❌ Error syncing gallery data: {e}")
    
    # Sync users data
    print("\n2. Syncing users data...")
    try:
        cloud_users_data = get_data_from_gcs(GCS_DATA_USERS, [])
        if cloud_users_data:
            with open('users_data.json', 'w', encoding='utf-8') as f:
                json.dump(cloud_users_data, f, indent=2, default=str)
            print(f"✅ Synced {len(cloud_users_data)} users to local storage")
            for user in cloud_users_data:
                print(f"   - {user.get('email')} (Admin: {user.get('is_admin', False)})")
        else:
            print("⚠️  No users data found in cloud storage")
    except Exception as e:
        print(f"❌ Error syncing users data: {e}")
    
    print("\n=== Sync Complete ===")
    print("\nNow when you run the app locally, it will:")
    print("1. Always read from cloud storage first")
    print("2. Show the same data as everyone else")
    print("3. Save new items to cloud storage so others can see them")
    print("4. Keep local files in sync for development")

if __name__ == '__main__':
    sync_cloud_data() 