"""SVG に依存しない図形の中間表現。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Self, TypeAlias

from .metadata import MetadataDict, merge_metadata
from .transforms import AffineTransform, compose, rotate, scale, translate
from .units import Millimeter, ensure_mm


@dataclass(frozen=True, slots=True)
class Point:
    """mm 単位の 2D 点。"""

    x_mm: Millimeter
    y_mm: Millimeter

    def transformed(self, transform: AffineTransform) -> "Point":
        x_mm, y_mm = transform.apply_xy(self.x_mm, self.y_mm)
        return Point(x_mm=x_mm, y_mm=y_mm)


PointLike: TypeAlias = Point | tuple[float, float]


def _point(value: PointLike) -> Point:
    if isinstance(value, Point):
        return value
    x_mm, y_mm = value
    return Point(x_mm=ensure_mm(x_mm), y_mm=ensure_mm(y_mm))


def _points(values: tuple[PointLike, ...] | list[PointLike]) -> tuple[Point, ...]:
    return tuple(_point(value) for value in values)


@dataclass(frozen=True, slots=True)
class Bounds:
    """軸平行の bounding box。"""

    min_x_mm: Millimeter
    min_y_mm: Millimeter
    max_x_mm: Millimeter
    max_y_mm: Millimeter

    def __post_init__(self) -> None:
        if self.max_x_mm < self.min_x_mm or self.max_y_mm < self.min_y_mm:
            raise ValueError("Bounds の最小値/最大値が不正です。")

    @property
    def width_mm(self) -> Millimeter:
        return self.max_x_mm - self.min_x_mm

    @property
    def height_mm(self) -> Millimeter:
        return self.max_y_mm - self.min_y_mm

    @classmethod
    def zero(cls) -> "Bounds":
        return cls(0.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_points(cls, points: tuple[Point, ...]) -> "Bounds":
        if not points:
            raise ValueError("Bounds.from_points には 1 点以上必要です。")
        xs = [point.x_mm for point in points]
        ys = [point.y_mm for point in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    def union(self, other: "Bounds") -> "Bounds":
        return Bounds(
            min(self.min_x_mm, other.min_x_mm),
            min(self.min_y_mm, other.min_y_mm),
            max(self.max_x_mm, other.max_x_mm),
            max(self.max_y_mm, other.max_y_mm),
        )

    def expanded(self, margin_mm: float) -> "Bounds":
        margin = ensure_mm(margin_mm)
        return Bounds(
            self.min_x_mm - margin,
            self.min_y_mm - margin,
            self.max_x_mm + margin,
            self.max_y_mm + margin,
        )

    def transformed(self, transform: AffineTransform) -> "Bounds":
        corners = (
            Point(self.min_x_mm, self.min_y_mm),
            Point(self.max_x_mm, self.min_y_mm),
            Point(self.max_x_mm, self.max_y_mm),
            Point(self.min_x_mm, self.max_y_mm),
        )
        return Bounds.from_points(tuple(point.transformed(transform) for point in corners))


@dataclass(frozen=True, slots=True, kw_only=True)
class Style:
    """線や塗りの見た目。"""

    stroke: str | None = "#000000"
    fill: str | None = "none"
    stroke_width_mm: Millimeter | None = None
    stroke_linecap: str | None = None
    stroke_linejoin: str | None = None
    fill_rule: str | None = None
    opacity: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphicObject:
    """すべての図形オブジェクトの基底型。"""

    style: Style | None = None
    metadata: MetadataDict = field(default_factory=dict)
    transform: AffineTransform = field(default_factory=AffineTransform)

    def local_bounds(self) -> Bounds:
        raise NotImplementedError

    def bounds(self) -> Bounds:
        base_bounds = self.local_bounds()
        if self.style and self.style.stroke not in (None, "none") and self.style.stroke_width_mm:
            base_bounds = base_bounds.expanded(self.style.stroke_width_mm / 2.0)
        return base_bounds.transformed(self.transform)

    def with_metadata(self: Self, **extra: object) -> Self:
        return replace(self, metadata=merge_metadata(self.metadata, **extra))

    def with_transform(self: Self, transform: AffineTransform) -> Self:
        return replace(self, transform=compose(self.transform, transform))

    def translated(self: Self, x_mm: float, y_mm: float) -> Self:
        return self.with_transform(translate(x_mm, y_mm))

    def scaled(
        self: Self,
        x_factor: float,
        y_factor: float | None = None,
        *,
        origin_x_mm: float = 0.0,
        origin_y_mm: float = 0.0,
    ) -> Self:
        return self.with_transform(
            scale(
                x_factor,
                y_factor,
                origin_x_mm=origin_x_mm,
                origin_y_mm=origin_y_mm,
            )
        )

    def rotated(
        self: Self,
        angle_deg: float,
        *,
        origin_x_mm: float = 0.0,
        origin_y_mm: float = 0.0,
    ) -> Self:
        return self.with_transform(
            rotate(
                angle_deg,
                origin_x_mm=origin_x_mm,
                origin_y_mm=origin_y_mm,
            )
        )


@dataclass(frozen=True, slots=True)
class Polyline(GraphicObject):
    """折れ線。"""

    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        normalized_points = _points(list(self.points))
        if len(normalized_points) < 2:
            raise ValueError("Polyline には 2 点以上必要です。")
        object.__setattr__(self, "points", normalized_points)

    def local_bounds(self) -> Bounds:
        return Bounds.from_points(self.points)


@dataclass(frozen=True, slots=True)
class Polygon(GraphicObject):
    """閉じた多角形。"""

    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        normalized_points = _points(list(self.points))
        if len(normalized_points) < 3:
            raise ValueError("Polygon には 3 点以上必要です。")
        object.__setattr__(self, "points", normalized_points)

    def local_bounds(self) -> Bounds:
        return Bounds.from_points(self.points)


@dataclass(frozen=True, slots=True)
class Circle(GraphicObject):
    """円。"""

    center: Point
    radius_mm: Millimeter

    def __post_init__(self) -> None:
        object.__setattr__(self, "center", _point(self.center))
        object.__setattr__(self, "radius_mm", ensure_mm(self.radius_mm))
        if self.radius_mm <= 0:
            raise ValueError("Circle の半径は正の値で指定してください。")

    def local_bounds(self) -> Bounds:
        return Bounds(
            self.center.x_mm - self.radius_mm,
            self.center.y_mm - self.radius_mm,
            self.center.x_mm + self.radius_mm,
            self.center.y_mm + self.radius_mm,
        )


@dataclass(frozen=True, slots=True)
class Rectangle(GraphicObject):
    """軸平行長方形。"""

    origin: Point
    width_mm: Millimeter
    height_mm: Millimeter
    corner_radius_mm: Millimeter = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin", _point(self.origin))
        object.__setattr__(self, "width_mm", ensure_mm(self.width_mm))
        object.__setattr__(self, "height_mm", ensure_mm(self.height_mm))
        object.__setattr__(self, "corner_radius_mm", ensure_mm(self.corner_radius_mm))
        if self.width_mm <= 0 or self.height_mm <= 0:
            raise ValueError("Rectangle の width/height は正の値で指定してください。")
        if self.corner_radius_mm < 0:
            raise ValueError("Rectangle の corner_radius_mm は 0 以上で指定してください。")

    def local_bounds(self) -> Bounds:
        return Bounds(
            self.origin.x_mm,
            self.origin.y_mm,
            self.origin.x_mm + self.width_mm,
            self.origin.y_mm + self.height_mm,
        )


@dataclass(frozen=True, slots=True)
class MoveTo:
    point: Point

    def __post_init__(self) -> None:
        object.__setattr__(self, "point", _point(self.point))


@dataclass(frozen=True, slots=True)
class LineTo:
    point: Point

    def __post_init__(self) -> None:
        object.__setattr__(self, "point", _point(self.point))


@dataclass(frozen=True, slots=True)
class ArcTo:
    end: Point
    radius_x_mm: Millimeter
    radius_y_mm: Millimeter
    rotation_deg: float = 0.0
    large_arc: bool = False
    sweep: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "end", _point(self.end))
        object.__setattr__(self, "radius_x_mm", ensure_mm(self.radius_x_mm))
        object.__setattr__(self, "radius_y_mm", ensure_mm(self.radius_y_mm))
        if self.radius_x_mm <= 0 or self.radius_y_mm <= 0:
            raise ValueError("ArcTo の半径は正の値で指定してください。")


@dataclass(frozen=True, slots=True)
class ClosePath:
    pass


PathCommand: TypeAlias = MoveTo | LineTo | ArcTo | ClosePath


@dataclass(frozen=True, slots=True)
class Path(GraphicObject):
    """SVG path に近い中間表現。"""

    commands: tuple[PathCommand, ...]

    def __post_init__(self) -> None:
        normalized_commands = tuple(self.commands)
        if not normalized_commands:
            raise ValueError("Path には 1 つ以上の command が必要です。")
        if not isinstance(normalized_commands[0], MoveTo):
            raise ValueError("Path の先頭 command は MoveTo である必要があります。")
        object.__setattr__(self, "commands", normalized_commands)

    def local_bounds(self) -> Bounds:
        collected_bounds: list[Bounds] = []
        collected_points: list[Point] = []
        current_point: Point | None = None
        subpath_start: Point | None = None

        for command in self.commands:
            if isinstance(command, MoveTo):
                current_point = command.point
                subpath_start = command.point
                collected_points.append(command.point)
                continue

            if isinstance(command, LineTo):
                current_point = command.point
                collected_points.append(command.point)
                continue

            if isinstance(command, ArcTo):
                if current_point is None:
                    raise ValueError("ArcTo の前に current point が必要です。")
                pad_x = max(abs(command.radius_x_mm), abs(command.radius_y_mm))
                pad_y = pad_x if command.rotation_deg % 180 else abs(command.radius_y_mm)
                collected_bounds.append(
                    Bounds(
                        min(current_point.x_mm, command.end.x_mm) - pad_x,
                        min(current_point.y_mm, command.end.y_mm) - pad_y,
                        max(current_point.x_mm, command.end.x_mm) + pad_x,
                        max(current_point.y_mm, command.end.y_mm) + pad_y,
                    )
                )
                current_point = command.end
                collected_points.append(command.end)
                continue

            if isinstance(command, ClosePath) and subpath_start is not None:
                current_point = subpath_start
                collected_points.append(subpath_start)

        base_bounds = Bounds.from_points(tuple(collected_points))
        for extra_bounds in collected_bounds:
            base_bounds = base_bounds.union(extra_bounds)
        return base_bounds


@dataclass(frozen=True, slots=True)
class Group(GraphicObject):
    """複数図形のまとまり。"""

    items: tuple["RenderableGraphic", ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))

    def local_bounds(self) -> Bounds:
        if not self.items:
            return Bounds.zero()

        result: Bounds | None = None
        for item in self.items:
            item_bounds = item.bounds()
            result = item_bounds if result is None else result.union(item_bounds)
        return result if result is not None else Bounds.zero()


@dataclass(frozen=True, slots=True, kw_only=True)
class LayeredGraphic:
    """白レイヤと通常色レイヤを分けて扱う。"""

    white_layer: tuple["RenderableGraphic", ...] = ()
    color_layer: tuple["RenderableGraphic", ...] = ()
    metadata: MetadataDict = field(default_factory=dict)

    def all_items(self) -> tuple["RenderableGraphic", ...]:
        return (*self.white_layer, *self.color_layer)

    def bounds(self) -> Bounds:
        items = self.all_items()
        if not items:
            return Bounds.zero()

        result: Bounds | None = None
        for item in items:
            item_bounds = item.bounds()
            result = item_bounds if result is None else result.union(item_bounds)
        return result if result is not None else Bounds.zero()


RenderableGraphic: TypeAlias = GraphicObject | Group
