"""透明デカール紙向けのサンプル job。"""

from __future__ import annotations

from export.templates import build_clear_decal_sample_layout

EXPORT_NAME = "clear_decal_sample"
TARGET_SCALE = "1/144"
DESCRIPTION = "透明デカール紙向けの printable サンプルシート"
EXPORT_METADATA = {
    "job_kind": "sample",
    "sheet_kind": "postcard",
    "paper_mode": "clear_decal",
}


def build_layout():
    layout = build_clear_decal_sample_layout()
    return layout
