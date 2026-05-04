from integration.google_sheets import (
    get_sheet, read_sheet_id_to_changed_tms, batch_update_rows, batch_delete_rows,
    batch_create_rows, get_sheet_header, compact_sheet, validate_sheet_header
)
from integration.sheets_transformer import prepare_sheet_data, normalize_rows, vehicle_to_feed_dict


class SheetClient:
    """Client for interacting with Google Sheets."""

    def __init__(self):
        """Initialize the Sheet client and connect to the sheet."""
        self.sheet = get_sheet()

    def get_id_to_changed_tms(self) -> dict:
        """
        Reads all vehicle IDs and their changed_tms values from the sheet.

        Returns:
            dict: Mapping of vehicle IDs to their changed_tms values
        """
        return read_sheet_id_to_changed_tms(self.sheet)

    def get_header(self) -> list[str]:
        """
        Retrieves the header row from the sheet.

        Returns:
            list: List of column header names
        """
        return get_sheet_header(self.sheet)

    def update_rows(self, vehicles):
        """
        Updates rows in the sheet with new vehicle data.

        Args:
            vehicles: List of Vehicle objects with updated data
        """
        header = self.get_header()
        batch_update_rows(self.sheet, header, vehicles)

    def delete_rows(self, vehicle_ids: list[int]):
        """
        Deletes rows from the sheet for the given vehicle IDs.

        Args:
            vehicle_ids: List of vehicle IDs to delete
        """
        batch_delete_rows(self.sheet, vehicle_ids)

    def create_rows(self, vehicles):
        """
        Creates new rows in the sheet for the given vehicles.

        Args:
            vehicles: List of Vehicle objects to create
        """
        header = self.get_header()
        if header:
            validate_sheet_header(header)
            rows = normalize_rows([vehicle_to_feed_dict(v) for v in vehicles], header)
        else:
            header, rows = prepare_sheet_data(vehicles)

        batch_create_rows(self.sheet, rows, header)

    def compact(self):
        """
        Compacts the sheet by removing empty rows after deletion.
        """
        header = self.get_header()
        compact_sheet(self.sheet, header)
