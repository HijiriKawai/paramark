"""透明 / 白デカール紙の挙動差を確認するサンプルテンプレート。

このテンプレートは「混在図形を小さめに大量生成してハガキへ詰める」ことで、
印刷密度や白領域の扱い（透明 / 白デカール紙）をまとめて確認できるようにする。

- clear_decal: white_layer は未印刷（透明）として扱う
- white_decal: white_layer に貼り付け先色のアウトライン(stroke)を付けて、紙白を白として見せる

サンプル用途のため、配置しきれない場合は deterministic に末尾から削って再試行する。
"""

from __future__ import annotations

from core import LayeredGraphic, POSTCARD
from decals import (
    generate_circle,
    generate_dot_grid,
    generate_double_stripe,
    generate_hazard_stripes,
    generate_hex_grid,
    generate_regular_polygon,
    generate_ring,
    generate_stripe,
)
from layouts import SheetLayout, pack_postcard_sheet

from ..decal_paper import prepare_layout_for_clear_decal, prepare_layout_for_white_decal


def _white_region_only(graphic: LayeredGraphic, *, region_type: str) -> LayeredGraphic:
    return LayeredGraphic(
        white_layer=graphic.color_layer,
        metadata={
            "type": region_type,
        },
    )


def _white_region_with_black_ring(radius_mm: float, ring_width_mm: float) -> LayeredGraphic:
    white_region = generate_circle(radius_mm)
    outline_ring = generate_ring(
        radius_mm + (ring_width_mm / 2.0),
        radius_mm - (ring_width_mm / 2.0),
        color="#111111",
    )
    return LayeredGraphic(
        white_layer=white_region.color_layer,
        color_layer=outline_ring.color_layer,
        metadata={
            "type": "white_region_with_black_ring",
            "radius_mm": radius_mm,
            "ring_width_mm": ring_width_mm,
        },
    )


def _normalized(graphic: LayeredGraphic) -> LayeredGraphic:
    bounds = graphic.bounds()
    return graphic.translated(-bounds.min_x_mm, -bounds.min_y_mm)


def _build_mixed_small_graphics() -> tuple[LayeredGraphic, ...]:
    """小さめの混在図形を大量に生成する（deterministic）。"""

    items: list[LayeredGraphic] = []

    # 白領域のみ（透明では未印刷、白デカールでは紙白＋アウトライン）
    for side_count in (3, 4, 5, 6, 8):
        for radius_mm in (1.8, 2.5, 3.2, 4.0):
            items.append(
                _normalized(
                    _white_region_only(
                        generate_regular_polygon(side_count, radius_mm),
                        region_type=f"white_polygon_{side_count}",
                    ).with_metadata(size_kind="small")
                )
            )

    for radius_mm in (1.5, 2.0, 2.8, 3.5):
        items.append(
            _normalized(
                _white_region_only(
                    generate_circle(radius_mm),
                    region_type="white_circle_region",
                ).with_metadata(size_kind="small")
            )
        )

    # 白領域＋黒リング（白デカールでのアウトライン確認に向く）
    for radius_mm in (2.2, 3.0, 3.8):
        for ring_width_mm in (0.35, 0.5):
            items.append(_normalized(_white_region_with_black_ring(radius_mm, ring_width_mm)))

    # 白マーカー（白領域＋小さな黒リング）
    for radius_mm in (1.2, 1.6, 2.0, 2.5):
        items.append(
            _normalized(
                LayeredGraphic(
                    white_layer=generate_circle(radius_mm).color_layer,
                    color_layer=generate_ring(radius_mm + 0.55, radius_mm + 0.2, color="#111111").color_layer,
                    metadata={"type": "white_marker", "radius_mm": radius_mm},
                )
            )
        )

    # 色のみの混在図形（密度・パターン確認）
    for width_mm in (10.0, 14.0, 18.0, 22.0):
        for height_mm in (3.5, 5.0, 6.5):
            items.append(
                _normalized(
                    generate_hazard_stripes(
                        angle_deg=45.0,
                        pitch_mm=2.0,
                        width_mm=width_mm,
                        height_mm=height_mm,
                        color="#202020",
                    )
                )
            )

    for length_mm in (8.0, 12.0, 16.0, 20.0, 28.0, 36.0):
        for width_mm in (0.6, 1.0, 1.6):
            items.append(_normalized(generate_stripe(length_mm, width_mm, color="#111111")))

    for length_mm in (10.0, 14.0, 18.0, 24.0, 30.0, 38.0):
        for gap_mm in (0.6, 1.0):
            for stripe_width_mm in (0.3, 0.45, 0.6):
                items.append(
                    _normalized(generate_double_stripe(length_mm, gap_mm, stripe_width_mm, color="#8c1d18"))
                )

    for outer_radius_mm in (2.0, 3.2, 4.4, 5.6):
        items.append(_normalized(generate_ring(outer_radius_mm, outer_radius_mm - 0.6, color="#111111")))

    # 小タイル状パターン
    for tile_w, tile_h, pitch, radius in (
        (10.0, 10.0, 2.5, 0.25),
        (12.0, 8.0, 2.0, 0.22),
        (14.0, 10.0, 2.8, 0.3),
    ):
        items.append(_normalized(generate_dot_grid(pitch, radius, tile_w, tile_h, color="#111111")))

    for tile_w, tile_h, cell_mm, line_w in (
        (12.0, 10.0, 1.8, 0.25),
        (14.0, 12.0, 2.2, 0.25),
        (16.0, 10.0, 2.0, 0.3),
    ):
        items.append(
            _normalized(
                generate_hex_grid(
                    cell_mm,
                    tile_w,
                    tile_h,
                    line_width_mm=line_w,
                    color="#111111",
                    orientation="flat",
                )
            )
        )

    # 量を増やす：小さいものは複製して密度を上げる（deterministic）
    duplicated: list[LayeredGraphic] = []
    for index, item in enumerate(items):
        bounds = item.bounds()
        is_small = bounds.width_mm <= 20.0 and bounds.height_mm <= 10.0
        repeat = 4 if is_small else 2
        for repeat_index in range(repeat):
            duplicated.append(item.with_metadata(sample_index=index + 1, sample_repeat=repeat_index + 1))

    # shelf packing は入力順依存なので、背の低い順→背の高い順に揃えると密度が安定する
    def _sort_key(graphic: LayeredGraphic) -> tuple[float, float]:
        b = graphic.bounds()
        return (b.height_mm, b.width_mm)

    return tuple(sorted(duplicated, key=_sort_key))


