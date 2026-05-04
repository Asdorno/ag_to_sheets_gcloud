import unittest

from integration.google_sheets import (
    InvalidSheetHeaderError,
    batch_create_rows,
    read_sheet_id_to_changed_tms,
)


class FakeSheet:
    def __init__(self, header=None, records=None):
        self.header = header or []
        self.records = records or []
        self.appended_rows = []

    def row_values(self, row_number):
        if row_number == 1:
            return self.header
        return []

    def get_all_records(self):
        return self.records

    def append_rows(self, rows):
        self.appended_rows.extend(rows)


class GoogleSheetsTests(unittest.TestCase):
    def test_read_sheet_id_to_changed_tms_returns_empty_dict_for_empty_sheet(self):
        sheet = FakeSheet()

        result = read_sheet_id_to_changed_tms(sheet)

        self.assertEqual(result, {})

    def test_read_sheet_id_to_changed_tms_reads_existing_records(self):
        sheet = FakeSheet(
            header=["id", "changed_tms"],
            records=[
                {"id": "10", "changed_tms": "100"},
                {"id": "20", "changed_tms": "200"},
            ],
        )

        result = read_sheet_id_to_changed_tms(sheet)

        self.assertEqual(result, {10: "100", 20: "200"})

    def test_read_sheet_id_to_changed_tms_rejects_non_empty_sheet_without_required_header(self):
        sheet = FakeSheet(header=["vehicle", "updated_at"])

        with self.assertRaisesRegex(InvalidSheetHeaderError, "missing required header"):
            read_sheet_id_to_changed_tms(sheet)

    def test_batch_create_rows_adds_header_when_sheet_is_empty(self):
        sheet = FakeSheet()

        batch_create_rows(
            sheet,
            rows=[[10, "100", "Renault Clio"]],
            header=["id", "changed_tms", "title"],
        )

        self.assertEqual(
            sheet.appended_rows,
            [
                ["id", "changed_tms", "title"],
                [10, "100", "Renault Clio"],
            ],
        )

    def test_batch_create_rows_does_not_add_header_when_sheet_already_has_one(self):
        sheet = FakeSheet(header=["id", "changed_tms", "title"])

        batch_create_rows(
            sheet,
            rows=[[10, "100", "Renault Clio"]],
            header=["id", "changed_tms", "title"],
        )

        self.assertEqual(sheet.appended_rows, [[10, "100", "Renault Clio"]])

    def test_batch_create_rows_rejects_non_empty_sheet_without_required_header(self):
        sheet = FakeSheet(header=["vehicle", "updated_at"])

        with self.assertRaisesRegex(InvalidSheetHeaderError, "missing required header"):
            batch_create_rows(
                sheet,
                rows=[[10, "100", "Renault Clio"]],
                header=["id", "changed_tms", "title"],
            )

        self.assertEqual(sheet.appended_rows, [])


if __name__ == "__main__":
    unittest.main()
