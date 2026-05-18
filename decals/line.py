"""Line 系の基本図形。"""

from __future__ import annotations

from collections.abc import Sequence
from math import cos, radians, sin

from core import LayeredGraphic, Point, Polyline

from ._common import build_layered_graphic, ensure_positive_mm, make_stroke_style


def generate_line(
    length_mm: float,
    width_mm: float,
    *,
    color: str = "#000000",
    linecap: str = "butt",
) -> LayeredGraphic:
    """水平な直線デカールを生成する。"""

    resolved_length = ensure_positive_mm("length_mm", length_mm)
    resolved_width = ensure_positive_mm("width_mm", width_mm)
    metadata = {
        "type": "line",
        "length_mm": resolved_length,
        "width_mm": resolved_width,
    }
    graphic = Polyline(
        points=(Point(0.0, 0.0), Point(resolved_length, 0.0)),
        style=make_stroke_style(resolved_width, color=color, linecap=linecap),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


def generate_polyline(
    lengths_mm: Sequence[float],
    angles_deg: Sequence[float],
    width_mm: float,
    *,
    start_angle_deg: float = 0.0,
    color: str = "#000000",
    linecap: str = "butt",
    linejoin: str = "round",
) -> LayeredGraphic:
    """相対角指定で多段折れ線デカールを生成する。"""

    if len(lengths_mm) < 2:
        raise ValueError("lengths_mm には 2 要素以上必要です。")
    if len(lengths_mm) != len(angles_deg) + 1:
        raise ValueError("angles_deg の要素数は lengths_mm より 1 少なくしてください。")

    resolved_lengths = tuple(ensure_positive_mm(f"lengths_mm[{index}]", value) for index, value in enumerate(lengths_mm))
    resolved_angles = tuple(float(value) for value in angles_deg)
    resolved_width = ensure_positive_mm("width_mm", width_mm)

    x_mm = 0.0
    y_mm = 0.0
    heading_deg = float(start_angle_deg)
    points = [Point(x_mm, y_mm)]

    for index, segment_length_mm in enumerate(resolved_lengths):
        heading_rad = radians(heading_deg)
        x_mm += segment_length_mm * cos(heading_rad)
        y_mm += segment_length_mm * sin(heading_rad)
        points.append(Point(x_mm, y_mm))

        if index < len(resolved_angles):
            heading_deg += resolved_angles[index]

    metadata = {
        "type": "polyline",
        "lengths_mm": list(resolved_lengths),
        "angles_deg": list(resolved_angles),
        "width_mm": resolved_width,
        "start_angle_deg": float(start_angle_deg),
    }
    graphic = Polyline(
        points=tuple(points),
        style=make_stroke_style(
            resolved_width,
            color=color,
            linecap=linecap,
            linejoin=linejoin,
        ),
        metadata=metadata,
    )
    return build_layered_graphic(color_graphics=(graphic,), metadata=metadata)


__all__ = [
    "generate_line",
    "generate_polyline",
]
