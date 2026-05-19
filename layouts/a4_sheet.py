"""A4 シートの preset。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from core import A4, LayeredGraphic, SvgDocument

from ._common import SheetLayout, SheetPlacement, pack_graphics_on_sheet

DEFAULT_A4_MARGIN_MM = 8.0


def create_a4_sheet(
    placements: Sequence[SheetPlacement] = (),
    *,
    margin_mm: float = DEFAULT_A4_MARGIN_MM,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SheetLayout:
    """A4 サイズの SheetLayout を作る。"""

    return SheetLayout(
        sheet_size=A4,
        placements=tuple(placements),
        margin_mm=margin_mm,
        title=title,
        description=description,
        metadata={} if metadata is None else dict(metadata),
    )


def create_a4_svg_document(
    placements: Sequence[SheetPlacement] = (),
    *,
    margin_mm: float = DEFAULT_A4_MARGIN_MM,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
    strict: bool = True,
) -> SvgDocument:
    """A4 サイズの SvgDocument を直接作る。"""

    return create_a4_sheet(
        placements,
        margin_mm=margin_mm,
        title=title,
        description=description,
        metadata=metadata,
    ).to_document(strict=strict)


def pack_a4_sheet(
    graphics: Sequence[LayeredGraphic],
    *,
    margin_mm: float = DEFAULT_A4_MARGIN_MM,
    gap_mm: float = 2.0,
    min_gap_mm: float = 1.0,
    allow_rotation: bool = False,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SheetLayout:
    """図形群を A4 サイズへ自動配置する。"""

    return pack_graphics_on_sheet(
        graphics,
        sheet_size=A4,
        margin_mm=margin_mm,
        gap_mm=gap_mm,
        min_gap_mm=min_gap_mm,
        allow_rotation=allow_rotation,
        title=title,
        description=description,
        metadata=metadata,
    )


__all__ = [
    "DEFAULT_A4_MARGIN_MM",
    "create_a4_sheet",
    "create_a4_svg_document",
    "pack_a4_sheet",
]
