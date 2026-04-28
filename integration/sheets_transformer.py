from datetime import datetime
from model.vehicle import Vehicle


## Transforms a list of Vehicle objects into a header and rows format suitable for Google Sheets, by converting each vehicle to a dict, building a comprehensive header, and normalizing the rows to match the header structure.
def prepare_sheet_data(vehicles: list[Vehicle]):
    """
    Transforms a list of Vehicle objects into a header and rows format suitable for Google Sheets.

    Converts each vehicle to a dict, builds a comprehensive header, and normalizes the rows to match the header structure.
    """
    """
    1. convert
    """
    rows_dict = [vehicle_to_feed_dict(v) for v in vehicles]
    """
    2. build header
    """
    header = build_header(rows_dict)
    """
    3. normalize
    """
    rows = normalize_rows(rows_dict, header)
    """
    4. final sheet payload
    """
    return header, rows


def build_description(vehicle: Vehicle):
    """
    Builds the description case for the sheet, which is just a list of equipments.
    """
    description = (f"🚗 Marque: {vehicle.carmaker}\n"
                   f"🚙 Modèle: {vehicle.model}\n"
                   f"✨ Version: {vehicle.finishing}\n"
                   f"📅 1ère mise en circulation: {datetime.fromtimestamp(vehicle.first_registration_tms_B).year}\n"
                   f"🛣️ Kilométrage: {vehicle.mileage}\n"
                   f"⛽ Carburant: {vehicle.energy}\n"
                   f"⚙️ Boîte: {vehicle.transmission}\n"
                   f"🌿 CO2: {vehicle.co2}\n"
                   f"⚡ Puissance: {vehicle.power}\n"
                   f"🚪 Nombre de portes: {vehicle.doors}\n"
                   f"👥 Nombre de places:  {vehicle.seats}\n"
                   f"🔵 Couleur:  {vehicle.color}\n"
                   f"🚘 Carrosserie: {vehicle.body_j2}\n\n"
                   f"🔧 Options:\n")

    for equip in vehicle.equipments:
        description += f"✅{equip}\n"

    return description


def vehicle_to_feed_dict(vehicle: Vehicle) -> dict:
    """
    Converts a Vehicle object into a dict format that matches the expected fields for the Google Sheets feed.

    Includes dynamic handling of additional images and custom labels/numbers based on the vehicle's attributes.
    """
    data = {
        "id": vehicle.vehicle_id,
        "changed_tms": vehicle.changed_tms,
        "title": vehicle.title,
        "description": build_description(vehicle),
        "availability": "in stock",
        "condition": "used",
        "price": f"{vehicle.price} EUR" if vehicle.price else "",
        "image_link": vehicle.photos[0] if vehicle.photos else "",
        "link": f"https://garage-app-2b21b.web.app/react-detail/?id=Auto-Gestion%3A{vehicle.vehicle_id}&back=%2Fclient-v2.html%3Fscroll%3D0%26focus%3DAuto-Gestion%253A{vehicle.vehicle_id}",
    }

    """
    dynamic images
    """
    for i, img in enumerate(vehicle.photos[1:], start=1):
        data[f"additional_image_link[{i}]"] = img

    """
    custom labels (still dynamic-safe)
    """
    custom_labels = [
        vehicle.carmaker,
        vehicle.model,
        vehicle.energy,
        vehicle.transmission,
        vehicle.color,
    ]
    for i, val in enumerate(custom_labels):
        data[f"custom_label_{i}"] = val or ""

    """
    numeric custom fields
    """
    custom_numbers = [
        vehicle.mileage,
        vehicle.power,
        vehicle.year,
        vehicle.co2,
    ]
    for i, val in enumerate(custom_numbers):
        data[f"custom_number_{i}"] = val or ""

    return data


def build_header(rows: list[dict]) -> list[str]:
    """
    Builds a comprehensive header for the Google Sheets feed by collecting all unique keys from the list of row dicts.

    Optionally orders important fields first followed by the rest alphabetically to ensure a consistent structure in the sheet.
    """
    header = set()
    for row in rows:
        header.update(row.keys())

    """
    optional: stable ordering (important for Sheets)
    """
    preferred_order = [
        "id", "changed_tms", "image_link", "description", "availability", "title",
        "price", "link", "condition"
    ]
    sorted_header = []

    """
    first: important fields
    """
    for key in preferred_order:
        if key in header:
            sorted_header.append(key)

    """
    Separate remaining fields by category for proper ordering
    """
    additional_images = []
    custom_labels = []
    custom_numbers = []
    other_fields = []

    remaining = header - set(sorted_header)
    for field in remaining:
        if field.startswith("additional_image_link"):
            additional_images.append(field)
        elif field.startswith("custom_label_"):
            custom_labels.append(field)
        elif field.startswith("custom_number_"):
            custom_numbers.append(field)
        else:
            other_fields.append(field)

    """
    Add fields in order: additional images, custom labels, custom numbers, then everything else
    """
    sorted_header.extend(sorted(additional_images))
    sorted_header.extend(sorted(custom_labels))
    sorted_header.extend(sorted(custom_numbers))
    sorted_header.extend(sorted(other_fields))

    return sorted_header


def normalize_rows(rows: list[dict], header: list[str]) -> list[list]:
    """
    Normalizes the rows of data to match the header structure by ensuring that each row dict has values for all header columns.

    Fills in missing keys with empty strings. This creates a consistent 2D list format where each sublist corresponds to a row of values in the same order as the header, which is essential for correctly populating the Google Sheets feed.
    """
    normalized = []
    for row in rows:
        normalized.append([row.get(col, "") for col in header])
    return normalized
