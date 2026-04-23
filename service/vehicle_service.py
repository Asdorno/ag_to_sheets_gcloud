from model.vehicle import Vehicle
from api.ag_api import get_ag_vehicle_details, get_all_ag_vehicles_xml
from parser.vehicle_parser import parse_ag_vehicle_details, parse_all_ag_vehicles_id_to_changed_tms


## Returns a Vehicle object with all details for a specific vehicle ID by fetching the XML from the AG API and parsing it.
def get_vehicle(vehicle_id: int) -> Vehicle:
    xml = get_ag_vehicle_details(vehicle_id)
    return parse_ag_vehicle_details(xml)


def get_all_vehicles_id_to_changed_tms():
    xml = get_all_ag_vehicles_xml()
    return parse_all_ag_vehicles_id_to_changed_tms(xml)


def get_vehicles_details_by_ids(vehicle_ids: list[int]):
    vehicles: list[Vehicle] = []
    for vehicle_id in vehicle_ids:
        vehicles.append(get_vehicle(vehicle_id))
    return vehicles


## Compares the API vehicle data with the sheet data and returns three lists:
## - to_update: vehicle IDs that exist in both but have different changed_tms values
## - to_create: vehicle IDs that are in the API but not in the sheet
## - to_delete: vehicle IDs that are in the sheet but not in the API
def compare_id_to_changed_tms(api_id_to_changed_tms: dict, sheet_id_to_changed_tms: dict):
    to_update = []
    to_create = []
    to_delete = []

    # Find updates and creates
    for api_id, api_changed_tms in api_id_to_changed_tms.items():
        if api_id in sheet_id_to_changed_tms:
            # Both exist, check if changed_tms differs
            api_tms_str = str(api_changed_tms).strip() if api_changed_tms is not None else ""
            sheet_tms_str = str(sheet_id_to_changed_tms[api_id]).strip() if sheet_id_to_changed_tms[
                                                                                api_id] is not None else ""

            if api_tms_str and sheet_tms_str and api_tms_str != sheet_tms_str:
                to_update.append(api_id)
        else:
            # ID only in API, needs to be created
            to_create.append(api_id)

    # Find deletes
    for sheet_id in sheet_id_to_changed_tms:
        if sheet_id not in api_id_to_changed_tms:
            to_delete.append(sheet_id)

    return to_update, to_create, to_delete
