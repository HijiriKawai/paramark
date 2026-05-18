"""白デカール紙向けのサンプル job。"""

from __future__ import annotations

from export.templates import build_white_decal_sample_layout

EXPORT_NAME = "white_decal_sample"
TARGET_SCALE = "1/144"
DESCRIPTION = "白デカール紙向けの printable サンプルシート"
EXPORT_METADATA = {
    "job_kind": "sample",
    "sheet_kind": "postcard",
    "paper_mode": "white_decal",
    "surface_color": "#5c6773",
}


def build_layout():
    layout = build_white_decal_sample_layout(
        surface_color=EXPORT_METADATA["surface_color"],
        outline_width_mm=0.3,
    )
    return layout
