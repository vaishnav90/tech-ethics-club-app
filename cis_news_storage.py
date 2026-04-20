"""JSON blob in GCS for short CIS news posts (title, body, optional image URL)."""

import json
import os
import threading
import uuid
from datetime import datetime

from google.cloud import storage


class CisNewsStorage:
    _shared_blob = None
    _lock = threading.Lock()

    def __init__(self):
        self.bucket_name = os.environ.get("STORAGE_BUCKET", "tech-ethics-club-uploads")
        self.blob_name = "cis_news.json"
        self.process_id = os.getpid()

        try:
            if os.path.exists("tech-ethics-club-sa-key.json"):
                self.client = storage.Client.from_service_account_json(
                    "tech-ethics-club-sa-key.json"
                )
            else:
                self.client = storage.Client()

            self.bucket = self.client.bucket(self.bucket_name)

            if CisNewsStorage._shared_blob is None:
                CisNewsStorage._shared_blob = self.bucket.blob(self.blob_name)

            self._blob = CisNewsStorage._shared_blob

        except Exception as e:
            print(f"Error initializing CIS news storage: {e}")
            raise

    def _load_items(self):
        with self._lock:
            try:
                blob = self._blob
                if blob.exists():
                    data = json.loads(blob.download_as_text())
                    if not isinstance(data, list):
                        return []
                    print(
                        f"✅ [PID:{self.process_id}] Loaded {len(data)} CIS news items from "
                        f"{self.bucket_name}/{self.blob_name}"
                    )
                    return data
                print(
                    f"📝 No CIS news file at {self.bucket_name}/{self.blob_name}; starting empty"
                )
                return []
            except Exception as e:
                print(f"❌ Error loading CIS news: {e}")
                return []

    def _save_items(self, items):
        """Persist list (may be empty after deleting all items)."""
        with self._lock:
            try:
                if not isinstance(items, list):
                    print("❌ CIS news save rejected: payload must be a list")
                    return False
                content = json.dumps(items, indent=2, default=str)
                self._blob.upload_from_string(content, content_type="application/json")
                print(
                    f"✅ [PID:{self.process_id}] Saved {len(items)} CIS news items to "
                    f"{self.bucket_name}/{self.blob_name}"
                )
                return True
            except Exception as e:
                print(f"❌ Error saving CIS news: {e}")
                return False

    def get_all_items(self):
        try:
            items = self._load_items()
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return items
        except Exception as e:
            print(f"Error listing CIS news: {e}")
            return []

    def add_item(self, title, body, image_url, created_by_email):
        try:
            items = self._load_items()
            new_item = {
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "body": body.strip(),
                "image_url": image_url or None,
                "created_at": datetime.now().isoformat(),
                "created_by_email": created_by_email,
            }
            items.append(new_item)
            if self._save_items(items):
                return new_item
            return None
        except Exception as e:
            print(f"Error adding CIS news item: {e}")
            return None

    def delete_item(self, item_id):
        try:
            items = self._load_items()
            before = len(items)
            items = [i for i in items if i.get("id") != item_id]
            if len(items) < before:
                return self._save_items(items)
            return False
        except Exception as e:
            print(f"Error deleting CIS news item: {e}")
            return False

    def get_item_by_id(self, item_id):
        try:
            for item in self._load_items():
                if item.get("id") == item_id:
                    return item
            return None
        except Exception as e:
            print(f"Error fetching CIS news item: {e}")
            return None


cis_news_storage = CisNewsStorage()
