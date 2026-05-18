"""PDF export の共通実装。"""

from __future__ import annotations

import argparse
from math import atan2, ceil, cos, pi, sin, sqrt
from pathlib import Path
from types import ModuleType

from core import SvgDocument
from core.geometry import (
    ArcTo,
    Circle,
    ClosePath,
    GraphicObject,
    Group,
    LayeredGraphic,
    LineTo,
    MoveTo,
    Path as GraphicPath,
    Point,
    Polygon,
    Polyline,
    Rectangle,
    RenderableGraphic,
    Style,
)

from .export_svg import DEFAULT_OUTPUT_DIR, ExportJobSpec, ExportResult, extract_job_spec, render_export_document

MM_TO_PT = 72.0 / 25.4
KAPPA = 4.0 * (sqrt(2.0) - 1.0) / 3.0
LINECAP_MAP = {"butt": 0, "round": 1, "square": 2}
LINEJOIN_MAP = {"miter": 0, "round": 1, "bevel": 2}
NAMED_COLORS = {
    "black": (0.0, 0.0, 0.0),
    "white": (1.0, 1.0, 1.0),
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 1.0, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "gray": (0.5, 0.5, 0.5),
    "grey": (0.5, 0.5, 0.5),
}


def _format_number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def _format_color_triplet(color: tuple[float, float, float]) -> str:
    return " ".join(_format_number(component) for component in color)


def _parse_color(color: str) -> tuple[float, float, float]:
    normalized = color.strip().lower()
    if normalized in NAMED_COLORS:
        return NAMED_COLORS[normalized]
    if normalized.startswith("#"):
        hex_value = normalized[1:]
        if len(hex_value) == 3:
            hex_value = "".join(char * 2 for char in hex_value)
        if len(hex_value) != 6:
            raise ValueError(f"未対応の色指定です: {color}")
        return tuple(int(hex_value[index : index + 2], 16) / 255.0 for index in (0, 2, 4))
    raise ValueError(f"未対応の色指定です: {color}")


def _pdf_text_string(value: str) -> str:
    encoded = ("\ufeff" + value).encode("utf-16-be").hex().upper()
    return f"<{encoded}>"


def _is_identity_transform(graphic: GraphicObject) -> bool:
    transform = graphic.transform
    return (
        transform.a == 1.0
        and transform.b == 0.0
        and transform.c == 0.0
        and transform.d == 1.0
        and transform.e == 0.0
        and transform.f == 0.0
    )


def _style_has_stroke(style: Style | None) -> bool:
    return style is not None and style.stroke not in (None, "none")


def _style_has_fill(style: Style | None) -> bool:
    return style is not None and style.fill not in (None, "none")


def _collect_opacity_values_from_item(item: RenderableGraphic | LayeredGraphic) -> set[float]:
    values: set[float] = set()
    if isinstance(item, LayeredGraphic):
        for graphic in item.white_layer:
            values.update(_collect_opacity_values_from_item(graphic))
        for graphic in item.color_layer:
            values.update(_collect_opacity_values_from_item(graphic))
        return values

    if isinstance(item, Group):
        if item.style and item.style.opacity is not None:
            values.add(float(item.style.opacity))
        for graphic in item.items:
            values.update(_collect_opacity_values_from_item(graphic))
        return values

    if item.style and item.style.opacity is not None:
        values.add(float(item.style.opacity))
    return values


def _collect_opacity_names(document_items: tuple[RenderableGraphic | LayeredGraphic, ...]) -> dict[float, str]:
    opacities: set[float] = set()
    for item in document_items:
        opacities.update(_collect_opacity_values_from_item(item))
    return {value: f"GS{index}" for index, value in enumerate(sorted(opacities), start=1)}


def _append_transform_commands(commands: list[str], graphic: GraphicObject) -> None:
    if _is_identity_transform(graphic):
        return
    transform = graphic.transform
    commands.append(
        " ".join(
            [
                _format_number(transform.a),
                _format_number(transform.b),
                _format_number(transform.c),
                _format_number(transform.d),
                _format_number(transform.e),
                _format_number(transform.f),
                "cm",
            ]
        )
    )


