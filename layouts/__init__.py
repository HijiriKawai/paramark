"""シートレイアウトの共通 API とプリセット。"""

from ._common import (
    PlacementAnchor,
    SheetLayout,
    SheetPlacement,
    pack_graphics_on_sheet,
)
from .a4_sheet import (
    DEFAULT_A4_MARGIN_MM,
    create_a4_sheet,
    create_a4_svg_document,
    pack_a4_sheet,
)
from .postcard_sheet import (
    DEFAULT_POSTCARD_MARGIN_MM,
    create_postcard_sheet,
    create_postcard_svg_document,
    pack_postcard_sheet,
)

__all__ = [
    "DEFAULT_A4_MARGIN_MM",
    "DEFAULT_POSTCARD_MARGIN_MM",
    "PlacementAnchor",
    "SheetLayout",
    "SheetPlacement",
    "create_a4_sheet",
    "create_a4_svg_document",
    "create_postcard_sheet",
    "create_postcard_svg_document",
    "pack_a4_sheet",
    "pack_graphics_on_sheet",
    "pack_postcard_sheet",
]
