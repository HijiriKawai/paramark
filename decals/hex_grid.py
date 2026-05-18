"""六角格子パターン。"""

from __future__ import annotations

from math import sqrt

from core import Group, LayeredGraphic, Point, Polyline

from ._common import build_layered_graphic, edge_key, ensure_positive_mm, make_stroke_style, regular_polygon_points


def generate_hex_grid(
    cell_mm: float,
    width_mm: float,
    height_mm: float,
    *,
    line_width_mm: float = 0.2,
    color: str = "#000000",
    orientation: str = "flat",
) -> LayeredGraphic:
    """矩形領域内に収まる六角格子を生成する。"""

    resolved_cell = ensure_positive_mm("cell_mm", cell_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    resolved_height = ensure_positive_mm("height_mm", height_mm)
    resolved_line_width = ensure_positive_mm("line_width_mm", line_width_mm)
    style = make_stroke_style(resolved_line_width, color=color, linejoin="round")

    edges: dict[tuple[tuple[float, float], tuple[float, float]], tuple[Point, Point]] = {}
    for center_x_mm, center_y_mm in _hex_centers(
        cell_mm=resolved_cell,
        width_mm=resolved_width,
        height_mm=resolved_height,
        orientation=orientation,
    ):
        rotation_deg = 0.0 if orientation == "flat" else -90.0
        vertices = regular_polygon_points(
            side_count=6,
            radius_mm=resolved_cell,
            center_x_mm=center_x_mm,
            center_y_mm=center_y_mm,
            rotation_deg=rotation_deg,
        )
        for index, start in enumerate(vertices):
            end = vertices[(index + 1) % len(vertices)]
            edges.setdefault(edge_key(start, end), (start, end))

    lines = tuple(Polyline(points=edge, style=style) for edge in edges.values())
    metadata = {
        "type": "hexgrid",
        "cell_mm": resolved_cell,
        "tile_width_mm": resolved_width,
        "tile_height_mm": resolved_height,
        "line_width_mm": resolved_line_width,
        "orientation": orientation,
    }
    group = Group(items=lines, metadata=metadata)
    return build_layered_graphic(color_graphics=(group,), metadata=metadata)


def _hex_centers(
    *,
    cell_mm: float,
    width_mm: float,
    height_mm: float,
    orientation: str,
) -> tuple[tuple[float, float], ...]:
    if orientation == "flat":
        return _flat_hex_centers(cell_mm=cell_mm, width_mm=width_mm, height_mm=height_mm)
    if orientation == "pointy":
        return _pointy_hex_centers(cell_mm=cell_mm, width_mm=width_mm, height_mm=height_mm)
    raise ValueError("orientation は 'flat' または 'pointy' を指定してください。")


def _flat_hex_centers(*, cell_mm: float, width_mm: float, height_mm: float) -> tuple[tuple[float, float], ...]:
    hex_half_width = cell_mm
    hex_half_height = sqrt(3.0) * cell_mm / 2.0
    column_step = 1.5 * cell_mm
    row_step = hex_half_height * 2.0

    centers: list[tuple[float, float]] = []
    column_index = 0
    center_x_mm = hex_half_width
    while center_x_mm + hex_half_width <= width_mm:
        y_offset_mm = hex_half_height if column_index % 2 else 0.0
        center_y_mm = hex_half_height + y_offset_mm
        while center_y_mm + hex_half_height <= height_mm:
            centers.append((center_x_mm, center_y_mm))
            center_y_mm += row_step
        center_x_mm += column_step
        column_index += 1
    return tuple(centers)


def _pointy_hex_centers(*, cell_mm: float, width_mm: float, height_mm: float) -> tuple[tuple[float, float], ...]:
    hex_half_width = sqrt(3.0) * cell_mm / 2.0
    hex_half_height = cell_mm
    column_step = hex_half_width * 2.0
    row_step = 1.5 * cell_mm

    centers: list[tuple[float, float]] = []
    row_index = 0
    center_y_mm = hex_half_height
    while center_y_mm + hex_half_height <= height_mm:
        x_offset_mm = hex_half_width if row_index % 2 else 0.0
        center_x_mm = hex_half_width + x_offset_mm
        while center_x_mm + hex_half_width <= width_mm:
            centers.append((center_x_mm, center_y_mm))
            center_x_mm += column_step
        center_y_mm += row_step
        row_index += 1
    return tuple(centers)


__all__ = [
    "generate_hex_grid",
]
