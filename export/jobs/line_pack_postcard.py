"""線系図形をハガキへ詰めるサンプル job。"""

from __future__ import annotations

from decals import generate_line, generate_polyline
from export.presets import LayoutPreset
from layouts import pack_postcard_sheet

EXPORT_NAME = "line_pack_postcard"
TARGET_SCALE = "1/144"
DESCRIPTION = "ハガキサイズへ line / polyline を自動配置したテストシート"
EXPORT_METADATA = {
    "job_kind": "usage",
    "sheet_kind": "postcard",
}


def build_layout():
    dense_preset = LayoutPreset(
        name="postcard_line_dense",
        margin_mm=3.0,
        gap_mm=1.0,
        min_gap_mm=1.0,
        allow_rotation=False,
        description="line_pack_postcard 用の高密度 preset",
        metadata={"preset_kind": "postcard", "preset_density": "dense"},
    )

    # 線・折れ線のみでバリエーションを稼ぎつつ、高密度に詰める。
    # - 線幅 / linecap / linejoin / start angle を振る
    # - 角度違いの折れ線で高さのある形も混ぜる
    # - packing は deterministic にするため、bounds の大きい順に並べて shelf packing へ入力する

    # 太すぎると視覚的に潰れて「ベタ」に見えやすいので上限を控える。
    widths_mm = (0.2, 0.3, 0.4, 0.6, 0.8, 1.2)
    linecaps = ("butt", "round", "square")
    linejoins = ("round", "miter", "bevel")

    # 使える横幅は (100 - 2*margin)mm。stroke は左右にもはみ出すので少し控えめにする。
    max_core_length_mm = 86

    line_graphics = []
    polyline_graphics = []

    # 直線: 長さ・線幅・cap を広く振って量を稼ぐ（詰め込み優先なので刻みは粗め）
    base_lengths = tuple(range(10, max_core_length_mm + 1, 6))
    for width_index, width_mm in enumerate(widths_mm):
        cap = linecaps[width_index % len(linecaps)]
        # 同じ長さを複数回入れて量を増やす（太い線は棚高さが大きくなるので控えめに）
        if width_mm <= 0.4:
            repeat = 2
        elif width_mm <= 0.8:
            repeat = 1
        else:
            repeat = 1
        for _ in range(repeat):
            for length_mm in base_lengths:
                line_graphics.append(
                    generate_line(
                        length_mm,
                        width_mm,
                        linecap=cap,
                    )
                )

    # 折れ線: 形状パターンを複数、start angle も回して向きを変える
    poly_patterns = (
        # 2 セグメント
        ((10, 10), (90,)),
        ((12, 8), (60,)),
        ((14, 10), (45,)),
        # 3 セグメント
        ((10, 8, 10), (60, -60)),
        ((12, 10, 8), (90, -45)),
        ((16, 10, 12), (30, -75)),
        # 4 セグメント（高さが出やすい）
        ((10, 8, 10, 8), (90, -90, 90)),
        ((12, 8, 12, 8), (60, -120, 60)),
    )
    start_angles = (0.0, 45.0, 90.0, 135.0)

    for pattern_index, (lengths_mm, angles_deg) in enumerate(poly_patterns):
        width_mm = widths_mm[pattern_index % len(widths_mm)]
        cap = linecaps[pattern_index % len(linecaps)]
        join = linejoins[pattern_index % len(linejoins)]
        for start_angle in start_angles:
            # 同一パターンは複数回入れて量を稼ぐ（折れ線は高さが出やすいので控えめに）
            for _ in range(1):
                polyline_graphics.append(
                    generate_polyline(
                        lengths_mm,
                        angles_deg,
                        width_mm,
                        start_angle_deg=start_angle,
                        linecap=cap,
                        linejoin=join,
                    )
                )

    # shelf packing は入力順依存のため、背の低い順→背の高い順に揃えると密度が安定しやすい
    def _sort_key(graphic):
        b = graphic.bounds()
        return (b.height_mm, b.width_mm)

    polyline_sorted = sorted(polyline_graphics, key=_sort_key)
    line_sorted = sorted(line_graphics, key=_sort_key)

    # 折れ線が「末尾削りフォールバック」で全消しされないよう、先頭に少量だけ固定で確保する。
    # 残りは末尾削減の対象にして packing 成立を優先する。
    polyline_head_count = 20
    polyline_head = polyline_sorted[:polyline_head_count]
    shrinkable_sorted = [*line_sorted, *polyline_sorted[polyline_head_count:]]

    graphics_sorted = [*polyline_head, *shrinkable_sorted]

    # 明らかに入らないもの（幅/高さが usable を超える）は除外しておく
    usable_width_mm = 100.0 - (dense_preset.margin_mm * 2.0)
    usable_height_mm = 148.0 - (dense_preset.margin_mm * 2.0)
    graphics_sorted = [
        g
        for g in graphics_sorted
        if (g.bounds().width_mm <= usable_width_mm and g.bounds().height_mm <= usable_height_mm)
    ]

    # 置ききれない場合は shrinkable 部分の末尾を削って再試行（サンプル用途なので「必ず出る」こと優先）
    remaining_shrinkable = [g for g in shrinkable_sorted if g in graphics_sorted]
    last_error: Exception | None = None
    for _ in range(10):
        try:
            return pack_postcard_sheet(
                tuple([*polyline_head, *remaining_shrinkable]),
                margin_mm=dense_preset.margin_mm,
                gap_mm=dense_preset.gap_mm,
                min_gap_mm=dense_preset.min_gap_mm,
                allow_rotation=dense_preset.allow_rotation,
                title="Line Pack Postcard",
                description=DESCRIPTION,
                metadata={
                    "job_kind": "usage",
                    "template_name": "line_pack_postcard",
                    "preset_name": dense_preset.name,
                    "linecap_variants": list(linecaps),
                    "linejoin_variants": list(linejoins),
                    "width_variants_mm": list(widths_mm),
                    "generated_line_count": len(line_graphics),
                    "generated_polyline_count": len(polyline_graphics),
                    "filtered_total_count": len(graphics_sorted),
                    "polyline_head_count": len(polyline_head),
                    "packed_total_count": len(polyline_head) + len(remaining_shrinkable),
                },
            )
        except ValueError as exc:
            last_error = exc
            if len(remaining_shrinkable) < 50:
                break
            # 10% 削る（deterministic）: 末尾（大きめ図形寄り）から削る
            remaining_shrinkable = remaining_shrinkable[: int(len(remaining_shrinkable) * 0.9)]

    raise last_error or RuntimeError("line_pack_postcard の packing に失敗しました")
