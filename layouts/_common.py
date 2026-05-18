"""シートレイアウト共通実装。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, TypeAlias

from core import (
    Bounds,
    LayeredGraphic,
    MetadataDict,
    PackingItem,
    SheetSize,
    SvgDocument,
    merge_metadata,
    pack_shelves,
)
from core.units import ensure_mm

PlacementAnchor: TypeAlias = Literal["top_left", "center", "origin"]


def _ensure_non_negative_mm(name: str, value: float) -> float:
    resolved = ensure_mm(value)
    if resolved < 0:
        raise ValueError(f"{name} は 0 以上で指定してください。")
    return resolved


def _item_fits_within(item_bounds: Bounds, container_bounds: Bounds) -> bool:
    return (
        item_bounds.min_x_mm >= container_bounds.min_x_mm
        and item_bounds.min_y_mm >= container_bounds.min_y_mm
        and item_bounds.max_x_mm <= container_bounds.max_x_mm
        and item_bounds.max_y_mm <= container_bounds.max_y_mm
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SheetPlacement:
    """シート上の配置指定。"""

    graphic: LayeredGraphic
    x_mm: float
    y_mm: float
    anchor: PlacementAnchor = "top_left"
    identifier: str | None = None
    metadata: MetadataDict = field(default_factory=dict)

    def resolved_graphic(self) -> LayeredGraphic:
        """アンカーを解決した配置済み graphic を返す。"""

        base_bounds = self.graphic.bounds()
        x_mm = ensure_mm(self.x_mm)
        y_mm = ensure_mm(self.y_mm)

        if self.anchor == "top_left":
            translate_x_mm = x_mm - base_bounds.min_x_mm
            translate_y_mm = y_mm - base_bounds.min_y_mm
        elif self.anchor == "center":
            translate_x_mm = x_mm - (base_bounds.min_x_mm + (base_bounds.width_mm / 2.0))
            translate_y_mm = y_mm - (base_bounds.min_y_mm + (base_bounds.height_mm / 2.0))
        elif self.anchor == "origin":
            translate_x_mm = x_mm
            translate_y_mm = y_mm
        else:
            raise ValueError(f"未対応の anchor です: {self.anchor}")

        placement_metadata = merge_metadata(
            self.metadata,
            placement_anchor=self.anchor,
            placement_x_mm=x_mm,
            placement_y_mm=y_mm,
        )
        if self.identifier:
            placement_metadata["placement_id"] = self.identifier

        return self.graphic.translated(translate_x_mm, translate_y_mm).with_metadata(**placement_metadata)

    def bounds(self) -> Bounds:
        return self.resolved_graphic().bounds()


@dataclass(frozen=True, slots=True, kw_only=True)
class SheetLayout:
    """シート 1 枚分の配置定義。"""

    sheet_size: SheetSize
    placements: tuple[SheetPlacement, ...] = ()
    margin_mm: float = 0.0
    title: str | None = None
    description: str | None = None
    metadata: MetadataDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "placements", tuple(self.placements))
        object.__setattr__(self, "margin_mm", _ensure_non_negative_mm("margin_mm", self.margin_mm))

    @property
    def usable_bounds(self) -> Bounds:
        return Bounds(
            self.margin_mm,
            self.margin_mm,
            self.sheet_size.width_mm - self.margin_mm,
            self.sheet_size.height_mm - self.margin_mm,
        )

    def add_placement(
        self,
        graphic: LayeredGraphic,
        *,
        x_mm: float,
        y_mm: float,
        anchor: PlacementAnchor = "top_left",
        identifier: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> "SheetLayout":
        """placement を 1 つ追加した新しい layout を返す。"""

        placement = SheetPlacement(
            graphic=graphic,
            x_mm=x_mm,
            y_mm=y_mm,
            anchor=anchor,
            identifier=identifier,
            metadata={} if metadata is None else dict(metadata),
        )
        return replace(self, placements=(*self.placements, placement))

    def placed_graphics(self) -> tuple[LayeredGraphic, ...]:
        return tuple(placement.resolved_graphic() for placement in self.placements)

    def overflow_placements(self) -> tuple[SheetPlacement, ...]:
        return tuple(
            placement
            for placement in self.placements
            if not _item_fits_within(placement.bounds(), self.usable_bounds)
        )

    def to_document(self, *, strict: bool = True) -> SvgDocument:
        """配置済みシートを SvgDocument へ変換する。"""

        overflow = self.overflow_placements()
        if strict and overflow:
            labels = [placement.identifier or f"index:{index}" for index, placement in enumerate(overflow, start=1)]
            raise ValueError(f"シート範囲外へはみ出した placement があります: {', '.join(labels)}")

        document_metadata = merge_metadata(
            self.metadata,
            sheet_name=self.sheet_size.name,
            sheet_width_mm=self.sheet_size.width_mm,
            sheet_height_mm=self.sheet_size.height_mm,
            sheet_margin_mm=self.margin_mm,
            placement_count=len(self.placements),
        )
        return SvgDocument(
            width_mm=self.sheet_size.width_mm,
            height_mm=self.sheet_size.height_mm,
            items=self.placed_graphics(),
            title=self.title,
            description=self.description,
            metadata=document_metadata,
        )


def pack_graphics_on_sheet(
    graphics: Sequence[LayeredGraphic],
    *,
    sheet_size: SheetSize,
    margin_mm: float = 0.0,
    gap_mm: float = 0.0,
    min_gap_mm: float = 1.0,
    allow_rotation: bool = False,
    title: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SheetLayout:
    """図形群を簡易 shelf packing で自動配置する。"""

    resolved_margin = _ensure_non_negative_mm("margin_mm", margin_mm)
    resolved_gap = _ensure_non_negative_mm("gap_mm", gap_mm)
    resolved_min_gap = _ensure_non_negative_mm("min_gap_mm", min_gap_mm)
    effective_gap = max(resolved_gap, resolved_min_gap)
    usable_width_mm = sheet_size.width_mm - (resolved_margin * 2.0)
    usable_height_mm = sheet_size.height_mm - (resolved_margin * 2.0)
    if usable_width_mm <= 0 or usable_height_mm <= 0:
        raise ValueError("margin_mm が大きすぎて配置可能領域がありません。")

    packing_items: list[PackingItem] = []
    indexed_graphics: dict[str, LayeredGraphic] = {}
    for index, graphic in enumerate(graphics, start=1):
        identifier = f"item_{index}"
        graphic_bounds = graphic.bounds()
        indexed_graphics[identifier] = graphic
        packing_items.append(
            PackingItem(
                identifier=identifier,
                width_mm=graphic_bounds.width_mm,
                height_mm=graphic_bounds.height_mm,
                allow_rotation=allow_rotation,
            )
        )

    packing_result = pack_shelves(
        packing_items,
        sheet_width_mm=usable_width_mm,
        sheet_height_mm=usable_height_mm,
        gap_mm=effective_gap,
    )
    if packing_result.unplaced_items:
        names = ", ".join(item.identifier for item in packing_result.unplaced_items)
        raise ValueError(f"シートへ配置しきれない図形があります: {names}")

    placements: list[SheetPlacement] = []
    for packed_item in packing_result.placed_items:
        graphic = indexed_graphics[packed_item.identifier]
        if packed_item.rotated:
            bounds = graphic.bounds()
            graphic = graphic.rotated(
                90.0,
                origin_x_mm=bounds.min_x_mm + (bounds.width_mm / 2.0),
                origin_y_mm=bounds.min_y_mm + (bounds.height_mm / 2.0),
            )

        placements.append(
            SheetPlacement(
                graphic=graphic,
                x_mm=resolved_margin + packed_item.x_mm,
                y_mm=resolved_margin + packed_item.y_mm,
                anchor="top_left",
                identifier=packed_item.identifier,
                metadata={"packed": True},
            )
        )

    layout_metadata = merge_metadata(
        metadata,
        packed=True,
        packed_gap_mm=effective_gap,
        packed_requested_gap_mm=resolved_gap,
        packed_min_gap_mm=resolved_min_gap,
        packed_allow_rotation=allow_rotation,
        packed_fill_ratio=packing_result.fill_ratio,
        packed_used_width_mm=packing_result.used_width_mm,
        packed_used_height_mm=packing_result.used_height_mm,
    )
    return SheetLayout(
        sheet_size=sheet_size,
        placements=tuple(placements),
        margin_mm=resolved_margin,
        title=title,
        description=description,
        metadata=layout_metadata,
    )
