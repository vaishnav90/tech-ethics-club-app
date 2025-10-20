

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from google.cloud import storage
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class CloudStorageManager:
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.environ.get('STORAGE_BUCKET', 'tech-ethics-club-uploads')
        
        self.client = None
        self.bucket = None
        self.auth_error = None
        
        try:
            if os.environ.get('GAE_ENV'):
                print("Running on App Engine - using default credentials")
                self.client = storage.Client()
            elif os.path.exists('tech-ethics-club-sa-key.json'):
                print("Using service account key for authentication")
                self.client = storage.Client.from_service_account_json('tech-ethics-club-sa-key.json')
            else:
                print("Using default credentials for authentication")
                self.client = storage.Client()
            
            self.bucket = self.client.bucket(self.bucket_name)
            
            try:
                list(self.bucket.list_blobs(max_results=1))
                print(f"Successfully connected to bucket: {self.bucket_name}")
            except Exception as bucket_error:
                print(f"Warning: Could not access bucket {self.bucket_name}: {bucket_error}")
                
        except Exception as e:
            self.auth_error = str(e)
            print(f"Error initializing cloud storage: {e}")
            print("Cloud storage will be disabled. Make sure you have:")
            print("1. Google Cloud SDK installed and authenticated")
            print("2. Service account key file (tech-ethics-club-sa-key.json) for local development")
            print("3. Proper permissions for the storage bucket")
    
    def _get_blob(self, path: str):
        return self.bucket.blob(path)
    
    def _save_json(self, path: str, data: Dict):
        blob = self._get_blob(path)
        blob.upload_from_string(
            json.dumps(data, default=str),
            content_type='application/json'
        )
    
    def _load_json(self, path: str) -> Optional[Dict]:
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
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [blob.name for blob in blobs]
    
    def _delete_file(self, path: str):
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
    
    def create_user(self, email: str, password: str, is_admin: bool = False) -> Dict:
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': is_admin,
            'created_at': datetime.utcnow().isoformat()
        }
        
        if self.get_user_by_email(email):
            raise ValueError('Email already exists')
        
        self._save_json(f'users/{user_id}.json', user_data)
        return user_data
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        return self._load_json(f'users/{user_id}.json')
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        users = self._list_files('users/')
        for user_file in users:
            user_data = self._load_json(user_file)
            if user_data and user_data.get('email') == email:
                return user_data
        return None
    
    def get_all_users(self) -> List[Dict]:
        users = []
        user_files = self._list_files('users/')
        for user_file in user_files:
            user_data = self._load_json(user_file)
            if user_data:
                users.append(user_data)
        return users
    
    def _generate_title_based_id(self, title: str) -> str:
        import re
        base_id = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        base_id = re.sub(r'\s+', '-', base_id.strip())
        
        existing_items = self.get_all_gallery_items()
        existing_ids = [item.get('id', '') for item in existing_items]
        
        counter = 1
        final_id = base_id
        while final_id in existing_ids:
            final_id = f"{base_id}-{counter}"
            counter += 1
        
        return final_id

    def create_gallery_item(self, title: str, description: str, image_filename: str, image_url: str, created_by: str, creators: List[Dict] = None, creator_name: str = None, creator_email: str = None, creator_linkedin: str = None, creator_city: str = None, creator_state: str = None, creator_country: str = None, creator_school: str = None, project_link: str = None, tags: List[str] = None, additional_images: List[str] = None, additional_filenames: List[str] = None, videos: List[Dict] = None, course_id: str = None) -> Dict:
        item_id = self._generate_title_based_id(title)
        
        if creators:
            creators_list = creators
        elif creator_name:
            creators_list = [{
                'name': creator_name,
                'email': creator_email or '',
                'linkedin': creator_linkedin or '',
                'city': creator_city or '',
                'state': creator_state or '',
                'country': creator_country or '',
                'school': creator_school or ''
            }]
        else:
            creators_list = []
        
        item_data = {
            'id': item_id,
            'title': title,
            'description': description,
            'image_filename': image_filename,
            'image_url': image_url,
            'additional_images': additional_images or [],
            'additional_filenames': additional_filenames or [],
            'creators': creators_list,
            'creator_name': creator_name,
            'creator_email': creator_email,
            'creator_linkedin': creator_linkedin,
            'creator_city': creator_city,
            'creator_state': creator_state,
            'creator_country': creator_country,
            'creator_school': creator_school,
            'project_link': project_link,
            'tags': tags or [],
            'videos': videos or [],
            'course_id': course_id,
            'created_by': created_by,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        self._save_json(f'gallery/{item_id}.json', item_data)
        return item_data
    
    def get_gallery_item_by_id(self, item_id: str) -> Optional[Dict]:
        item_data = self._load_json(f'gallery/{item_id}.json')
        if item_data:
            return item_data
        
        all_items = self.get_all_gallery_items()
        for item in all_items:
            if item.get('id') == item_id:
                return item
        
        return None
    
    def get_all_gallery_items(self) -> List[Dict]:
        items = []
        item_files = self._list_files('gallery/')
        for item_file in item_files:
            item_data = self._load_json(item_file)
            if item_data and item_data.get('is_active', True):
                items.append(item_data)
        return sorted(items, key=lambda x: x['created_at'], reverse=True)
    
    def delete_gallery_item(self, item_id: str):
        try:
            delete_result = self._delete_file(f'gallery/{item_id}.json')
            if delete_result:
                print(f"Successfully deleted gallery item file: {item_id}")
                return True
            
            all_items = self.get_all_gallery_items()
            for item in all_items:
                if item.get('id') == item_id:
                    actual_filename = f"gallery/{item_id}.json"
                    delete_result = self._delete_file(actual_filename)
                    if delete_result:
                        print(f"Successfully deleted gallery item file: {item_id}")
                        return True
                    break
            
            print(f"Failed to delete gallery item file: {item_id}")
            return False
        except Exception as e:
            print(f"Error deleting gallery item {item_id}: {str(e)}")
            return False
    
    def update_gallery_item(self, item_id: str, **kwargs) -> Optional[Dict]:
        item_data = self.get_gallery_item_by_id(item_id)
        if item_data:
            for key, value in kwargs.items():
                if key in ['title', 'description', 'image_filename', 'image_url', 'creator_name', 'creator_email', 'creator_linkedin', 'creator_city', 'creator_state', 'creator_country', 'creator_school', 'project_link']:
                    item_data[key] = value
            
            item_data['updated_at'] = datetime.utcnow().isoformat()
            
            self._save_json(f'gallery/{item_id}.json', item_data)
            return item_data
        return None
    
    def upload_file(self, file_data, filename: str, folder: str = 'uploads') -> str:
        try:
            if not self.client or not self.bucket:
                print(f"Cloud storage not available. Auth error: {self.auth_error}")
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = f"{folder}/{unique_filename}"
            
            print(f"Uploading file: {filename} to path: {file_path}")
            
            blob = self._get_blob(file_path)
            blob.upload_from_file(file_data)
            
            print(f"File uploaded successfully to blob: {blob.name}")
            
            blob.make_public()
            public_url = blob.public_url
            
            print(f"File made public. URL: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Error uploading file {filename}: {str(e)}")
            print(f"This might be due to authentication issues. Auth error: {self.auth_error}")
            return None
    
    def create_course(self, title: str, description: str, created_by: str, instructor: str = None, course_code: str = None, semester: str = None) -> Dict:
        course_id = self._generate_title_based_id(title)
        course_data = {
            'id': course_id,
            'title': title,
            'description': description,
            'instructor': instructor,
            'course_code': course_code,
            'semester': semester,
            'created_by': created_by,
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            'project_count': 0
        }
        
        self._save_json(f'courses/{course_id}.json', course_data)
        return course_data
    
    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        return self._load_json(f'courses/{course_id}.json')
    
    def get_all_courses(self) -> List[Dict]:
        courses = []
        try:
            blobs = self.bucket.list_blobs(prefix='courses/')
            for blob in blobs:
                if blob.name.endswith('.json'):
                    course_data = self._load_json(blob.name)
                    if course_data and course_data.get('is_active', True):
                        course_data['project_count'] = self._count_course_projects(course_data['id'])
                        courses.append(course_data)
        except Exception as e:
            print(f"Error loading courses: {e}")
        return courses
    
    def _count_course_projects(self, course_id: str) -> int:
        try:
            gallery_items = self.get_all_gallery_items()
            count = 0
            for item in gallery_items:
                if item.get('course_id') == course_id:
                    count += 1
            return count
        except Exception as e:
            print(f"Error counting course projects: {e}")
            return 0
    
    def update_course(self, course_id: str, **kwargs) -> Optional[Dict]:
        course_data = self.get_course_by_id(course_id)
        if course_data:
            for key, value in kwargs.items():
                course_data[key] = value
            course_data['updated_at'] = datetime.utcnow().isoformat()
            self._save_json(f'courses/{course_id}.json', course_data)
            return course_data
        return None
    
    def delete_course(self, course_id: str) -> bool:
        try:
            gallery_items = self.get_all_gallery_items()
            for item in gallery_items:
                if item.get('course_id') == course_id:
                    item['course_id'] = None
                    self._save_json(f'gallery/{item["id"]}.json', item)
            
            blob = self._get_blob(f'courses/{course_id}.json')
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting course: {e}")
            return False
    
    def get_course_projects(self, course_id: str) -> List[Dict]:
        try:
            gallery_items = self.get_all_gallery_items()
            course_projects = []
            for item in gallery_items:
                if item.get('course_id') == course_id:
                    course_projects.append(item)
            return course_projects
        except Exception as e:
            print(f"Error loading course projects: {e}")
            return []
    
    def move_gallery_item_to_course(self, item_id: str, course_id: str = None) -> bool:
        try:
            item_data = self.get_gallery_item_by_id(item_id)
            if not item_data:
                print(f"Gallery item {item_id} not found")
                return False
            
            item_data['course_id'] = course_id
            item_data['updated_at'] = datetime.utcnow().isoformat()
            
            self._save_json(f'gallery/{item_id}.json', item_data)
            
            print(f"Gallery item {item_id} moved to course {course_id}")
            return True
            
        except Exception as e:
            print(f"Error moving gallery item to course: {e}")
            return False
    
    def move_multiple_gallery_items_to_course(self, item_ids: List[str], course_id: str = None) -> Dict[str, bool]:
        results = {}
        for item_id in item_ids:
            results[item_id] = self.move_gallery_item_to_course(item_id, course_id)
        return results

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        user = self.get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None


cloud_storage = CloudStorageManager() 