from datetime import datetime
from model.vehicle import Vehicle


def prepare_sheet_data(vehicles: list[Vehicle]):
    # 1. convert
    rows_dict = [vehicle_to_feed_dict(v) for v in vehicles]
    # 2. build header
    header = build_header(rows_dict)
    # 3. normalize
    rows = normalize_rows(rows_dict, header)
    # 4. final sheet payload
    return header, rows

## Builds the description case for the sheet, which is just a list of equipments.
def build_description(vehicle: Vehicle):
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
    data = {
        "id": vehicle.vehicle_id,
        "title": vehicle.title,
        "description": build_description(vehicle),
        "availability": "in stock",
        "condition": "used",
        "price": f"{vehicle.price} EUR" if vehicle.price else "",
        "image_link": vehicle.photos[0] if vehicle.photos else "",
        "link": f"https://garage-app-2b21b.web.app/react-detail/?id=Auto-Gestion%3A{vehicle.vehicle_id}&back=%2Fclient-v2.html%3Fscroll%3D0%26focus%3DAuto-Gestion%253A{vehicle.vehicle_id}",
    }

    # dynamic images
    for i, img in enumerate(vehicle.photos[1:], start=1):
        data[f"additional_image_link[{i}]"] = img

    # custom labels (still dynamic-safe)
    custom_labels = [
        vehicle.carmaker,
        vehicle.model,
        vehicle.energy,
        vehicle.transmission,
        vehicle.color,
    ]
    for i, val in enumerate(custom_labels):
        data[f"custom_label_{i}"] = val or ""

    # numeric custom fields
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
    header = set()
    for row in rows:
        header.update(row.keys())

    # optional: stable ordering (important for Sheets)
    preferred_order = [
        "id", "image_link", "description", "availability", "title",
        "price", "link", "condition"
    ]
    sorted_header = []

    # first: important fields
    for key in preferred_order:
        if key in header:
            sorted_header.append(key)

    # then: everything else alphabetically
    remaining = sorted(header - set(sorted_header))
    sorted_header.extend(remaining)

    return sorted_header

def normalize_rows(rows: list[dict], header: list[str]) -> list[list]:
    normalized = []
    for row in rows:
        normalized.append([row.get(col, "") for col in header])
    return normalized