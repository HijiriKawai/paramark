"""Circle 系の基本図形。"""

from __future__ import annotations

from core import Circle, LayeredGraphic, Point, Polyline

from ._common import (
    build_closed_loops_path,
    build_layered_graphic,
    ensure_positive_mm,
    make_fill_style,
    make_stroke_style,
    sample_ellipse_points,
)


def generate_circle(
    radius_mm: float,
    *,
    color: str = "#000000",
) -> LayeredGraphic:
    """原点中心の塗り円を生成する。"""

    resolved_radius = ensure_positive_mm("radius_mm", radius_mm)
    metadata = {
        "type": "circle",
        "radius_mm": resolved_radius,
    }
    graphic = Circle(
        center=Point(0.0, 0.0),
        radius_mm=resolved_radius,
        style=make_fill_style(color),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


def generate_arc(
    radius_mm: float,
    sweep_angle_deg: float,
    width_mm: float,
    *,
    start_angle_deg: float = 0.0,
    color: str = "#000000",
    segment_count: int | None = None,
    linecap: str = "butt",
) -> LayeredGraphic:
    """原点中心の円弧デカールを生成する。"""

    resolved_radius = ensure_positive_mm("radius_mm", radius_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    points = sample_ellipse_points(
        radius_x_mm=resolved_radius,
        radius_y_mm=resolved_radius,
        start_angle_deg=float(start_angle_deg),
        sweep_angle_deg=float(sweep_angle_deg),
        segment_count=segment_count,
    )
    metadata = {
        "type": "arc",
        "radius_mm": resolved_radius,
        "sweep_angle_deg": float(sweep_angle_deg),
        "start_angle_deg": float(start_angle_deg),
        "width_mm": resolved_width,
    }
    graphic = Polyline(
        points=points,
        style=make_stroke_style(resolved_width, color=color, linecap=linecap, linejoin="round"),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


def generate_ring(
    outer_radius_mm: float,
    inner_radius_mm: float,
    *,
    color: str = "#000000",
    segment_count: int | None = None,
) -> LayeredGraphic:
    """原点中心のリングを生成する。"""

    resolved_outer = ensure_positive_mm("outer_radius_mm", outer_radius_mm)
    resolved_inner = ensure_positive_mm("inner_radius_mm", inner_radius_mm)
    if resolved_inner >= resolved_outer:
        raise ValueError("inner_radius_mm は outer_radius_mm より小さくしてください。")

    outer_loop = sample_ellipse_points(
        radius_x_mm=resolved_outer,
        radius_y_mm=resolved_outer,
        start_angle_deg=0.0,
        sweep_angle_deg=360.0,
        segment_count=segment_count,
        closed=True,
    )
    inner_loop = sample_ellipse_points(
        radius_x_mm=resolved_inner,
        radius_y_mm=resolved_inner,
        start_angle_deg=0.0,
        sweep_angle_deg=-360.0,
        segment_count=segment_count,
        closed=True,
    )
    metadata = {
        "type": "ring",
        "outer_radius_mm": resolved_outer,
        "inner_radius_mm": resolved_inner,
    }
    graphic = build_closed_loops_path(
        (outer_loop, inner_loop),
        style=make_fill_style(color, fill_rule="evenodd"),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


__all__ = [
    "generate_arc",
    "generate_circle",
    "generate_ring",
]
