from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
from typing import Iterable

import Super
from app_info import APP_VERSION
from criteria_info import applicable_drawings_label, calculation_sources_label, criteria_for_result
from super_lane import build_lane_rows


def _asset_constants() -> tuple[str, dict[str, str]]:
    import super_ui

    return (
        getattr(super_ui, "DIAGRAM_PNG_B64", ""),
        getattr(super_ui, "STAMP_PNG_B64", {}),
    )


def _decode_asset(value: str) -> bytes | None:
    if not value:
        return None
    try:
        return base64.b64decode(value)
    except Exception:
        return None


def stamp_images() -> dict[str, bytes]:
    _, stamp_b64 = _asset_constants()
    images: dict[str, bytes] = {}
    for key, value in stamp_b64.items():
        decoded = _decode_asset(value)
        if decoded:
            images[key] = decoded
    return images


def select_stamps(results: dict) -> list[str]:
    _, stamp_b64 = _asset_constants()
    inputs = results.get("inputs", {})
    area = str(inputs.get("area_type", "")).lower()
    facility = str(inputs.get("facility", "")).lower()
    speed = inputs.get("speed_mph", 0)
    stamps: list[str] = []

    if area.startswith("local"):
        if "SE-1" in stamp_b64:
            stamps.append("SE-1")
    elif area.startswith("urban"):
        if speed <= 45 and "center" in facility:
            if "SE-2E" in stamp_b64:
                stamps.append("SE-2E")
        elif speed == 50 and "center" in facility:
            if "SE-2C" in stamp_b64:
                stamps.append("SE-2C")
        elif speed == 50 and "edge" in facility:
            if "SE-2D" in stamp_b64:
                stamps.append("SE-2D")
    elif "edge" in facility:
        if "SE-2B" in stamp_b64:
            stamps.append("SE-2B")
        if "SE-3B" in stamp_b64:
            stamps.append("SE-3B")
    else:
        if "SE-2A" in stamp_b64:
            stamps.append("SE-2A")
        if "SE-3A" in stamp_b64:
            stamps.append("SE-3A")
    return stamps


