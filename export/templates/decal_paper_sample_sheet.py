"""透明 / 白デカール紙の挙動差を確認するサンプルテンプレート。"""

from __future__ import annotations

from core import LayeredGraphic
from decals import (
    generate_circle,
    generate_double_stripe,
    generate_hazard_stripes,
    generate_regular_polygon,
    generate_ring,
)
from layouts import SheetPlacement, create_postcard_sheet

from ..decal_paper import prepare_layout_for_clear_decal, prepare_layout_for_white_decal


def _white_region_only(graphic: LayeredGraphic, *, region_type: str) -> LayeredGraphic:
    return LayeredGraphic(
        white_layer=graphic.color_layer,
        metadata={
            "type": region_type,
        },
    )


def _white_region_with_black_ring(radius_mm: float, ring_width_mm: float) -> LayeredGraphic:
    white_region = generate_circle(radius_mm)
    outline_ring = generate_ring(radius_mm + (ring_width_mm / 2.0), radius_mm - (ring_width_mm / 2.0), color="#111111")
    return LayeredGraphic(
        white_layer=white_region.color_layer,
        color_layer=outline_ring.color_layer,
        metadata={
            "type": "white_region_with_black_ring",
            "radius_mm": radius_mm,
            "ring_width_mm": ring_width_mm,
        },
    )


def build_decal_paper_sample_base_layout():
    """下地違いサンプルの共通レイアウトを生成する。"""

    white_hex = _white_region_only(
        generate_regular_polygon(6, 6.0),
        region_type="white_hex_region",
    )
    white_roundel = _white_region_with_black_ring(5.5, 0.5)
    white_marker = LayeredGraphic(
        white_layer=generate_circle(2.5).color_layer,
        color_layer=generate_ring(3.1, 2.8, color="#111111").color_layer,
        metadata={"type": "white_marker"},
    )
    hazard = generate_hazard_stripes(
        angle_deg=45.0,
        pitch_mm=2.0,
        width_mm=24.0,
        height_mm=8.0,
        color="#202020",
    )
    stripes = generate_double_stripe(20.0, 0.8, 0.45, color="#8c1d18")

    return create_postcard_sheet(
        (
            SheetPlacement(graphic=white_hex, x_mm=16.0, y_mm=16.0, identifier="white_hex"),
            SheetPlacement(graphic=white_roundel, x_mm=58.0, y_mm=21.0, anchor="center", identifier="white_roundel"),
            SheetPlacement(graphic=white_marker, x_mm=58.0, y_mm=46.0, anchor="center", identifier="white_marker"),
            SheetPlacement(graphic=hazard, x_mm=16.0, y_mm=64.0, identifier="hazard"),
            SheetPlacement(graphic=stripes, x_mm=16.0, y_mm=92.0, identifier="double_stripe"),
        ),
        title="Decal Paper Sample Base",
        description="透明デカール紙 / 白デカール紙の差を確認する共通サンプル",
        metadata={
            "template_name": "decal_paper_sample_sheet",
            "sample_kind": "paper_mode_comparison",
        },
    )


def build_clear_decal_sample_layout():
    """透明デカール紙向けの printable サンプルを返す。"""

    base_layout = build_decal_paper_sample_base_layout()
    return prepare_layout_for_clear_decal(
        base_layout,
        metadata={
            "sample_paper_mode": "clear_decal",
        },
    )


def build_white_decal_sample_layout(
    *,
    surface_color: str = "#5c6773",
    outline_width_mm: float = 0.3,
):
    """白デカール紙向けの printable サンプルを返す。"""

    base_layout = build_decal_paper_sample_base_layout()
    return prepare_layout_for_white_decal(
        base_layout,
        surface_color=surface_color,
        outline_width_mm=outline_width_mm,
        metadata={
            "sample_paper_mode": "white_decal",
        },
    )


__all__ = [
    "build_clear_decal_sample_layout",
    "build_decal_paper_sample_base_layout",
    "build_white_decal_sample_layout",
]
