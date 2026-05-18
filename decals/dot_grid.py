"""ドット格子パターン。"""

from __future__ import annotations

from core import Circle, Group, LayeredGraphic, Point

from ._common import build_layered_graphic, ensure_positive_mm, make_fill_style


def generate_dot_grid(
    pitch_mm: float,
    radius_mm: float,
    width_mm: float,
    height_mm: float,
    *,
    color: str = "#000000",
) -> LayeredGraphic:
    """矩形領域内に収まるドット格子を生成する。"""

    resolved_pitch = ensure_positive_mm("pitch_mm", pitch_mm)
    resolved_radius = ensure_positive_mm("radius_mm", radius_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    resolved_height = ensure_positive_mm("height_mm", height_mm)
    style = make_fill_style(color)

    circles: list[Circle] = []
    center_y_mm = resolved_radius
    while center_y_mm <= resolved_height - resolved_radius + 1e-9:
        center_x_mm = resolved_radius
        while center_x_mm <= resolved_width - resolved_radius + 1e-9:
            circles.append(
                Circle(
                    center=Point(center_x_mm, center_y_mm),
                    radius_mm=resolved_radius,
                    style=style,
                )
            )
            center_x_mm += resolved_pitch
        center_y_mm += resolved_pitch

    metadata = {
        "type": "dotgrid",
        "pitch_mm": resolved_pitch,
        "radius_mm": resolved_radius,
        "tile_width_mm": resolved_width,
        "tile_height_mm": resolved_height,
    }
    group = Group(items=tuple(circles), metadata=metadata)
    return build_layered_graphic(color_graphics=(group,), metadata=metadata)


__all__ = [
    "generate_dot_grid",
]
