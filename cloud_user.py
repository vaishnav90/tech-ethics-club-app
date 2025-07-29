#!/usr/bin/env python3
"""
Cloud User class for Flask-Login integration
"""

from flask_login import UserMixin
from cloud_storage import cloud_storage

class CloudUser(UserMixin):
    def __init__(self, user_data: dict):
        self.user_data = user_data
        self.id = user_data['id']
        self.email = user_data['email']
        self.is_admin = user_data.get('is_admin', False)
        self.created_at = user_data['created_at']
    
    def get_id(self):
        return self.id
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.user_data['password_hash'], password)
    
    @staticmethod
    def get(user_id):
        """Get user by ID for Flask-Login."""
        user_data = cloud_storage.get_user_by_id(user_id)
        if user_data:
            return CloudUser(user_data)
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        user_data = cloud_storage.get_user_by_email(email)
        if user_data:
            return CloudUser(user_data)
        return None
    
    def __repr__(self):
        return f'<CloudUser {self.email}>' 