def build_decal_paper_sample_base_layout(
    *,
    margin_mm: float = 3.0,
    gap_mm: float = 1.0,
) -> SheetLayout:
    """下地違いサンプルの共通レイアウトを生成する。"""

    graphics = _build_mixed_small_graphics()

    # 置ききれない場合は末尾（大きめ図形寄り）から削る
    remaining: tuple[LayeredGraphic, ...] = graphics

    # まず明らかに入らないものは除外
    usable_width_mm = POSTCARD.width_mm - (margin_mm * 2.0)
    usable_height_mm = POSTCARD.height_mm - (margin_mm * 2.0)
    remaining = tuple(
        g
        for g in remaining
        if (g.bounds().width_mm <= usable_width_mm and g.bounds().height_mm <= usable_height_mm)
    )

    last_error: Exception | None = None
    for _ in range(10):
        try:
            return pack_postcard_sheet(
                remaining,
                margin_mm=margin_mm,
                gap_mm=gap_mm,
                allow_rotation=False,
                title="Decal Paper Sample Base",
                description="透明デカール紙 / 白デカール紙の差を確認する共通サンプル（混在図形・高密度）",
                metadata={
                    "template_name": "decal_paper_sample_sheet",
                    "sample_kind": "paper_mode_comparison",
                    "generated_item_count": len(graphics),
                    "filtered_item_count": len(remaining),
                    "sheet_width_mm": POSTCARD.width_mm,
                    "sheet_height_mm": POSTCARD.height_mm,
                },
            )
        except ValueError as exc:
            last_error = exc
            if len(remaining) < 30:
                break
            remaining = remaining[: int(len(remaining) * 0.9)]

    raise last_error or RuntimeError("decal_paper_sample_sheet の packing に失敗しました")


def build_clear_decal_sample_layout() -> SheetLayout:
    """透明デカール紙向けの printable サンプルを返す。"""

    base_layout = build_decal_paper_sample_base_layout()
    return prepare_layout_for_clear_decal(
        base_layout,
        include_white_region_preview=True,
        metadata={
            "sample_paper_mode": "clear_decal",
            "note": "clear_decal_sample はサンプル視認性のため white_region_preview を有効化",
        },
    )


def build_white_decal_sample_layout(
    *,
    surface_color: str = "#5c6773",
    outline_width_mm: float = 0.3,
) -> SheetLayout:
    """白デカール紙向けの printable サンプルを返す。"""

    # 白デカール紙向けはアウトライン追加で外形が stroke 幅/2 だけ膨らむ。
    # packing 時点で少し内側へ寄せ、layout の margin 定義自体は基準値のままに戻す。
    base_margin_mm = 3.0
    safety_inset_mm = outline_width_mm / 2.0

    packed_layout = build_decal_paper_sample_base_layout(margin_mm=base_margin_mm + safety_inset_mm)
    prepared_layout = prepare_layout_for_white_decal(
        packed_layout,
        surface_color=surface_color,
        outline_width_mm=outline_width_mm,
        metadata={
            "sample_paper_mode": "white_decal",
        },
    )

    metadata = dict(prepared_layout.metadata)
    metadata.update(
        {
            "base_margin_mm": base_margin_mm,
            "packing_margin_mm": base_margin_mm + safety_inset_mm,
            "packing_safety_inset_mm": safety_inset_mm,
        }
    )
    return SheetLayout(
        sheet_size=prepared_layout.sheet_size,
        placements=prepared_layout.placements,
        margin_mm=base_margin_mm,
        title=prepared_layout.title,
        description=prepared_layout.description,
        metadata=metadata,
    )


__all__ = [
    "build_clear_decal_sample_layout",
    "build_decal_paper_sample_base_layout",
    "build_white_decal_sample_layout",
]
