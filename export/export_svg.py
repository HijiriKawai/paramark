"""SVG export の共通実装。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import TypeAlias

from core import BASE_MODEL_SCALE, MetadataDict, SvgDocument, merge_metadata, save_svg
from layouts import SheetLayout

DEFAULT_OUTPUT_DIR = Path("output")
JobModuleRef: TypeAlias = str | ModuleType


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportJobSpec:
    """export job に付随するメタ情報。"""

    export_name: str
    target_scale: str = BASE_MODEL_SCALE.to_text()
    description: str | None = None
    metadata: MetadataDict = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.build_filename("svg")

    def build_filename(self, extension: str) -> str:
        """拡張子付きの成果物名を返す。"""

        normalized_extension = extension.lstrip(".")
        return f"{self.export_name}.{normalized_extension}"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportResult:
    """export 実行結果。"""

    output_path: Path
    document: SvgDocument
    layout: SheetLayout
    spec: ExportJobSpec


def render_export_document(
    layout: SheetLayout,
    *,
    spec: ExportJobSpec,
    strict: bool = True,
) -> SvgDocument:
    """SheetLayout と job metadata から export 用 SvgDocument を組み立てる。"""

    document = layout.to_document(strict=strict)
    resolved_title = document.title or spec.export_name
    resolved_description = document.description or spec.description
    resolved_metadata = merge_metadata(
        document.metadata,
        spec.metadata,
        export_name=spec.export_name,
        export_target_scale=spec.target_scale,
    )
    if spec.description:
        resolved_metadata["export_description"] = spec.description

    return SvgDocument(
        width_mm=document.width_mm,
        height_mm=document.height_mm,
        items=document.items,
        title=resolved_title,
        description=resolved_description,
        metadata=resolved_metadata,
        view_box=document.view_box,
    )


def export_layout_svg(
    layout: SheetLayout,
    *,
    spec: ExportJobSpec,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    strict: bool = True,
    pretty: bool = True,
) -> ExportResult:
    """SheetLayout を SVG ファイルとして書き出す。"""

    document = render_export_document(layout, spec=spec, strict=strict)
    resolved_output_dir = Path(output_dir)
    output_path = resolved_output_dir / spec.build_filename("svg")
    saved_path = save_svg(output_path, document, pretty=pretty)
    return ExportResult(
        output_path=saved_path,
        document=document,
        layout=layout,
        spec=spec,
    )


def extract_job_spec(job_module: ModuleType) -> ExportJobSpec:
    """job module の metadata 定義から ExportJobSpec を生成する。"""

    export_name = getattr(job_module, "EXPORT_NAME")
    target_scale = getattr(job_module, "TARGET_SCALE", BASE_MODEL_SCALE.to_text())
    description = getattr(job_module, "DESCRIPTION", None)
    metadata = getattr(job_module, "EXPORT_METADATA", {})
    return ExportJobSpec(
        export_name=export_name,
        target_scale=target_scale,
        description=description,
        metadata=dict(metadata),
    )


def _resolve_job_module(job_module: JobModuleRef) -> ModuleType:
    if isinstance(job_module, ModuleType):
        return job_module
    return import_module(job_module)


def export_job_module(
    job_module: JobModuleRef,
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    strict: bool = True,
    pretty: bool = True,
) -> ExportResult:
    """job module の `build_layout()` を呼んで SVG を出力する。"""

    resolved_module = _resolve_job_module(job_module)
    build_layout = getattr(resolved_module, "build_layout")
    layout = build_layout()
    spec = extract_job_spec(resolved_module)
    return export_layout_svg(
        layout,
        spec=spec,
        output_dir=output_dir,
        strict=strict,
        pretty=pretty,
    )


def main(argv: list[str] | None = None) -> int:
    """`python -m export.export_svg export.jobs.line_pack_postcard` 用 CLI。"""

    parser = argparse.ArgumentParser(description="paramark export job runner")
    parser.add_argument("job_module", help="実行する export.jobs モジュール")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="出力先ディレクトリ")
    parser.add_argument("--no-strict", action="store_true", help="シート範囲チェックを緩和する")
    parser.add_argument("--compact", action="store_true", help="整形なしで SVG を出力する")
    args = parser.parse_args(argv)

    result = export_job_module(
        args.job_module,
        output_dir=args.output_dir,
        strict=not args.no_strict,
        pretty=not args.compact,
    )
    print(result.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
