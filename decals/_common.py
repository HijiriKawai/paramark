"""decals モジュールで共有する小さなユーティリティ。"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import ceil, cos, radians, sin

from core.geometry import ClosePath, LayeredGraphic, LineTo, MoveTo, Path, Point, RenderableGraphic, Style
from core.metadata import MetadataDict
from core.units import ensure_mm


DEFAULT_COLOR = "#000000"
EPSILON = 1e-9


def ensure_positive_mm(name: str, value: float, *, allow_zero: bool = False) -> float:
    """正の mm 値を正規化する。"""

    resolved = ensure_mm(value)
    if allow_zero:
        if resolved < 0:
            raise ValueError(f"{name} は 0 以上で指定してください。")
        return resolved

    if resolved <= 0:
        raise ValueError(f"{name} は正の値で指定してください。")
    return resolved


def ensure_minimum_int(name: str, value: int, minimum: int) -> int:
    """最小値付き整数パラメータを検証する。"""

    if value < minimum:
        raise ValueError(f"{name} は {minimum} 以上で指定してください。")
    return int(value)


def make_stroke_style(
    width_mm: float,
    *,
    color: str = DEFAULT_COLOR,
    linecap: str = "butt",
    linejoin: str = "round",
) -> Style:
    """線図形向け Style を生成する。"""

    return Style(
        stroke=color,
        fill="none",
        stroke_width_mm=ensure_positive_mm("stroke_width_mm", width_mm),
        stroke_linecap=linecap,
        stroke_linejoin=linejoin,
    )


def make_fill_style(
    color: str = DEFAULT_COLOR,
    *,
    fill_rule: str | None = None,
    opacity: float | None = None,
) -> Style:
    """塗り図形向け Style を生成する。"""

    return Style(
        stroke=None,
        fill=color,
        fill_rule=fill_rule,
        opacity=opacity,
    )


def build_layered_graphic(
    *,
    color_graphics: Iterable[RenderableGraphic],
    metadata: MetadataDict,
    white_graphics: Iterable[RenderableGraphic] = (),
) -> LayeredGraphic:
    """標準的な LayeredGraphic を生成する。"""

    return LayeredGraphic(
        white_layer=tuple(white_graphics),
        color_layer=tuple(color_graphics),
        metadata=dict(metadata),
    )


def inferred_segment_count(
    *,
    radius_x_mm: float,
    radius_y_mm: float,
    sweep_angle_deg: float,
    segment_count: int | None,
) -> int:
    """円弧近似に使う分割数を決める。"""

    if segment_count is not None:
        return ensure_minimum_int("segment_count", segment_count, 2)

    max_radius = max(abs(radius_x_mm), abs(radius_y_mm))
    return max(
        12,
        ceil(abs(sweep_angle_deg) / 7.5),
        ceil((max_radius * abs(sweep_angle_deg)) / 45.0),
    )


def sample_ellipse_points(
    *,
    radius_x_mm: float,
    radius_y_mm: float,
    start_angle_deg: float,
    sweep_angle_deg: float,
    center_x_mm: float = 0.0,
    center_y_mm: float = 0.0,
    segment_count: int | None = None,
    closed: bool = False,
) -> tuple[Point, ...]:
    """楕円弧を line segment 群として近似する。"""

    resolved_radius_x = ensure_positive_mm("radius_x_mm", radius_x_mm)
    resolved_radius_y = ensure_positive_mm("radius_y_mm", radius_y_mm)
    resolved_segments = inferred_segment_count(
        radius_x_mm=resolved_radius_x,
        radius_y_mm=resolved_radius_y,
        sweep_angle_deg=sweep_angle_deg,
        segment_count=segment_count,
    )
    point_count = resolved_segments if closed else resolved_segments + 1

    points: list[Point] = []
    for index in range(point_count):
        angle_deg = start_angle_deg + (sweep_angle_deg * index / resolved_segments)
        angle_rad = radians(angle_deg)
        points.append(
            Point(
                x_mm=center_x_mm + (resolved_radius_x * cos(angle_rad)),
                y_mm=center_y_mm + (resolved_radius_y * sin(angle_rad)),
            )
        )
    return tuple(points)


def regular_polygon_points(
    *,
    side_count: int,
    radius_mm: float,
    center_x_mm: float = 0.0,
    center_y_mm: float = 0.0,
    rotation_deg: float = -90.0,
) -> tuple[Point, ...]:
    """正多角形の頂点列を返す。"""

    resolved_sides = ensure_minimum_int("side_count", side_count, 3)
    resolved_radius = ensure_positive_mm("radius_mm", radius_mm)

    points: list[Point] = []
    for index in range(resolved_sides):
        angle_rad = radians(rotation_deg + (360.0 * index / resolved_sides))
        points.append(
            Point(
                x_mm=center_x_mm + (resolved_radius * cos(angle_rad)),
                y_mm=center_y_mm + (resolved_radius * sin(angle_rad)),
            )
        )
    return tuple(points)


def build_closed_loops_path(
    loops: Sequence[Sequence[Point]],
    *,
    style: Style,
    metadata: MetadataDict,
) -> Path:
    """複数閉ループから even-odd path を作る。"""

    commands: list[MoveTo | LineTo | ClosePath] = []
    for loop in loops:
        points = tuple(loop)
        if len(points) < 3:
            raise ValueError("閉ループには 3 点以上必要です。")

        commands.append(MoveTo(points[0]))
        commands.extend(LineTo(point) for point in points[1:])
        commands.append(ClosePath())

    return Path(commands=tuple(commands), style=style, metadata=dict(metadata))


def rectangle_points(width_mm: float, height_mm: float) -> tuple[Point, ...]:
    """原点左上の矩形頂点列を返す。"""

    resolved_width = ensure_positive_mm("width_mm", width_mm)
    resolved_height = ensure_positive_mm("height_mm", height_mm)
    return (
        Point(0.0, 0.0),
        Point(resolved_width, 0.0),
        Point(resolved_width, resolved_height),
        Point(0.0, resolved_height),
    )


def clip_polygon_to_band(
    polygon: Sequence[Point],
    *,
    normal_x: float,
    normal_y: float,
    lower_bound: float,
    upper_bound: float,
) -> tuple[Point, ...]:
    """凸多角形を 2 本の平行線で挟まれた帯へ切り抜く。"""

    clipped = _clip_polygon_against_half_plane(
        polygon,
        normal_x=normal_x,
        normal_y=normal_y,
        bound=lower_bound,
        keep_greater=True,
    )
    clipped = _clip_polygon_against_half_plane(
        clipped,
        normal_x=normal_x,
        normal_y=normal_y,
        bound=upper_bound,
        keep_greater=False,
    )
    return tuple(clipped)


def _clip_polygon_against_half_plane(
    polygon: Sequence[Point],
    *,
    normal_x: float,
    normal_y: float,
    bound: float,
    keep_greater: bool,
) -> list[Point]:
    if not polygon:
        return []

    def signed_distance(point: Point) -> float:
        return (normal_x * point.x_mm) + (normal_y * point.y_mm) - bound

    def is_inside(point: Point) -> bool:
        distance = signed_distance(point)
        return distance >= -EPSILON if keep_greater else distance <= EPSILON

    def intersection(start: Point, end: Point) -> Point:
        start_value = signed_distance(start)
        end_value = signed_distance(end)
        denominator = end_value - start_value
        if abs(denominator) <= EPSILON:
            return end
        ratio = -start_value / denominator
        return Point(
            x_mm=start.x_mm + ((end.x_mm - start.x_mm) * ratio),
            y_mm=start.y_mm + ((end.y_mm - start.y_mm) * ratio),
        )

    output: list[Point] = []
    previous = polygon[-1]
    previous_inside = is_inside(previous)

    for current in polygon:
        current_inside = is_inside(current)

        if current_inside:
            if not previous_inside:
                output.append(intersection(previous, current))
            output.append(current)
        elif previous_inside:
            output.append(intersection(previous, current))

        previous = current
        previous_inside = current_inside

    return output


def edge_key(start: Point, end: Point, *, precision: int = 6) -> tuple[tuple[float, float], tuple[float, float]]:
    """順序に依存しない edge 識別子を返す。"""

    left = (round(start.x_mm, precision), round(start.y_mm, precision))
    right = (round(end.x_mm, precision), round(end.y_mm, precision))
    return tuple(sorted((left, right)))


def project_points(points: Sequence[Point], *, normal_x: float, normal_y: float) -> tuple[float, float]:
    """点列を法線方向へ射影した最小値と最大値を返す。"""

    projections = [(normal_x * point.x_mm) + (normal_y * point.y_mm) for point in points]
    return min(projections), max(projections)


def degrees_to_unit_normal(angle_deg: float) -> tuple[float, float]:
    """角度に対応する線の法線ベクトルを返す。"""

    angle_rad = radians(angle_deg)
    direction_x = cos(angle_rad)
    direction_y = sin(angle_rad)
    return (-direction_y, direction_x)
