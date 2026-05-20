import json

from google.cloud import storage

from model.vehicle import Vehicle


def vehicles_to_json(vehicles: list[Vehicle]) -> str:
    """
    Serializes Vehicle objects to the JSON payload written to storage.
    """
    vehicle_dicts = [
        vehicle.model_dump(mode="json")
        for vehicle in vehicles
    ]
    return json.dumps(vehicle_dicts, ensure_ascii=False, indent=2)


def upload_json_to_gcs(bucket_name: str, object_name: str, json_content: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    blob.upload_from_string(
        json_content,
        content_type="application/json",
    )
