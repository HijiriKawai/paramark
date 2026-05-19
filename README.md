# paramark

Python でプラモデル用デカール・ステンシル・マスキング素材を生成し、SVG / PDF として出力するための実験プロジェクトです。

このリポジトリでは SVG を直接編集しません。Python コードで図形を組み立てて、中間表現を経由してシート化し、最後に export します。

```text
Python コード
↓
図形生成
↓
シート配置
↓
SVG / PDF export
```

## 現在の方針

- 制作基準スケールは `1/144`
- 図形寸法は「`1/144` でそのまま出力される模型寸法」を基準に指定する
- 必要な場合だけ `1/100` などへ拡大する
- 生成処理と export 処理は分離する
- 図形は SVG 文字列ではなく、中間図形オブジェクトとして扱う
- 白として見せたい領域と色印刷領域を分けられる構造を持つ

## 現在の実装範囲

### `core/`

- 図形中間表現
  - `Point`
  - `Bounds`
  - `Polyline`
  - `Polygon`
  - `Circle`
  - `Rectangle`
  - `Path`
  - `Group`
  - `LayeredGraphic`
- 変換
  - `translate()`
  - `rotate()`
  - `scale()`
- 単位・縮尺
  - `BASE_MODEL_SCALE = 1/144`
  - `scaled_length_mm()`
  - `rescale_model_length_mm()`
  - `full_size_length_mm()`
- SVG 出力
  - `SvgDocument`
  - `render_svg_document()`
  - `save_svg()`
- 簡易 packing
  - `pack_shelves()`

### `decals/`

export ファイル命名規則に対応する基本図形を実装済みです。

- `generate_line()`
- `generate_polyline()`
- `generate_circle()`
- `generate_arc()`
- `generate_ring()`
- `generate_regular_polygon()`
- `generate_stripe()`
- `generate_double_stripe()`
- `generate_hazard_stripes()`
- `generate_hex_grid()`
- `generate_dot_grid()`

### `layouts/`

- `postcard`
- `A4`

手置き配置と簡易 auto-pack の両方を使えます。

- `SheetPlacement`
- `SheetLayout`
- `create_postcard_sheet()`
- `create_a4_sheet()`
- `pack_postcard_sheet()`
- `pack_a4_sheet()`

### `export/`

- デカール紙変換
  - `prepare_layout_for_clear_decal()`
  - `prepare_layout_for_white_decal()`
- SVG 出力
  - `export_layout_svg()`
  - `export_job_module()`
- PDF 出力
  - `export_layout_pdf()`
  - `export_job_module_pdf()`
- presets
  - `POSTCARD_SIMPLE`
  - `A4_DENSE`
  - `STENCIL_MARGIN`
- templates
  - `build_line_decal_sheet()`
  - `build_mono_warning_sheet()`
- sample jobs
  - `export.jobs.clear_decal_sample`
  - `export.jobs.line_pack_postcard`
  - `export.jobs.warning_dense_a4`
  - `export.jobs.white_alignment_test`
  - `export.jobs.white_decal_sample`
  - `export.jobs.hexgrid_density_test`

## 動作確認環境

- Python 標準ライブラリのみで動作する構成
- 現状は `Python 3.14.5` で確認済み

## ディレクトリ構成

```text
core/
decals/
layouts/
export/
  jobs/
  presets/
  templates/
output/
```

## 使い方

### 1. 図形を作る

```python
from decals import generate_line, generate_ring

line = generate_line(20, 0.4, color="#000000")
ring = generate_ring(10, 8, color="#ff6600")
```

すべての図形生成関数は `LayeredGraphic` を返します。

`LayeredGraphic.white_layer` は「白インク」ではなく、「白として見せたい領域」の定義です。
そのまま SVG に描くと白で可視化されますが、白デカール紙向けの実際の printable 化は export 側で行います。

### 2. シートに配置する

手で配置する例:

```python
from layouts import SheetPlacement, create_postcard_sheet

layout = create_postcard_sheet(
    placements=(
        SheetPlacement(graphic=line, x_mm=8, y_mm=8, identifier="line_1"),
        SheetPlacement(graphic=ring, x_mm=50, y_mm=30, anchor="center", identifier="ring_1"),
    ),
    title="manual postcard",
)
```

自動配置する例:

```python
from layouts import pack_a4_sheet

layout = pack_a4_sheet(
    graphics=(line, ring),
    margin_mm=8.0,
    gap_mm=2.0,
    min_gap_mm=1.0,
    title="packed a4",
)
```

`gap_mm` は「希望する隙間」、`min_gap_mm` は「最低限確保したい隙間」です。
packing では `effective_gap_mm = max(gap_mm, min_gap_mm)` を使うため、
たとえば `gap_mm=0.0` の指定でも `min_gap_mm` 未満には詰まりません。

