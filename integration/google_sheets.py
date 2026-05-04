import gspread
from google.auth import default
from secret_accessor import get_secret

REQUIRED_HEADER_COLUMNS = ("id", "changed_tms")


class InvalidSheetHeaderError(ValueError):
    """Raised when the target sheet is not empty and does not match the expected format."""


def get_sheet():
    """
    Initializes the Google Sheets client using service account credentials and returns the first sheet of the spreadsheet identified by SHEET_ID.

    The function uses the google-auth library to obtain credentials and gspread to interact with the Google Sheets API. It assumes that the necessary credentials are properly set up in the environment.

    When run on Google Cloud and all rights and services are correctly configured, authentification is automatic and the function should work without any additional setup.
    If running locally, ensure that the environment variables and credentials are correctly configured for authentication to succeed.
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    sheet_id = get_secret("SHEET_ID")
    creds, _ = default(scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1


def read_sheet_id_to_changed_tms(sheet):
    """
    Reads all data from the given sheet and returns a dictionary mapping vehicle IDs to their changed_tms values.

    Empty sheets are treated as having no existing vehicles. Non-empty sheets
    must contain the required managed header columns.
    """
    header = get_sheet_header(sheet)
    if not header:
        return {}
    validate_sheet_header(header)

    all_values = sheet.get_all_records()
    sheet_id_to_changed_tms = {
        int(record.get("id", "")): record.get("changed_tms", "")
        for record in all_values
        if record.get("id", "")
    }
    return sheet_id_to_changed_tms


def column_number_to_letter(col_num):
    """
    Converts a column number (1-based) to its letter representation (A, B, ..., Z, AA, AB, etc.)
    """
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(col_num % 26 + ord('A')) + result
        col_num //= 26
    return result


def batch_update_rows(sheet, header, vehicles_dict):
    """
    Performs batch update on the sheet for rows with vehicle IDs in the update_ids list.

    Fetches the row indices for each ID, then updates only those rows with the new data.
    """
    all_records = sheet.get_all_records()

    for vehicle in vehicles_dict:
        vehicle_id = vehicle.vehicle_id
        """
        Find the row index for this vehicle ID (add 2 because row 1 is header, row indexing starts at 1)
        """
        for idx, record in enumerate(all_records):
            try:
                record_id = int(record.get("id", ""))
                if record_id == vehicle_id:
                    row_index = idx + 2
                    """
                    Convert vehicle to row format using the header
                    """
                    from integration.sheets_transformer import vehicle_to_feed_dict
                    vehicle_dict = vehicle_to_feed_dict(vehicle)
                    row_values = [vehicle_dict.get(col, "") for col in header]
                    """
                    Use gspread update method with range notation
                    """
                    end_col = column_number_to_letter(len(header))
                    sheet.update(f"A{row_index}:{end_col}{row_index}", [row_values])
                    break
            except (ValueError, TypeError):
                """
                Skip records with invalid IDs
                """
                continue


def batch_delete_rows(sheet, delete_ids):
    """
    Deletes rows from the sheet that correspond to the vehicle IDs in the delete_ids list.
    """
    all_records = sheet.get_all_records()
    rows_to_delete = []

    """
    Find row indices to delete (iterate in reverse to maintain correct indices)
    """
    for vehicle_id in delete_ids:
        for idx, record in enumerate(all_records):
            try:
                record_id = int(record.get("id", ""))
                if record_id == vehicle_id:
                    """
                    +2 because header is row 1 and indexing starts at 1
                    """
                    row_index = idx + 2
                    rows_to_delete.append(row_index)
                    break
            except (ValueError, TypeError):
                """
                Skip records with invalid or empty IDs
                """
                continue

    """
    Delete rows in reverse order to maintain correct indices
    """
    for row_index in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(row_index)


def batch_create_rows(sheet, rows, header=None):
    """
    Appends new rows to the sheet with data for the vehicle IDs in the create_ids list.
    """
    current_header = get_sheet_header(sheet)
    if header and not current_header:
        sheet.append_rows([header] + rows)
        return

    validate_sheet_header(current_header)
    sheet.append_rows(rows)


def get_sheet_header(sheet):
    """
    Reads the header row directly from the sheet.
    """
    return sheet.row_values(1)


def validate_sheet_header(header):
    """
    Validates that a non-empty sheet has the minimum columns required by the sync.
    """
    normalized_header = {str(column).strip() for column in header if str(column).strip()}
    missing_columns = [
        column for column in REQUIRED_HEADER_COLUMNS
        if column not in normalized_header
    ]

    if missing_columns:
        raise InvalidSheetHeaderError(
            "Target Google Sheet is not empty and is missing required header "
            f"column(s): {', '.join(missing_columns)}. Use a completely empty "
            "sheet, or a sheet previously initialized by this pipeline."
        )


def compact_sheet(sheet, header):
    """
    Compacts the sheet after deletion by removing empty rows, ensuring all data rows follow each other without gaps.
    """
    all_records = sheet.get_all_records()

    if not all_records:
        """
        If no records left, just ensure header is there
        """
        sheet.clear()
        sheet.append_rows([header])
        return

    """
    Clear the sheet entirely
    """
    sheet.clear()

    """
    Rebuild: add header + all records as rows
    """
    rows = []
    for record in all_records:
        row_values = [record.get(col, "") for col in header]
        rows.append(row_values)

    """
    Write back header + all rows
    """
    sheet.append_rows([header] + rows)
