from model.vehicle import Vehicle
from api.ag_api import get_ag_vehicle_details, get_all_ag_vehicles_xml
from parser.vehicle_parser import parse_ag_vehicle_details, parse_all_ag_vehicles_id_to_changed_tms


def get_vehicle(vehicle_id: int) -> Vehicle:
    """
    Returns a Vehicle object with all details for a specific vehicle ID.

    Fetches the XML from the AG API and parses it.
    """
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

