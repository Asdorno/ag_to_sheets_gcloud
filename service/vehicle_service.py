from model.vehicle import Vehicle
from api.ag_api import get_ag_vehicle_details, get_all_ag_vehicles_xml
from parser.vehicle_parser import parse_all_ag_vehicles_id, parse_ag_vehicle_details


## Returns a Vehicle object with all details for a specific vehicle ID by fetching the XML from the AG API and parsing it.
def get_vehicle(vehicle_id: int) -> Vehicle:
    xml = get_ag_vehicle_details(vehicle_id)
    return parse_ag_vehicle_details(xml)


## Returns a list of all vehicles id's by fetching the XML from the AG API and parsing it to extract the IDs.
def get_all_vehicles_ids():
    xml = get_all_ag_vehicles_xml()
    return parse_all_ag_vehicles_id(xml)


## Returns a list of all vehicles with their details by first fetching all vehicle IDs and then fetching details for each ID.
## To use for transforming the entire dataset for Google Sheets export.
def get_all_vehicles_details():
    vehicles: list[Vehicle] = []
    vehicle_ids = get_all_vehicles_ids()

    for vehicle_id in vehicle_ids:
        vehicles.append(get_vehicle(vehicle_id))
    return vehicles
