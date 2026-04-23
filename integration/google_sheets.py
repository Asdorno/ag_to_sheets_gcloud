import gspread
from google.auth import default
from secret_accessor import get_secret

sheet_id = get_secret("SHEET_ID")


## Initializes the Google Sheets client using service account credentials and returns the first sheet of the spreadsheet identified by SHEET_ID.
## The function uses the google-auth library to obtain credentials and gspread to interact with the Google Sheets API. It assumes that the necessary credentials are properly set up in the environment.
## When run on Google Cloud and all rights and services are correctly configured, authentification is authomatic and the function should work without any additional setup.
## If running locally, ensure that the environment variables and credentials are correctly configured for authentication to succeed.
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds, _ = default(scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1


## Reads all data from the given sheet and returns a dictionary mapping vehicle IDs to their changed_tms values.
## The function assumes the sheet has "id" and "changed_tms" columns.
def read_sheet_id_to_changed_tms(sheet):
    all_values = sheet.get_all_records()
    sheet_id_to_changed_tms = {
        int(record.get("id", "")): record.get("changed_tms", "")
        for record in all_values
        if record.get("id", "")
    }
    return sheet_id_to_changed_tms


## Converts a column number (1-based) to its letter representation (A, B, ..., Z, AA, AB, etc.)
def column_number_to_letter(col_num):
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(col_num % 26 + ord('A')) + result
        col_num //= 26
    return result


## Performs batch update on the sheet for rows with vehicle IDs in the update_ids list.
## Fetches the row indices for each ID, then updates only those rows with the new data.
def batch_update_rows(sheet, header, vehicles_dict):
    all_records = sheet.get_all_records()

    for vehicle in vehicles_dict:
        vehicle_id = vehicle.vehicle_id
        # Find the row index for this vehicle ID (add 2 because row 1 is header, row indexing starts at 1)
        for idx, record in enumerate(all_records):
            try:
                record_id = int(record.get("id", ""))
                if record_id == vehicle_id:
                    row_index = idx + 2
                    # Convert vehicle to row format using the header
                    from integration.sheets_transformer import vehicle_to_feed_dict
                    vehicle_dict = vehicle_to_feed_dict(vehicle)
                    row_values = [vehicle_dict.get(col, "") for col in header]
                    # Use gspread update method with range notation
                    end_col = column_number_to_letter(len(header))
                    sheet.update(f"A{row_index}:{end_col}{row_index}", [row_values])
                    break
            except (ValueError, TypeError):
                # Skip records with invalid IDs
                continue


## Deletes rows from the sheet that correspond to the vehicle IDs in the delete_ids list.
def batch_delete_rows(sheet, delete_ids):
    all_records = sheet.get_all_records()
    rows_to_delete = []

    # Find row indices to delete (iterate in reverse to maintain correct indices)
    for vehicle_id in delete_ids:
        for idx, record in enumerate(all_records):
            try:
                record_id = int(record.get("id", ""))
                if record_id == vehicle_id:
                    row_index = idx + 2  # +2 because header is row 1 and indexing starts at 1
                    rows_to_delete.append(row_index)
                    break
            except (ValueError, TypeError):
                # Skip records with invalid or empty IDs
                continue

    # Delete rows in reverse order to maintain correct indices
    for row_index in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(row_index)


## Appends new rows to the sheet with data for the vehicle IDs in the create_ids list.
def batch_create_rows(sheet, rows):
    # Append all new rows at once
    sheet.append_rows(rows)


## Reads the header row directly from the sheet.
def get_sheet_header(sheet):
    return sheet.row_values(1)


## Compacts the sheet after deletion by removing empty rows, ensuring all data rows follow each other without gaps.
def compact_sheet(sheet, header):
    all_records = sheet.get_all_records()

    if not all_records:
        # If no records left, just ensure header is there
        sheet.clear()
        sheet.append_rows([header])
        return

    # Clear the sheet entirely
    sheet.clear()

    # Rebuild: add header + all records as rows
    from integration.sheets_transformer import vehicle_to_feed_dict
    rows = []
    for record in all_records:
        row_values = [record.get(col, "") for col in header]
        rows.append(row_values)

    # Write back header + all rows
    sheet.append_rows([header] + rows)
