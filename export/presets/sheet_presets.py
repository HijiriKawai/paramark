"""再利用可能なシート preset 定義。"""

from __future__ import annotations

from dataclasses import dataclass, field

from core import MetadataDict


@dataclass(frozen=True, slots=True, kw_only=True)
class LayoutPreset:
    """シート構成の再利用 preset。"""

    name: str
    margin_mm: float
    gap_mm: float
    allow_rotation: bool = False
    description: str | None = None
    metadata: MetadataDict = field(default_factory=dict)


POSTCARD_SIMPLE = LayoutPreset(
    name="postcard_simple",
    margin_mm=5.0,
    gap_mm=2.0,
    allow_rotation=False,
    description="ハガキサイズ向けの標準 preset",
    metadata={"preset_kind": "postcard"},
)

A4_DENSE = LayoutPreset(
    name="a4_dense",
    margin_mm=6.0,
    gap_mm=1.5,
    allow_rotation=False,
    description="A4 を高密度に使う preset",
    metadata={"preset_kind": "a4"},
)

STENCIL_MARGIN = LayoutPreset(
    name="stencil_margin",
    margin_mm=10.0,
    gap_mm=3.0,
    allow_rotation=False,
    description="ステンシル用途で余白を厚めに取る preset",
    metadata={"preset_kind": "stencil"},
)

_PRESETS = {
    POSTCARD_SIMPLE.name: POSTCARD_SIMPLE,
    A4_DENSE.name: A4_DENSE,
    STENCIL_MARGIN.name: STENCIL_MARGIN,
}


def resolve_layout_preset(name: str) -> LayoutPreset:
    """preset 名から LayoutPreset を返す。"""

    try:
        return _PRESETS[name]
    except KeyError as error:
        available = ", ".join(sorted(_PRESETS))
        raise ValueError(f"未知の preset です: {name}. 利用可能: {available}") from error


def default_preset_for_sheet(sheet_kind: str) -> LayoutPreset:
    """シート種別ごとの既定 preset を返す。"""

    normalized = sheet_kind.lower()
    if normalized == "postcard":
        return POSTCARD_SIMPLE
    if normalized == "a4":
        return A4_DENSE
    raise ValueError("sheet_kind は 'postcard' または 'a4' を指定してください。")
