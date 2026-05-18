"""Polygon 系の基本図形。"""

from __future__ import annotations

from core import LayeredGraphic, Polygon

from ._common import build_layered_graphic, ensure_positive_mm, make_fill_style, regular_polygon_points


def generate_regular_polygon(
    side_count: int,
    radius_mm: float,
    *,
    rotation_deg: float = -90.0,
    color: str = "#000000",
) -> LayeredGraphic:
    """原点中心の正多角形を生成する。"""

    resolved_radius = ensure_positive_mm("radius_mm", radius_mm)
    points = regular_polygon_points(
        side_count=side_count,
        radius_mm=resolved_radius,
        rotation_deg=rotation_deg,
    )
    metadata = {
        "type": "polygon",
        "side_count": int(side_count),
        "radius_mm": resolved_radius,
        "rotation_deg": float(rotation_deg),
    }
    graphic = Polygon(
        points=points,
        style=make_fill_style(color),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


__all__ = [
    "generate_regular_polygon",
]
