import unittest
import xml.etree.ElementTree as ET

from parser.vehicle_parser import (
    extract_special_fields,
    parse_ag_vehicle_details,
    parse_all_ag_vehicles_id,
    parse_all_ag_vehicles_id_to_changed_tms,
    xml_to_dict,
)


class VehicleParserTests(unittest.TestCase):
    def test_parse_all_ag_vehicles_id(self):
        xml = """
        <root>
            <item><vehicle_id>101</vehicle_id></item>
            <item><vehicle_id>202</vehicle_id></item>
        </root>
        """

        self.assertEqual(parse_all_ag_vehicles_id(xml), ["101", "202"])

    def test_parse_all_ag_vehicles_id_to_changed_tms(self):
        xml = """
        <root>
            <item><vehicle_id>101</vehicle_id><changed>123</changed></item>
            <item><vehicle_id>202</vehicle_id><changed>456</changed></item>
        </root>
        """

        self.assertEqual(
            parse_all_ag_vehicles_id_to_changed_tms(xml),
            {101: "123", 202: "456"},
        )

    def test_invalid_xml_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_all_ag_vehicles_id("<root>")

    def test_xml_to_dict_preserves_repeated_tags_as_lists(self):
        root = ET.fromstring(
            """
            <vehicle>
                <vehicle_id>10</vehicle_id>
                <photos>
                    <item>a.jpg</item>
                    <item>b.jpg</item>
                </photos>
            </vehicle>
            """
        )

        self.assertEqual(
            xml_to_dict(root),
            {
                "vehicle_id": "10",
                "photos": {"item": ["a.jpg", "b.jpg"]},
            },
        )

    def test_extract_special_fields_promotes_nested_values(self):
        data = {
            "vehicle_id": "10",
            "siv": {
                "first_registration_tms_B": "1704067200",
                "body_J2": "SUV",
            },
            "ad": {
                "price": "19990",
            },
        }

        normalized = extract_special_fields(data)

        self.assertEqual(normalized["first_registration_tms_B"], "1704067200")
        self.assertEqual(normalized["body_j2"], "SUV")
        self.assertEqual(normalized["price"], "19990")

    def test_parse_ag_vehicle_details_builds_vehicle(self):
        xml = """
        <vehicle>
            <vehicle_id>10</vehicle_id>
            <title>Clio</title>
            <created_tms>101</created_tms>
            <changed_tms>111</changed_tms>
            <year>2021</year>
            <carmaker>Renault</carmaker>
            <model>Clio</model>
            <energy>Essence</energy>
            <motorisation>1.0 TCe</motorisation>
            <transmission>Manual</transmission>
            <finishing>Techno</finishing>
            <color>Blue</color>
            <doors>5</doors>
            <seats>5</seats>
            <power>90</power>
            <co2>99.5</co2>
            <critair>1</critair>
            <drive_mode>FWD</drive_mode>
            <mileage>42000</mileage>
            <equipments>
                <item>GPS</item>
                <item>Camera</item>
            </equipments>
            <photos>
                <item>a.jpg</item>
                <item>b.jpg</item>
            </photos>
            <siv>
                <first_registration_tms_B>1704067200</first_registration_tms_B>
                <body_J2>Berline</body_J2>
            </siv>
            <ad>
                <price>15990</price>
            </ad>
        </vehicle>
        """

        vehicle = parse_ag_vehicle_details(xml)

        self.assertEqual(vehicle.vehicle_id, 10)
        self.assertEqual(vehicle.title, "Clio")
        self.assertEqual(vehicle.changed_tms, 111)
        self.assertEqual(vehicle.year, 2021)
        self.assertEqual(vehicle.equipments, ["GPS", "Camera"])
        self.assertEqual(vehicle.photos, ["a.jpg", "b.jpg"])
        self.assertEqual(vehicle.body_j2, "Berline")
        self.assertEqual(vehicle.price, 15990.0)


if __name__ == "__main__":
    unittest.main()
