#!/usr/bin/env python3
"""
One-off maintenance: clear `tags` on gallery items that have a course_id.

Run from repo root: python remove_tags_from_course_projects.py
Requires same GCS credentials as the main app. Uses CloudStorageManager._save_json
(internal API) — prefer a proper cloud_storage method if you add more migrations.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cloud_storage import CloudStorageManager

def remove_tags_from_course_projects():
    """Remove tags from all gallery items assigned to a course."""
    cloud_storage = CloudStorageManager()
    
    print("Fetching all gallery items...")
    all_items = cloud_storage.get_all_gallery_items()
    
    updated_count = 0
    items_with_tags = 0
    
    for item in all_items:
        course_id = item.get('course_id')
        tags = item.get('tags', [])
        
        if course_id and tags:
            items_with_tags += 1
            print(f"\nFound item '{item.get('title', 'Unknown')}' (ID: {item.get('id')}) assigned to course {course_id} with tags: {tags}")
            
            # Remove tags
            item['tags'] = []
            from datetime import datetime
            item['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated item
            item_id = item.get('id')
            if item_id:
                try:
                    cloud_storage._save_json(f'gallery/{item_id}.json', item)
                    updated_count += 1
                    print(f"  ✓ Removed tags from '{item.get('title', 'Unknown')}'")
                except Exception as e:
                    print(f"  ✗ Error updating item {item_id}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total items checked: {len(all_items)}")
    print(f"  Items assigned to courses with tags: {items_with_tags}")
    print(f"  Items updated: {updated_count}")
    print(f"{'='*60}")
    
    return updated_count

if __name__ == '__main__':
    try:
        count = remove_tags_from_course_projects()
        if count > 0:
            print(f"\n✓ Successfully removed tags from {count} course-assigned project(s)")
        else:
            print("\n✓ No course-assigned projects with tags found")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

