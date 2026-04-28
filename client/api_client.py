from service.vehicle_service import get_all_vehicles_id_to_changed_tms, get_vehicles_details_by_ids


class APIClient:
    """Client for interacting with the AG API."""

    def __init__(self):
        """Initialize the API client."""
        pass

    def get_all_vehicles_id_to_changed_tms(self) -> dict:
        """
        Fetches all vehicles from the API with their IDs and changed_tms values.

        Returns:
            dict: Mapping of vehicle IDs to their changed_tms values
        """
        return get_all_vehicles_id_to_changed_tms()

    def get_vehicles_details_by_ids(self, vehicle_ids: list[int]):
        """
        Fetches full details for a list of vehicle IDs from the API.

        Args:
            vehicle_ids: List of vehicle IDs to fetch

        Returns:
            list: List of Vehicle objects with full details
        """
        return get_vehicles_details_by_ids(vehicle_ids)

