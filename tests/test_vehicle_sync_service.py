import unittest

from service.vehicle_sync_service import VehicleSyncService


class FakeAPIClient:
    def __init__(self, id_to_changed_tms, vehicles_by_id=None):
        self.id_to_changed_tms = id_to_changed_tms
        self.vehicles_by_id = vehicles_by_id or {}
        self.requested_detail_ids = []

    def get_all_vehicles_id_to_changed_tms(self):
        return self.id_to_changed_tms

    def get_vehicles_details_by_ids(self, vehicle_ids):
        self.requested_detail_ids.append(list(vehicle_ids))
        return [
            self.vehicles_by_id[vehicle_id]
            for vehicle_id in vehicle_ids
        ]


class FakeSheetClient:
    def __init__(self, id_to_changed_tms):
        self.id_to_changed_tms = id_to_changed_tms
        self.updated = []
        self.deleted = []
        self.created = []
        self.compacted = False

    def get_id_to_changed_tms(self):
        return self.id_to_changed_tms

    def update_rows(self, vehicles):
        self.updated.extend(vehicles)

    def delete_rows(self, vehicle_ids):
        self.deleted.extend(vehicle_ids)

    def create_rows(self, vehicles):
        self.created.extend(vehicles)

    def compact(self):
        self.compacted = True


class FakeStorageClient:
    def __init__(self):
        self.rewritten_payloads = []

    def rewrite_vehicles_json(self, vehicles):
        self.rewritten_payloads.append(vehicles)


class FakeVehicle:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id


class VehicleSyncServiceTests(unittest.TestCase):
    def test_reuses_updated_vehicle_when_rewriting_vehicle_json(self):
        first = FakeVehicle(1)
        second = FakeVehicle(2)
        api_client = FakeAPIClient(
            {1: "100", 2: "200"},
            {
                1: first,
                2: second,
            },
        )
        sheet_client = FakeSheetClient({1: "101", 2: "200"})
        storage_client = FakeStorageClient()

        VehicleSyncService(api_client, sheet_client, storage_client).sync()

        self.assertEqual(api_client.requested_detail_ids, [[1], [2]])
        self.assertEqual(sheet_client.updated, [first])
        self.assertEqual(storage_client.rewritten_payloads, [[first, second]])

    def test_reuses_created_vehicle_when_rewriting_vehicle_json(self):
        first = FakeVehicle(1)
        second = FakeVehicle(2)
        api_client = FakeAPIClient(
            {1: "100", 2: "200"},
            {
                1: first,
                2: second,
            },
        )
        sheet_client = FakeSheetClient({1: "100"})
        storage_client = FakeStorageClient()

        VehicleSyncService(api_client, sheet_client, storage_client).sync()

        self.assertEqual(api_client.requested_detail_ids, [[2], [1]])
        self.assertEqual(sheet_client.created, [second])
        self.assertEqual(storage_client.rewritten_payloads, [[first, second]])

    def test_does_not_rewrite_vehicle_json_when_nothing_changed(self):
        api_client = FakeAPIClient({1: "100"})
        sheet_client = FakeSheetClient({1: "100"})
        storage_client = FakeStorageClient()

        VehicleSyncService(api_client, sheet_client, storage_client).sync()

        self.assertEqual(api_client.requested_detail_ids, [])
        self.assertEqual(storage_client.rewritten_payloads, [])


if __name__ == "__main__":
    unittest.main()
