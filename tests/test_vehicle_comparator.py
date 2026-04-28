import unittest

from service.vehicle_comparator import compare_vehicles, create_lightweight_vehicle


class VehicleComparatorTests(unittest.TestCase):
    def test_create_lightweight_vehicle_sets_only_minimal_payload(self):
        vehicle = create_lightweight_vehicle(10, "123")

        self.assertEqual(vehicle.vehicle_id, 10)
        self.assertEqual(vehicle.changed_tms, 123)
        self.assertIsNone(vehicle.title)
        self.assertEqual(vehicle.equipments, [])
        self.assertEqual(vehicle.photos, [])

    def test_compare_vehicles_returns_updates_creates_and_deletes(self):
        api = {
            1: "100",
            2: "200",
            3: "300",
        }
        sheet = {
            1: "100",
            2: " 201 ",
            4: "400",
        }

        result = compare_vehicles(api, sheet)

        self.assertEqual([v.vehicle_id for v in result.to_update], [2])
        self.assertEqual([v.vehicle_id for v in result.to_create], [3])
        self.assertEqual([v.vehicle_id for v in result.to_delete], [4])

    def test_compare_vehicles_ignores_equal_timestamps_with_whitespace(self):
        api = {1: " 100 "}
        sheet = {1: "100"}

        result = compare_vehicles(api, sheet)

        self.assertEqual(result.to_update, [])
        self.assertEqual(result.to_create, [])
        self.assertEqual(result.to_delete, [])

    def test_compare_vehicles_does_not_mark_update_when_timestamp_missing(self):
        api = {1: None}
        sheet = {1: "100"}

        result = compare_vehicles(api, sheet)

        self.assertEqual(result.to_update, [])


if __name__ == "__main__":
    unittest.main()
