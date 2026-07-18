from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import Super


NS = {"lx": "http://www.landxml.org/schema/LandXML-1.2"}


def _parse_point(text: str) -> tuple[float, float]:
    values = [float(value) for value in text.split()]
    # LandXML stores horizontal coordinates as Northing, Easting. DXF/CAD
    # expects X=Easting and Y=Northing, so swap at the import boundary.
    return values[1], values[0]


def _normalized_angle(value: float) -> float:
    while value < 0:
        value += math.tau
    while value >= math.tau:
        value -= math.tau
    return value


@dataclass(frozen=True)
class LineSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    length: float


@dataclass(frozen=True)
class ArcSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    center: tuple[float, float]
    radius: float
    length: float
    rotation: str


@dataclass
class LandXMLData:
    path: Path
    alignment_name: str
    start_station: float
    alignment_length: float
    linear_unit: str
    lines: list[LineSegment]
    curves: list[ArcSegment]
    spirals: list[dict]
    station_equations: list[dict]
    superelevation_nodes: list[dict]
    coordinate_system: str | None
    warnings: list[str]
    _segments: list[LineSegment | ArcSegment]

    def station_range(self) -> tuple[float, float]:
        return self.start_station, self.start_station + sum(segment.length for segment in self._segments)

    def _arc_sweep_sign(self, segment: ArcSegment) -> int:
        expected = segment.length / segment.radius if segment.radius else 0.0
        start_angle = math.atan2(segment.start[1] - segment.center[1], segment.start[0] - segment.center[0])
        end_angle = math.atan2(segment.end[1] - segment.center[1], segment.end[0] - segment.center[0])
        ccw = _normalized_angle(end_angle - start_angle)
        cw = _normalized_angle(start_angle - end_angle)
        return 1 if abs(ccw - expected) <= abs(cw - expected) else -1

    def validate_station(self, station: float) -> None:
        start, end = self.station_range()
        if station < start or station > end:
            raise ValueError(f"Station {station:.3f} is outside alignment limits {start:.3f} to {end:.3f}.")

    def xy_at_station(self, station: float) -> tuple[float, float]:
        self.validate_station(station)
        remaining = station - self.start_station
        for segment in self._segments:
            if remaining <= segment.length + 1e-9:
                if isinstance(segment, LineSegment):
                    ratio = 0.0 if segment.length == 0 else remaining / segment.length
                    x = segment.start[0] + (segment.end[0] - segment.start[0]) * ratio
                    y = segment.start[1] + (segment.end[1] - segment.start[1]) * ratio
                    return x, y
                angle = remaining / segment.radius
                start_angle = math.atan2(segment.start[1] - segment.center[1], segment.start[0] - segment.center[0])
                current_angle = start_angle + (self._arc_sweep_sign(segment) * angle)
                x = segment.center[0] + segment.radius * math.cos(current_angle)
                y = segment.center[1] + segment.radius * math.sin(current_angle)
                return x, y
            remaining -= segment.length
        last = self._segments[-1]
        return last.end if isinstance(last, LineSegment) else last.end

    def tangent_at_station(self, station: float) -> tuple[float, float]:
        self.validate_station(station)
        remaining = station - self.start_station
        for segment in self._segments:
            if remaining <= segment.length + 1e-9:
                if isinstance(segment, LineSegment):
                    dx = segment.end[0] - segment.start[0]
                    dy = segment.end[1] - segment.start[1]
                    length = math.hypot(dx, dy) or 1.0
                    return dx / length, dy / length
                angle = remaining / segment.radius
                start_angle = math.atan2(segment.start[1] - segment.center[1], segment.start[0] - segment.center[0])
                sign = self._arc_sweep_sign(segment)
                current_angle = start_angle + (sign * angle)
                if sign < 0:
                    return math.sin(current_angle), -math.cos(current_angle)
                return -math.sin(current_angle), math.cos(current_angle)
            remaining -= segment.length
        last = self._segments[-1]
        if isinstance(last, LineSegment):
            dx = last.end[0] - last.start[0]
            dy = last.end[1] - last.start[1]
            length = math.hypot(dx, dy) or 1.0
            return dx / length, dy / length
        return self.tangent_at_station(self.station_range()[1] - 0.001)

    def curve_records(self) -> list[dict]:
        records: list[dict] = []
        station = self.start_station
        curve_index = 1
        for segment in self._segments:
            if isinstance(segment, LineSegment):
                station += segment.length
                continue
            pc_station = station
            pt_station = station + segment.length
            # Infer turn direction along increasing station after converting
            # LandXML Northing/Easting to CAD X/Y.
            direction = "left" if self._arc_sweep_sign(segment) > 0 else "right"
            records.append(
                {
                    "alignment_name": self.alignment_name or "Unnamed alignment",
                    "curve_name": f"Curve {curve_index}",
                    "curve_direction": direction,
                    "pc_station_ft": pc_station,
                    "pc_station_label": Super.format_station(Super.internal_to_civil_station(pc_station, self.station_equations), True),
                    "pt_station_ft": pt_station,
                    "pt_station_label": Super.format_station(Super.internal_to_civil_station(pt_station, self.station_equations), True),
                    # LandXML commonly serializes exact design radii with
                    # floating-point noise (for example 3499.9999999999995).
                    # Use the intended three-decimal design value for lookup
                    # calculations while retaining segment.radius for geometry.
                    "radius_ft": round(segment.radius, 3),
                    "curve_length_ft": segment.length,
                    "rotation": segment.rotation,
                    "station_equations": self.station_equations,
                    "alignment_station_range": self.station_range(),
                }
            )
            curve_index += 1
            station = pt_station
        return records


