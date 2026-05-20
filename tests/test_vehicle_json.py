import json
import unittest

from model.vehicle import Vehicle
from storage.gcs_uploader import vehicles_to_json


class VehicleJsonTests(unittest.TestCase):
    def test_vehicles_to_json_serializes_vehicle_model_fields(self):
        vehicle = Vehicle(
            vehicle_id=10,
            title="Renault Clio",
            created_tms=100,
            changed_tms=200,
            year=2021,
            first_registration_tms_B=1704067200,
            carmaker="Renault",
            model="Clio",
            energy="Essence",
            motorisation="1.0 TCe",
            transmission="Manual",
            finishing="Techno",
            color="Blue",
            doors=5,
            seats=5,
            power=90,
            co2=99.5,
            critair=1,
            drive_mode="FWD",
            mileage=42000,
            body_j2="Berline",
            price=15990.0,
            equipments=["GPS"],
            photos=["a.jpg"],
        )

        payload = json.loads(vehicles_to_json([vehicle]))

        self.assertEqual(payload[0]["vehicle_id"], 10)
        self.assertEqual(payload[0]["title"], "Renault Clio")
        self.assertEqual(payload[0]["equipments"], ["GPS"])
        self.assertEqual(payload[0]["photos"], ["a.jpg"])
