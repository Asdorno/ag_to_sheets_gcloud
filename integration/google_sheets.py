import gspread
from google.auth import default
from secret_accessor import get_secret

sheet_id = get_secret("SHEET_ID")

## Writes the provided header and rows to the given Google Sheets sheet. The function first combines the header and rows into a single list of values, then clears the existing content of the sheet before updating it with the new values. This ensures that the sheet is refreshed with the latest data each time this function is called.
def write_to_sheet(sheet, header, rows):
    values = [header] + rows
    sheet.clear()
    sheet.update(values)

## Initializes the Google Sheets client using service account credentials and returns the first sheet of the spreadsheet identified by SHEET_ID.
## The function uses the google-auth library to obtain credentials and gspread to interact with the Google Sheets API. It assumes that the necessary credentials are properly set up in the environment.
## When run on Google Cloud and all rights and services are correctly configured, authentification is authomatic and the function should work without any additional setup.
## If running locally, ensure that the environment variables and credentials are correctly configured for authentication to succeed.
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds, _ = default(scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1
