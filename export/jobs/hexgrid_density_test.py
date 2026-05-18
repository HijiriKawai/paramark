"""六角格子密度の確認用テスト job。"""

from __future__ import annotations

from decals import generate_dot_grid, generate_hex_grid
from layouts import SheetPlacement, create_a4_sheet

EXPORT_NAME = "hexgrid_density_test"
TARGET_SCALE = "1/144"
DESCRIPTION = "cell/pitch の違いによる格子密度を比較するための A4 テストシート"
EXPORT_METADATA = {
    "job_kind": "experiment",
    "sheet_kind": "a4",
}


def build_layout():
    layout = create_a4_sheet(
        margin_mm=8.0,
        title="Hexgrid Density Test",
        description=DESCRIPTION,
        metadata={"job_kind": "experiment"},
    )
    placements = (
        SheetPlacement(
            graphic=generate_hex_grid(3.0, 48.0, 36.0, line_width_mm=0.2),
            x_mm=12.0,
            y_mm=12.0,
            identifier="hex_3",
        ),
        SheetPlacement(
            graphic=generate_hex_grid(4.5, 48.0, 36.0, line_width_mm=0.2),
            x_mm=72.0,
            y_mm=12.0,
            identifier="hex_45",
        ),
        SheetPlacement(
            graphic=generate_hex_grid(6.0, 48.0, 36.0, line_width_mm=0.2),
            x_mm=132.0,
            y_mm=12.0,
            identifier="hex_6",
        ),
        SheetPlacement(
            graphic=generate_dot_grid(3.0, 0.45, 48.0, 36.0),
            x_mm=12.0,
            y_mm=60.0,
            identifier="dot_3",
        ),
        SheetPlacement(
            graphic=generate_dot_grid(4.5, 0.6, 48.0, 36.0),
            x_mm=72.0,
            y_mm=60.0,
            identifier="dot_45",
        ),
        SheetPlacement(
            graphic=generate_dot_grid(6.0, 0.75, 48.0, 36.0),
            x_mm=132.0,
            y_mm=60.0,
            identifier="dot_6",
        ),
    )
    for placement in placements:
        layout = layout.add_placement(
            placement.graphic,
            x_mm=placement.x_mm,
            y_mm=placement.y_mm,
            anchor=placement.anchor,
            identifier=placement.identifier,
            metadata=placement.metadata,
        )
    return layout
