"""Stripe 系の基本図形。"""

from __future__ import annotations

from math import floor

from core import Group, LayeredGraphic, Point, Polygon, Rectangle

from ._common import (
    build_layered_graphic,
    clip_polygon_to_band,
    degrees_to_unit_normal,
    ensure_positive_mm,
    make_fill_style,
    project_points,
    rectangle_points,
)


def generate_stripe(
    length_mm: float,
    width_mm: float,
    *,
    color: str = "#000000",
) -> LayeredGraphic:
    """x 軸方向の単線ストライプを生成する。"""

    resolved_length = ensure_positive_mm("length_mm", length_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    metadata = {
        "type": "stripe",
        "length_mm": resolved_length,
        "width_mm": resolved_width,
    }
    graphic = Rectangle(
        origin=Point(0.0, -resolved_width / 2.0),
        width_mm=resolved_length,
        height_mm=resolved_width,
        style=make_fill_style(color),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


def generate_double_stripe(
    length_mm: float,
    gap_mm: float,
    stripe_width_mm: float,
    *,
    color: str = "#000000",
) -> LayeredGraphic:
    """2 本平行なストライプを生成する。"""

    resolved_length = ensure_positive_mm("length_mm", length_mm)
    resolved_gap = ensure_positive_mm("gap_mm", gap_mm, allow_zero=True)
    resolved_stripe_width = ensure_positive_mm("stripe_width_mm", stripe_width_mm)
    top_y_mm = -(resolved_gap / 2.0) - resolved_stripe_width
    bottom_y_mm = resolved_gap / 2.0
    style = make_fill_style(color)
    metadata = {
        "type": "double_stripe",
        "length_mm": resolved_length,
        "gap_mm": resolved_gap,
        "stripe_width_mm": resolved_stripe_width,
    }
    top = Rectangle(
        origin=Point(0.0, top_y_mm),
        width_mm=resolved_length,
        height_mm=resolved_stripe_width,
        style=style,
    )
    bottom = Rectangle(
        origin=Point(0.0, bottom_y_mm),
        width_mm=resolved_length,
        height_mm=resolved_stripe_width,
        style=style,
    )
    group = Group(items=(top, bottom), metadata=metadata)
    return build_layered_graphic(color_graphics=(group,), metadata=metadata)


def generate_hazard_stripes(
    angle_deg: float,
    pitch_mm: float,
    width_mm: float,
    height_mm: float,
    *,
    stripe_width_mm: float | None = None,
    color: str = "#000000",
) -> LayeredGraphic:
    """矩形領域に切り抜かれた警告斜線パターンを生成する。"""

    resolved_pitch = ensure_positive_mm("pitch_mm", pitch_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    resolved_height = ensure_positive_mm("height_mm", height_mm)
    resolved_stripe_width = (
        ensure_positive_mm("stripe_width_mm", stripe_width_mm)
        if stripe_width_mm is not None
        else resolved_pitch / 2.0
    )

    tile = rectangle_points(resolved_width, resolved_height)
    normal_x, normal_y = degrees_to_unit_normal(float(angle_deg))
    min_projection, max_projection = project_points(tile, normal_x=normal_x, normal_y=normal_y)
    start_index = floor((min_projection - resolved_stripe_width) / resolved_pitch) - 1
    end_index = floor((max_projection + resolved_stripe_width) / resolved_pitch) + 1

    style = make_fill_style(color)
    stripe_polygons: list[Polygon] = []
    for index in range(start_index, end_index + 1):
        center_projection = index * resolved_pitch
        clipped = clip_polygon_to_band(
            tile,
            normal_x=normal_x,
            normal_y=normal_y,
            lower_bound=center_projection - (resolved_stripe_width / 2.0),
            upper_bound=center_projection + (resolved_stripe_width / 2.0),
        )
        if len(clipped) < 3:
            continue
        stripe_polygons.append(Polygon(points=clipped, style=style))

    metadata = {
        "type": "hazard",
        "angle_deg": float(angle_deg),
        "pitch_mm": resolved_pitch,
        "stripe_width_mm": resolved_stripe_width,
        "tile_width_mm": resolved_width,
        "tile_height_mm": resolved_height,
    }
    group = Group(items=tuple(stripe_polygons), metadata=metadata)
    return build_layered_graphic(color_graphics=(group,), metadata=metadata)


__all__ = [
    "generate_double_stripe",
    "generate_hazard_stripes",
    "generate_stripe",
]
