from integration.google_sheets import get_sheet, write_to_sheet
from integration.sheets_transformer import prepare_sheet_data
from service.vehicle_service import get_all_vehicles_details


def main():
    sheet = get_sheet()
    vehicles = get_all_vehicles_details()
    header, rows = prepare_sheet_data(vehicles)
    write_to_sheet(sheet, header, rows)


if __name__ == '__main__':
    main()
