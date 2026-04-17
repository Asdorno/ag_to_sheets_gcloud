from model.vehicle import Vehicle
from api.ag_api import get_ag_vehicle_details, get_all_ag_vehicles_xml
from parser.vehicle_parser import parse_all_ag_vehicles_id, parse_ag_vehicle_details

def get_vehicle(vehicle_id: int) -> Vehicle:
    xml = get_ag_vehicle_details(vehicle_id)
    return parse_ag_vehicle_details(xml)


def get_all_vehicles_ids():
    xml = get_all_ag_vehicles_xml()
    return parse_all_ag_vehicles_id(xml)


def get_all_vehicles_details():
    vehicles:list[Vehicle] = []
    vehicle_ids = get_all_vehicles_ids()

    for vehicle_id in vehicle_ids:
        vehicles.append(get_vehicle(vehicle_id))
    return vehicles