from model.vehicle import Vehicle


class ComparisonResult:
    """Holds the results of a vehicle comparison between API and sheet data."""
    def __init__(self, to_update: list[Vehicle], to_create: list[Vehicle], to_delete: list[Vehicle]):
        self.to_update = to_update
        self.to_create = to_create
        self.to_delete = to_delete


def create_lightweight_vehicle(vehicle_id: int, changed_tms) -> Vehicle:
    """Creates a Vehicle object with only id and changed_tms populated."""
    return Vehicle(
        vehicle_id=vehicle_id,
        changed_tms=changed_tms,
        title=None,
        created_tms=None,
        year=None,
        first_registration_tms_B=None,
        carmaker=None,
        model=None,
        energy=None,
        motorisation=None,
        transmission=None,
        finishing=None,
        color=None,
        doors=None,
        seats=None,
        power=None,
        co2=None,
        critair=None,
        drive_mode=None,
        mileage=None,
        body_j2=None,
        price=None,
        equipments=[],
        photos=[]
    )


def compare_vehicles(api_id_to_changed_tms: dict, sheet_id_to_changed_tms: dict) -> ComparisonResult:
    """
    Compares API vehicle data with sheet data and returns a ComparisonResult.

    Args:
        api_id_to_changed_tms: Dict mapping vehicle IDs to their changed_tms values from API
        sheet_id_to_changed_tms: Dict mapping vehicle IDs to their changed_tms values from sheet

    Returns:
        ComparisonResult with three lists of Vehicle objects:
        - to_update: Vehicle objects that exist in both but have different changed_tms
        - to_create: Vehicle objects that are in API but not in sheet
        - to_delete: Vehicle objects that are in sheet but not in API
    """
    to_update = []
    to_create = []
    to_delete = []

    """
    Find updates and creates
    """
    for api_id, api_changed_tms in api_id_to_changed_tms.items():
        if api_id in sheet_id_to_changed_tms:
            """
            Both exist, check if changed_tms differs
            """
            api_tms_str = str(api_changed_tms).strip() if api_changed_tms is not None else ""
            sheet_tms_str = str(sheet_id_to_changed_tms[api_id]).strip() if sheet_id_to_changed_tms[
                                                                                api_id] is not None else ""

            if api_tms_str and sheet_tms_str and api_tms_str != sheet_tms_str:
                vehicle = create_lightweight_vehicle(api_id, api_changed_tms)
                to_update.append(vehicle)
        else:
            """
            ID only in API, needs to be created
            """
            vehicle = create_lightweight_vehicle(api_id, api_changed_tms)
            to_create.append(vehicle)

    """
    Find deletes
    """
    for sheet_id in sheet_id_to_changed_tms:
        if sheet_id not in api_id_to_changed_tms:
            vehicle = create_lightweight_vehicle(sheet_id, sheet_id_to_changed_tms[sheet_id])
            to_delete.append(vehicle)

    return ComparisonResult(to_update, to_create, to_delete)

