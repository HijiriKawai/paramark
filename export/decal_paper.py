"""デカール紙種別ごとの printable layer 変換。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal, TypeAlias

from core import LayeredGraphic, MetadataDict, Style, merge_metadata
from core.geometry import Group, GraphicObject, RenderableGraphic
from core.units import ensure_mm
from layouts import SheetLayout, SheetPlacement

DecalPaperMode: TypeAlias = Literal["clear_decal", "white_decal"]


@dataclass(frozen=True, slots=True, kw_only=True)
class DecalPaperConfig:
    """デカール紙ごとの printable 化設定。"""

    paper_mode: DecalPaperMode
    surface_color: str | None = None
    outline_width_mm: float = 0.25
    include_white_region_preview: bool = False
    metadata: MetadataDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "outline_width_mm", ensure_mm(self.outline_width_mm))
        if self.outline_width_mm <= 0:
            raise ValueError("outline_width_mm は正の値で指定してください。")
        if self.paper_mode not in ("clear_decal", "white_decal"):
            raise ValueError("paper_mode は 'clear_decal' または 'white_decal' を指定してください。")
        if self.paper_mode == "white_decal" and not self.surface_color:
            raise ValueError("white_decal では surface_color の指定が必要です。")


def _outline_style(style: Style | None, *, surface_color: str, outline_width_mm: float) -> Style:
    base = style or Style()
    return Style(
        stroke=surface_color,
        fill="none",
        stroke_width_mm=outline_width_mm,
        stroke_linecap=base.stroke_linecap or "round",
        stroke_linejoin=base.stroke_linejoin or "round",
        opacity=base.opacity,
    )


def _surface_match_outline(
    graphic: RenderableGraphic,
    *,
    surface_color: str,
    outline_width_mm: float,
) -> RenderableGraphic:
    if isinstance(graphic, Group):
        return replace(
            graphic,
            items=tuple(
                _surface_match_outline(
                    item,
                    surface_color=surface_color,
                    outline_width_mm=outline_width_mm,
                )
                for item in graphic.items
            ),
            metadata=merge_metadata(
                graphic.metadata,
                printable_role="surface_match_outline_group",
                surface_color=surface_color,
                outline_width_mm=outline_width_mm,
            ),
        )

    if not isinstance(graphic, GraphicObject):
        raise TypeError(f"未対応の graphic type です: {type(graphic)!r}")

    return replace(
        graphic,
        style=_outline_style(
            graphic.style,
            surface_color=surface_color,
            outline_width_mm=outline_width_mm,
        ),
        metadata=merge_metadata(
            graphic.metadata,
            printable_role="surface_match_outline",
            surface_color=surface_color,
            outline_width_mm=outline_width_mm,
        ),
    )


def prepare_graphic_for_decal_paper(
    graphic: LayeredGraphic,
    *,
    config: DecalPaperConfig,
) -> LayeredGraphic:
    """設計用 LayeredGraphic を printable な構成へ変換する。"""

    preview_white_layer = graphic.white_layer if config.include_white_region_preview else ()

    if config.paper_mode == "clear_decal":
        metadata = merge_metadata(
            graphic.metadata,
            config.metadata,
            paper_mode=config.paper_mode,
            white_region_behavior="transparent_unprinted",
            white_region_count=len(graphic.white_layer),
        )
        return LayeredGraphic(
            white_layer=preview_white_layer,
            color_layer=graphic.color_layer,
            metadata=metadata,
        )

    outlined_white_regions = tuple(
        _surface_match_outline(
            item,
            surface_color=config.surface_color or "#808080",
            outline_width_mm=config.outline_width_mm,
        )
        for item in graphic.white_layer
    )
    metadata = merge_metadata(
        graphic.metadata,
        config.metadata,
        paper_mode=config.paper_mode,
        surface_color=config.surface_color,
        outline_width_mm=config.outline_width_mm,
        white_region_behavior="paper_white_with_surface_outline",
        white_region_count=len(graphic.white_layer),
    )
    return LayeredGraphic(
        white_layer=preview_white_layer,
        color_layer=(*outlined_white_regions, *graphic.color_layer),
        metadata=metadata,
    )


def prepare_layout_for_decal_paper(
    layout: SheetLayout,
    *,
    config: DecalPaperConfig,
) -> SheetLayout:
    """layout 全体へデカール紙種別の printable 変換を適用する。"""

    prepared_placements: list[SheetPlacement] = []
    for placement in layout.placements:
        positioned_graphic = placement.resolved_graphic()
        prepared_graphic = prepare_graphic_for_decal_paper(positioned_graphic, config=config)
        if not prepared_graphic.all_items():
            continue
        prepared_placements.append(
            SheetPlacement(
                graphic=prepared_graphic,
                x_mm=0.0,
                y_mm=0.0,
                anchor="origin",
                identifier=placement.identifier,
            )
        )

    layout_metadata = merge_metadata(
        layout.metadata,
        config.metadata,
        paper_mode=config.paper_mode,
        surface_color=config.surface_color,
        outline_width_mm=config.outline_width_mm,
        white_region_preview=config.include_white_region_preview,
    )
    return SheetLayout(
        sheet_size=layout.sheet_size,
        placements=tuple(prepared_placements),
        margin_mm=layout.margin_mm,
        title=layout.title,
        description=layout.description,
        metadata=layout_metadata,
    )


def prepare_layout_for_clear_decal(
    layout: SheetLayout,
    *,
    include_white_region_preview: bool = False,
    metadata: MetadataDict | None = None,
) -> SheetLayout:
    """透明デカール紙向け printable layout を生成する。"""

    return prepare_layout_for_decal_paper(
        layout,
        config=DecalPaperConfig(
            paper_mode="clear_decal",
            include_white_region_preview=include_white_region_preview,
            metadata={} if metadata is None else dict(metadata),
        ),
    )


def prepare_layout_for_white_decal(
    layout: SheetLayout,
    *,
    surface_color: str,
    outline_width_mm: float = 0.25,
    include_white_region_preview: bool = False,
    metadata: MetadataDict | None = None,
) -> SheetLayout:
    """白デカール紙向け printable layout を生成する。"""

    return prepare_layout_for_decal_paper(
        layout,
        config=DecalPaperConfig(
            paper_mode="white_decal",
            surface_color=surface_color,
            outline_width_mm=outline_width_mm,
            include_white_region_preview=include_white_region_preview,
            metadata={} if metadata is None else dict(metadata),
        ),
    )


__all__ = [
    "DecalPaperConfig",
    "DecalPaperMode",
    "prepare_graphic_for_decal_paper",
    "prepare_layout_for_clear_decal",
    "prepare_layout_for_decal_paper",
    "prepare_layout_for_white_decal",
]