印刷・カット用途では、運用上の安全余白として `min_gap_mm=1.0`〜`2.0` 程度を検討してください。

### 3. SVG を出力する

```python
from export import ExportJobSpec, export_layout_svg

result = export_layout_svg(
    layout,
    spec=ExportJobSpec(
        export_name="example_postcard",
        target_scale="1/144",
        description="manual layout example",
    ),
)

print(result.output_path)
```

### 4. PDF を出力する

```python
from export import ExportJobSpec, export_layout_pdf

result = export_layout_pdf(
    layout,
    spec=ExportJobSpec(
        export_name="example_postcard",
        target_scale="1/144",
        description="manual layout example",
    ),
)

print(result.output_path)
```

### 5. 透明デカール紙 / 白デカール紙へ変換する

透明デカール紙では `white_layer` は基本的に未印刷透明部です。

```python
from export import prepare_layout_for_clear_decal

printable_layout = prepare_layout_for_clear_decal(layout)
```

白デカール紙では `white_layer` 自体は印刷せず、貼り付け先の色でアウトラインを作ります。

```python
from export import prepare_layout_for_white_decal

printable_layout = prepare_layout_for_white_decal(
    layout,
    surface_color="#5c6773",
    outline_width_mm=0.3,
)
```

その後に `export_layout_svg()` / `export_layout_pdf()` を呼びます。

## job ベースの使い方

`export/jobs/` は最終成果物を生成するための構成スクリプトです。

各 job は最低限次を持ちます。

- `EXPORT_NAME`
- `TARGET_SCALE`
- `DESCRIPTION`
- `build_layout()`

Python から実行する例:

```python
from export import export_job_module, export_job_module_pdf

svg_result = export_job_module("export.jobs.line_pack_postcard")
pdf_result = export_job_module_pdf("export.jobs.line_pack_postcard")
```

CLI から実行する例:

```bash
python3 -m export.export_svg export.jobs.line_pack_postcard
python3 -m export.export_pdf export.jobs.line_pack_postcard
```

出力先を変える場合:

```bash
python3 -m export.export_svg export.jobs.warning_dense_a4 --output-dir output/custom
python3 -m export.export_pdf export.jobs.warning_dense_a4 --output-dir output/custom
```

下地違いサンプルを試す場合:

```bash
python3 -m export.export_svg export.jobs.clear_decal_sample
python3 -m export.export_svg export.jobs.white_decal_sample
python3 -m export.export_pdf export.jobs.white_decal_sample
```

## 色の扱い

各図形生成関数は `color` 引数を受け取ります。

```python
from decals import generate_circle

circle = generate_circle(5, color="#00aa88")
```

SVG は指定した色文字列をそのまま出力します。

PDF は現在、次の色指定を安全に扱えます。

- `#RRGGBB`
- `#RGB`
- `black`
- `white`
- `red`
- `green`
- `blue`
- `gray`
- `grey`

白デカール紙向けの `surface_color` も同じ指定方法を使います。

## スケール変換

通常は `1/144` 寸法をそのまま使います。

```python
from core import BASE_MODEL_SCALE, Scale, rescale_model_length_mm

value_144 = 10.0
value_100 = rescale_model_length_mm(value_144, Scale(1, 100))
print(value_100)  # 14.4
```

## 現在の制約

- packing は現状 `shelf packing` のみ
- PDF export は 1 ページのみ
- PDF の `ArcTo` は内部的に折れ線近似
- 白デカール紙向け処理は現状「貼り付け先の色のアウトライン生成」で、面塗り bleed までは未実装
- DXF / GUI / 高度な polygon nesting は未実装
- サンプル job はあくまで雛形で、機体別デカールはまだ未実装

## まず試すなら

```bash
python3 -m export.export_svg export.jobs.line_pack_postcard
python3 -m export.export_svg export.jobs.clear_decal_sample
python3 -m export.export_svg export.jobs.white_decal_sample
python3 -m export.export_pdf export.jobs.white_alignment_test
```

生成物は既定で `output/` に保存されます。

## SVG カタログアプリ（Issue #6）

Streamlit ベースの簡易 UI で、次を 1 画面で扱えます。

- Decals（登録テンプレ）: 選択 → パラメータ編集 → SVG 生成 → プレビュー
- Jobs: 実行 → SVG 生成 → プレビュー
- Outputs: `output/**/*.svg` の一覧 → プレビュー

依存管理は `uv` を使います。

```bash
uv sync
uv run streamlit run apps/catalog_app.py
```

生成/キャッシュは `output/catalog_app/` 配下へ保存されます。
