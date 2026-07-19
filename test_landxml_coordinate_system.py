from __future__ import annotations

import html
import unittest

from pyproj import CRS

import super_landxml


def _landxml(coordinate_system: str = "") -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2" version="1.2">
  <Units><Imperial linearUnit="USSurveyFoot" /></Units>
  {coordinate_system}
  <Alignments>
    <Alignment name="Test" length="100" staStart="0">
      <CoordGeom>
        <Line length="100"><Start>1000 2000 0</Start><End>1100 2000 0</End></Line>
      </CoordGeom>
    </Alignment>
  </Alignments>
</LandXML>
"""


class LandXMLCoordinateSystemTests(unittest.TestCase):
    def test_explicit_epsg_code_is_recognized(self):
        data = super_landxml.parse_landxml_text(
            _landxml(
                '<CoordinateSystem epsgCode="6576" horizontalDatum="NAD83(2011)" '
                'horizontalCoordinateSystemName="TN83/2011F" />'
            )
        )

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "recognized")
        self.assertEqual(summary["authority"], "EPSG")
        self.assertEqual(summary["code"], "6576")
        self.assertEqual(summary["detection_source"], "epsgCode")
        self.assertIn("Tennessee", summary["display_name"])
        self.assertEqual(data.warnings, [])

    def test_tdot_map_zone_name_is_recognized_without_epsg_attribute(self):
        data = super_landxml.parse_landxml_text(
            _landxml('<CoordinateSystem horizontalCoordinateSystemName="TN83/2011F" />')
        )

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "recognized")
        self.assertEqual(summary["code"], "6576")
        self.assertEqual(summary["detection_source"], "horizontalCoordinateSystemName")

    def test_wkt_is_recognized_and_resolved_to_authority(self):
        wkt = html.escape(CRS.from_epsg(2274).to_wkt(), quote=True)
        data = super_landxml.parse_landxml_text(_landxml(f'<CoordinateSystem ogcWktCode="{wkt}" />'))

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "recognized")
        self.assertEqual(summary["authority"], "EPSG")
        self.assertEqual(summary["code"], "2274")
        self.assertEqual(summary["detection_source"], "ogcWktCode")

    def test_missing_coordinate_system_is_reported_without_inference(self):
        data = super_landxml.parse_landxml_text(_landxml())

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "missing")
        self.assertEqual(summary["display_name"], "Not declared in LandXML")
        self.assertTrue(summary["preserve_xy"])
        self.assertTrue(any("does not declare" in warning for warning in data.warnings))

    def test_unrecognized_declaration_is_preserved_for_review(self):
        data = super_landxml.parse_landxml_text(
            _landxml(
                '<CoordinateSystem name="Project Grid" horizontalDatum="Local" '
                'horizontalCoordinateSystemName="Contractor Ground Grid" desc="Adjusted coordinates" />'
            )
        )

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "declared_unrecognized")
        self.assertEqual(summary["horizontal_datum"], "Local")
        self.assertEqual(summary["description"], "Adjusted coordinates")
        self.assertTrue(any("could not be identified" in warning for warning in data.warnings))

    def test_conflicting_coordinate_fields_are_not_silently_selected(self):
        data = super_landxml.parse_landxml_text(
            _landxml(
                '<CoordinateSystem epsgCode="6576" '
                'horizontalCoordinateSystemName="MS83/2011-EF" />'
            )
        )

        summary = super_landxml.coordinate_system_summary(data.coordinate_system)
        self.assertEqual(summary["status"], "conflicting")
        self.assertIsNone(summary["code"])
        self.assertTrue(any("disagree" in warning for warning in data.warnings))


if __name__ == "__main__":
    unittest.main()