def _parse_landxml_root(root: ET.Element, source_name: str) -> LandXMLData:
    file_path = Path(source_name)

    alignment = root.find(".//lx:Alignment", NS)
    if alignment is None:
        raise ValueError("No Alignment node found in LandXML.")

    coord_geom = alignment.find("lx:CoordGeom", NS)
    if coord_geom is None:
        raise ValueError("Alignment has no CoordGeom definition.")

    units_node = root.find(".//lx:Units/lx:Imperial", NS)
    if units_node is None:
        units_node = root.find(".//lx:Units/lx:Metric", NS)
    linear_unit = units_node.get("linearUnit", "") if units_node is not None else ""
    warnings: list[str] = []
    if not linear_unit:
        warnings.append("LandXML does not declare linear units.")

    lines: list[LineSegment] = []
    curves: list[ArcSegment] = []
    segments: list[LineSegment | ArcSegment] = []
    spirals = []

    for child in list(coord_geom):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "Line":
            line = LineSegment(
                start=_parse_point(child.findtext("lx:Start", namespaces=NS, default="0 0 0")),
                end=_parse_point(child.findtext("lx:End", namespaces=NS, default="0 0 0")),
                length=float(child.get("length", "0") or 0.0),
            )
            lines.append(line)
            segments.append(line)
        elif tag == "Curve":
            curve = ArcSegment(
                start=_parse_point(child.findtext("lx:Start", namespaces=NS, default="0 0 0")),
                end=_parse_point(child.findtext("lx:End", namespaces=NS, default="0 0 0")),
                center=_parse_point(child.findtext("lx:Center", namespaces=NS, default="0 0 0")),
                radius=float(child.get("radius", "0") or 0.0),
                length=float(child.get("length", "0") or 0.0),
                rotation=str(child.get("rot", "ccw") or "ccw"),
            )
            curves.append(curve)
            segments.append(curve)
        elif tag == "Spiral":
            spirals.append(dict(child.attrib))
            warnings.append("Spiral geometry found; overlay export currently supports only lines and circular arcs.")

    station_equations = [dict(node.attrib) for node in alignment.findall("lx:StaEquation", NS)]
    if station_equations:
        warnings.append("Station equations found; displayed civil stationing will be applied to inputs and export labels.")

    superelevation_nodes = [dict(node.attrib) for node in root.findall(".//lx:Superelevation", NS)]
    coordinate_system = None
    for candidate in root.findall(".//lx:CoordinateSystem", NS):
        coordinate_system = ET.tostring(candidate, encoding="unicode")
        break

    return LandXMLData(
        path=file_path,
        alignment_name=str(alignment.get("name", "") or ""),
        start_station=float(alignment.get("staStart", "0") or 0.0),
        alignment_length=float(alignment.get("length", "0") or 0.0),
        linear_unit=linear_unit,
        lines=lines,
        curves=curves,
        spirals=spirals,
        station_equations=station_equations,
        superelevation_nodes=superelevation_nodes,
        coordinate_system=coordinate_system,
        warnings=warnings,
        _segments=segments,
    )


def parse_landxml_text(content: str, source_name: str = "alignment.xml") -> LandXMLData:
    """Parse LandXML already held in memory, as required by browser clients."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError(f"The LandXML is not valid XML (line {exc.position[0]}, column {exc.position[1]}).") from exc
    return _parse_landxml_root(root, source_name)


def load_landxml(path: str | Path) -> LandXMLData:
    file_path = Path(path)
    try:
        tree = ET.parse(file_path)
    except ET.ParseError as exc:
        raise ValueError(f"The LandXML is not valid XML (line {exc.position[0]}, column {exc.position[1]}).") from exc
    return _parse_landxml_root(tree.getroot(), str(file_path))
