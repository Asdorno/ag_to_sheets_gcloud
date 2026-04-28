from model.vehicle import Vehicle
import xml.etree.ElementTree as ET


def parse_all_ag_vehicles_id(all_ag_vehicles_xml: str):
    """
    Parses the XML response from the AG API to extract a list of vehicle IDs.
    """
    try:
        root = ET.fromstring(all_ag_vehicles_xml.strip())
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    vehicle_ids = [
        item.findtext("vehicle_id")
        for item in root.findall("item")
    ]
    return vehicle_ids


def parse_all_ag_vehicles_id_to_changed_tms(all_ag_vehicles_xml: str):
    """
    Parses the XML response from the AG API to extract a dictionary mapping vehicle IDs to their last-changed timestamps.
    """
    try:
        root = ET.fromstring(all_ag_vehicles_xml.strip())
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    id_to_changed_tms = {
        int(item.findtext("vehicle_id")): item.findtext("changed")
        for item in root.findall("item")
        if item.findtext("vehicle_id")
    }
    return id_to_changed_tms


def parse_ag_vehicle_details(xml: str) -> Vehicle:
    """
    Parses the XML response from the AG API for a single vehicle's details and converts it into a Vehicle object.
    """
    try:
        root = ET.fromstring(xml.strip())
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    raw_dict = xml_to_dict(root)
    normalized = extract_special_fields(raw_dict)
    return Vehicle.model_validate(normalized)


def xml_to_dict(element: ET.Element):
    """
    Makes a dict out of XML, handling both text and nested elements.

    Converts repeated tags into lists.
    """
    children = list(element)
    if not children:
        return element.text.strip() if element.text else None
    result = {}
    for child in children:
        value = xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(value)
        else:
            result[child.tag] = value
    return result


def extract_special_fields(data: dict) -> dict:
    """
    Extracts specific fields from the raw dict that are nested under "siv" and "ad".

    Promotes them to top-level keys for easier access in the Vehicle model.
    """
    """
    flatten nested values you actually care about
    """
    siv = data.get("siv") or {}
    ad = data.get("ad") or {}

    data["first_registration_tms_B"] = siv.get("first_registration_tms_B")
    data["body_j2"] = siv.get("body_J2")
    data["price"] = ad.get("price")
    return data
