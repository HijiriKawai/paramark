"""成果物 export の共通 API。"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .decal_paper import (
    DecalPaperConfig,
    DecalPaperMode,
    prepare_graphic_for_decal_paper,
    prepare_layout_for_clear_decal,
    prepare_layout_for_decal_paper,
    prepare_layout_for_white_decal,
)
# NOTE:
# `python -m export.export_svg ...` 実行時に、package 初期化で `export_svg` を import してしまうと
# runpy から RuntimeWarning が出る。
# ここではトップレベル API は維持しつつ、必要になるまで遅延 import する。

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "DecalPaperConfig",
    "DecalPaperMode",
    "ExportJobSpec",
    "ExportResult",
    "export_job_module",
    "export_job_module_pdf",
    "export_layout_pdf",
    "export_layout_svg",
    "extract_job_spec",
    "prepare_graphic_for_decal_paper",
    "prepare_layout_for_clear_decal",
    "prepare_layout_for_decal_paper",
    "prepare_layout_for_white_decal",
    "render_pdf_bytes",
    "render_export_document",
    "save_pdf",
]


_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # export_svg
    "DEFAULT_OUTPUT_DIR": ("export.export_svg", "DEFAULT_OUTPUT_DIR"),
    "ExportJobSpec": ("export.export_svg", "ExportJobSpec"),
    "ExportResult": ("export.export_svg", "ExportResult"),
    "export_job_module": ("export.export_svg", "export_job_module"),
    "export_layout_svg": ("export.export_svg", "export_layout_svg"),
    "extract_job_spec": ("export.export_svg", "extract_job_spec"),
    "render_export_document": ("export.export_svg", "render_export_document"),
    # export_pdf
    "export_job_module_pdf": ("export.export_pdf", "export_job_module_pdf"),
    "export_layout_pdf": ("export.export_pdf", "export_layout_pdf"),
    "render_pdf_bytes": ("export.export_pdf", "render_pdf_bytes"),
    "save_pdf": ("export.export_pdf", "save_pdf"),
}


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name not in _LAZY_EXPORTS:
        raise AttributeError(name)
    module_name, attr = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:  # pragma: no cover
    return sorted(set(globals().keys()) | set(_LAZY_EXPORTS.keys()))
