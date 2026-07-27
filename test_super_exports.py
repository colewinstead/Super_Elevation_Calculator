import csv
import hashlib
import io
import json
import math
import tempfile
import unittest
from pathlib import Path

import Super
from super_lane import build_lane_rows

import super_batch
import super_dxf
import super_exports
import super_landxml
import super_service


LANDXML_FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "sr82_synthetic.xml"
CW_REVERSE_FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "cw_reverse_curve.xml"


def _synthetic_landxml_data(
    *, radius: float = 2000.0, station_equations: list[dict] | None = None
) -> super_landxml.LandXMLData:
    """Build invented alignment geometry without relying on local project files."""
    line = super_landxml.LineSegment(start=(0.0, 0.0), end=(150.0, 0.0), length=150.0)
    arc_length = math.pi * radius / 6.0
    arc = super_landxml.ArcSegment(
        start=(150.0, 0.0),
        end=(150.0 + radius * 0.5, radius * (1.0 - math.sqrt(3.0) / 2.0)),
        center=(150.0, radius),
        radius=radius,
        length=arc_length,
        rotation="ccw",
    )
    tail = super_landxml.LineSegment(
        start=arc.end,
        end=(arc.end[0] + 100.0, arc.end[1]),
        length=100.0,
    )
    segments = [line, arc, tail]
    return super_landxml.LandXMLData(
        path=Path("synthetic.xml"),
        alignment_name="Synthetic Alignment",
        start_station=900.0,
        alignment_length=sum(segment.length for segment in segments),
        linear_unit="USSurveyFoot",
        lines=[line, tail],
        curves=[arc],
        spirals=[],
        station_equations=station_equations or [],
        superelevation_nodes=[],
        coordinate_system=None,
        warnings=[],
        _segments=segments,
    )


def _parse_dxf_entities(text: str) -> list[dict]:
    tokens = text.splitlines()
    entities: list[dict] = []
    index = 0
    while index + 1 < len(tokens):
        code = tokens[index].strip()
        value = tokens[index + 1]
        if code == "0" and value in {"TEXT", "LINE"}:
            entity = {"type": value}
            index += 2
            while index + 1 < len(tokens) and tokens[index].strip() != "0":
                entity[tokens[index].strip()] = tokens[index + 1]
                index += 2
            entities.append(entity)
            continue
        index += 2
    return entities


