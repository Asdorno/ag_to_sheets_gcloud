import os
from dotenv import load_dotenv
from google.cloud import secretmanager
import google.auth


def get_project_id() -> str:
    """
        Retrieves the Google Cloud project ID.

        Returns:
            str: the Google Cloud project ID.

        Raises:
            RuntimeError: If Google Cloud project ID is not accessible through default auth or environment variables.
        """
    load_dotenv()
    _, project_id = google.auth.default()

    if project_id:
        return project_id

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError(
            "Could not determine Google Cloud project ID."
            "Set GOOGLE_CLOUD_PROJECT environment variable or configure Application Default Credentials"
        )
    return project_id


def get_secret(secret_id):
    """
    Retrieves a secret from Google Cloud Secret Manager.

    Args:
        secret_id: The ID of the secret to retrieve.

    Returns:
        str: The decoded secret value.
    """
    client = secretmanager.SecretManagerServiceClient()
    project_id = get_project_id()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')
