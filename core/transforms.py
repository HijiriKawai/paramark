"""2D affine 変換の共通実装。"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

from .units import Degrees, Millimeter, ensure_mm


@dataclass(frozen=True, slots=True)
class AffineTransform:
    """SVG と互換性のある 2D affine 行列。"""

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def apply_xy(self, x_mm: float, y_mm: float) -> tuple[Millimeter, Millimeter]:
        return (
            (self.a * x_mm) + (self.c * y_mm) + self.e,
            (self.b * x_mm) + (self.d * y_mm) + self.f,
        )

    def to_svg_matrix(self) -> str:
        return f"matrix({self.a:g} {self.b:g} {self.c:g} {self.d:g} {self.e:g} {self.f:g})"


def _multiply(left: AffineTransform, right: AffineTransform) -> AffineTransform:
    """left(right(point)) となる合成行列を返す。"""

    return AffineTransform(
        a=(left.a * right.a) + (left.c * right.b),
        b=(left.b * right.a) + (left.d * right.b),
        c=(left.a * right.c) + (left.c * right.d),
        d=(left.b * right.c) + (left.d * right.d),
        e=(left.a * right.e) + (left.c * right.f) + left.e,
        f=(left.b * right.e) + (left.d * right.f) + left.f,
    )


def compose(*transforms: AffineTransform) -> AffineTransform:
    """与えた順に適用される変換を 1 つへまとめる。"""

    combined = AffineTransform()
    for transform in transforms:
        combined = _multiply(transform, combined)
    return combined


def translate(x_mm: float = 0.0, y_mm: float = 0.0) -> AffineTransform:
    return AffineTransform(e=ensure_mm(x_mm), f=ensure_mm(y_mm))


def scale(
    x_factor: float,
    y_factor: float | None = None,
    *,
    origin_x_mm: float = 0.0,
    origin_y_mm: float = 0.0,
) -> AffineTransform:
    """任意原点付きの拡大縮小。"""

    resolved_y = x_factor if y_factor is None else y_factor
    base = AffineTransform(a=float(x_factor), d=float(resolved_y))
    if origin_x_mm == 0.0 and origin_y_mm == 0.0:
        return base
    return compose(
        translate(-origin_x_mm, -origin_y_mm),
        base,
        translate(origin_x_mm, origin_y_mm),
    )


def rotate(
    angle_deg: Degrees,
    *,
    origin_x_mm: float = 0.0,
    origin_y_mm: float = 0.0,
) -> AffineTransform:
    """任意原点付きの回転。"""

    theta = radians(angle_deg)
    base = AffineTransform(
        a=cos(theta),
        b=sin(theta),
        c=-sin(theta),
        d=cos(theta),
    )
    if origin_x_mm == 0.0 and origin_y_mm == 0.0:
        return base
    return compose(
        translate(-origin_x_mm, -origin_y_mm),
        base,
        translate(origin_x_mm, origin_y_mm),
    )
