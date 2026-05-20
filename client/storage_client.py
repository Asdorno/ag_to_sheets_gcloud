import os

from secret_accessor import get_secret
from storage.gcs_uploader import upload_json_to_gcs, vehicles_to_json


class StorageClient:
    """Client for writing the generated vehicle JSON file to Google Cloud Storage."""

    def __init__(self, bucket_name: str | None = None, object_name: str | None = None):
        self.bucket_name = bucket_name or get_secret("GCS_BUCKET_NAME").strip()
        self.object_name = object_name or os.getenv("GCS_JSON_OBJECT_NAME", "vehicles.json")

    def rewrite_vehicles_json(self, vehicles):
        json_content = vehicles_to_json(vehicles)
        upload_json_to_gcs(self.bucket_name, self.object_name, json_content)
