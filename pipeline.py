from integration.google_sheets import get_sheet, read_sheet_id_to_changed_tms, batch_update_rows, batch_delete_rows, \
    batch_create_rows, get_sheet_header, compact_sheet
from service.vehicle_service import get_all_vehicles_id_to_changed_tms, compare_id_to_changed_tms, \
    get_vehicles_details_by_ids


def main():
    sheet = get_sheet()

    # Get API data
    api_id_to_changed_tms = get_all_vehicles_id_to_changed_tms()
    # Get sheet data
    sheet_id_to_changed_tms = read_sheet_id_to_changed_tms(sheet)

    # Compare
    to_update, to_create, to_delete = compare_id_to_changed_tms(api_id_to_changed_tms, sheet_id_to_changed_tms)

    print(f"To update: {to_update}")
    print(f"To create: {to_create}")
    print(f"To delete: {to_delete}")

    # Get header from the sheet
    header = get_sheet_header(sheet)

    # 1. Update affected rows
    if to_update:
        print(f"Updating {len(to_update)} vehicles...")
        update_vehicles = get_vehicles_details_by_ids(to_update)
        batch_update_rows(sheet, header, update_vehicles)

    # 2. Delete affected rows
    if to_delete:
        print(f"Deleting {len(to_delete)} vehicles...")
        batch_delete_rows(sheet, to_delete)
        # Compact sheet to remove gaps after deletion
        compact_sheet(sheet, header)

    # 3. Create new rows
    if to_create:
        print(f"Creating {len(to_create)} vehicles...")
        create_vehicles = get_vehicles_details_by_ids(to_create)
        _, create_rows = prepare_sheet_data(create_vehicles)
        batch_create_rows(sheet, create_rows)

    print("Pipeline completed!")


if __name__ == '__main__':
    main()
