#!/usr/bin/env python3
"""
Test the new cloud storage system.
"""

from cloud_storage import cloud_storage

def test_new_system():
    """Test the new cloud storage system"""
    print("=== Testing New Cloud Storage System ===\n")
    
    print("1. Testing user management...")
    try:
        # Test creating a user
        user = cloud_storage.create_user(email="test@example.com", password="test123", is_admin=True)
        print(f"   Created user: {user['email']}")
        
        # Test getting user by email
        found_user = cloud_storage.get_user_by_email("test@example.com")
        print(f"   Found user: {found_user['email'] if found_user else 'Not found'}")
        
        # Test authentication
        auth_user = cloud_storage.authenticate_user("test@example.com", "test123")
        print(f"   Authentication: {'Success' if auth_user else 'Failed'}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Testing gallery management...")
    try:
        # Test creating a gallery item
        item = cloud_storage.create_gallery_item(
            title="Test Item",
            description="Test Description",
            image_filename="test.jpg",
            image_url="https://example.com/test.jpg",
            created_by="test-user-id"
        )
        print(f"   Created gallery item: {item['title']}")
        
        # Test getting all gallery items
        items = cloud_storage.get_all_gallery_items()
        print(f"   Total gallery items: {len(items)}")
        
        # Test getting item by ID
        found_item = cloud_storage.get_gallery_item_by_id(item['id'])
        print(f"   Found item: {found_item['title'] if found_item else 'Not found'}")
        
        # Test deleting item
        success = cloud_storage.delete_gallery_item(item['id'])
        print(f"   Deleted item: {'Success' if success else 'Failed'}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Testing file listing...")
    try:
        # List all files in the bucket
        all_files = cloud_storage._list_files('')
        print(f"   Total files in bucket: {len(all_files)}")
        
        # List gallery files
        gallery_files = cloud_storage._list_files('gallery/')
        print(f"   Gallery files: {len(gallery_files)}")
        
        # List user files
        user_files = cloud_storage._list_files('users/')
        print(f"   User files: {len(user_files)}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_new_system() 