class SuperExportTests(unittest.TestCase):
    def overlay_record_digest(self) -> tuple[int, str]:
        content = LANDXML_FIXTURE.read_text(encoding="utf-8")
        data = super_landxml.parse_landxml_text(content, LANDXML_FIXTURE.name)
        curves = super_service.build_all_landxml_curves(
            content,
            LANDXML_FIXTURE.name,
            {
                "speed": "45",
                "facility": "centerline",
                "area": "rural",
                "lane_width": "12",
                "lanes_rotated": "2",
                "normal_crown": "0.02",
            },
        )
        captured = {}
        original = super_dxf.DxfWriter.save

        def capture(writer, *_args, **_kwargs):
            captured["records"] = list(writer._records)

        super_dxf.DxfWriter.save = capture
        try:
            super_dxf.export_overlay_dxf("unused.dxf", curves, data)
        finally:
            super_dxf.DxfWriter.save = original
        def canonicalize(value):
            if isinstance(value, float):
                # Ignore platform-level trig noise while retaining sub-micro-inch geometry changes.
                rounded = round(value, 8)
                return 0.0 if rounded == 0 else rounded
            if isinstance(value, (list, tuple)):
                return [canonicalize(item) for item in value]
            if isinstance(value, dict):
                return {key: canonicalize(item) for key, item in value.items()}
            return value

        encoded = json.dumps(
            canonicalize(captured["records"]), separators=(",", ":")
        ).encode("utf-8")
        return len(captured["records"]), hashlib.sha256(encoded).hexdigest()

    def sample_results(self):
        return Super.calculate_superelevation(
            "10+00",
            "12+00",
            "45",
            "1200",
            "centerline",
            "rural",
            "12",
            "2",
            "",
            "",
            "",
            "0.02",
            "",
            "",
        )

    def sample_curve(self, direction="right"):
        return {
            "meta": {
                "project_name": "Demo Project",
                "route_name": "SR 82",
                "alignment_name": "SR 82",
                "curve_name": "Curve 1",
                "curve_direction": direction,
            },
            "results": self.sample_results(),
            "notes": "Export note",
        }

    def sample_overlay_curve(self, direction="right"):
        results = Super.calculate_superelevation(
            "120+00",
            "140+00",
            "45",
            "1200",
            "centerline",
            "rural",
            "12",
            "2",
            "",
            "",
            "",
            "0.02",
            "",
            "",
        )
        return {
            "meta": {
                "project_name": "Demo Project",
                "route_name": "SR 82",
                "alignment_name": "SR 82",
                "curve_name": "Curve 1",
                "curve_direction": direction,
            },
            "results": results,
            "notes": "Overlay note",
        }

    def test_slope_labels_keep_explicit_plus_sign(self):
        self.assertEqual(super_exports.format_slope_label(6.0), "+6.00%")
        self.assertEqual(super_exports.format_slope_label(-6.0), "-6.00%")
        self.assertEqual(super_exports.format_slope_label(0.0), "0.00%")

    def test_right_curve_lane_signs_match_requested_convention(self):
        results = self.sample_results()
        left_rows, right_rows = build_lane_rows(results, "right")

        self.assertEqual(next(row for row in left_rows if row["label"] == "NC")["slope"], "-2.00")
        self.assertEqual(next(row for row in left_rows if row["label"] == "0%")["slope"], "0.00")
        self.assertEqual(next(row for row in left_rows if row["label"] == "PC")["slope"], "+4.90")
        self.assertEqual(next(row for row in left_rows if row["label"] == "FULL SUPER")["slope"], "+7.00")

        self.assertEqual(next(row for row in right_rows if row["label"] == "NC")["slope"], "-2.00")
        self.assertEqual(next(row for row in right_rows if row["label"] == "PC")["slope"], "-4.90")
        self.assertEqual(next(row for row in right_rows if row["label"] == "FULL SUPER")["slope"], "-7.00")

    def test_pc_and_pt_follow_each_lanes_linear_runoff(self):
        results = Super.calculate_superelevation(
            "100+00", "110+00", "25", "1250", "centerline", "rural",
            "12", "2", "", "", "", "0.02", "", "",
        )
        self.assertAlmostEqual(results["e"], 0.028)
        left_rows, right_rows = build_lane_rows(results, "left")

        outside_pc = next(row for row in right_rows if row["label"] == "PC")
        outside_pt = next(row for row in right_rows if row["label"] == "PT")
        inside_pc = next(row for row in left_rows if row["label"] == "PC")
        inside_pt = next(row for row in left_rows if row["label"] == "PT")

        self.assertAlmostEqual(outside_pc["slope_pct"], 1.96)
        self.assertAlmostEqual(outside_pt["slope_pct"], 1.96)
        self.assertAlmostEqual(inside_pc["slope_pct"], -2.0)
        self.assertAlmostEqual(inside_pt["slope_pct"], -2.0)

    def test_user_reported_two_point_six_percent_pc_and_pt_case(self):
        results = Super.calculate_superelevation(
            "20+08.438", "30+07.098", "25", "1250", "centerline", "rural",
            "12", "2", "0.026", "", "", "0.02", "", "",
        )
        left_rows, right_rows = build_lane_rows(results, "right")

        for rows, expected in ((left_rows, 1.82), (right_rows, -2.0)):
            self.assertAlmostEqual(next(row for row in rows if row["label"] == "PC")["slope_pct"], expected)
            self.assertAlmostEqual(next(row for row in rows if row["label"] == "PT")["slope_pct"], expected)

    def test_mdots_runoff_is_linear_after_tangent_runout(self):
        results = Super.calculate_superelevation(
            "1493+78.219", "1499+59.391", "65", "7650", "centerline", "rural",
            "12", "2", "0.052", "", "", "0.02", "145", "56",
        )
        left_rows, right_rows = build_lane_rows(results, "left", station_format=False)

        for rows, start_label in ((left_rows, "BEGIN ROTATION"), (right_rows, "0%")):
            pc = next(row for row in rows if row["label"] == "PC")
            full = next(row for row in rows if row["label"] == "FULL SUPER")
            start = next(row for row in rows if row["label"] == start_label)
            fraction = (pc["station_ft"] - start["station_ft"]) / (full["station_ft"] - start["station_ft"])
            expected = start["slope_pct"] + fraction * (full["slope_pct"] - start["slope_pct"])
            self.assertAlmostEqual(pc["slope_pct"], expected)

        for rows in (left_rows, right_rows):
            self.assertAlmostEqual(abs(next(row for row in rows if row["label"] == "PC")["slope_pct"]), 3.64)
            self.assertAlmostEqual(abs(next(row for row in rows if row["label"] == "PT")["slope_pct"]), 3.64)

    def test_low_super_inside_nc_precedes_pc(self):
        results = Super.calculate_superelevation(
            "8+58.877", "18+60.436", "65", "7650", "centerline", "rural",
            "12", "2", "0.026", "", "", "0.02", "73", "56",
        )
        left_rows, right_rows = build_lane_rows(results, "left", station_format=False)
        inside_rows = left_rows
        entry_nc = next(row for row in inside_rows if row["event_type"] == "Normal crown")
        rotation_start = next(row for row in inside_rows if row["label"] == "BEGIN ROTATION")
        pc = next(row for row in inside_rows if row["label"] == "PC")

        self.assertLess(entry_nc["station_ft"], pc["station_ft"])
        self.assertGreater(rotation_start["station_ft"], pc["station_ft"])
        self.assertAlmostEqual(pc["slope_pct"], -2.0)
        self.assertEqual([row["station_ft"] for row in left_rows], sorted(row["station_ft"] for row in left_rows))
        self.assertEqual([row["station_ft"] for row in right_rows], sorted(row["station_ft"] for row in right_rows))

    def test_reverse_curve_coordination_preserves_low_super_entry_order(self):
        first = {
            "meta": {"curve_direction": "left"},
            "results": Super.calculate_superelevation(
                "8+58.877", "18+60.436", "65", "7650", "centerline", "rural",
                "12", "2", "0.026", "", "", "0.02", "73", "56",
            ),
        }
        second = {
            "meta": {"curve_direction": "right"},
            "results": Super.calculate_superelevation(
                "20+06.436", "30+07.996", "65", "7650", "centerline", "rural",
                "12", "2", "0.026", "", "", "0.02", "73", "56",
            ),
        }
        coordinated = super_batch.coordinate_reverse_curve_transitions([first, second], pairs=[[0, 1]])
        left_rows, _ = build_lane_rows(coordinated[0]["results"], "left", station_format=False)
        entry_nc = next(row for row in left_rows if row["event_type"] == "Normal crown")
        pc = next(row for row in left_rows if row["label"] == "PC")

        self.assertLess(entry_nc["station_ft"], pc["station_ft"])
        self.assertAlmostEqual(pc["slope_pct"], -2.0)

    def test_normalized_export_rows_include_signed_labels(self):
        rows = super_exports.build_normalized_rows([self.sample_curve("right")])
        self.assertTrue(rows)

        first_left = next(row for row in rows if row["side"] == "left" and row["event_type"] == "Normal crown")
        first_full = next(row for row in rows if row["side"] == "left" and row["event_type"] == "Full super")
        first_right_full = next(row for row in rows if row["side"] == "right" and row["event_type"] == "Full super")

        self.assertEqual(first_left["project_name"], "Demo Project")
        self.assertEqual(first_left["route_name"], "SR 82")
        self.assertEqual(first_left["station_label"], "8+46.800")
        self.assertEqual(first_left["slope_label"], "-2.00%")
        self.assertEqual(first_full["slope_label"], "+7.00%")
        self.assertEqual(first_right_full["slope_label"], "-7.00%")

    def test_normal_crown_curve_exports_only_normal_crown_events(self):
        results = Super.calculate_superelevation(
            "1526+96.224", "1532+16.129", "65", "22000", "centerline", "rural", "12", "2", "", "", "", "0.02", "", ""
        )
        curve = self.sample_curve("right")
        curve["results"] = results

        self.assertTrue(results["normal_crown_only"])
        self.assertEqual(results["Lr"], 0.0)
        self.assertEqual(results["Lt"], 0.0)
        left_rows, right_rows = build_lane_rows(results, "right")
        self.assertEqual([row["event_type"] for row in left_rows], ["Normal crown", "Normal crown"])
        self.assertEqual([row["event_type"] for row in right_rows], ["Normal crown", "Normal crown"])
        self.assertTrue(all(row["slope_label"] == "-2.00%" for row in left_rows + right_rows))
        self.assertIn("Normal crown maintained", left_rows[0]["note"])

    def test_ord_csv_uses_bentley_header_and_decimal_cross_slope(self):
        buffer = io.StringIO()
        super_exports.write_ord_csv(buffer, [self.sample_curve("right")])
        buffer.seek(0)

        reader = csv.DictReader(buffer)
        self.assertEqual(
            reader.fieldnames,
            [
                "SuperelevationLane",
                "Station",
                "CrossSlope",
                "PivotAbout",
                "PointType",
                "TransitionType",
                "NonLinearCurveLength",
            ],
        )
        rows = list(reader)
        self.assertTrue(rows)
        self.assertIn("+", rows[0]["Station"])
        self.assertIn(rows[0]["PivotAbout"], {"LS", "RS"})
        self.assertTrue(rows[0]["CrossSlope"].startswith("-0."))

    def test_ord_csv_appends_station_region_after_landxml_equation(self):
        data = _synthetic_landxml_data(
            station_equations=[{"staInternal": "1000", "staBack": "1000", "staAhead": "500"}]
        )
        curves = super_batch.build_curves_from_presets(
            data.curve_records(),
            {
                "project_name": "SR8",
                "route_name": "SR8",
                "speed": "65",
                "facility": "centerline",
                "area": "rural",
                "lane_width": "12",
                "lanes_rotated": "2",
                "e_manual": "",
                "friction": "",
                "rel_grad": "",
                "normal_crown": "0.02",
                "Lr_manual": "",
                "Lt_manual": "",
                "curve_notes": "",
            },
        )
        buffer = io.StringIO()
        super_exports.write_ord_csv(buffer, curves)
        buffer.seek(0)
        rows = list(csv.DictReader(buffer))
        stations = [row["Station"] for row in rows]

        self.assertTrue(any(not station.endswith("R2") for station in stations))
        self.assertTrue(any(station.endswith("R2") for station in stations))
        self.assertTrue(all("R1" not in station for station in stations))

    def test_ord_station_region_increments_for_each_equation(self):
        equations = [{"internal": 1000.0}, {"internal": 2000.0}]
        self.assertEqual(super_exports._station_region(999.0, equations), 1)
        self.assertEqual(super_exports._station_region(1000.0, equations), 2)
        self.assertEqual(super_exports._station_region(2001.0, equations), 3)

    def test_landxml_sample_is_parsed_and_station_maps_to_xy(self):
        path = LANDXML_FIXTURE
        data = super_landxml.load_landxml(path)

        self.assertEqual(data.alignment_name, "SR 82")
        self.assertEqual(data.start_station, 10000.0)
        self.assertEqual(data.linear_unit, "USSurveyFoot")
        self.assertEqual(len(data.lines), 3)
        self.assertEqual(len(data.curves), 2)
        self.assertEqual(len(data.spirals), 0)
        self.assertEqual(len(data.station_equations), 0)
        self.assertEqual(len(data.superelevation_nodes), 0)

        start_xy = data.xy_at_station(10000.0)
        self.assertAlmostEqual(start_xy[0], 986327.5959036754, places=3)
        self.assertAlmostEqual(start_xy[1], 1453411.9250950934, places=3)

        line_end_xy = data.xy_at_station(10000.0 + 7407.4478297109072)
        self.assertAlmostEqual(line_end_xy[0], 993735.0437333863, places=3)
        self.assertAlmostEqual(line_end_xy[1], 1453411.9250950934, places=3)

        curve_records = data.curve_records()
        self.assertEqual(len(curve_records), 2)
        self.assertEqual(curve_records[0]["alignment_name"], "SR 82")
        self.assertEqual(curve_records[0]["curve_name"], "Curve 1")
        self.assertEqual(curve_records[0]["curve_direction"], "right")
        self.assertEqual(curve_records[0]["pc_station_label"], "174+07.448")
        self.assertEqual(curve_records[0]["pt_station_label"], "197+63.816")
        self.assertEqual(curve_records[0]["radius_ft"], 2000.0)
        self.assertEqual(curve_records[1]["curve_direction"], "left")
        self.assertEqual(curve_records[1]["pc_station_label"], "239+03.806")
        self.assertEqual(curve_records[1]["pt_station_label"], "252+20.075")

        first_curve_mid_station = curve_records[0]["pc_station_ft"] + (curve_records[0]["curve_length_ft"] / 2.0)
        mid_xy = data.xy_at_station(first_curve_mid_station)
        self.assertGreater(mid_xy[0], data.curves[0].start[0])

    def test_landxml_station_equation_uses_civil_labels_and_internal_geometry(self):
        data = _synthetic_landxml_data(
            station_equations=[{"staInternal": "1000", "staBack": "1000", "staAhead": "500"}]
        )
        curve = data.curve_records()[0]

        self.assertEqual(curve["pc_station_label"], "5+50.000")
        self.assertNotEqual(curve["pc_station_label"], Super.format_station(curve["pc_station_ft"], True))
        self.assertAlmostEqual(
            Super.civil_to_internal_station(
                Super.parse_station(curve["pc_station_label"]), data.station_equations, data.station_range()
            ),
            curve["pc_station_ft"],
            places=3,
        )

    def test_landxml_curve_direction_follows_increasing_station_geometry(self):
        data = super_landxml.load_landxml(LANDXML_FIXTURE)
        records = data.curve_records()

        # Curve 1 is clockwise after converting LandXML Northing/Easting to
        # CAD X/Y, so it turns right along increasing station.
        self.assertEqual(records[0]["rotation"], "cw")
        self.assertEqual(records[0]["curve_direction"], "right")
        self.assertEqual(records[1]["curve_direction"], "left")

    def test_landxml_radius_is_rounded_to_three_decimals_before_table_lookup(self):
        data = _synthetic_landxml_data(radius=3499.9999999999995)
        curve = data.curve_records()[0]

        self.assertEqual(data.curves[0].radius, 3499.9999999999995)
        self.assertEqual(curve["radius_ft"], 3500.0)
        results = Super.calculate_superelevation(
            curve["pc_station_label"],
            curve["pt_station_label"],
            "65",
            str(curve["radius_ft"]),
            "centerline",
            "rural",
            "12",
            "2",
            "",
            "",
            "",
            "0.02",
            "",
            "",
            data.station_equations,
            data.station_range(),
        )
        self.assertAlmostEqual(results["e"], 0.052)

    def test_dxf_declares_landxml_us_survey_foot_units(self):
        self.assertEqual(super_dxf.dxf_insunits("USSurveyFoot"), 21)
        self.assertEqual(super_dxf.dxf_insunits("foot"), 2)
        self.assertEqual(super_dxf.dxf_insunits("meter"), 6)

    def test_dxf_r2000_entities_include_required_class_markers(self):
        writer = super_dxf.DxfWriter()
        writer.add_line(1, 2, 3, 4, "TEST")
        writer.add_text(5, 6, "Label", 1, "TEST")
        payload = "\n".join(writer.entities)

        self.assertIn("LINE\n5\n100\n100\nAcDbEntity\n8\nTEST\n100\nAcDbLine", payload)
        self.assertIn("TEXT\n5\n101\n100\nAcDbEntity\n8\nTEST\n100\nAcDbText", payload)

    def test_dxf_r2000_header_includes_handle_seed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "handles.dxf"
            writer = super_dxf.DxfWriter()
            writer.add_line(1, 2, 3, 4, "TEST")
            writer.save(path, 21)
            text = path.read_text(encoding="utf-8")

        self.assertRegex(text, r"\$HANDSEED\s+5\s+[0-9A-F]+")

    def test_overlay_dxf_preserves_landxml_xy_coordinates(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        first_line = landxml.lines[0]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "preserved_xy.dxf"
            super_dxf.export_overlay_dxf(path, [self.sample_overlay_curve("right")], landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        alignment_line = next(
            entity
            for entity in entities
            if entity["type"] == "LINE" and entity.get("8") == "ALI_DESIGN_ML_CURVES"
        )
        self.assertEqual(float(alignment_line["10"]), first_line.start[0])
        self.assertEqual(float(alignment_line["20"]), first_line.start[1])
        self.assertEqual(float(alignment_line["11"]), first_line.end[0])
        self.assertEqual(float(alignment_line["21"]), first_line.end[1])

    def test_overlay_entity_sequence_is_preserved(self):
        self.assertEqual(
            self.overlay_record_digest(),
            (210, "332287b22b6b403924fbd77a4766db5d832b194cd32996d3ca941378e127adc7"),
        )

    def test_overlay_alignment_layer_uses_gray_aci(self):
        self.assertEqual(
            super_dxf.DEFAULT_CONFIG["overlay_layer_styles"]["ALI_DESIGN_ML_CURVES"]["color"],
            8,
        )

    def test_detail_dxf_contains_curve_labels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "detail.dxf"
            warnings = super_dxf.export_detail_dxf(path, [self.sample_curve("right")])
            text = path.read_text(encoding="utf-8")

        self.assertEqual(warnings, [])
        self.assertIn("Superelevation Detail", text)
        self.assertIn("Curve 1", text)
        self.assertIn("Left Lane Profile", text)
        self.assertIn("Right Lane Profile", text)
        self.assertIn("Key Stations", text)

    def test_overlay_dxf_uses_real_alignment_geometry(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay.dxf"
            warnings = super_dxf.export_overlay_dxf(path, [self.sample_overlay_curve("right")], landxml)
            text = path.read_text(encoding="utf-8")

        self.assertEqual(warnings, [])
        self.assertIn("ALI_DESIGN_ML_CURVES", text)
        self.assertIn("ALI_DESIGN_ML_LABELS", text)
        self.assertIn("ALI_DESIGN_ML_STA", text)
        self.assertIn("ALI_DESIGN_ML_LABELS_TX", text)

    def test_overlay_dxf_uses_mdot_layer_colors_and_weights(self):
        import ezdxf

        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_symbology.dxf"
            super_dxf.export_overlay_dxf(path, [self.sample_overlay_curve("right")], landxml)
            document = ezdxf.readfile(path)

        expected = {
            "ALI_DESIGN_ML_CURVES": (8, 40),
            "ALI_DESIGN_ML_LABELS": (10, 40),
            "ALI_DESIGN_ML_STA": (7, 40),
            "ALI_DESIGN_ML_LABELS_TX": (7, 40),
        }
        for layer_name, (color, lineweight) in expected.items():
            layer = document.layers.get(layer_name)
            self.assertEqual(layer.dxf.color, color)
            self.assertEqual(layer.dxf.linetype.upper(), "CONTINUOUS")
            self.assertEqual(layer.dxf.lineweight, lineweight)

    def test_overlay_dxf_uses_engineering_regular_text_style(self):
        import ezdxf

        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_font.dxf"
            super_dxf.export_overlay_dxf(path, [self.sample_overlay_curve("right")], landxml)
            document = ezdxf.readfile(path)

        style = document.styles.get("Engineering Regular")
        self.assertEqual(style.dxf.font, "EngineeringRegular.ttf")
        self.assertTrue(style.has_extended_font_data)
        self.assertEqual(style.get_extended_font_data(), ("Engineering Regular", False, False))
        overlay_text = [
            entity
            for entity in document.modelspace()
            if entity.dxftype() == "TEXT"
            and entity.dxf.layer in {"ALI_DESIGN_ML_STA", "ALI_DESIGN_ML_LABELS_TX"}
        ]
        self.assertTrue(overlay_text)
        self.assertTrue(all(entity.dxf.style == "Engineering Regular" for entity in overlay_text))

    def test_overlay_dxf_labels_include_station_and_both_lane_slopes(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")
        rows = super_exports.build_normalized_rows([curve])
        left_full = next(row for row in rows if row["side"] == "left" and row["event_type"] == "Full super")
        right_full = next(row for row in rows if row["side"] == "right" and row["event_type"] == "Full super")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_labels.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            text = path.read_text(encoding="utf-8")

        entities = _parse_dxf_entities(text)
        label_text = [
            entity.get("1", "")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") in {"ALI_DESIGN_ML_STA", "ALI_DESIGN_ML_LABELS_TX"}
        ]

        self.assertGreaterEqual(label_text.count(left_full["station_label"]), 2)
        self.assertIn(left_full["slope_label"], label_text)
        self.assertIn(right_full["slope_label"], label_text)
        self.assertNotIn(f"L:{left_full['slope_label']}", label_text)
        self.assertNotIn(f"R:{right_full['slope_label']}", label_text)

    def test_overlay_dxf_prefixes_pc_and_pt_station_callouts(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_pc_pt_labels.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        labels = [entity.get("1", "") for entity in entities if entity["type"] == "TEXT"]
        self.assertIn("PC 120+00.000", labels)
        self.assertIn("PT 140+00.000", labels)

    def test_overlay_dxf_uses_compact_reverse_callouts_on_normal_layers(self):
        content = CW_REVERSE_FIXTURE.read_text(encoding="utf-8")
        landxml = super_landxml.parse_landxml_text(content, CW_REVERSE_FIXTURE.name)
        independent = super_service.build_all_landxml_curves(
            content,
            CW_REVERSE_FIXTURE.name,
            {
                "speed": "65", "facility": "centerline", "area": "rural",
                "lane_width": "12", "lanes_rotated": "2", "normal_crown": "0.02",
            },
        )
        curves = super_batch.coordinate_reverse_curve_transitions(independent, pairs=[[0, 1]])
        critical_rows = [
            row for row in super_exports.build_normalized_rows(curves)
            if row.get("reverse_pair_critical")
        ]
        self.assertTrue(critical_rows)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "reverse_pair.dxf"
            super_dxf.export_overlay_dxf(path, curves, landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        self.assertFalse(any(
            entity.get("8") == "ALI_DESIGN_ML_SE_REVERSE"
            for entity in entities
        ))
        station_text = [
            entity.get("1", "")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") == "ALI_DESIGN_ML_STA"
        ]
        slope_text = [
            entity.get("1", "")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") == "ALI_DESIGN_ML_LABELS_TX"
        ]
        compact_rows = super_dxf._compact_reverse_callouts(critical_rows)
        expected_callouts = {
            super_dxf._reverse_station_label(
                row,
                curves[int(row["curve_index"])],
            )
            for row in compact_rows
        }
        self.assertTrue(expected_callouts.issubset(set(station_text)))
        self.assertTrue({row["slope_label"] for row in compact_rows}.issubset(set(slope_text)))
        self.assertFalse(any(
            "Reverse" in text or text.startswith(("LEFT ", "RIGHT "))
            for text in station_text
        ))

        preview = super_dxf.overlay_preview_model(curves, landxml)
        reverse_station_entities = [
            entity
            for entity in preview["entities"]
            if entity["type"] == "TEXT"
            and entity["layer"] == "ALI_DESIGN_ML_STA"
            and (entity.get("preview") or {}).get("reverse_pair_critical")
        ]
        positions = {
            (round(float(entity["x"]), 7), round(float(entity["y"]), 7))
            for entity in reverse_station_entities
        }
        self.assertEqual(len(positions), len(reverse_station_entities))
        for side in ("left", "right"):
            label_stations = sorted(
                float(entity["preview"]["label_station_ft"])
                for entity in reverse_station_entities
                if entity["preview"]["side"] == side
            )
            self.assertTrue(all(
                following - prior
                >= super_dxf.DEFAULT_CONFIG["overlay_min_label_spacing"] - 1e-7
                for prior, following in zip(label_stations, label_stations[1:])
            ))
        self.assertTrue(all(
            entity["layer"] in {
                "ALI_DESIGN_ML_LABELS",
                "ALI_DESIGN_ML_STA",
                "ALI_DESIGN_ML_LABELS_TX",
            }
            for entity in preview["entities"]
            if (entity.get("preview") or {}).get("reverse_pair_critical")
        ))

    def test_ord_and_dxf_include_real_unequal_rate_handoff_after_pc(self):
        content = CW_REVERSE_FIXTURE.read_text(encoding="utf-8")
        landxml = super_landxml.parse_landxml_text(content, CW_REVERSE_FIXTURE.name)
        curves = super_batch.build_curves_from_presets(
            [
                {
                    "pc_station_label": "149576.601",
                    "pt_station_label": "150576.601",
                    "radius_ft": 3000.0,
                    "curve_direction": "left",
                    "curve_name": "Outgoing",
                    "alignment_name": "ML",
                },
                {
                    "pc_station_label": "150704.801",
                    "pt_station_label": "151704.801",
                    "radius_ft": 6000.0,
                    "curve_direction": "right",
                    "curve_name": "Incoming",
                    "alignment_name": "ML",
                },
            ],
            {
                "speed": "55", "facility": "centerline", "area": "rural",
                "lane_width": "12", "lanes_rotated": "2", "normal_crown": "0.02",
            },
        )
        curves = super_batch.coordinate_reverse_curve_transitions(curves, pairs=[[0, 1]])
        check = curves[0]["results"]["reverse_curve_coordination"]["checks"][0]
        self.assertEqual(check["status"], "coordinated")

        handoff_row = next(
            row for row in super_exports.build_normalized_rows(curves)
            if row.get("reverse_pair_critical")
            and row["event_type"] == "Reverse handoff"
        )
        self.assertGreater(handoff_row["station"], curves[1]["results"]["pc_ft"])
        self.assertLess(handoff_row["station"], curves[1]["results"]["full_super_ft"])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "unequal_rate_handoff.dxf"
            super_dxf.export_overlay_dxf(path, curves, landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        station_text = {
            entity.get("1", "")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") == "ALI_DESIGN_ML_STA"
        }
        slope_text = {
            entity.get("1", "")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") == "ALI_DESIGN_ML_LABELS_TX"
        }
        expected_callout = super_dxf._reverse_station_label(
            handoff_row,
            curves[int(handoff_row["curve_index"])],
        )
        self.assertIn(expected_callout, station_text)
        self.assertIn(handoff_row["slope_label"], slope_text)
        self.assertNotIn("ALI_DESIGN_ML_SE_REVERSE", {entity.get("8") for entity in entities})

    def test_ord_rows_include_real_reverse_controls_without_artificial_hold_handoffs(self):
        content = CW_REVERSE_FIXTURE.read_text(encoding="utf-8")
        independent = super_service.build_all_landxml_curves(
            content,
            CW_REVERSE_FIXTURE.name,
            {
                "speed": "65", "facility": "centerline", "area": "rural",
                "lane_width": "12", "lanes_rotated": "2", "normal_crown": "0.02",
            },
        )
        curves = super_batch.coordinate_reverse_curve_transitions(independent, pairs=[[0, 1]])
        rows = super_exports.build_normalized_rows(curves)
        reverse_rows = [row for row in rows if row.get("reverse_pair_critical")]
        event_types = {row["event_type"] for row in reverse_rows}
        self.assertNotIn("Reverse handoff", event_types)
        self.assertIn("Reverse curve zero", event_types)
        self.assertIn("Normal crown hold start", event_types)
        self.assertIn("Normal crown hold end", event_types)
        self.assertIn("End full super", event_types)
        self.assertIn("PT reverse-curve runoff", event_types)
        self.assertIn("PC reverse-curve runoff", event_types)
        self.assertIn("Full super", event_types)
        self.assertTrue(all(row["reverse_pair_id"] == "reverse-pair-0-1" for row in reverse_rows))
        canonical_keys = {
            (
                row["reverse_pair_id"],
                row["side"],
                row["event_type"],
                round(float(row["station"]), 7),
                round(float(row["slope_percent"]), 7),
            )
            for row in reverse_rows
        }
        self.assertEqual(len(canonical_keys), len(reverse_rows))

    def test_overlay_dxf_rotates_callout_text_perpendicular_to_alignment(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")
        rows = super_exports.build_normalized_rows([curve])
        left_full = next(row for row in rows if row["side"] == "left" and row["event_type"] == "Full super")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_rotation.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            text = path.read_text(encoding="utf-8")

        entities = _parse_dxf_entities(text)
        station_entities = [entity for entity in entities if entity["type"] == "TEXT" and entity.get("1") == left_full["station_label"]]
        self.assertGreaterEqual(len(station_entities), 1)

        tx, ty = landxml.tangent_at_station(float(left_full["station"]))
        normal_rotation = math.degrees(math.atan2(tx, -ty))
        actual_rotation = float(station_entities[0]["50"])

        diff = min(
            abs(actual_rotation - normal_rotation),
            abs(actual_rotation - (normal_rotation + 180.0)),
            abs(actual_rotation - (normal_rotation - 180.0)),
        )
        self.assertLess(diff, 1.0)

    def test_overlay_curve_title_is_parallel_and_larger_than_callouts(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")
        first_station = min(float(row["station"]) for row in super_exports.build_normalized_rows([curve]))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_title.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        title = next(
            entity
            for entity in entities
            if entity["type"] == "TEXT" and entity.get("1") == "Curve 1 (right)"
        )
        tx, ty = landxml.tangent_at_station(first_station)
        expected_rotation = math.degrees(math.atan2(ty, tx))
        if expected_rotation > 90.0 or expected_rotation <= -90.0:
            expected_rotation = ((expected_rotation + 180.0) % 360.0) - 180.0
            if expected_rotation > 90.0:
                expected_rotation -= 180.0
        actual_rotation = float(title.get("50", 0.0))
        self.assertLess(abs(actual_rotation - expected_rotation), 1.0)
        self.assertGreater(float(title["40"]), super_dxf.DEFAULT_CONFIG["text_height"])

    def test_overlay_curve_title_formats_radius_to_three_decimals(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")
        curve["results"]["inputs"]["radius_ft"] = 5654.5779999999995

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_title_radius.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        titles = [entity.get("1", "") for entity in entities if entity["type"] == "TEXT"]
        self.assertIn("Curve 1 (right)", titles)
        self.assertIn("R=5,654.578'", titles)

    def test_overlay_dxf_extends_lane_leaders_for_close_labels(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_leaders.dxf"
            super_dxf.export_overlay_dxf(
                path,
                [curve],
                landxml,
                config={"tick_length": 25.0, "overlay_label_gap": 1000.0},
            )
            text = path.read_text(encoding="utf-8")

        entities = _parse_dxf_entities(text)
        leader_lengths = []
        for entity in entities:
            if entity["type"] != "LINE" or entity.get("8") != "ALI_DESIGN_ML_LABELS":
                continue
            x1 = float(entity["10"])
            y1 = float(entity["20"])
            x2 = float(entity["11"])
            y2 = float(entity["21"])
            leader_lengths.append(round(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 3))

        self.assertTrue(leader_lengths)
        self.assertGreater(max(leader_lengths), min(leader_lengths))

    def test_overlay_label_packing_enforces_minimum_spacing_by_side(self):
        rows = [
            {"side": "left", "station": 1000.0},
            {"side": "left", "station": 1008.0},
            {"side": "left", "station": 1015.0},
            {"side": "right", "station": 1000.0},
            {"side": "right", "station": 1004.0},
        ]
        super_dxf._pack_overlay_label_stations(rows, 55.0, 220.0, 900.0, 1200.0)

        for side in ("left", "right"):
            packed = [row["_label_station"] for row in rows if row["side"] == side]
            self.assertTrue(all(b - a >= 55.0 for a, b in zip(packed, packed[1:])))

    def test_overlay_text_uses_side_aware_endpoint_alignment(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_text_alignment.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            text = path.read_text(encoding="utf-8")

        entities = _parse_dxf_entities(text)
        text_alignments = {
            entity.get("72", "0")
            for entity in entities
            if entity["type"] == "TEXT"
            and entity.get("8") in {"ALI_DESIGN_ML_STA", "ALI_DESIGN_ML_LABELS_TX"}
        }
        self.assertIn("0", text_alignments)
        self.assertIn("2", text_alignments)

    def test_overlay_dxf_separates_station_and_slope_across_alignment_direction(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curve = self.sample_overlay_curve("right")
        rows = super_exports.build_normalized_rows([curve])
        left_full = next(row for row in rows if row["side"] == "left" and row["event_type"] == "Full super")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_station_slope_spacing.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            text = path.read_text(encoding="utf-8")

        entities = _parse_dxf_entities(text)
        station_entity = next(
            entity for entity in entities if entity["type"] == "TEXT" and entity.get("1") == left_full["station_label"]
        )
        slope_entity = next(
            entity for entity in entities if entity["type"] == "TEXT" and entity.get("1") == left_full["slope_label"]
        )

        sx = float(station_entity["10"])
        sy = float(station_entity["20"])
        px = float(slope_entity["10"])
        py = float(slope_entity["20"])
        tx, ty = landxml.tangent_at_station(float(left_full["station"]))
        tangent_delta = abs((px - sx) * tx + (py - sy) * ty)
        normal_delta = abs((px - sx) * (-ty) + (py - sy) * tx)

        self.assertGreater(tangent_delta, 5.0)
        self.assertLess(normal_delta, tangent_delta)

    def test_overlay_dxf_combined_export_includes_multiple_curve_labels(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curves = super_batch.build_curves_from_presets(
            landxml.curve_records(),
            {
                "project_name": "20189900",
                "route_name": "SR 82",
                "speed": "60",
                "facility": "centerline",
                "area": "rural",
                "lane_width": "12",
                "lanes_rotated": "2",
                "e_manual": "",
                "friction": "",
                "rel_grad": "",
                "normal_crown": "0.02",
                "Lr_manual": "",
                "Lt_manual": "",
                "curve_notes": "",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_multi.dxf"
            warnings = super_dxf.export_overlay_dxf(path, curves, landxml)
            text = path.read_text(encoding="utf-8")

        self.assertEqual(warnings, [])
        self.assertIn("Curve 1", text)
        self.assertIn("Curve 2", text)

    def test_build_all_curves_from_landxml_presets(self):
        landxml = super_landxml.load_landxml(LANDXML_FIXTURE)
        curves = super_batch.build_curves_from_presets(
            landxml.curve_records(),
            {
                "project_name": "20189900",
                "route_name": "SR 82",
                "speed": "60",
                "facility": "centerline",
                "area": "rural",
                "lane_width": "12",
                "lanes_rotated": "2",
                "e_manual": "",
                "friction": "",
                "rel_grad": "",
                "normal_crown": "0.02",
                "Lr_manual": "",
                "Lt_manual": "",
                "curve_notes": "",
            },
        )

        self.assertEqual(len(curves), 2)
        self.assertEqual(curves[0]["meta"]["project_name"], "20189900")
        self.assertEqual(curves[0]["meta"]["curve_name"], "Curve 1")
        self.assertEqual(curves[0]["meta"]["curve_direction"], "right")
        self.assertEqual(curves[0]["results"]["inputs"]["pc"], "174+07.448")
        self.assertEqual(curves[0]["results"]["inputs"]["pt"], "197+63.816")
        self.assertEqual(curves[0]["results"]["inputs"]["radius_ft"], 2000.0)
        self.assertEqual(curves[1]["meta"]["curve_name"], "Curve 2")
        self.assertEqual(curves[1]["meta"]["curve_direction"], "left")


if __name__ == "__main__":
    unittest.main()
