import csv
import io
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

        self.assertEqual(left_rows[0]["slope"], "-2.00")
        self.assertEqual(left_rows[2]["slope"], "+2.00")
        self.assertEqual(left_rows[3]["slope"], "+4.90")
        self.assertEqual(left_rows[4]["slope"], "+7.00")

        self.assertEqual(right_rows[0]["slope"], "-2.00")
        self.assertEqual(right_rows[1]["slope"], "-4.90")
        self.assertEqual(right_rows[2]["slope"], "-7.00")

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
        data = super_landxml.load_landxml(Path("Sample Data") / "SR8.xml")
        curves = super_batch.build_curves_from_presets(
            [data.curve_records()[4]],
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

        self.assertIn("1542+93.903", stations)
        self.assertIn("1233+15.920R2", stations)
        self.assertTrue(all("R1" not in station for station in stations))

    def test_ord_station_region_increments_for_each_equation(self):
        equations = [{"internal": 1000.0}, {"internal": 2000.0}]
        self.assertEqual(super_exports._station_region(999.0, equations), 1)
        self.assertEqual(super_exports._station_region(1000.0, equations), 2)
        self.assertEqual(super_exports._station_region(2001.0, equations), 3)

    def test_landxml_sample_is_parsed_and_station_maps_to_xy(self):
        path = Path("Sample Data") / "SR 82.xml"
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
        data = super_landxml.load_landxml(Path("Sample Data") / "SR8.xml")
        curve_six = data.curve_records()[5]

        self.assertEqual(curve_six["pc_station_label"], "1240+08.228")
        self.assertEqual(curve_six["pt_station_label"], "1260+16.005")
        self.assertAlmostEqual(
            Super.civil_to_internal_station(
                Super.parse_station(curve_six["pc_station_label"]), data.station_equations, data.station_range()
            ),
            curve_six["pc_station_ft"],
            places=3,
        )

    def test_landxml_curve_direction_follows_increasing_station_geometry(self):
        data = super_landxml.load_landxml(Path("Sample Data") / "SR8.xml")
        records = data.curve_records()

        # Curve 1 is clockwise after converting LandXML Northing/Easting to
        # CAD X/Y, so it turns right along increasing station.
        self.assertEqual(records[0]["rotation"], "cw")
        self.assertEqual(records[0]["curve_direction"], "right")
        self.assertEqual(records[1]["curve_direction"], "left")

    def test_landxml_radius_is_rounded_to_three_decimals_before_table_lookup(self):
        data = super_landxml.load_landxml(Path("Sample Data") / "SR8.xml")
        curve_two = data.curve_records()[1]

        self.assertEqual(data.curves[1].radius, 3499.9999999999995)
        self.assertEqual(curve_two["radius_ft"], 3500.0)
        results = Super.calculate_superelevation(
            curve_two["pc_station_label"],
            curve_two["pt_station_label"],
            "65",
            str(curve_two["radius_ft"]),
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

    def test_same_mdot_coordinate_system_preserves_coordinates(self):
        coordinate_system = next(iter(super_dxf.MDOT_COORDINATE_SYSTEMS))
        transform = super_dxf.coordinate_transformer(coordinate_system, coordinate_system)
        self.assertEqual(transform(1568586.0, 827908.0), (1568586.0, 827908.0))

    def test_mdot_east_and_west_transform_round_trip(self):
        east, west = list(super_dxf.MDOT_COORDINATE_SYSTEMS)
        point = (1568586.0, 827908.0)
        west_point = super_dxf.coordinate_transformer(east, west)(*point)
        round_trip = super_dxf.coordinate_transformer(west, east)(*west_point)
        self.assertAlmostEqual(round_trip[0], point[0], places=3)
        self.assertAlmostEqual(round_trip[1], point[1], places=3)

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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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

        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_symbology.dxf"
            super_dxf.export_overlay_dxf(path, [self.sample_overlay_curve("right")], landxml)
            document = ezdxf.readfile(path)

        expected = {
            "ALI_DESIGN_ML_CURVES": (55, 40),
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

        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
        curve = self.sample_overlay_curve("right")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "overlay_pc_pt_labels.dxf"
            super_dxf.export_overlay_dxf(path, [curve], landxml)
            entities = _parse_dxf_entities(path.read_text(encoding="utf-8"))

        labels = [entity.get("1", "") for entity in entities if entity["type"] == "TEXT"]
        self.assertIn("PC 120+00.000", labels)
        self.assertIn("PT 140+00.000", labels)

    def test_overlay_dxf_rotates_callout_text_perpendicular_to_alignment(self):
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
        landxml = super_landxml.load_landxml(Path("Sample Data") / "SR 82.xml")
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
