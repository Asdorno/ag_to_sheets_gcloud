from google.cloud import secretmanager


def get_secret(secret_id):
    """
    Retrieves a secret from Google Cloud Secret Manager.

    Args:
        secret_id: The ID of the secret to retrieve.

    Returns:
        str: The decoded secret value.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/whats-app-project-toni-wihbe/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')
