from client.api_client import APIClient
from client.sheet_client import SheetClient
from service.vehicle_sync_service import VehicleSyncService


def main():
    api_client = APIClient()
    sheet_client = SheetClient()
    service = VehicleSyncService(api_client, sheet_client)
    service.sync()


if __name__ == "__main__":
    main()
