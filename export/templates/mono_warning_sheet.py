"""単色 warning パターンをまとめるテンプレート。"""

from __future__ import annotations

from typing import Literal

from decals import generate_hazard_stripes
from layouts import SheetLayout, pack_a4_sheet, pack_postcard_sheet

from ..presets import LayoutPreset, default_preset_for_sheet


def build_mono_warning_sheet(
    *,
    tile_width_mm: float = 24.0,
    tile_height_mm: float = 8.0,
    angle_deg: float = 45.0,
    pitch_mm: float = 2.0,
    stripe_width_mm: float | None = None,
    repeat_count: int = 24,
    color: str = "#000000",
    sheet_kind: Literal["postcard", "a4"] = "a4",
    preset: LayoutPreset | None = None,
    title: str | None = None,
    description: str | None = None,
) -> SheetLayout:
    """同一パラメータの warning パターンをシートへ自動配置する。"""

    if repeat_count <= 0:
        raise ValueError("repeat_count は 1 以上で指定してください。")

    resolved_preset = default_preset_for_sheet(sheet_kind) if preset is None else preset
    graphics = tuple(
        generate_hazard_stripes(
            angle_deg=angle_deg,
            pitch_mm=pitch_mm,
            width_mm=tile_width_mm,
            height_mm=tile_height_mm,
            stripe_width_mm=stripe_width_mm,
            color=color,
        )
        for _ in range(repeat_count)
    )
    metadata = {
        "template_name": "mono_warning_sheet",
        "preset_name": resolved_preset.name,
        "repeat_count": repeat_count,
        "angle_deg": angle_deg,
        "pitch_mm": pitch_mm,
    }
    if sheet_kind == "postcard":
        return pack_postcard_sheet(
            graphics,
            margin_mm=resolved_preset.margin_mm,
            gap_mm=resolved_preset.gap_mm,
            allow_rotation=resolved_preset.allow_rotation,
            title=title,
            description=description,
            metadata=metadata,
        )
    return pack_a4_sheet(
        graphics,
        margin_mm=resolved_preset.margin_mm,
        gap_mm=resolved_preset.gap_mm,
        allow_rotation=resolved_preset.allow_rotation,
        title=title,
        description=description,
        metadata=metadata,
    )


__all__ = [
    "build_mono_warning_sheet",
]
