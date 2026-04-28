import unittest

from model.vehicle import Vehicle


def make_vehicle(**overrides):
    data = {
        "vehicle_id": 1,
        "title": None,
        "created_tms": None,
        "changed_tms": None,
        "year": None,
        "first_registration_tms_B": None,
        "carmaker": None,
        "model": None,
        "energy": None,
        "motorisation": None,
        "transmission": None,
        "finishing": None,
        "color": None,
        "doors": None,
        "seats": None,
        "power": None,
        "co2": None,
        "critair": None,
        "drive_mode": None,
        "mileage": None,
        "body_j2": None,
        "price": None,
        "equipments": [],
        "photos": [],
    }
    data.update(overrides)
    return Vehicle(**data)


class VehicleModelTests(unittest.TestCase):
    def test_empty_strings_are_normalized_to_none(self):
        vehicle = make_vehicle(
            title="",
            created_tms="",
            changed_tms="",
            year="",
            first_registration_tms_B="",
            carmaker="",
            model="",
            energy="",
            motorisation="",
            transmission="",
            finishing="",
            color="",
            doors="",
            seats="",
            power="",
            co2="",
            critair="",
            drive_mode="",
            mileage="",
            body_j2="",
            price="",
        )

        self.assertIsNone(vehicle.title)
        self.assertIsNone(vehicle.changed_tms)
        self.assertIsNone(vehicle.year)
        self.assertIsNone(vehicle.price)

    def test_equipments_accepts_dict_string_and_list(self):
        from_dict = make_vehicle(
            equipments={"item": ["gps", "camera"]},
        )
        from_string = make_vehicle(
            vehicle_id=2,
            equipments="gps",
        )
        from_list = make_vehicle(
            vehicle_id=3,
            equipments=["gps", "camera"],
        )

        self.assertEqual(from_dict.equipments, ["gps", "camera"])
        self.assertEqual(from_string.equipments, ["gps"])
        self.assertEqual(from_list.equipments, ["gps", "camera"])

    def test_photos_accepts_dict_string_and_list(self):
        from_dict = make_vehicle(
            photos={"item": ["a.jpg", "b.jpg"]},
        )
        from_string = make_vehicle(
            vehicle_id=2,
            photos="a.jpg",
        )
        from_list = make_vehicle(
            vehicle_id=3,
            photos=["a.jpg", "b.jpg"],
        )

        self.assertEqual(from_dict.photos, ["a.jpg", "b.jpg"])
        self.assertEqual(from_string.photos, ["a.jpg"])
        self.assertEqual(from_list.photos, ["a.jpg", "b.jpg"])


if __name__ == "__main__":
    unittest.main()
