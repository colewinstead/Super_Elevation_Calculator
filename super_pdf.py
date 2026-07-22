from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
from typing import Iterable
from xml.sax.saxutils import escape

import Super
from app_info import APP_VERSION
from criteria_info import applicable_drawings_label, calculation_sources_label, criteria_for_result
from super_lane import build_lane_rows


CHARCOAL = "#263238"
INK = "#1F2933"
MUTED = "#5F6B73"
LIGHT_GRAY = "#F2F4F5"
MID_GRAY = "#D5DADD"
ORANGE = "#D96521"
ORANGE_TINT = "#FFF2E8"
WHITE = "#FFFFFF"


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
    profile_id = str(((results.get("calculation_metadata", {}) or {}).get("criteria", {}) or {}).get("profile_id", ""))
    if profile_id.startswith("tdot"):
        return []
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


def _text(value: object, fallback: str = "Not provided") -> str:
    rendered = str(value).strip() if value is not None else ""
    return escape(rendered or fallback)


def _number(value: object, digits: int = 2, suffix: str = "") -> str:
    try:
        return f"{float(value):,.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return "Not provided"


def _station(results: dict, value: object) -> str:
    if value is None:
        return "Not provided"
    return Super.format_result_station(results, float(value), True)


def _curve_status(results: dict) -> str:
    if results.get("warnings"):
        return "Review"
    overrides = ((results.get("calculation_metadata", {}) or {}).get("manual_overrides", {}) or {}).values()
    if any(overrides):
        return "Override"
    if results.get("normal_crown_only"):
        return "Normal crown"
    return "Calculated"


def _shared_meta(curves: list[dict], key: str) -> str:
    values = {
        str((curve.get("meta", {}) or {}).get(key, "")).strip()
        for curve in curves
        if str((curve.get("meta", {}) or {}).get(key, "")).strip()
    }
    if not values:
        return "Not provided"
    if len(values) > 1:
        return "Mixed - see curve index"
    return values.pop()


