from client.api_client import APIClient
from client.sheet_client import SheetClient
from client.storage_client import StorageClient
from service.vehicle_sync_service import VehicleSyncService


def main():
    api_client = APIClient()
    sheet_client = SheetClient()
    storage_client = StorageClient()
    service = VehicleSyncService(api_client, sheet_client, storage_client)
    service.sync()


if __name__ == "__main__":
    main()
