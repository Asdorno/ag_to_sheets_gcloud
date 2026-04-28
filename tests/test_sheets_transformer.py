import unittest

from integration.sheets_transformer import (
    build_description,
    build_header,
    normalize_rows,
    prepare_sheet_data,
    vehicle_to_feed_dict,
)
from model.vehicle import Vehicle


def make_vehicle(**overrides):
    data = {
        "vehicle_id": 10,
        "title": "Renault Clio",
        "created_tms": 100,
        "changed_tms": 200,
        "year": 2021,
        "first_registration_tms_B": 1704067200,
        "carmaker": "Renault",
        "model": "Clio",
        "energy": "Essence",
        "motorisation": "1.0 TCe",
        "transmission": "Manual",
        "finishing": "Techno",
        "color": "Blue",
        "doors": 5,
        "seats": 5,
        "power": 90,
        "co2": 99.5,
        "critair": 1,
        "drive_mode": "FWD",
        "mileage": 42000,
        "body_j2": "Berline",
        "price": 15990.0,
        "equipments": ["GPS", "Camera"],
        "photos": ["a.jpg", "b.jpg", "c.jpg"],
    }
    data.update(overrides)
    return Vehicle(**data)


class SheetsTransformerTests(unittest.TestCase):
    def test_build_description_contains_core_vehicle_data(self):
        vehicle = make_vehicle()

        description = build_description(vehicle)

        self.assertIn("Marque: Renault", description)
        self.assertIn("Modèle: Clio", description)
        self.assertIn("1ère mise en circulation: 2024", description)
        self.assertIn("✅GPS", description)
        self.assertIn("✅Camera", description)

    def test_vehicle_to_feed_dict_maps_dynamic_fields(self):
        vehicle = make_vehicle()

        feed = vehicle_to_feed_dict(vehicle)

        self.assertEqual(feed["id"], 10)
        self.assertEqual(feed["changed_tms"], 200)
        self.assertEqual(feed["price"], "15990.0 EUR")
        self.assertEqual(feed["image_link"], "a.jpg")
        self.assertEqual(feed["additional_image_link[1]"], "b.jpg")
        self.assertEqual(feed["additional_image_link[2]"], "c.jpg")
        self.assertEqual(feed["custom_label_0"], "Renault")
        self.assertEqual(feed["custom_label_4"], "Blue")
        self.assertEqual(feed["custom_number_0"], 42000)
        self.assertEqual(feed["custom_number_3"], 99.5)

    def test_build_header_orders_preferred_and_dynamic_fields(self):
        rows = [
            {
                "custom_label_1": "Clio",
                "additional_image_link[2]": "c.jpg",
                "title": "Title",
                "price": "10 EUR",
                "id": 1,
                "changed_tms": 2,
                "condition": "used",
                "link": "url",
                "image_link": "a.jpg",
                "description": "desc",
                "availability": "in stock",
                "custom_number_0": 1000,
                "additional_image_link[1]": "b.jpg",
                "custom_label_0": "Renault",
                "zzz": "last",
            }
        ]

        header = build_header(rows)

        self.assertEqual(
            header[:9],
            [
                "id",
                "changed_tms",
                "image_link",
                "description",
                "availability",
                "title",
                "price",
                "link",
                "condition",
            ],
        )
        self.assertEqual(
            header[9:14],
            [
                "additional_image_link[1]",
                "additional_image_link[2]",
                "custom_label_0",
                "custom_label_1",
                "custom_number_0",
            ],
        )
        self.assertEqual(header[-1], "zzz")

    def test_normalize_rows_fills_missing_columns(self):
        rows = [{"id": 1, "title": "A"}, {"id": 2}]
        header = ["id", "title", "price"]

        normalized = normalize_rows(rows, header)

        self.assertEqual(
            normalized,
            [
                [1, "A", ""],
                [2, "", ""],
            ],
        )

    def test_prepare_sheet_data_returns_header_and_rows(self):
        first = make_vehicle()
        second = make_vehicle(
            vehicle_id=20,
            photos=["one.jpg"],
            color="Red",
            equipments=["Radar"],
        )

        header, rows = prepare_sheet_data([first, second])

        self.assertIn("id", header)
        self.assertIn("title", header)
        self.assertIn("additional_image_link[2]", header)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), len(header))
        self.assertEqual(len(rows[1]), len(header))


if __name__ == "__main__":
    unittest.main()