def _append_style_commands(commands: list[str], style: Style | None, opacity_names: dict[float, str]) -> None:
    if style is None:
        return

    if style.opacity is not None:
        commands.append(f"/{opacity_names[float(style.opacity)]} gs")
    if _style_has_stroke(style):
        commands.append(f"{_format_color_triplet(_parse_color(style.stroke or '#000000'))} RG")
    if _style_has_fill(style):
        commands.append(f"{_format_color_triplet(_parse_color(style.fill or '#000000'))} rg")
    if style.stroke_width_mm is not None:
        commands.append(f"{_format_number(style.stroke_width_mm)} w")
    if style.stroke_linecap:
        commands.append(f"{LINECAP_MAP.get(style.stroke_linecap, 0)} J")
    if style.stroke_linejoin:
        commands.append(f"{LINEJOIN_MAP.get(style.stroke_linejoin, 0)} j")


def _append_circle_path(commands: list[str], graphic: Circle) -> None:
    radius = graphic.radius_mm
    center_x = graphic.center.x_mm
    center_y = graphic.center.y_mm
    offset = radius * KAPPA

    commands.append(f"{_format_number(center_x + radius)} {_format_number(center_y)} m")
    commands.append(
        " ".join(
            [
                _format_number(center_x + radius),
                _format_number(center_y + offset),
                _format_number(center_x + offset),
                _format_number(center_y + radius),
                _format_number(center_x),
                _format_number(center_y + radius),
                "c",
            ]
        )
    )
    commands.append(
        " ".join(
            [
                _format_number(center_x - offset),
                _format_number(center_y + radius),
                _format_number(center_x - radius),
                _format_number(center_y + offset),
                _format_number(center_x - radius),
                _format_number(center_y),
                "c",
            ]
        )
    )
    commands.append(
        " ".join(
            [
                _format_number(center_x - radius),
                _format_number(center_y - offset),
                _format_number(center_x - offset),
                _format_number(center_y - radius),
                _format_number(center_x),
                _format_number(center_y - radius),
                "c",
            ]
        )
    )
    commands.append(
        " ".join(
            [
                _format_number(center_x + offset),
                _format_number(center_y - radius),
                _format_number(center_x + radius),
                _format_number(center_y - offset),
                _format_number(center_x + radius),
                _format_number(center_y),
                "c",
            ]
        )
    )
    commands.append("h")


def _append_rectangle_path(commands: list[str], graphic: Rectangle) -> None:
    x0 = graphic.origin.x_mm
    y0 = graphic.origin.y_mm
    width = graphic.width_mm
    height = graphic.height_mm
    radius = min(graphic.corner_radius_mm, width / 2.0, height / 2.0)

    if radius <= 0:
        commands.append(
            f"{_format_number(x0)} {_format_number(y0)} {_format_number(width)} {_format_number(height)} re"
        )
        return

    offset = radius * KAPPA
    x1 = x0 + width
    y1 = y0 + height

    commands.append(f"{_format_number(x0 + radius)} {_format_number(y0)} m")
    commands.append(f"{_format_number(x1 - radius)} {_format_number(y0)} l")
    commands.append(
        " ".join(
            [
                _format_number(x1 - radius + offset),
                _format_number(y0),
                _format_number(x1),
                _format_number(y0 + radius - offset),
                _format_number(x1),
                _format_number(y0 + radius),
                "c",
            ]
        )
    )
    commands.append(f"{_format_number(x1)} {_format_number(y1 - radius)} l")
    commands.append(
        " ".join(
            [
                _format_number(x1),
                _format_number(y1 - radius + offset),
                _format_number(x1 - radius + offset),
                _format_number(y1),
                _format_number(x1 - radius),
                _format_number(y1),
                "c",
            ]
        )
    )
    commands.append(f"{_format_number(x0 + radius)} {_format_number(y1)} l")
    commands.append(
        " ".join(
            [
                _format_number(x0 + radius - offset),
                _format_number(y1),
                _format_number(x0),
                _format_number(y1 - radius + offset),
                _format_number(x0),
                _format_number(y1 - radius),
                "c",
            ]
        )
    )
    commands.append(f"{_format_number(x0)} {_format_number(y0 + radius)} l")
    commands.append(
        " ".join(
            [
                _format_number(x0),
                _format_number(y0 + radius - offset),
                _format_number(x0 + radius - offset),
                _format_number(y0),
                _format_number(x0 + radius),
                _format_number(y0),
                "c",
            ]
        )
    )
    commands.append("h")


