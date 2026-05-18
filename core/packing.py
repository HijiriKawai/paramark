"""最小構成の deterministic な shelf packing。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .units import Millimeter, ensure_mm


@dataclass(frozen=True, slots=True)
class PackingItem:
    """配置対象の矩形近似情報。"""

    identifier: str
    width_mm: Millimeter
    height_mm: Millimeter
    margin_mm: Millimeter = 0.0
    allow_rotation: bool = False
    payload: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "width_mm", ensure_mm(self.width_mm))
        object.__setattr__(self, "height_mm", ensure_mm(self.height_mm))
        object.__setattr__(self, "margin_mm", ensure_mm(self.margin_mm))
        if self.width_mm <= 0 or self.height_mm <= 0:
            raise ValueError("PackingItem の width/height は正の値で指定してください。")
        if self.margin_mm < 0:
            raise ValueError("PackingItem の margin_mm は 0 以上で指定してください。")


@dataclass(frozen=True, slots=True)
class PackedItem:
    """配置済みアイテム。"""

    identifier: str
    x_mm: Millimeter
    y_mm: Millimeter
    width_mm: Millimeter
    height_mm: Millimeter
    rotated: bool = False
    payload: Any = None


@dataclass(frozen=True, slots=True)
class PackingResult:
    """packing 結果。"""

    sheet_width_mm: Millimeter
    sheet_height_mm: Millimeter
    placed_items: tuple[PackedItem, ...] = ()
    unplaced_items: tuple[PackingItem, ...] = ()
    used_width_mm: Millimeter = 0.0
    used_height_mm: Millimeter = 0.0

    @property
    def fill_ratio(self) -> float:
        sheet_area = self.sheet_width_mm * self.sheet_height_mm
        if sheet_area <= 0:
            return 0.0
        used_area = sum(item.width_mm * item.height_mm for item in self.placed_items)
        return used_area / sheet_area


@dataclass(slots=True)
class _ShelfState:
    y_mm: Millimeter = 0.0
    height_mm: Millimeter = 0.0
    cursor_x_mm: Millimeter = 0.0
    used_width_mm: Millimeter = 0.0


def _footprint(item: PackingItem, rotated: bool) -> tuple[Millimeter, Millimeter]:
    width_mm = item.height_mm if rotated else item.width_mm
    height_mm = item.width_mm if rotated else item.height_mm
    margin = item.margin_mm * 2.0
    return width_mm + margin, height_mm + margin


def pack_shelves(
    items: list[PackingItem] | tuple[PackingItem, ...],
    *,
    sheet_width_mm: float,
    sheet_height_mm: float,
    gap_mm: float = 0.0,
) -> PackingResult:
    """入力順を保ちながら配置する単純な shelf packing。"""

    normalized_items = tuple(items)
    sheet_width = ensure_mm(sheet_width_mm)
    sheet_height = ensure_mm(sheet_height_mm)
    gap = ensure_mm(gap_mm)

    placed: list[PackedItem] = []
    unplaced: list[PackingItem] = []
    shelf = _ShelfState()
    used_height = 0.0

    for item in normalized_items:
        candidates = [False]
        if item.allow_rotation:
            candidates.append(True)

        chosen_rotation: bool | None = None
        chosen_width = 0.0
        chosen_height = 0.0

        for rotated in candidates:
            footprint_width, footprint_height = _footprint(item, rotated)
            fits_current_shelf = (
                shelf.cursor_x_mm + footprint_width <= sheet_width
                and shelf.y_mm + max(shelf.height_mm, footprint_height) <= sheet_height
            )
            if fits_current_shelf:
                chosen_rotation = rotated
                chosen_width = footprint_width
                chosen_height = footprint_height
                break

        if chosen_rotation is None:
            shelf = _ShelfState(
                y_mm=shelf.y_mm + shelf.height_mm + gap,
                height_mm=0.0,
                cursor_x_mm=0.0,
                used_width_mm=shelf.used_width_mm,
            )

            for rotated in candidates:
                footprint_width, footprint_height = _footprint(item, rotated)
                fits_new_shelf = (
                    footprint_width <= sheet_width and shelf.y_mm + footprint_height <= sheet_height
                )
                if fits_new_shelf:
                    chosen_rotation = rotated
                    chosen_width = footprint_width
                    chosen_height = footprint_height
                    break

        if chosen_rotation is None:
            unplaced.append(item)
            continue

        x_mm = shelf.cursor_x_mm + item.margin_mm
        y_mm = shelf.y_mm + item.margin_mm
        content_width = item.height_mm if chosen_rotation else item.width_mm
        content_height = item.width_mm if chosen_rotation else item.height_mm
        placed.append(
            PackedItem(
                identifier=item.identifier,
                x_mm=x_mm,
                y_mm=y_mm,
                width_mm=content_width,
                height_mm=content_height,
                rotated=chosen_rotation,
                payload=item.payload,
            )
        )

        shelf.cursor_x_mm += chosen_width + gap
        shelf.height_mm = max(shelf.height_mm, chosen_height)
        shelf.used_width_mm = max(shelf.used_width_mm, shelf.cursor_x_mm - gap if shelf.cursor_x_mm else 0.0)
        used_height = max(used_height, shelf.y_mm + shelf.height_mm)

    return PackingResult(
        sheet_width_mm=sheet_width,
        sheet_height_mm=sheet_height,
        placed_items=tuple(placed),
        unplaced_items=tuple(unplaced),
        used_width_mm=shelf.used_width_mm,
        used_height_mm=used_height,
    )
