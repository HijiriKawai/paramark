"""SVG カタログアプリ（Streamlit）。

Issue #6 の MVP 実装:
- Decals: `decals/templates` registry から一覧し、パラメータ編集→SVG生成→プレビュー
- Jobs: `export/jobs/*.py` を一覧し、実行→SVG生成→プレビュー
- Outputs: `output/**/*.svg` を一覧し、既存ファイルをプレビュー

実行例:
- `uv run streamlit run apps/catalog_app.py`

注意:
- 本アプリはローカル開発用の簡易 UI。
- Jobs 実行は任意コード実行になり得るため、実行対象は `export/jobs` のみに限定する。
"""

from __future__ import annotations

import sys
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import streamlit as st
import streamlit.components.v1 as components

# `streamlit run apps/catalog_app.py` は実行ディレクトリが `apps/` になりやすく、
# リポジトリルート（= core/ decals/ export/ layouts/ がある場所）が import パスに入らない。
# このアプリはローカル開発用途のため、起動時に明示的にルートを追加する。
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core import SvgDocument, merge_metadata, render_svg_document, save_svg
from decals.templates import TEMPLATES, resolve_decal_template
from export.export_svg import export_job_module
from layouts import SheetPlacement, create_postcard_sheet


ROOT_DIR = REPO_ROOT
OUTPUT_DIR = ROOT_DIR / "output"
CATALOG_DIR = OUTPUT_DIR / "catalog_app"
DECAL_CACHE_DIR = CATALOG_DIR / "decals"
JOB_CACHE_DIR = CATALOG_DIR / "jobs"


@dataclass(frozen=True, slots=True)
class FileEntry:
    label: str
    path: Path


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()[:12]


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KiB"
    return f"{value / (1024 * 1024):.1f} MiB"


