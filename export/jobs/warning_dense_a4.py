"""warning パターンを A4 へ高密度配置するサンプル job。"""

from __future__ import annotations

from export.presets import A4_DENSE
from export.templates import build_mono_warning_sheet

EXPORT_NAME = "warning_dense_a4"
TARGET_SCALE = "1/144"
DESCRIPTION = "A4 に単色 warning パターンを高密度に並べたテストシート"
EXPORT_METADATA = {
    "job_kind": "usage",
    "sheet_kind": "a4",
}


def build_layout():
    return build_mono_warning_sheet(
        tile_width_mm=22.0,
        tile_height_mm=8.0,
        angle_deg=45.0,
        pitch_mm=2.0,
        repeat_count=72,
        sheet_kind="a4",
        preset=A4_DENSE,
        title="Warning Dense A4",
        description=DESCRIPTION,
    )
