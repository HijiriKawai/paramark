"""ハガキサイズシートの preset。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from core import LayeredGraphic, POSTCARD, SvgDocument

from ._common import SheetLayout, SheetPlacement, pack_graphics_on_sheet

DEFAULT_POSTCARD_MARGIN_MM = 5.0


def create_postcard_sheet(
    placements: Sequence[SheetPlacement] = (),
    *,
    margin_mm: float = DEFAULT_POSTCARD_MARGIN_MM,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SheetLayout:
    """ハガキサイズの SheetLayout を作る。"""

    return SheetLayout(
        sheet_size=POSTCARD,
        placements=tuple(placements),
        margin_mm=margin_mm,
        title=title,
        description=description,
        metadata={} if metadata is None else dict(metadata),
    )


def create_postcard_svg_document(
    placements: Sequence[SheetPlacement] = (),
    *,
    margin_mm: float = DEFAULT_POSTCARD_MARGIN_MM,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
    strict: bool = True,
) -> SvgDocument:
    """ハガキサイズの SvgDocument を直接作る。"""

    return create_postcard_sheet(
        placements,
        margin_mm=margin_mm,
        title=title,
        description=description,
        metadata=metadata,
    ).to_document(strict=strict)


def pack_postcard_sheet(
    graphics: Sequence[LayeredGraphic],
    *,
    margin_mm: float = DEFAULT_POSTCARD_MARGIN_MM,
    gap_mm: float = 2.0,
    allow_rotation: bool = False,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SheetLayout:
    """図形群をハガキサイズへ自動配置する。"""

    return pack_graphics_on_sheet(
        graphics,
        sheet_size=POSTCARD,
        margin_mm=margin_mm,
        gap_mm=gap_mm,
        allow_rotation=allow_rotation,
        title=title,
        description=description,
        metadata=metadata,
    )


__all__ = [
    "DEFAULT_POSTCARD_MARGIN_MM",
    "create_postcard_sheet",
    "create_postcard_svg_document",
    "pack_postcard_sheet",
]
