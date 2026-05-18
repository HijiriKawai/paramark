"""線系図形をハガキへ詰めるサンプル job。"""

from __future__ import annotations

from export.templates import build_line_decal_sheet

EXPORT_NAME = "line_pack_postcard"
TARGET_SCALE = "1/144"
DESCRIPTION = "ハガキサイズへ line / polyline を自動配置したテストシート"
EXPORT_METADATA = {
    "job_kind": "usage",
    "sheet_kind": "postcard",
}


def build_layout():
    return build_line_decal_sheet(
        lengths_mm=(4, 6, 8, 10, 12, 15, 20, 25, 30, 35),
        polyline_specs=(
            ((10, 10), (45,)),
            ((12, 10, 12), (60, -60)),
            ((20, 12, 16), (30, -45)),
        ),
        width_mm=0.4,
        sheet_kind="postcard",
        title="Line Pack Postcard",
        description=DESCRIPTION,
    )