def open_file(path: str) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def export_pdf(path: str, curves: Iterable[dict]) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    curve_list = list(curves)
    diagram_b64, _ = _asset_constants()
    diagram_bytes = _decode_asset(diagram_b64)
    stamps = stamp_images()

    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle(f"Superelevation Calculation Report - Application {APP_VERSION}")
    c.setAuthor("Superelevation Calculator")
    c.setSubject("Superelevation report; calculation engine and criteria are recorded on each curve page")
    engine_versions = sorted(
        {
            str((curve.get("results") or {}).get("calculation_metadata", {}).get("engine_version") or "legacy-unversioned")
            for curve in curve_list
        }
    )
    c.setKeywords(f"application={APP_VERSION}; calculation_engines={','.join(engine_versions)}")
    width, height = letter

    def draw_wrapped_text(
        text: str,
        x: float,
        y: float,
        max_width: float,
        line_height: float,
        font_name: str = "Helvetica",
        font_size: float = 8,
    ) -> float:
        c.setFont(font_name, font_size)
        words = text.split()
        if not words:
            c.drawString(x, y, text)
            return y - line_height
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if c.stringWidth(candidate, font_name, font_size) <= max_width:
                line = candidate
            else:
                if line:
                    c.drawString(x, y, line)
                    y -= line_height
                line = word
        if line:
            c.drawString(x, y, line)
            y -= line_height
        return y

    def draw_lane_table(left: float, y: float, title: str, rows: list[dict]) -> float:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left, y, title)
        y -= 0.15 * inch
        col_widths = [0.9 * inch, 1.4 * inch, 0.75 * inch, 3.4 * inch]
        x_positions = [left]
        for col_width in col_widths:
            x_positions.append(x_positions[-1] + col_width)
        row_height = 0.19 * inch
        headers = ["Point", "Station", "Slope", "Note"]
        c.setFont("Helvetica-Bold", 7.5)
        for idx, header in enumerate(headers):
            c.drawString(x_positions[idx] + 3, y, header)
        y -= 0.12 * inch
        c.line(left, y, left + sum(col_widths), y)
        y -= 0.12 * inch
        c.setFont("Helvetica", 7.2)
        for row in rows:
            if y < 0.7 * inch:
                c.showPage()
                y = height - 0.75 * inch
                c.setFont("Helvetica", 7.2)
            c.drawString(x_positions[0] + 3, y, str(row["label"]))
            c.drawString(x_positions[1] + 3, y, str(row["station"]))
            c.drawRightString(x_positions[3] - 8, y, str(row["slope"]))
            y = draw_wrapped_text(str(row["note"]), x_positions[3] + 3, y, col_widths[3] - 6, row_height)
        return y - 0.12 * inch

    for idx, curve in enumerate(curve_list):
        if idx > 0:
            c.showPage()
        results = curve.get("results") or {}
        calculation_metadata = results.get("calculation_metadata", {}) or {}
        engine_version = calculation_metadata.get("engine_version") or "legacy-unversioned"
        criteria = criteria_for_result(results)
        meta = curve.get("meta", {}) or {}
        notes = curve.get("notes", "")
        inputs = results.get("inputs", {}) or {}
        segments = results.get("segments", {}) or {}
        margin = 0.58 * inch
        left = margin
        right_x = 4.75 * inch
        y = height - margin

        c.setFont("Helvetica-Bold", 14)
        c.drawString(left, y, "Superelevation Transition Summary")
        y -= 0.23 * inch
        c.setFont("Helvetica", 8)
        y = draw_wrapped_text(
            f"Application {APP_VERSION} | Calculation engine {engine_version}",
            left,
            y,
            3.95 * inch,
            0.12 * inch,
            "Helvetica",
            8,
        )
        y = draw_wrapped_text(
            f"Applicable: {applicable_drawings_label(criteria)}",
            left,
            y,
            3.95 * inch,
            0.12 * inch,
            "Helvetica-Bold",
            7.5,
        )
        y = draw_wrapped_text(
            f"Calculation sources: {calculation_sources_label(criteria)}",
            left,
            y,
            3.95 * inch,
            0.11 * inch,
            "Helvetica",
            6.8,
        )
        c.setFont("Helvetica", 8)
        c.drawString(left, y, f"Alignment: {meta.get('alignment_name', 'n/a')}")
        y -= 0.13 * inch
        c.drawString(left, y, f"Curve: {meta.get('curve_name', 'n/a')}    Direction: {meta.get('curve_direction', 'left')}")
        y -= 0.22 * inch

        if diagram_bytes:
            diagram_img = ImageReader(io.BytesIO(diagram_bytes))
            iw, ih = diagram_img.getSize()
            scale = min((width - right_x - margin) / iw, (2.0 * inch) / ih)
            c.drawImage(
                diagram_img,
                right_x,
                height - margin - 2.35 * inch,
                iw * scale,
                ih * scale,
                preserveAspectRatio=True,
            )

        stamp_y = height - margin - 2.48 * inch
        for stamp_key in select_stamps(results):
            asset = stamps.get(stamp_key)
            if not asset:
                continue
            stamp_img = ImageReader(io.BytesIO(asset))
            sw, sh = stamp_img.getSize()
            scale = min((width - right_x - margin) / sw, (0.58 * inch) / sh)
            stamp_h = sh * scale
            stamp_y -= stamp_h
            c.drawImage(stamp_img, right_x, stamp_y, sw * scale, stamp_h, preserveAspectRatio=True)
            stamp_y -= 0.06 * inch

        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "Inputs")
        y -= 0.16 * inch
        c.setFont("Helvetica", 8)
        input_lines = [
            f"PC station: {inputs.get('pc', '')}",
            f"PT station: {inputs.get('pt', '') or 'n/a'}",
            f"Design speed: {inputs.get('speed_mph', '')} mph",
            f"Curve radius: {inputs.get('radius_ft', '')} ft",
            f"Facility / area: {inputs.get('facility', '')} / {inputs.get('area_type', '')}",
            f"Lane width / lanes rotated: {inputs.get('lane_width_ft', '')} ft / {inputs.get('lanes_rotated', '')}",
        ]
        for line in input_lines:
            c.drawString(left, y, line)
            y -= 0.13 * inch

        y -= 0.05 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "Results")
        y -= 0.16 * inch
        c.setFont("Helvetica-Bold", 8.5)
        result_lines = [
            f"Superelevation rate e: {results.get('e', 0):.4f} ft/ft ({results.get('e_source', '')})",
            f"Runoff length Lr: {results.get('Lr', 0):.2f} ft",
            f"Tangent runout Lt: {results.get('Lt', 0):.2f} ft",
            f"Total transition: {segments.get('total_transition', 0):.2f} ft",
        ]
        if results.get("normal_crown_only"):
            result_lines.append("Normal crown is maintained; no superelevation transition is required.")
        if results.get("extra_width", 0.0) > 0:
            result_lines.append(f"Extra width: {results.get('extra_width', 0):.2f} ft")
        for line in result_lines:
            c.drawString(left, y, line)
            y -= 0.14 * inch

        c.setFont("Helvetica", 7.4)
        note_parts = [
            results.get("friction_note"),
            results.get("rel_grad_note"),
            results.get("lanes_note"),
            results.get("r_note"),
            results.get("e_note"),
            results.get("runoff_note"),
            results.get("extra_width_note"),
        ]
        note_text = "; ".join(part for part in note_parts if part)
        if note_text:
            y = draw_wrapped_text(f"Calculation notes: {note_text}", left, y, 3.95 * inch, 0.12 * inch, "Helvetica", 7.4)
        if notes:
            y = draw_wrapped_text(f"Curve notes: {notes}", left, y, 3.95 * inch, 0.12 * inch, "Helvetica", 7.4)

        y -= 0.05 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "Station References")
        y -= 0.16 * inch
        c.setFont("Helvetica", 8)
        if results.get("normal_crown_only"):
            station_lines = [("Normal crown begins", results.get("reverse_crown_ft")), ("Normal crown ends", results.get("pt_ft"))]
        else:
            station_lines = [
                ("Point of normal crown", results.get("pnc_ft")),
                ("Point of reverse crown", results.get("reverse_crown_ft")),
                ("Full super near PC", results.get("full_super_ft")),
                ("Full super near PT", results.get("full_super_out_ft")),
                ("Reverse crown out", results.get("reverse_crown_out_ft")),
                ("Normal crown out", results.get("pnc_out_ft")),
            ]
        for label, station in station_lines:
            if station is None:
                continue
            c.drawString(left, y, f"{label}: {Super.format_result_station(results, station, True)}")
            y -= 0.13 * inch

        min_table_y = min(y - 0.08 * inch, stamp_y - 0.12 * inch)
        y = max(min_table_y, 2.2 * inch)
        left_rows, right_rows = build_lane_rows(results, meta.get("curve_direction", "left"), True)
        y = draw_lane_table(left, y, "Left Lane", left_rows)
        draw_lane_table(left, y, "Right Lane", right_rows)

    c.save()