def export_pdf(path: str, curves: Iterable[dict]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import (
        BaseDocTemplate,
        Flowable,
        Frame,
        Image,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    class ContextMarker(Flowable):
        """Record the footer context for the current page without consuming space."""

        def __init__(self, context: str) -> None:
            super().__init__()
            self.context = context

        def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
            return 0, 0

        def draw(self) -> None:
            self.canv._report_context = self.context

    class NumberedCanvas(Canvas):
        def __init__(self, *args: object, report_info: dict[str, str], **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._saved_page_states: list[dict] = []
            self._report_info = report_info
            self._report_context = "Report summary"
            self.setPageCompression(0)
            self.setTitle(f"Superelevation Calculation Report - Application {APP_VERSION}")
            self.setAuthor("Superelevation Calculator")
            self.setSubject("Superelevation calculation report with project summary, criteria, and curve details")
            self.setKeywords(
                f"application={APP_VERSION}; calculation_engines={report_info['engines']}; criteria={report_info['criteria']}"
            )

        def showPage(self) -> None:
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            page_count = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_footer(page_count)
                Canvas.showPage(self)
            Canvas.save(self)

        def _draw_footer(self, page_count: int) -> None:
            page_width, page_height = self._pagesize
            self.saveState()
            self.setFillColor(HexColor(ORANGE))
            self.rect(0, page_height - 0.11 * inch, page_width, 0.11 * inch, fill=1, stroke=0)
            self.setFillColor(HexColor(MUTED))
            self.setFont("Helvetica-Bold", 6.7)
            self.drawString(0.58 * inch, page_height - 0.42 * inch, "SUPERELEVATION CALCULATION REPORT")
            self.setFont("Helvetica", 6.7)
            self.drawRightString(page_width - 0.58 * inch, page_height - 0.42 * inch, self._report_info["project"])
            self.setStrokeColor(HexColor(MID_GRAY))
            self.setLineWidth(0.5)
            self.line(0.58 * inch, 0.48 * inch, page_width - 0.58 * inch, 0.48 * inch)
            self.setFillColor(HexColor(MUTED))
            self.setFont("Helvetica", 6.5)
            project_route = f"{self._report_info['project']} | {self._report_info['route']}"
            if len(project_route) > 58:
                project_route = f"{project_route[:55]}..."
            self.drawString(0.58 * inch, 0.3 * inch, project_route)
            context = str(getattr(self, "_report_context", "Report summary"))
            if len(context) > 52:
                context = f"{context[:49]}..."
            self.drawCentredString(page_width / 2, 0.3 * inch, context)
            self.drawRightString(page_width - 0.58 * inch, 0.3 * inch, f"Page {self._pageNumber} of {page_count}")
            self.restoreState()

    curve_list = list(curves)
    diagram_b64, _ = _asset_constants()
    diagram_bytes = _decode_asset(diagram_b64)
    stamps = stamp_images()

    engine_versions = sorted(
        {
            str((curve.get("results") or {}).get("calculation_metadata", {}).get("engine_version") or "legacy-unversioned")
            for curve in curve_list
        }
    ) or ["legacy-unversioned"]
    criteria_ids = sorted(
        {
            str(criteria_for_result(curve.get("results") or {}).get("profile_id") or "legacy-unversioned")
            for curve in curve_list
        }
    ) or ["legacy-unversioned"]
    report_info = {"engines": ", ".join(engine_versions), "criteria": ", ".join(criteria_ids)}

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=27, textColor=HexColor(INK), spaceAfter=8, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=HexColor(MUTED), spaceAfter=14))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=HexColor(INK), spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="CurveTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=HexColor(INK), spaceAfter=3))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontName="Helvetica", fontSize=7.2, leading=9.2, textColor=HexColor(INK)))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Small"], textColor=HexColor(MUTED)))
    styles.add(ParagraphStyle(name="Tiny", parent=styles["Normal"], fontName="Helvetica", fontSize=6.3, leading=8, textColor=HexColor(MUTED)))
    styles.add(ParagraphStyle(name="TableHeader", parent=styles["Small"], fontName="Helvetica-Bold", textColor=HexColor(WHITE), alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="TableHeaderRight", parent=styles["TableHeader"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="TableCell", parent=styles["Small"], alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="TableCellRight", parent=styles["Small"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="LaneHeader", parent=styles["TableHeader"], fontSize=6.4, leading=7.2))
    styles.add(ParagraphStyle(name="LaneHeaderRight", parent=styles["LaneHeader"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="LaneCell", parent=styles["TableCell"], fontSize=6.4, leading=7.5))
    styles.add(ParagraphStyle(name="LaneCellRight", parent=styles["LaneCell"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="KpiLabel", parent=styles["Tiny"], fontName="Helvetica-Bold", textColor=HexColor(MUTED), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="KpiValue", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=HexColor(INK), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="AgencyBadge", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=HexColor(WHITE), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="AgencyDetail", parent=styles["Small"], leading=10))
    styles.add(ParagraphStyle(name="Alert", parent=styles["Small"], fontName="Helvetica-Bold", textColor=HexColor(INK)))
    styles.add(ParagraphStyle(name="Provenance", parent=styles["Tiny"], backColor=HexColor(LIGHT_GRAY), borderColor=HexColor(MID_GRAY), borderWidth=0.5, borderPadding=6, spaceBefore=5))

    width, height = letter
    margin = 0.58 * inch
    top_margin = 0.7 * inch
    bottom_margin = 0.58 * inch
    document = BaseDocTemplate(
        path,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title=f"Superelevation Calculation Report - Application {APP_VERSION}",
        author="Superelevation Calculator",
        subject="Superelevation calculation report with project summary, criteria, and curve details",
        keywords=f"application={APP_VERSION}; calculation_engines={report_info['engines']}; criteria={report_info['criteria']}",
    )

    report_info["project"] = _shared_meta(curve_list, "project_name")
    report_info["route"] = _shared_meta(curve_list, "route_name")

    frame = Frame(margin, bottom_margin, width - 2 * margin, height - top_margin - bottom_margin, id="report-frame", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates([PageTemplate(id="report", frames=[frame])])

    story: list[object] = [ContextMarker("Report summary")]

    story.extend(
        [
            Spacer(1, 0.2 * inch),
            Paragraph("Superelevation Calculation Report", styles["ReportTitle"]),
            Paragraph("Project summary and curve-by-curve transition review", styles["ReportSubtitle"]),
        ]
    )

    summary_data = [
        [Paragraph("PROJECT", styles["Tiny"]), Paragraph("ROUTE", styles["Tiny"]), Paragraph("ALIGNMENT", styles["Tiny"]), Paragraph("CURVES", styles["Tiny"])],
        [Paragraph(_text(_shared_meta(curve_list, "project_name")), styles["KpiValue"]), Paragraph(_text(_shared_meta(curve_list, "route_name")), styles["KpiValue"]), Paragraph(_text(_shared_meta(curve_list, "alignment_name")), styles["KpiValue"]), Paragraph(str(len(curve_list)), styles["KpiValue"])],
    ]
    summary = Table(summary_data, colWidths=[1.85 * inch, 1.7 * inch, 2.25 * inch, 0.95 * inch], rowHeights=[0.24 * inch, 0.52 * inch])
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(LIGHT_GRAY)),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor(INK)),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(MID_GRAY)),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, HexColor(MID_GRAY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([summary, Spacer(1, 0.2 * inch)])

    report_criteria = [criteria_for_result(curve.get("results") or {}) for curve in curve_list]
    agency_codes = sorted(
        {
            str(criteria.get("profile_id") or "legacy").split("-", 1)[0].upper()
            for criteria in report_criteria
        }
    ) or ["LEGACY"]
    agency_names = sorted(
        {
            str(criteria.get("governing_authority") or "Governing agency not recorded")
            for criteria in report_criteria
        }
    ) or ["Governing agency not recorded"]
    profile_names = sorted(
        {str(criteria.get("profile_name") or "Legacy criteria") for criteria in report_criteria}
    ) or ["Legacy criteria"]
    drawing_labels = sorted(
        {
            applicable_drawings_label(criteria)
            for criteria in report_criteria
            if applicable_drawings_label(criteria)
        }
    ) or ["No standard drawing identified"]
    agency_badge = agency_codes[0] if len(agency_codes) == 1 else "MULTI-DOT"
    governing_detail = (
        f"<b>{_text(' / '.join(agency_names))}</b><br/>"
        f"{_text(' / '.join(profile_names))}<br/>"
        f"<font color='{MUTED}'>Applicable standards: {_text(' / '.join(drawing_labels))}</font>"
    )
    governing_standard = Table(
        [[Paragraph(_text(agency_badge), styles["AgencyBadge"]), Paragraph(governing_detail, styles["AgencyDetail"])]],
        colWidths=[1.25 * inch, 5.5 * inch],
    )
    governing_standard.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), HexColor(CHARCOAL)),
        ("BACKGROUND", (1, 0), (1, 0), HexColor(LIGHT_GRAY)),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(MID_GRAY)),
        ("LINEABOVE", (0, 0), (-1, 0), 2.5, HexColor(ORANGE)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([Paragraph("Governing standard", styles["Section"]), governing_standard, Spacer(1, 0.14 * inch), Paragraph("Curve index", styles["Section"])])

    index_headers = ["#", "Curve", "Direction", "PC - PT", "Speed", "Radius", "e", "Status"]
    index_data = [[Paragraph(header, styles["TableHeaderRight"] if header in {"Speed", "Radius", "e"} else styles["TableHeader"]) for header in index_headers]]
    for index, curve in enumerate(curve_list, start=1):
        results = curve.get("results", {}) or {}
        inputs = results.get("inputs", {}) or {}
        meta = curve.get("meta", {}) or {}
        index_data.append([
            Paragraph(str(index), styles["TableCell"]),
            Paragraph(_text(meta.get("curve_name")), styles["TableCell"]),
            Paragraph(_text(meta.get("curve_direction", "left")).title(), styles["TableCell"]),
            Paragraph(f"{_text(inputs.get('pc'))} - {_text(inputs.get('pt'), 'N/A')}", styles["TableCell"]),
            Paragraph(_number(inputs.get("speed_mph"), 0, " mph"), styles["TableCellRight"]),
            Paragraph(_number(inputs.get("radius_ft"), 0, " ft"), styles["TableCellRight"]),
            Paragraph(_number(results.get("e"), 4), styles["TableCellRight"]),
            Paragraph(_curve_status(results), styles["TableCell"]),
        ])
    if not curve_list:
        index_data.append([Paragraph("No calculated curves are available.", styles["TableCell"])] + [""] * 7)
    curve_index = Table(index_data, colWidths=[0.3 * inch, 1.0 * inch, 0.65 * inch, 1.65 * inch, 0.7 * inch, 0.78 * inch, 0.62 * inch, 1.05 * inch], repeatRows=1)
    index_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(CHARCOAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(WHITE)),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(MID_GRAY)),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor(MID_GRAY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index in range(1, len(index_data)):
        index_style.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.white if row_index % 2 else HexColor(LIGHT_GRAY)))
    curve_index.setStyle(TableStyle(index_style))
    story.append(curve_index)

    def key_value_table(rows: list[tuple[str, str]], width_value: float = 2.15 * inch) -> object:
        data = [[Paragraph(_text(label), styles["Tiny"]), Paragraph(value, styles["Small"])] for label, value in rows]
        table = Table(data, colWidths=[1.15 * inch, width_value])
        commands = [
            ("BACKGROUND", (0, 0), (0, -1), HexColor(LIGHT_GRAY)),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor(MID_GRAY)),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor(MID_GRAY)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        table.setStyle(TableStyle(commands))
        return table

    def lane_table(title: str, rows: list[dict]) -> object:
        data = [
            [Paragraph(title.upper(), styles["LaneHeader"]), "", "", ""],
            [Paragraph("POINT", styles["LaneHeader"]), Paragraph("STATION", styles["LaneHeader"]), Paragraph("SLOPE", styles["LaneHeaderRight"]), Paragraph("NOTE", styles["LaneHeader"])],
        ]
        for row in rows:
            data.append([
                Paragraph(_text(row.get("label")), styles["LaneCell"]),
                Paragraph(_text(row.get("station")), styles["LaneCell"]),
                Paragraph(_text(row.get("slope")), styles["LaneCellRight"]),
                Paragraph(_text(row.get("note")), styles["LaneCell"]),
            ])
        table = Table(data, colWidths=[0.55 * inch, 0.9 * inch, 0.55 * inch, 1.25 * inch], repeatRows=2, splitByRow=1)
        commands = [
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 1), HexColor(CHARCOAL)),
            ("TEXTCOLOR", (0, 0), (-1, 1), HexColor(WHITE)),
            ("BOX", (0, 0), (-1, -1), 0.6, HexColor(MID_GRAY)),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor(MID_GRAY)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for row_index in range(2, len(data)):
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.white if row_index % 2 else HexColor(LIGHT_GRAY)))
        table.setStyle(TableStyle(commands))
        return table

    for curve_index_number, curve in enumerate(curve_list, start=1):
        results = curve.get("results", {}) or {}
        inputs = results.get("inputs", {}) or {}
        segments = results.get("segments", {}) or {}
        meta = curve.get("meta", {}) or {}
        criteria = criteria_for_result(results)
        profile_id = str(criteria.get("profile_id") or "legacy-unversioned")
        profile_name = str(criteria.get("profile_name") or "Legacy criteria")
        curve_name = str(meta.get("curve_name") or f"Curve {curve_index_number}")

        story.extend([
            PageBreak(),
            ContextMarker(f"Curve {curve_index_number:02d} | {profile_name}"),
            Paragraph(f"Curve {curve_index_number:02d} / {_text(curve_name)}", styles["CurveTitle"]),
            Paragraph(
                f"{_text(meta.get('route_name'))} | {_text(meta.get('alignment_name'))} | {_text(meta.get('curve_direction', 'left')).title()} curve",
                styles["ReportSubtitle"],
            ),
        ])

        kpis = [
            ("SUPERELEVATION RATE", f"{_number(results.get('e'), 4)} ft/ft"),
            ("RUNOFF LENGTH", _number(results.get("Lr"), 2, " ft")),
            ("TANGENT RUNOUT", _number(results.get("Lt"), 2, " ft")),
            ("TOTAL TRANSITION", _number(segments.get("total_transition"), 2, " ft")),
        ]
        kpi_data = [[Paragraph(label, styles["KpiLabel"]) for label, _ in kpis], [Paragraph(value, styles["KpiValue"]) for _, value in kpis]]
        kpi_table = Table(kpi_data, colWidths=[1.69 * inch] * 4, rowHeights=[0.27 * inch, 0.47 * inch])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(LIGHT_GRAY)),
            ("BOX", (0, 0), (-1, -1), 0.7, HexColor(MID_GRAY)),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, HexColor(MID_GRAY)),
            ("LINEABOVE", (0, 0), (-1, 0), 2.5, HexColor(ORANGE)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.extend([kpi_table, Spacer(1, 0.12 * inch)])

        warnings = [str(value) for value in (results.get("warnings", []) or []) if value]
        if results.get("normal_crown_only"):
            warnings.insert(0, "Normal crown is maintained; no superelevation transition is required.")
        if warnings:
            alert_text = "<br/>".join(f"- {_text(value)}" for value in warnings)
            alert = Table([[Paragraph(f"REVIEW NOTICE<br/>{alert_text}", styles["Alert"])]], colWidths=[6.75 * inch])
            alert.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor(ORANGE_TINT)),
                ("BOX", (0, 0), (-1, -1), 0.8, HexColor(ORANGE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.extend([alert, Spacer(1, 0.1 * inch)])

        input_rows = [
            ("PC station", _text(inputs.get("pc"))),
            ("PT station", _text(inputs.get("pt"), "N/A")),
            ("Design speed", _number(inputs.get("speed_mph"), 0, " mph")),
            ("Curve radius", _number(inputs.get("radius_ft"), 2, " ft")),
            ("Facility / area", f"{_text(inputs.get('facility'))} / {_text(inputs.get('area_type'))}"),
            ("Lane configuration", f"{_number(inputs.get('lane_width_ft'), 2, ' ft')} / {_number(inputs.get('lanes_rotated'), 0, ' rotated')}"),
            ("Rate source", _text(results.get("e_source"))),
        ]

        if results.get("normal_crown_only"):
            station_rows = [("Normal crown begins", _station(results, results.get("reverse_crown_ft"))), ("Normal crown ends", _station(results, results.get("pt_ft")))]
        elif results.get("transition_method") == "tdot_simple_curve_half_total":
            station_rows = [
                ("Start normal crown", _station(results, results.get("pnc_ft"))),
                ("Zero crown / start runoff", _station(results, results.get("zero_crown_ft"))),
                ("Reverse-crown section", _station(results, results.get("reverse_section_ft"))),
                ("Full super near PC", _station(results, results.get("full_super_ft"))),
                ("Full super near PT", _station(results, results.get("full_super_out_ft"))),
                ("Zero crown / end runoff", _station(results, results.get("zero_crown_out_ft"))),
                ("Normal crown restored", _station(results, results.get("pnc_out_ft"))),
            ]
        else:
            station_rows = []
            if results.get("reverse_curve_entry_zero_ft") is not None:
                station_rows.extend([
                    ("Shared reverse-curve 0% meeting", _station(results, results.get("reverse_curve_entry_zero_ft"))),
                    ("Full super after PC (PC + 0.3Lr)", _station(results, results.get("full_super_ft"))),
                ])
            else:
                station_rows.extend([
                    ("Point of normal crown", _station(results, results.get("pnc_ft"))),
                    ("Point of reverse crown", _station(results, results.get("reverse_crown_ft"))),
                    ("Full super near PC", _station(results, results.get("full_super_ft"))),
                ])
            if results.get("reverse_curve_exit_zero_ft") is not None:
                station_rows.extend([
                    ("Full super before PT (PT - 0.3Lr)", _station(results, results.get("full_super_out_ft"))),
                    ("Shared reverse-curve 0% meeting", _station(results, results.get("reverse_curve_exit_zero_ft"))),
                ])
            else:
                station_rows.extend([
                    ("Full super near PT", _station(results, results.get("full_super_out_ft"))),
                    ("Reverse crown out", _station(results, results.get("reverse_crown_out_ft"))),
                    ("Normal crown out", _station(results, results.get("pnc_out_ft"))),
                ])

            coordination = results.get("reverse_curve_coordination", {}) or {}
            if coordination.get("checks"):
                check = coordination["checks"][0]
                station_rows.extend([
                    ("Available reverse-curve tangent", _number(check.get("available_tangent_ft"), 2, " ft")),
                    ("Minimum reverse-curve tangent", _number(check.get("minimum_tangent_ft"), 2, " ft")),
                    ("Transition-rate status", _text(check.get("transition_rate_status", "standard")).replace("_", " ")),
                    ("Reverse-curve rule", _text(check.get("rule"))),
                ])

        note_parts = [
            results.get("friction_note"),
            results.get("rel_grad_note"),
            results.get("lanes_note"),
            results.get("r_note"),
            results.get("e_note"),
            results.get("runoff_note"),
            results.get("extra_width_note"),
        ]
        calculation_notes = "; ".join(str(part) for part in note_parts if part)
        curve_notes = str(curve.get("notes") or "").strip()
        notes_in_reference = len(calculation_notes) + len(curve_notes) <= 1_200

        left_column = [Paragraph("Inputs", styles["Section"]), key_value_table(input_rows), Paragraph("Station references", styles["Section"]), key_value_table(station_rows)]
        reference_elements: list[object] = [Paragraph("Criteria reference", styles["Section"])]
        reference_elements.append(Paragraph(f"<b>Applicable:</b> {_text(applicable_drawings_label(criteria))}", styles["Small"]))
        reference_elements.append(Spacer(1, 0.05 * inch))
        reference_elements.append(Paragraph(f"<b>Sources:</b> {_text(calculation_sources_label(criteria))}", styles["Tiny"]))
        is_tdot = profile_id.startswith("tdot")
        if diagram_bytes and not is_tdot:
            reference_elements.extend([Spacer(1, 0.08 * inch), Image(io.BytesIO(diagram_bytes), width=2.25 * inch, height=1.18 * inch, kind="proportional")])
        for stamp_key in select_stamps(results):
            asset = stamps.get(stamp_key)
            if asset:
                reference_elements.extend([Spacer(1, 0.05 * inch), Paragraph(f"Reference sheet {stamp_key}", styles["Tiny"]), Image(io.BytesIO(asset), width=1.48 * inch, height=0.55 * inch, kind="proportional")])
        if is_tdot:
            reference_elements.extend([Spacer(1, 0.12 * inch), Paragraph("TDOT criteria pages intentionally omit MDOT reference artwork.", styles["SmallMuted"])])
        if notes_in_reference:
            reference_elements.extend([
                Spacer(1, 0.12 * inch),
                Paragraph("<b>Notes and provenance</b>", styles["Small"]),
                Spacer(1, 0.04 * inch),
                Paragraph(f"<b>Calculation:</b> {_text(calculation_notes)}", styles["Tiny"]),
                Spacer(1, 0.03 * inch),
                Paragraph(f"<b>Curve:</b> {_text(curve_notes)}", styles["Tiny"]),
                Spacer(1, 0.03 * inch),
                Paragraph(f"<b>Design standard:</b> {_text(profile_name)}", styles["Tiny"]),
            ])

        detail_columns = Table([[left_column, reference_elements]], colWidths=[3.55 * inch, 3.05 * inch], hAlign="LEFT")
        detail_columns.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("LINEBEFORE", (1, 0), (1, 0), 0.6, HexColor(MID_GRAY)),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.extend([detail_columns, Spacer(1, 0.08 * inch)])

        left_rows, right_rows = build_lane_rows(results, meta.get("curve_direction", "left"), True)
        lane_columns = Table(
            [[lane_table("Left lane", left_rows), lane_table("Right lane", right_rows)]],
            colWidths=[3.3 * inch, 3.3 * inch],
            hAlign="LEFT",
        )
        lane_columns.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 4),
            ("LEFTPADDING", (1, 0), (1, 0), 4),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.extend([Paragraph("Lane transitions", styles["Section"]), lane_columns])

        if not notes_in_reference:
            provenance_text = (
                f"<b>NOTES AND PROVENANCE</b><br/>"
                f"<b>Calculation:</b> {_text(calculation_notes)}<br/>"
                f"<b>Curve:</b> {_text(curve_notes)}<br/>"
                f"<b>Design standard:</b> {_text(profile_name)}"
            )
            story.append(Paragraph(provenance_text, styles["Provenance"]))

    def canvas_factory(*args: object, **kwargs: object) -> NumberedCanvas:
        return NumberedCanvas(*args, report_info=report_info, **kwargs)

    document.build(story, canvasmaker=canvas_factory)