def _append_polyline_path(commands: list[str], points: tuple[Point, ...], *, closed: bool) -> None:
    first_point = points[0]
    commands.append(f"{_format_number(first_point.x_mm)} {_format_number(first_point.y_mm)} m")
    for point in points[1:]:
        commands.append(f"{_format_number(point.x_mm)} {_format_number(point.y_mm)} l")
    if closed:
        commands.append("h")


def _angle_between(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> float:
    ax, ay = vector_a
    bx, by = vector_b
    dot = (ax * bx) + (ay * by)
    det = (ax * by) - (ay * bx)
    return atan2(det, dot)


def _sample_arc_points(start: Point, command: ArcTo) -> tuple[Point, ...]:
    x1 = start.x_mm
    y1 = start.y_mm
    x2 = command.end.x_mm
    y2 = command.end.y_mm
    if x1 == x2 and y1 == y2:
        return ()

    rx = abs(command.radius_x_mm)
    ry = abs(command.radius_y_mm)
    phi = command.rotation_deg * pi / 180.0
    cos_phi = cos(phi)
    sin_phi = sin(phi)

    dx2 = (x1 - x2) / 2.0
    dy2 = (y1 - y2) / 2.0
    x1_prime = (cos_phi * dx2) + (sin_phi * dy2)
    y1_prime = (-sin_phi * dx2) + (cos_phi * dy2)

    lambda_value = (x1_prime * x1_prime) / (rx * rx) + (y1_prime * y1_prime) / (ry * ry)
    if lambda_value > 1.0:
        scale = sqrt(lambda_value)
        rx *= scale
        ry *= scale

    numerator = (rx * rx * ry * ry) - (rx * rx * y1_prime * y1_prime) - (ry * ry * x1_prime * x1_prime)
    denominator = (rx * rx * y1_prime * y1_prime) + (ry * ry * x1_prime * x1_prime)
    factor = 0.0 if denominator == 0 else sqrt(max(0.0, numerator / denominator))
    if command.large_arc == command.sweep:
        factor *= -1.0

    cx_prime = factor * ((rx * y1_prime) / ry)
    cy_prime = factor * (-(ry * x1_prime) / rx)

    center_x = (cos_phi * cx_prime) - (sin_phi * cy_prime) + ((x1 + x2) / 2.0)
    center_y = (sin_phi * cx_prime) + (cos_phi * cy_prime) + ((y1 + y2) / 2.0)

    unit_start = ((x1_prime - cx_prime) / rx, (y1_prime - cy_prime) / ry)
    unit_end = ((-x1_prime - cx_prime) / rx, (-y1_prime - cy_prime) / ry)
    start_angle = _angle_between((1.0, 0.0), unit_start)
    sweep_angle = _angle_between(unit_start, unit_end)

    if not command.sweep and sweep_angle > 0:
        sweep_angle -= 2.0 * pi
    elif command.sweep and sweep_angle < 0:
        sweep_angle += 2.0 * pi

    segment_count = max(4, ceil(abs(sweep_angle) / (pi / 8.0)))
    points: list[Point] = []
    for index in range(1, segment_count + 1):
        angle = start_angle + (sweep_angle * index / segment_count)
        x_prime = rx * cos(angle)
        y_prime = ry * sin(angle)
        points.append(
            Point(
                x_mm=(cos_phi * x_prime) - (sin_phi * y_prime) + center_x,
                y_mm=(sin_phi * x_prime) + (cos_phi * y_prime) + center_y,
            )
        )
    return tuple(points)


def _append_graphic_path(commands: list[str], graphic: GraphicPath) -> None:
    current_point: Point | None = None
    subpath_start: Point | None = None

    for command in graphic.commands:
        if isinstance(command, MoveTo):
            current_point = command.point
            subpath_start = command.point
            commands.append(f"{_format_number(command.point.x_mm)} {_format_number(command.point.y_mm)} m")
            continue

        if isinstance(command, LineTo):
            current_point = command.point
            commands.append(f"{_format_number(command.point.x_mm)} {_format_number(command.point.y_mm)} l")
            continue

        if isinstance(command, ArcTo):
            if current_point is None:
                raise ValueError("ArcTo の前に current point が必要です。")
            for point in _sample_arc_points(current_point, command):
                commands.append(f"{_format_number(point.x_mm)} {_format_number(point.y_mm)} l")
            current_point = command.end
            continue

        if isinstance(command, ClosePath):
            if subpath_start is not None:
                current_point = subpath_start
            commands.append("h")


def _paint_operator(style: Style | None) -> str:
    has_stroke = _style_has_stroke(style)
    has_fill = _style_has_fill(style)
    evenodd = style is not None and style.fill_rule == "evenodd"

    if has_stroke and has_fill:
        return "B*" if evenodd else "B"
    if has_fill:
        return "f*" if evenodd else "f"
    if has_stroke:
        return "S"
    return "n"


def _render_graphic(commands: list[str], graphic: RenderableGraphic, opacity_names: dict[float, str]) -> None:
    if isinstance(graphic, Group):
        commands.append("q")
        _append_transform_commands(commands, graphic)
        for child in graphic.items:
            _render_graphic(commands, child, opacity_names)
        commands.append("Q")
        return

    commands.append("q")
    _append_transform_commands(commands, graphic)
    _append_style_commands(commands, graphic.style, opacity_names)

    if isinstance(graphic, Polyline):
        _append_polyline_path(commands, graphic.points, closed=False)
    elif isinstance(graphic, Polygon):
        _append_polyline_path(commands, graphic.points, closed=True)
    elif isinstance(graphic, Circle):
        _append_circle_path(commands, graphic)
    elif isinstance(graphic, Rectangle):
        _append_rectangle_path(commands, graphic)
    elif isinstance(graphic, GraphicPath):
        _append_graphic_path(commands, graphic)
    else:
        raise TypeError(f"未対応の graphic type です: {type(graphic)!r}")

    commands.append(_paint_operator(graphic.style))
    commands.append("Q")


def _render_item(commands: list[str], item: RenderableGraphic | LayeredGraphic, opacity_names: dict[float, str]) -> None:
    if isinstance(item, LayeredGraphic):
        for graphic in item.white_layer:
            _render_graphic(commands, graphic, opacity_names)
        for graphic in item.color_layer:
            _render_graphic(commands, graphic, opacity_names)
        return
    _render_graphic(commands, item, opacity_names)


def _build_resources(opacity_names: dict[float, str]) -> str:
    if not opacity_names:
        return "<< >>"

    states = " ".join(
        f"/{name} << /Type /ExtGState /ca {_format_number(opacity)} /CA {_format_number(opacity)} >>"
        for opacity, name in opacity_names.items()
    )
    return f"<< /ExtGState << {states} >> >>"


def _build_pdf_content_stream(document: SvgDocument, opacity_names: dict[float, str]) -> bytes:
    page_height_pt = document.height_mm * MM_TO_PT
    commands = [
        "q",
        f"{_format_number(MM_TO_PT)} 0 0 {_format_number(-MM_TO_PT)} 0 {_format_number(page_height_pt)} cm",
    ]
    for item in document.items:
        _render_item(commands, item, opacity_names)
    commands.append("Q")
    return "\n".join(commands).encode("ascii")


def _build_info_object(document: SvgDocument) -> bytes | None:
    entries = ["/Producer " + _pdf_text_string("paramark export_pdf.py")]
    if document.title:
        entries.append("/Title " + _pdf_text_string(document.title))
    if document.description:
        entries.append("/Subject " + _pdf_text_string(document.description))
    if not entries:
        return None
    return ("<< " + " ".join(entries) + " >>").encode("ascii")


def _serialize_pdf_objects(objects: list[bytes], *, info_object_number: int | None = None) -> bytes:
    parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets: list[int] = [0]

    current_offset = len(parts[0])
    for object_number, object_bytes in enumerate(objects, start=1):
        offsets.append(current_offset)
        header = f"{object_number} 0 obj\n".encode("ascii")
        footer = b"\nendobj\n"
        parts.extend((header, object_bytes, footer))
        current_offset += len(header) + len(object_bytes) + len(footer)

    xref_offset = current_offset
    xref_lines = [f"xref\n0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    xref_lines.extend(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets[1:])
    parts.extend(xref_lines)

    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R".encode("ascii")
    if info_object_number is not None:
        trailer += f" /Info {info_object_number} 0 R".encode("ascii")
    trailer += b" >>\n"
    parts.append(trailer)
    parts.append(f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return b"".join(parts)


def render_pdf_bytes(document: SvgDocument) -> bytes:
    """SvgDocument から 1 ページ PDF バイト列を生成する。"""

    opacity_names = _collect_opacity_names(document.items)
    content_stream = _build_pdf_content_stream(document, opacity_names)
    width_pt = document.width_mm * MM_TO_PT
    height_pt = document.height_mm * MM_TO_PT

    resources = _build_resources(opacity_names)
    content_object = (
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
        + content_stream
        + b"\nendstream"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {_format_number(width_pt)} {_format_number(height_pt)}] "
            f"/Resources {resources} /Contents 4 0 R >>"
        ).encode("ascii"),
        content_object,
    ]

    info_object = _build_info_object(document)
    info_object_number: int | None = None
    if info_object is not None:
        objects.append(info_object)
        info_object_number = len(objects)

    return _serialize_pdf_objects(objects, info_object_number=info_object_number)


def save_pdf(path: str | Path, document: SvgDocument) -> Path:
    """PDF をファイルへ保存する。"""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(render_pdf_bytes(document))
    return output_path


def export_layout_pdf(
    layout,
    *,
    spec: ExportJobSpec,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    strict: bool = True,
) -> ExportResult:
    """SheetLayout を PDF ファイルとして書き出す。"""

    document = render_export_document(layout, spec=spec, strict=strict)
    resolved_output_dir = Path(output_dir)
    output_path = resolved_output_dir / spec.build_filename("pdf")
    saved_path = save_pdf(output_path, document)
    return ExportResult(
        output_path=saved_path,
        document=document,
        layout=layout,
        spec=spec,
    )


def _resolve_job_module(job_module: str | ModuleType) -> ModuleType:
    if isinstance(job_module, ModuleType):
        return job_module
    from importlib import import_module

    return import_module(job_module)


def export_job_module_pdf(
    job_module: str | ModuleType,
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    strict: bool = True,
) -> ExportResult:
    """job module の `build_layout()` を呼んで PDF を出力する。"""

    resolved_module = _resolve_job_module(job_module)
    build_layout = getattr(resolved_module, "build_layout")
    layout = build_layout()
    spec = extract_job_spec(resolved_module)
    return export_layout_pdf(
        layout,
        spec=spec,
        output_dir=output_dir,
        strict=strict,
    )


def main(argv: list[str] | None = None) -> int:
    """`python -m export.export_pdf export.jobs.line_pack_postcard` 用 CLI。"""

    parser = argparse.ArgumentParser(description="paramark export pdf runner")
    parser.add_argument("job_module", help="実行する export.jobs モジュール")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="出力先ディレクトリ")
    parser.add_argument("--no-strict", action="store_true", help="シート範囲チェックを緩和する")
    args = parser.parse_args(argv)

    result = export_job_module_pdf(
        args.job_module,
        output_dir=args.output_dir,
        strict=not args.no_strict,
    )
    print(result.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
