import gspread
import os
from dotenv import load_dotenv
from google.auth import default

load_dotenv()
sheet_name = os.getenv("SHEET_NAME")
sheet_id = os.getenv("SHEET_ID")


def write_to_sheet(sheet, header, rows):
    values = [header] + rows
    sheet.clear()
    sheet.update(values)

def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds, _ = default(scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1
