#!/usr/bin/env python3
"""
Cloud Storage Manager for Tech Ethics Club Website
Handles all data storage using Google Cloud Storage buckets
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from google.cloud import storage
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class CloudStorageManager:
    def __init__(self, bucket_name: str = None):
        """Initialize cloud storage manager."""
        self.bucket_name = bucket_name or os.environ.get('STORAGE_BUCKET', 'tech-ethics-club-uploads')
        
        # Initialize storage client with authentication
        try:
            # For local development, use service account key if available
            if os.path.exists('tech-ethics-club-sa-key.json'):
                self.client = storage.Client.from_service_account_json('tech-ethics-club-sa-key.json')
            else:
                # For production (App Engine), use default credentials
                self.client = storage.Client()
            
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Ensure bucket exists
            if not self.bucket.exists():
                self.bucket.create()
                print(f"Created bucket: {self.bucket_name}")
                
        except Exception as e:
            print(f"Error initializing cloud storage: {e}")
            print("Make sure you have:")
            print("1. Google Cloud SDK installed and authenticated")
            print("2. Service account key file (tech-ethics-club-sa-key.json) for local development")
            print("3. Proper permissions for the storage bucket")
            raise
    
    def _get_blob(self, path: str):
        """Get a blob from the bucket."""
        return self.bucket.blob(path)
    
    def _save_json(self, path: str, data: Dict):
        """Save JSON data to cloud storage."""
        blob = self._get_blob(path)
        blob.upload_from_string(
            json.dumps(data, default=str),
            content_type='application/json'
        )
    
    def _load_json(self, path: str) -> Optional[Dict]:
        """Load JSON data from cloud storage."""
        try:
            blob = self._get_blob(path)
            if blob.exists():
                return json.loads(blob.download_as_text())
            else:
                print(f"File {path} does not exist")
                return None
        except Exception as e:
            print(f"Error loading JSON from {path}: {str(e)}")
            return None
    
    def _list_files(self, prefix: str) -> List[str]:
        """List files with a specific prefix."""
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [blob.name for blob in blobs]
    
    def _delete_file(self, path: str):
        """Delete a file from cloud storage."""
        try:
            blob = self._get_blob(path)
            if blob.exists():
                blob.delete()
                return True
            else:
                print(f"File {path} does not exist")
                return False
        except Exception as e:
            print(f"Error deleting file {path}: {str(e)}")
            return False
    
    # User Management
    def create_user(self, email: str, password: str, is_admin: bool = False) -> Dict:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': is_admin,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Check if email already exists
        if self.get_user_by_email(email):
            raise ValueError('Email already exists')
        
        self._save_json(f'users/{user_id}.json', user_data)
        return user_data
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        return self._load_json(f'users/{user_id}.json')
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        users = self._list_files('users/')
        for user_file in users:
            user_data = self._load_json(user_file)
            if user_data and user_data.get('email') == email:
                return user_data
        return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users."""
        users = []
        user_files = self._list_files('users/')
        for user_file in user_files:
            user_data = self._load_json(user_file)
            if user_data:
                users.append(user_data)
        return users
    
    # Gallery Management
    def create_gallery_item(self, title: str, description: str, image_filename: str, image_url: str, created_by: str, creator_name: str = None, project_link: str = None) -> Dict:
        """Create a new gallery item."""
        item_id = str(uuid.uuid4())
        item_data = {
            'id': item_id,
            'title': title,
            'description': description,
            'image_filename': image_filename,
            'image_url': image_url,
            'creator_name': creator_name,
            'project_link': project_link,
            'created_by': created_by,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        self._save_json(f'gallery/{item_id}.json', item_data)
        return item_data
    
    def get_gallery_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Get gallery item by ID."""
        return self._load_json(f'gallery/{item_id}.json')
    
    def get_all_gallery_items(self) -> List[Dict]:
        """Get all active gallery items."""
        items = []
        item_files = self._list_files('gallery/')
        for item_file in item_files:
            item_data = self._load_json(item_file)
            if item_data and item_data.get('is_active', True):
                items.append(item_data)
        return sorted(items, key=lambda x: x['created_at'], reverse=True)
    
    def delete_gallery_item(self, item_id: str):
        """Hard delete a gallery item."""
        try:
            # Delete the file from cloud storage
            delete_result = self._delete_file(f'gallery/{item_id}.json')
            if delete_result:
                print(f"Successfully deleted gallery item file: {item_id}")
                return True
            else:
                print(f"Failed to delete gallery item file: {item_id}")
                return False
        except Exception as e:
            print(f"Error deleting gallery item {item_id}: {str(e)}")
            return False
    
    def update_gallery_item(self, item_id: str, **kwargs) -> Optional[Dict]:
        """Update a gallery item."""
        item_data = self.get_gallery_item_by_id(item_id)
        if item_data:
            # Update provided fields
            for key, value in kwargs.items():
                if key in ['title', 'description', 'image_filename', 'image_url', 'creator_name', 'project_link']:
                    item_data[key] = value
            
            # Update timestamp
            item_data['updated_at'] = datetime.utcnow().isoformat()
            
            self._save_json(f'gallery/{item_id}.json', item_data)
            return item_data
        return None
    
    # File Upload Management
    def upload_file(self, file_data, filename: str, folder: str = 'uploads') -> str:
        """Upload a file to cloud storage and return the URL."""
        try:
            # Create unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = f"{folder}/{unique_filename}"
            
            print(f"Uploading file: {filename} to path: {file_path}")
            
            # Upload file
            blob = self._get_blob(file_path)
            blob.upload_from_file(file_data)
            
            print(f"File uploaded successfully to blob: {blob.name}")
            
            # Make public and return URL
            blob.make_public()
            public_url = blob.public_url
            
            print(f"File made public. URL: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Error uploading file {filename}: {str(e)}")
            return None
    
    # Authentication
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate a user."""
        user = self.get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

# Global instance
cloud_storage = CloudStorageManager() 