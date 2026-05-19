"""Decals テンプレの registry。

Issue #6 の「生成単位の明確化（最重要）」のため、
UI から列挙可能なテンプレ一覧をここで定義する。

- factory: params -> LayeredGraphic
- default_params: UI の初期値
- presets: 定型のパラメータセット

注意:
- params は UI から来るため型が曖昧になりやすい。
  ここでは最低限の型変換を行い、生成関数側のバリデーションに委ねる。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, TypeAlias

from core import LayeredGraphic
from decals import (
    generate_arc,
    generate_circle,
    generate_dot_grid,
    generate_double_stripe,
    generate_hazard_stripes,
    generate_hex_grid,
    generate_line,
    generate_polyline,
    generate_regular_polygon,
    generate_ring,
    generate_stripe,
)

Params: TypeAlias = dict[str, Any]
Factory: TypeAlias = Callable[[Mapping[str, Any]], LayeredGraphic]


def _as_float(params: Mapping[str, Any], key: str) -> float:
    value = params[key]
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} は数値として解釈できません: {value!r}") from error


def _as_int(params: Mapping[str, Any], key: str) -> int:
    value = params[key]
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} は整数として解釈できません: {value!r}") from error


def _as_str(params: Mapping[str, Any], key: str) -> str:
    value = params[key]
    if value is None:
        raise ValueError(f"{key} は None では指定できません")
    return str(value)


def _as_float_list(params: Mapping[str, Any], key: str) -> list[float]:
    value = params[key]
    if isinstance(value, str):
        raw = [part.strip() for part in value.replace("\n", ",").split(",")]
        parts = [part for part in raw if part]
        return [float(part) for part in parts]
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value]
    raise ValueError(f"{key} はカンマ区切り文字列または配列で指定してください: {value!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class DecalTemplate:
    """Decals の生成テンプレ。"""

    id: str
    title: str
    description: str
    factory: Factory
    default_params: Params = field(default_factory=dict)
    presets: dict[str, Params] = field(default_factory=dict)

    def build(self, params: Mapping[str, Any] | None = None) -> LayeredGraphic:
        resolved = dict(self.default_params)
        if params:
            resolved.update(params)
        return self.factory(resolved)


def resolve_decal_template(template_id: str) -> DecalTemplate:
    try:
        return _TEMPLATES_BY_ID[template_id]
    except KeyError as error:
        available = ", ".join(sorted(_TEMPLATES_BY_ID))
        raise ValueError(f"未知の template_id です: {template_id}. 利用可能: {available}") from error


def _template_line() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_line(
            _as_float(params, "length_mm"),
            _as_float(params, "width_mm"),
            color=_as_str(params, "color"),
            linecap=_as_str(params, "linecap"),
        )

    return DecalTemplate(
        id="line",
        title="Line",
        description="水平な直線ストローク（Polyline）",
        factory=factory,
        default_params={
            "length_mm": 20.0,
            "width_mm": 0.4,
            "color": "#000000",
            "linecap": "butt",
        },
        presets={
            "thin": {"width_mm": 0.2},
            "medium": {"width_mm": 0.4},
            "thick": {"width_mm": 0.8},
        },
    )


def _template_polyline() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_polyline(
            lengths_mm=_as_float_list(params, "lengths_mm"),
            angles_deg=_as_float_list(params, "angles_deg"),
            width_mm=_as_float(params, "width_mm"),
            start_angle_deg=_as_float(params, "start_angle_deg"),
            color=_as_str(params, "color"),
            linecap=_as_str(params, "linecap"),
            linejoin=_as_str(params, "linejoin"),
        )

    return DecalTemplate(
        id="polyline",
        title="Polyline",
        description="相対角指定の多段折れ線",
        factory=factory,
        default_params={
            "lengths_mm": [20.0, 20.0, 20.0],
            "angles_deg": [60.0, -120.0],
            "width_mm": 0.4,
            "start_angle_deg": 0.0,
            "color": "#000000",
            "linecap": "butt",
            "linejoin": "round",
        },
        presets={
            "L-shape": {"lengths_mm": [30.0, 20.0], "angles_deg": [90.0]},
            "Zigzag": {"lengths_mm": [12.0, 12.0, 12.0, 12.0], "angles_deg": [60.0, -120.0, 60.0]},
        },
    )


def _template_circle() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_circle(_as_float(params, "radius_mm"), color=_as_str(params, "color"))

    return DecalTemplate(
        id="circle",
        title="Circle",
        description="原点中心の塗り円",
        factory=factory,
        default_params={
            "radius_mm": 5.0,
            "color": "#000000",
        },
        presets={
            "r2": {"radius_mm": 2.0},
            "r5": {"radius_mm": 5.0},
            "r10": {"radius_mm": 10.0},
        },
    )


def _template_ring() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_ring(
            _as_float(params, "outer_radius_mm"),
            _as_float(params, "inner_radius_mm"),
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="ring",
        title="Ring",
        description="原点中心のリング（even-odd）",
        factory=factory,
        default_params={
            "outer_radius_mm": 10.0,
            "inner_radius_mm": 8.0,
            "color": "#000000",
        },
        presets={
            "thin": {"outer_radius_mm": 10.0, "inner_radius_mm": 9.2},
            "standard": {"outer_radius_mm": 10.0, "inner_radius_mm": 8.0},
        },
    )


def _template_arc() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_arc(
            _as_float(params, "radius_mm"),
            _as_float(params, "sweep_angle_deg"),
            _as_float(params, "width_mm"),
            start_angle_deg=_as_float(params, "start_angle_deg"),
            color=_as_str(params, "color"),
            segment_count=None,
            linecap=_as_str(params, "linecap"),
        )

    return DecalTemplate(
        id="arc",
        title="Arc",
        description="原点中心の円弧（Polyline 近似）",
        factory=factory,
        default_params={
            "radius_mm": 10.0,
            "sweep_angle_deg": 120.0,
            "start_angle_deg": 0.0,
            "width_mm": 0.4,
            "color": "#000000",
            "linecap": "butt",
        },
        presets={
            "90deg": {"sweep_angle_deg": 90.0},
            "180deg": {"sweep_angle_deg": 180.0},
            "270deg": {"sweep_angle_deg": 270.0},
        },
    )


def _template_polygon() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_regular_polygon(
            _as_int(params, "side_count"),
            _as_float(params, "radius_mm"),
            rotation_deg=_as_float(params, "rotation_deg"),
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="polygon",
        title="Polygon",
        description="原点中心の正多角形（塗り）",
        factory=factory,
        default_params={
            "side_count": 6,
            "radius_mm": 8.0,
            "rotation_deg": -90.0,
            "color": "#000000",
        },
        presets={
            "triangle": {"side_count": 3},
            "square": {"side_count": 4},
            "hex": {"side_count": 6},
        },
    )


def _template_stripe() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_stripe(
            _as_float(params, "length_mm"),
            _as_float(params, "width_mm"),
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="stripe",
        title="Stripe",
        description="単線ストライプ（塗り長方形）",
        factory=factory,
        default_params={
            "length_mm": 30.0,
            "width_mm": 1.5,
            "color": "#000000",
        },
        presets={
            "narrow": {"width_mm": 0.8},
            "wide": {"width_mm": 2.5},
        },
    )


def _template_double_stripe() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_double_stripe(
            _as_float(params, "length_mm"),
            _as_float(params, "gap_mm"),
            _as_float(params, "stripe_width_mm"),
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="double_stripe",
        title="Double Stripe",
        description="平行2本ストライプ（塗り）",
        factory=factory,
        default_params={
            "length_mm": 35.0,
            "gap_mm": 1.0,
            "stripe_width_mm": 1.0,
            "color": "#000000",
        },
        presets={
            "tight": {"gap_mm": 0.4},
            "spaced": {"gap_mm": 2.0},
        },
    )


def _template_hazard() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_hazard_stripes(
            _as_float(params, "angle_deg"),
            _as_float(params, "pitch_mm"),
            _as_float(params, "width_mm"),
            _as_float(params, "height_mm"),
            stripe_width_mm=None,
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="hazard",
        title="Hazard",
        description="矩形内の警告斜線パターン（塗り）",
        factory=factory,
        default_params={
            "angle_deg": 45.0,
            "pitch_mm": 3.0,
            "width_mm": 25.0,
            "height_mm": 10.0,
            "color": "#000000",
        },
        presets={
            "dense": {"pitch_mm": 2.0},
            "sparse": {"pitch_mm": 4.0},
        },
    )


def _template_hex_grid() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_hex_grid(
            _as_float(params, "cell_mm"),
            _as_float(params, "width_mm"),
            _as_float(params, "height_mm"),
            line_width_mm=_as_float(params, "line_width_mm"),
            color=_as_str(params, "color"),
            orientation=_as_str(params, "orientation"),
        )

    return DecalTemplate(
        id="hex_grid",
        title="Hex Grid",
        description="矩形内に収まる六角格子（線）",
        factory=factory,
        default_params={
            "cell_mm": 2.0,
            "width_mm": 30.0,
            "height_mm": 20.0,
            "line_width_mm": 0.2,
            "color": "#000000",
            "orientation": "flat",
        },
        presets={
            "flat": {"orientation": "flat"},
            "pointy": {"orientation": "pointy"},
            "fine": {"cell_mm": 1.2, "line_width_mm": 0.15},
        },
    )


def _template_dot_grid() -> DecalTemplate:
    def factory(params: Mapping[str, Any]) -> LayeredGraphic:
        return generate_dot_grid(
            _as_float(params, "pitch_mm"),
            _as_float(params, "radius_mm"),
            _as_float(params, "width_mm"),
            _as_float(params, "height_mm"),
            color=_as_str(params, "color"),
        )

    return DecalTemplate(
        id="dot_grid",
        title="Dot Grid",
        description="矩形内に収まるドット格子（塗り）",
        factory=factory,
        default_params={
            "pitch_mm": 2.5,
            "radius_mm": 0.4,
            "width_mm": 30.0,
            "height_mm": 20.0,
            "color": "#000000",
        },
        presets={
            "fine": {"pitch_mm": 2.0, "radius_mm": 0.35},
            "bold": {"pitch_mm": 3.0, "radius_mm": 0.6},
        },
    )


TEMPLATES: list[DecalTemplate] = [
    _template_line(),
    _template_polyline(),
    _template_circle(),
    _template_ring(),
    _template_arc(),
    _template_polygon(),
    _template_stripe(),
    _template_double_stripe(),
    _template_hazard(),
    _template_hex_grid(),
    _template_dot_grid(),
]

_TEMPLATES_BY_ID = {template.id: template for template in TEMPLATES}