def _read_svg(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _preview_svg(svg_text: str, *, height: int = 640) -> None:
    # Streamlit 側に「SVGそのもの」を渡すと表示が崩れることがあるため、HTML として埋め込む。
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <style>
      body {{ margin: 0; padding: 0; }}
      svg {{ width: 100%; height: auto; }}
    </style>
  </head>
  <body>
    {svg_text}
  </body>
</html>"""
    components.html(html, height=height, scrolling=True)


def _build_decal_document_single_canvas(
    *,
    template_id: str,
    graphic,
    params: Mapping[str, Any],
    padding_mm: float = 2.0,
) -> SvgDocument:
    bounds = graphic.bounds()
    translated = graphic.translated(-bounds.min_x_mm + padding_mm, -bounds.min_y_mm + padding_mm)
    width_mm = bounds.width_mm + (padding_mm * 2.0)
    height_mm = bounds.height_mm + (padding_mm * 2.0)

    metadata = merge_metadata(
        getattr(graphic, "metadata", {}),
        catalog_source="decals",
        catalog_template_id=template_id,
        catalog_params=dict(params),
        canvas_padding_mm=padding_mm,
    )
    return SvgDocument(
        width_mm=width_mm,
        height_mm=height_mm,
        items=(translated,),
        title=f"decal:{template_id}",
        description="Decal template preview (single canvas)",
        metadata=metadata,
    )


def _build_decal_document_on_postcard(
    *,
    template_id: str,
    graphic,
    params: Mapping[str, Any],
    margin_mm: float = 6.0,
) -> SvgDocument:
    # 実運用に近い見え方確認用（中央配置）。
    layout = create_postcard_sheet(
        placements=(
            SheetPlacement(
                graphic=graphic,
                x_mm=50.0,
                y_mm=74.0,
                anchor="center",
                identifier=f"decal:{template_id}",
            ),
        ),
        margin_mm=margin_mm,
        title=f"decal:{template_id}",
        description="Decal template preview (postcard)",
        metadata={
            "catalog_source": "decals",
            "catalog_template_id": template_id,
            "catalog_params": dict(params),
        },
    )
    return layout.to_document(strict=True)


def _coerce_widget_value(value: Any) -> Any:
    # Streamlit の number_input は int/float の区別が曖昧になりやすいので、
    # 入力値はそのまま保持し、テンプレ側 factory で解釈する。
    return value


def _edit_params_form(default_params: Mapping[str, Any], *, state_key: str) -> dict[str, Any]:
    if state_key not in st.session_state:
        st.session_state[state_key] = dict(default_params)

    params: dict[str, Any] = dict(st.session_state[state_key])

    for name, value in default_params.items():
        current = params.get(name, value)
        if isinstance(current, bool):
            params[name] = _coerce_widget_value(st.checkbox(name, value=bool(current)))
        elif isinstance(current, int) and not isinstance(current, bool):
            params[name] = _coerce_widget_value(
                st.number_input(name, value=int(current), step=1)
            )
        elif isinstance(current, float):
            params[name] = _coerce_widget_value(
                st.number_input(name, value=float(current), step=0.1, format="%.4f")
            )
        elif isinstance(current, (list, tuple)):
            text_value = ",".join(str(item) for item in current)
            params[name] = st.text_input(name, value=text_value)
        else:
            params[name] = st.text_input(name, value=str(current))

    st.session_state[state_key] = dict(params)
    return params


def _list_job_modules() -> list[str]:
    jobs_dir = ROOT_DIR / "export" / "jobs"
    modules: list[str] = []
    for path in sorted(jobs_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        if path.name.startswith("_"):
            continue
        modules.append(f"export.jobs.{path.stem}")
    return modules


def _list_output_svgs() -> list[FileEntry]:
    if not OUTPUT_DIR.exists():
        return []

    entries: list[FileEntry] = []
    for path in sorted(OUTPUT_DIR.rglob("*.svg")):
        # output/.gitkeep のような例外は拡張子が違うので除外される
        rel = path.relative_to(ROOT_DIR)
        stat = path.stat()
        label = f"{rel.as_posix()}  ({_format_bytes(stat.st_size)})"
        entries.append(FileEntry(label=label, path=path))
    return entries


def main() -> None:
    st.set_page_config(page_title="paramark catalog", layout="wide")

    st.title("paramark catalog")

    left, center, right = st.columns([1.2, 2.2, 1.4], gap="large")

    with left:
        source = st.selectbox("Source", ["Decals", "Jobs", "Outputs"], index=0)

        if source == "Decals":
            template_labels = [f"{template.id}: {template.title}" for template in TEMPLATES]
            selected_label = st.selectbox("Templates", template_labels)
            template_id = selected_label.split(":", 1)[0]
            selected = resolve_decal_template(template_id)
            selection = {"kind": "decal", "template": selected}
        elif source == "Jobs":
            modules = _list_job_modules()
            selected_module = st.selectbox("Jobs", modules)
            selection = {"kind": "job", "module": selected_module}
        else:
            outputs = _list_output_svgs()
            if outputs:
                selected_output = st.selectbox("Outputs", outputs, format_func=lambda e: e.label)
                selection = {"kind": "output", "path": selected_output.path}
            else:
                st.info("output 配下に SVG がありません")
                selection = {"kind": "output", "path": None}

    with right:
        if selection["kind"] == "decal":
            template = selection["template"]
            st.subheader("Parameters")

            preset_names = ["custom", *sorted(template.presets.keys())]
            chosen_preset = st.selectbox("Preset", preset_names, index=0, key=f"preset:{template.id}")
            params_state_key = f"params:{template.id}"

            if chosen_preset != "custom":
                if st.button("Apply preset"):
                    base = dict(template.default_params)
                    base.update(template.presets[chosen_preset])
                    st.session_state[params_state_key] = base

            render_mode = st.selectbox(
                "Render mode",
                ["Single canvas", "Postcard"],
                index=0,
                help="MVP は single canvas。postcard は見え方確認用。",
            )

            params = _edit_params_form(template.default_params, state_key=params_state_key)
            if st.button("Generate", type="primary"):
                DECAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                payload = {"template_id": template.id, "params": params, "render_mode": render_mode}
                digest = _stable_hash(payload)
                output_path = DECAL_CACHE_DIR / f"{template.id}__{digest}.svg"

                if not output_path.exists():
                    graphic = template.build(params)
                    if render_mode == "Postcard":
                        document = _build_decal_document_on_postcard(
                            template_id=template.id,
                            graphic=graphic,
                            params=params,
                        )
                    else:
                        document = _build_decal_document_single_canvas(
                            template_id=template.id,
                            graphic=graphic,
                            params=params,
                        )
                    save_svg(output_path, document, pretty=True)

                st.session_state["last_output_path"] = str(output_path)
                st.success(f"Saved: {output_path.relative_to(ROOT_DIR)}")

        elif selection["kind"] == "job":
            module = selection["module"]
            st.subheader("Job")
            st.write(f"Module: `{module}`")

            if st.button("Run job", type="primary"):
                JOB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                digest = _stable_hash({"job_module": module})
                output_path = JOB_CACHE_DIR / f"{module.split('.')[-1]}__{digest}.svg"

                if not output_path.exists():
                    # export_job_module は export_name のファイル名で保存するため、一度生成してから移動する。
                    tmp_dir = JOB_CACHE_DIR / "_tmp"
                    result = export_job_module(module, output_dir=tmp_dir, strict=True, pretty=True)
                    result.output_path.replace(output_path)
                st.session_state["last_output_path"] = str(output_path)
                st.success(f"Saved: {output_path.relative_to(ROOT_DIR)}")

        else:
            path = selection.get("path")
            st.subheader("Output")
            if path is not None:
                stat = path.stat()
                st.write(f"Path: `{path.relative_to(ROOT_DIR)}`")
                st.write(f"Size: {_format_bytes(stat.st_size)}")
                st.write(f"Modified: {stat.st_mtime:.0f}")

    with center:
        st.subheader("Preview")
        last = st.session_state.get("last_output_path")
        if selection["kind"] == "output" and selection.get("path") is not None:
            preview_path = selection["path"]
        elif last:
            preview_path = Path(last)
        else:
            preview_path = None

        if preview_path is None:
            st.info("左で選択し、Generate/Run を実行してください")
        else:
            try:
                svg_text = _read_svg(preview_path)
            except OSError as error:
                st.error(f"SVG を読み込めません: {error}")
            else:
                _preview_svg(svg_text)


if __name__ == "__main__":
    main()
