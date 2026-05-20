from service.vehicle_comparator import compare_vehicles


class VehicleSyncService:
    """Service that orchestrates the synchronization of vehicles between API and Google Sheets. It also rewrites the JSON file, stored in Google Cloud Storage when there are any changes."""

    def __init__(self, api_client, sheet_client, storage_client=None):
        """
        Initialize the sync service with API and Sheet clients.

        Args:
            api_client: APIClient instance for API operations
            sheet_client: SheetClient instance for Google Sheets operations
            storage_client: Optional client for writing the full vehicle JSON export
        """
        self.api_client = api_client
        self.sheet_client = sheet_client
        self.storage_client = storage_client

    def sync(self):
        """
        Synchronizes vehicles between API and Google Sheets.

        This method:
        1. Fetches vehicle data from both API and sheet
        2. Compares them to identify vehicles to update, create, and delete
        3. Performs the necessary operations on the sheet
        """
        api_id_to_changed_tms = self.api_client.get_all_vehicles_id_to_changed_tms()
        sheet_id_to_changed_tms = self.sheet_client.get_id_to_changed_tms()

        comparison_result = compare_vehicles(api_id_to_changed_tms, sheet_id_to_changed_tms)

        print(f"To update: {[v.vehicle_id for v in comparison_result.to_update]}")
        print(f"To create: {[v.vehicle_id for v in comparison_result.to_create]}")
        print(f"To delete: {[v.vehicle_id for v in comparison_result.to_delete]}")

        has_changes = (
            comparison_result.to_update
            or comparison_result.to_create
            or comparison_result.to_delete
        )
        fetched_vehicles_by_id = {}

        """
        Update affected rows - fetch full details for vehicles to update
        """
        if comparison_result.to_update:
            print(f"Updating {len(comparison_result.to_update)} vehicles...")
            update_ids = [v.vehicle_id for v in comparison_result.to_update]
            update_vehicles = self.api_client.get_vehicles_details_by_ids(update_ids)
            fetched_vehicles_by_id.update({
                vehicle.vehicle_id: vehicle
                for vehicle in update_vehicles
            })
            self.sheet_client.update_rows(update_vehicles)

        """
        Delete affected rows
        """
        if comparison_result.to_delete:
            print(f"Deleting {len(comparison_result.to_delete)} vehicles...")
            delete_ids = [v.vehicle_id for v in comparison_result.to_delete]
            self.sheet_client.delete_rows(delete_ids)
            """
            Compact sheet to remove gaps after deletion
            """
            self.sheet_client.compact()

        """
        Create new rows - fetch full details for vehicles to create
        """
        if comparison_result.to_create:
            print(f"Creating {len(comparison_result.to_create)} vehicles...")
            create_ids = [v.vehicle_id for v in comparison_result.to_create]
            create_vehicles = self.api_client.get_vehicles_details_by_ids(create_ids)
            fetched_vehicles_by_id.update({
                vehicle.vehicle_id: vehicle
                for vehicle in create_vehicles
            })
            self.sheet_client.create_rows(create_vehicles)

        if has_changes and self.storage_client:
            api_ids = list(api_id_to_changed_tms.keys())
            missing_ids = [
                vehicle_id
                for vehicle_id in api_ids
                if vehicle_id not in fetched_vehicles_by_id
            ]
            if missing_ids:
                missing_vehicles = self.api_client.get_vehicles_details_by_ids(missing_ids)
                fetched_vehicles_by_id.update({
                    vehicle.vehicle_id: vehicle
                    for vehicle in missing_vehicles
                })
            vehicles = [
                fetched_vehicles_by_id[vehicle_id]
                for vehicle_id in api_ids
            ]
            self.storage_client.rewrite_vehicles_json(vehicles)

        print("Pipeline completed!")
