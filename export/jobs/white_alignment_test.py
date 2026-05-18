"""白デカール紙向けアウトライン整合の確認用テスト job。"""

from __future__ import annotations

from core import LayeredGraphic
from decals import generate_circle, generate_line, generate_ring
from export.decal_paper import prepare_layout_for_white_decal
from layouts import SheetPlacement, create_postcard_sheet

EXPORT_NAME = "white_alignment_test"
TARGET_SCALE = "1/144"
DESCRIPTION = "白下地と色レイヤの位置合わせを確認するための簡易テストシート"
EXPORT_METADATA = {
    "job_kind": "test",
    "sheet_kind": "postcard",
    "paper_mode": "white_decal",
    "surface_color": "#68707b",
}


def _white_backed_ring(outer_radius_mm: float, inner_radius_mm: float) -> LayeredGraphic:
    white = generate_ring(outer_radius_mm + 0.25, inner_radius_mm - 0.25, color="#ffffff")
    color = generate_ring(outer_radius_mm, inner_radius_mm, color="#000000")
    return LayeredGraphic(
        white_layer=white.color_layer,
        color_layer=color.color_layer,
        metadata={
            "type": "white_alignment_ring",
            "outer_radius_mm": outer_radius_mm,
            "inner_radius_mm": inner_radius_mm,
        },
    )


def build_layout():
    horizontal = generate_line(20, 0.4)
    vertical = generate_line(20, 0.4).rotated(90.0)
    marker = LayeredGraphic(
        white_layer=generate_circle(1.4, color="#ffffff").color_layer,
        color_layer=generate_circle(1.0, color="#000000").color_layer,
        metadata={"type": "white_alignment_marker"},
    )
    ring = _white_backed_ring(7.0, 5.6)

    base_layout = create_postcard_sheet(
        (
            SheetPlacement(graphic=ring, x_mm=30.0, y_mm=35.0, anchor="center", identifier="ring_1"),
            SheetPlacement(graphic=horizontal, x_mm=30.0, y_mm=35.0, anchor="center", identifier="cross_h"),
            SheetPlacement(graphic=vertical, x_mm=30.0, y_mm=35.0, anchor="center", identifier="cross_v"),
            SheetPlacement(graphic=marker, x_mm=70.0, y_mm=35.0, anchor="center", identifier="marker_1"),
            SheetPlacement(graphic=_white_backed_ring(5.0, 4.0), x_mm=70.0, y_mm=70.0, anchor="center", identifier="ring_2"),
        ),
        title="White Alignment Test",
        description=DESCRIPTION,
        metadata={"job_kind": "test"},
    )
    return prepare_layout_for_white_decal(
        base_layout,
        surface_color=EXPORT_METADATA["surface_color"],
        outline_width_mm=0.25,
    )
