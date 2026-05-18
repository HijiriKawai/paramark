"""中間図形オブジェクトから SVG を生成する。"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .geometry import ArcTo, Circle, ClosePath, Group, LayeredGraphic, LineTo, MoveTo, Path as GraphicPath
from .geometry import Polygon, Polyline, Rectangle, RenderableGraphic, Style
from .metadata import MetadataDict
from .units import Millimeter


@dataclass(frozen=True, slots=True, kw_only=True)
class SvgDocument:
    """SVG 1 枚分のドキュメント。"""

    width_mm: Millimeter
    height_mm: Millimeter
    items: tuple[RenderableGraphic | LayeredGraphic, ...] = ()
    title: str | None = None
    description: str | None = None
    metadata: MetadataDict = field(default_factory=dict)
    view_box: tuple[float, float, float, float] | None = None


def _format_float(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def _mm(value: float) -> str:
    return f"{_format_float(value)}mm"


def _sanitize_data_key(key: str) -> str:
    sanitized = re.sub(r"[^a-z0-9_-]+", "-", key.lower()).strip("-")
    return sanitized or "value"


def _metadata_attributes(metadata: MetadataDict) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        name = f"data-meta-{_sanitize_data_key(key)}"
        if isinstance(value, (str, int, float, bool)):
            attributes[name] = str(value)
        else:
            attributes[name] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return attributes


def _style_attributes(style: Style | None) -> dict[str, str]:
    if style is None:
        return {}

    attributes: dict[str, str] = {}
    attributes["stroke"] = "none" if style.stroke is None else style.stroke
    attributes["fill"] = "none" if style.fill is None else style.fill

    if style.stroke_width_mm is not None:
        attributes["stroke-width"] = _mm(style.stroke_width_mm)
    if style.stroke_linecap:
        attributes["stroke-linecap"] = style.stroke_linecap
    if style.stroke_linejoin:
        attributes["stroke-linejoin"] = style.stroke_linejoin
    if style.fill_rule:
        attributes["fill-rule"] = style.fill_rule
    if style.opacity is not None:
        attributes["opacity"] = _format_float(style.opacity)
    return attributes


def _graphic_attributes(graphic: RenderableGraphic) -> dict[str, str]:
    attributes = _style_attributes(graphic.style)
    attributes.update(_metadata_attributes(graphic.metadata))
    if graphic.transform != graphic.transform.__class__():
        attributes["transform"] = graphic.transform.to_svg_matrix()
    return attributes


def _build_path_data(path: GraphicPath) -> str:
    parts: list[str] = []
    for command in path.commands:
        if isinstance(command, MoveTo):
            parts.append(f"M {_format_float(command.point.x_mm)} {_format_float(command.point.y_mm)}")
        elif isinstance(command, LineTo):
            parts.append(f"L {_format_float(command.point.x_mm)} {_format_float(command.point.y_mm)}")
        elif isinstance(command, ArcTo):
            large_arc = "1" if command.large_arc else "0"
            sweep = "1" if command.sweep else "0"
            parts.append(
                " ".join(
                    [
                        "A",
                        _format_float(command.radius_x_mm),
                        _format_float(command.radius_y_mm),
                        _format_float(command.rotation_deg),
                        large_arc,
                        sweep,
                        _format_float(command.end.x_mm),
                        _format_float(command.end.y_mm),
                    ]
                )
            )
        elif isinstance(command, ClosePath):
            parts.append("Z")
    return " ".join(parts)


def _append_graphic(parent: ET.Element, graphic: RenderableGraphic) -> None:
    if isinstance(graphic, Polyline):
        element = ET.SubElement(parent, "polyline", _graphic_attributes(graphic))
        element.set(
            "points",
            " ".join(f"{_format_float(point.x_mm)},{_format_float(point.y_mm)}" for point in graphic.points),
        )
        return

    if isinstance(graphic, Polygon):
        element = ET.SubElement(parent, "polygon", _graphic_attributes(graphic))
        element.set(
            "points",
            " ".join(f"{_format_float(point.x_mm)},{_format_float(point.y_mm)}" for point in graphic.points),
        )
        return

    if isinstance(graphic, Circle):
        element = ET.SubElement(parent, "circle", _graphic_attributes(graphic))
        element.set("cx", _format_float(graphic.center.x_mm))
        element.set("cy", _format_float(graphic.center.y_mm))
        element.set("r", _format_float(graphic.radius_mm))
        return

    if isinstance(graphic, Rectangle):
        element = ET.SubElement(parent, "rect", _graphic_attributes(graphic))
        element.set("x", _format_float(graphic.origin.x_mm))
        element.set("y", _format_float(graphic.origin.y_mm))
        element.set("width", _format_float(graphic.width_mm))
        element.set("height", _format_float(graphic.height_mm))
        if graphic.corner_radius_mm > 0:
            element.set("rx", _format_float(graphic.corner_radius_mm))
            element.set("ry", _format_float(graphic.corner_radius_mm))
        return

    if isinstance(graphic, GraphicPath):
        element = ET.SubElement(parent, "path", _graphic_attributes(graphic))
        element.set("d", _build_path_data(graphic))
        return

    if isinstance(graphic, Group):
        element = ET.SubElement(parent, "g", _graphic_attributes(graphic))
        for child in graphic.items:
            _append_graphic(element, child)
        return

    raise TypeError(f"未対応の graphic type です: {type(graphic)!r}")


def _append_item(parent: ET.Element, item: RenderableGraphic | LayeredGraphic) -> None:
    if isinstance(item, LayeredGraphic):
        group = ET.SubElement(parent, "g", _metadata_attributes(item.metadata))
        white_group = ET.SubElement(group, "g", {"data-layer": "white"})
        color_group = ET.SubElement(group, "g", {"data-layer": "color"})
        for graphic in item.white_layer:
            _append_graphic(white_group, graphic)
        for graphic in item.color_layer:
            _append_graphic(color_group, graphic)
        return

    _append_graphic(parent, item)


def render_svg_document(document: SvgDocument, *, pretty: bool = True) -> str:
    """SVG 文字列を生成する。"""

    attributes = {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": _mm(document.width_mm),
        "height": _mm(document.height_mm),
    }
    if document.view_box is None:
        attributes["viewBox"] = f"0 0 {_format_float(document.width_mm)} {_format_float(document.height_mm)}"
    else:
        x, y, width, height = document.view_box
        attributes["viewBox"] = " ".join(_format_float(value) for value in (x, y, width, height))

    root = ET.Element("svg", attributes)

    if document.title:
        title = ET.SubElement(root, "title")
        title.text = document.title
    if document.description:
        desc = ET.SubElement(root, "desc")
        desc.text = document.description
    if document.metadata:
        metadata = ET.SubElement(root, "metadata")
        metadata.text = json.dumps(document.metadata, ensure_ascii=False, indent=2, sort_keys=True)

    for item in document.items:
        _append_item(root, item)

    if pretty:
        ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


def save_svg(path: str | Path, document: SvgDocument, *, pretty: bool = True) -> Path:
    """SVG をファイルへ保存する。"""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_svg_document(document, pretty=pretty), encoding="utf-8")
    return output_path
