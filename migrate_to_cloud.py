#!/usr/bin/env python3
"""
Migration script to move local data to cloud storage.
This ensures that gallery items and user data will be available when deployed.
"""

import json
import os
from app import save_data_to_gcs, GCS_DATA_USERS, GCS_DATA_GALLERY

def migrate_data_to_cloud():
    """Migrate local data to cloud storage"""
    print("=== Migrating Data to Cloud Storage ===\n")
    
    # Migrate users data
    print("1. Migrating users data...")
    if os.path.exists('users_data.json'):
        try:
            with open('users_data.json', 'r') as f:
                users_data = json.load(f)
            
            if save_data_to_gcs(GCS_DATA_USERS, users_data):
                print(f"✅ Successfully migrated {len(users_data)} users to cloud storage")
                for user in users_data:
                    print(f"   - {user.get('email')} (Admin: {user.get('is_admin', False)})")
            else:
                print("❌ Failed to migrate users data to cloud storage")
        except Exception as e:
            print(f"❌ Error reading users data: {e}")
    else:
        print("⚠️  No local users data found")
    
    # Migrate gallery data
    print("\n2. Migrating gallery data...")
    if os.path.exists('gallery_data.json'):
        try:
            with open('gallery_data.json', 'r') as f:
                gallery_data = json.load(f)
            
            if save_data_to_gcs(GCS_DATA_GALLERY, gallery_data):
                print(f"✅ Successfully migrated {len(gallery_data)} gallery items to cloud storage")
                for item in gallery_data:
                    print(f"   - {item.get('title')} (Image: {item.get('image_filename')})")
            else:
                print("❌ Failed to migrate gallery data to cloud storage")
        except Exception as e:
            print(f"❌ Error reading gallery data: {e}")
    else:
        print("⚠️  No local gallery data found")
    
    print("\n=== Migration Complete ===")
    print("\nYour data is now available in both local and cloud storage.")
    print("When deployed, the app will automatically use cloud storage.")
    print("During development, it will use local storage for faster access.")

if __name__ == '__main__':
    migrate_data_to_cloud() 