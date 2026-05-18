"""線系デカールをまとめて並べるテンプレート。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, TypeAlias

from decals import generate_line, generate_polyline
from layouts import SheetLayout, pack_a4_sheet, pack_postcard_sheet

from ..presets import LayoutPreset, default_preset_for_sheet

PolylineSpec: TypeAlias = tuple[Sequence[float], Sequence[float]]


def build_line_decal_sheet(
    lengths_mm: Sequence[float],
    *,
    polyline_specs: Sequence[PolylineSpec] = (),
    width_mm: float = 0.4,
    color: str = "#000000",
    sheet_kind: Literal["postcard", "a4"] = "postcard",
    preset: LayoutPreset | None = None,
    title: str | None = None,
    description: str | None = None,
) -> SheetLayout:
    """line / polyline 図形群をシートへ自動配置する。"""

    resolved_preset = default_preset_for_sheet(sheet_kind) if preset is None else preset
    graphics = [generate_line(length_mm, width_mm, color=color) for length_mm in lengths_mm]
    graphics.extend(
        generate_polyline(polyline_lengths, polyline_angles, width_mm, color=color)
        for polyline_lengths, polyline_angles in polyline_specs
    )

    metadata = {
        "template_name": "line_decal_sheet",
        "preset_name": resolved_preset.name,
        "line_count": len(lengths_mm),
        "polyline_count": len(polyline_specs),
    }
    if sheet_kind == "postcard":
        return pack_postcard_sheet(
            tuple(graphics),
            margin_mm=resolved_preset.margin_mm,
            gap_mm=resolved_preset.gap_mm,
            allow_rotation=resolved_preset.allow_rotation,
            title=title,
            description=description,
            metadata=metadata,
        )
    return pack_a4_sheet(
        tuple(graphics),
        margin_mm=resolved_preset.margin_mm,
        gap_mm=resolved_preset.gap_mm,
        allow_rotation=resolved_preset.allow_rotation,
        title=title,
        description=description,
        metadata=metadata,
    )


__all__ = [
    "build_line_decal_sheet",
]
