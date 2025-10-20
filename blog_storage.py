

import os
import json
import uuid
import re
from datetime import datetime
from google.cloud import storage
import threading

class BlogStorage:
    _shared_data = None
    _shared_blob = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.bucket_name = os.environ.get('STORAGE_BUCKET', 'tech-ethics-club-uploads')
        self.blog_blob_name = 'blog_posts.json'
        self.process_id = os.getpid()
        
        try:
            if os.path.exists('tech-ethics-club-sa-key.json'):
                self.client = storage.Client.from_service_account_json('tech-ethics-club-sa-key.json')
            else:
                self.client = storage.Client()
            
            self.bucket = self.client.bucket(self.bucket_name)
            
            if BlogStorage._shared_blob is None:
                BlogStorage._shared_blob = self.bucket.blob(self.blog_blob_name)
            
            self._blog_blob = BlogStorage._shared_blob
            
        except Exception as e:
            print(f"Error initializing blog storage: {e}")
            raise
    
    def _get_blog_blob(self):
        return self._blog_blob
    
    def _load_blog_posts(self):
        with self._lock:
            try:
                blob = self._get_blog_blob()
                if blob.exists():
                    content = blob.download_as_text()
                    posts = json.loads(content)
                    print(f"✅ [PID:{self.process_id}] Loaded {len(posts)} blog posts from {self.bucket_name}/{self.blog_blob_name}")
                    return posts
                else:
                    print(f"📝 No blog posts file found at {self.bucket_name}/{self.blog_blob_name}")
                    initial_posts = []
                    blob = self._get_blog_blob()
                    content = json.dumps(initial_posts, indent=2, default=str)
                    blob.upload_from_string(content, content_type='application/json')
                    print(f"✅ [PID:{self.process_id}] Created initial blog posts file")
                    return initial_posts
            except Exception as e:
                print(f"❌ Error loading blog posts from {self.bucket_name}/{self.blog_blob_name}: {e}")
                return []
    
    def _generate_slug(self, title):
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def _save_blog_posts(self, blog_posts):
        with self._lock:
            try:
                if not blog_posts:
                    print("❌ Cannot save empty blog posts - this prevents data corruption")
                    return False
                
                blob = self._get_blog_blob()
                content = json.dumps(blog_posts, indent=2, default=str)
                blob.upload_from_string(content, content_type='application/json')
                
                print(f"✅ [PID:{self.process_id}] Saved {len(blog_posts)} blog posts to {self.bucket_name}/{self.blog_blob_name}")
                return True
                            
            except Exception as e:
                print(f"❌ Error saving blog posts to {self.bucket_name}/{self.blog_blob_name}: {e}")
                return False
    
    def add_blog_post(self, title, content, author_email, author_name, author_city=None, author_state=None, author_country=None, author_school=None, tags=None):
        try:
            blog_posts = self._load_blog_posts()
            
            slug = self._generate_slug(title)
            
            counter = 1
            original_slug = slug
            while any(post.get('slug') == slug for post in blog_posts):
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            new_post = {
                'id': str(uuid.uuid4()),
                'title': title,
                'slug': slug,
                'content': content,
                'author_email': author_email,
                'author_name': author_name,
                'author_city': author_city,
                'author_state': author_state,
                'author_country': author_country,
                'author_school': author_school,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if not blog_posts and not new_post:
                print("❌ Cannot save empty blog posts")
                return None
                
            blog_posts.append(new_post)
            
            if self._save_blog_posts(blog_posts):
                return new_post
            else:
                return None
                
        except Exception as e:
            print(f"Error adding blog post: {e}")
            return None
    
    def get_all_blog_posts(self):
        try:
            blog_posts = self._load_blog_posts()
            blog_posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return blog_posts
        except Exception as e:
            print(f"Error getting blog posts: {e}")
            return []
    
    def get_blog_post_by_id(self, post_id):
        try:
            blog_posts = self._load_blog_posts()
            for post in blog_posts:
                if post.get('id') == post_id:
                    return post
            return None
        except Exception as e:
            print(f"Error getting blog post: {e}")
            return None
    
    def get_blog_post_by_slug(self, slug):
        try:
            blog_posts = self._load_blog_posts()
            for post in blog_posts:
                if post.get('slug') == slug:
                    return post
            return None
        except Exception as e:
            print(f"Error getting blog post by slug: {e}")
            return None
    
    def update_blog_post(self, post_id, title, content, author_name, author_city=None, author_state=None, author_country=None, author_school=None, tags=None):
        try:
            blog_posts = self._load_blog_posts()
            
            for post in blog_posts:
                if post.get('id') == post_id:
                    if post.get('title') != title:
                        new_slug = self._generate_slug(title)
                        counter = 1
                        original_slug = new_slug
                        while any(p.get('slug') == new_slug and p.get('id') != post_id for p in blog_posts):
                            new_slug = f"{original_slug}-{counter}"
                            counter += 1
                        post['slug'] = new_slug
                    
                    post['title'] = title
                    post['content'] = content
                    post['author_name'] = author_name
                    post['author_city'] = author_city
                    post['author_state'] = author_state
                    post['author_country'] = author_country
                    post['author_school'] = author_school
                    post['tags'] = tags or []
                    post['updated_at'] = datetime.now().isoformat()
                    
                    if self._save_blog_posts(blog_posts):
                        return post
                    else:
                        return None
            
            return None
                
        except Exception as e:
            print(f"Error updating blog post: {e}")
            return None
    
    def delete_blog_post(self, post_id):
        try:
            blog_posts = self._load_blog_posts()
            
            original_count = len(blog_posts)
            blog_posts = [post for post in blog_posts if post.get('id') != post_id]
            
            if len(blog_posts) < original_count:
                if self._save_blog_posts(blog_posts):
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"Error deleting blog post: {e}")
            return False
    
    def search_blog_posts(self, query):
        try:
            blog_posts = self._load_blog_posts()
            query = query.lower()
            
            results = []
            for post in blog_posts:
                if query in post.get('title', '').lower():
                    results.append(post)
                    continue
                
                if query in post.get('content', '').lower():
                    results.append(post)
                    continue
                
                for tag in post.get('tags', []):
                    if query in tag.lower():
                        results.append(post)
                        break
            
            results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return results
            
        except Exception as e:
            print(f"Error searching blog posts: {e}")
            return []
    
    def ensure_data_consistency(self):
        try:
            print("🔍 Checking data consistency...")
            
            blob = self._get_blog_blob()
            if blob.exists():
                print("✅ Data consistency check completed")
                return True
            else:
                print("📝 Creating initial blog posts file")
                initial_posts = []
                self._save_blog_posts(initial_posts)
                return True
                
        except Exception as e:
            print(f"❌ Error ensuring data consistency: {e}")
            return False
    
    @classmethod
    def get_shared_instance(cls):
        if cls._shared_data is None:
            cls._shared_data = cls()
        return cls._shared_data


blog_storage = BlogStorage() 