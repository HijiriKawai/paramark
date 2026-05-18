# CLAUDE.md

# プロジェクト概要

本プロジェクトは、Python による SVG 生成を利用して、プラモデル用デカール・ステンシル・マスキング素材を生成するためのシステムである。

対象用途：

* 水転写デカール
* ステンシル
* マスキング
* カッティングプロッタ用データ
* レーザーカット用データ

最終出力形式は主に SVG とする。

本プロジェクトでは「SVGファイルを直接編集する」のではなく、

「Python によるパラメトリックな図形生成」

を基本思想とする。

---

# AIエージェントへの指示

* 基本的に日本語で応答すること
* コメント・docstring・説明文も日本語を優先すること
* メンテナンス性を最優先すること
* 一時的な実装より、拡張可能性を重視すること
* ハードコードされた座標を避けること
* 可能な限りパラメータ化すること
* SVG を直接書き出すコードより、中間図形オブジェクトを扱う設計を優先すること
* 生成処理と export 処理を分離すること
* 単一巨大ファイル化を避け、責務ごとに分割すること

---

# 基本設計思想

## 1. Python を唯一のソースとする

SVG は「生成物」であり、編集対象ではない。

編集対象は Python コードとする。

つまり：

```text
Pythonコード
↓
図形生成
↓
SVG export
```

という構造を前提とする。

---

## 2. 1ファイル = 1図形カテゴリ

各図形・デカール・模様は、再利用可能な図形カテゴリ単位でファイル分割する。

推奨：

```text
line.py
circle.py
polygon.py
warning.py
stripe.py
hex_grid.py
```

非推奨：

```text
line_20.py
line_40.py
circle_r10.py
```

固定値ごとにファイル分割しないこと。

パラメータ差分は関数引数として扱う。

---

## 3. 図形生成関数を中心に構築する

各モジュールは図形生成関数を提供する。

例：

```python
def generate_line(
    length_mm: float,
    width_mm: float,
):
    ...
```

```python
def generate_polyline(
    length1_mm: float,
    angle_deg: float,
    length2_mm: float,
    width_mm: float,
):
    ...
```

SVG文字列を直接返すのではなく、

* geometry object
* path object
* polygon object

など、中間表現を返す設計を優先する。

---

## 4. 白領域と通常レイヤを分離する

家庭用プリンタ・コンビニレーザープリンタでは白印刷できない。

そのため：

* 白デカール紙
* 透明デカール紙

両方に対応可能な設計とする。

各図形生成関数は：

* 白として見せたい領域
* 通常色として印刷する部分

を分離可能にすること。

ここでいう `white_layer` は「白インクの印刷レイヤ」ではなく、

「白デカール紙の紙白を残したい領域」

を意味する。

透明デカール紙ではこの領域は基本的に未印刷透明部となる。

白デカール紙では、この領域そのものは印刷せず、

* 必要に応じて貼り付け先の色に合わせたアウトライン
* 必要に応じた通常色レイヤ

を周囲へ印刷することで、白として見えるデカールを構成する。

したがって、白デカール紙向け export では少なくとも：

* `paper_mode`
* `surface_color`
* `outline_width_mm`

を扱える設計が望ましい。

例えば：

```python
{
    "white_layer": ...,
    "color_layer": ...,
}
```

に加えて、export 時に：

```python
{
    "paper_mode": "white_decal",
    "surface_color": "#5c6773",
    "outline_width_mm": 0.3,
}
```

のような指定を受けられる構造を許容する。

---

# 対応シートサイズ

基本対応サイズ：

* ハガキサイズ
* A4サイズ

定数例：

```python
POSTCARD_MM = (100, 148)
A4_MM = (210, 297)
```

---

# 推奨ディレクトリ構造

```text
project/
├─ decals/
│   ├─ line.py
│   ├─ circle.py
│   ├─ polygon.py
│   ├─ stripe.py
│   ├─ warning.py
│   ├─ hex_grid.py
│   └─ ...
│
├─ layouts/
│   ├─ postcard_sheet.py
│   ├─ a4_sheet.py
│   └─ ...
│
├─ core/
│   ├─ geometry.py
│   ├─ packing.py
│   ├─ transforms.py
│   ├─ svg.py
│   ├─ naming.py
│   ├─ metadata.py
│   ├─ units.py
│   └─ ...
│
├─ export/
│   ├─ jobs/
│   ├─ presets/
│   ├─ templates/
│   ├─ export_svg.py
│   ├─ export_pdf.py
│   └─ ...
│
├─ examples/
│   └─ ...
│
└─ output/
```

---

# export/jobs の思想

export/jobs は、

「最終成果物を生成するための構成スクリプト」

を格納する。

これは単なる export 処理ではなく、

* どの図形を使うか
* どう配置するか
* どのシートサイズを使うか
* どのスケールで出力するか

を定義する「デカールシート設計ファイル」として扱う。

---

# export/jobs 命名例

## 機体系

```text
hg_gm_command.py
mg_zaku_ground.py
```

---

## 用途系

```text
warning_dense_a4.py
line_pack_postcard.py
```

---

## テスト系

```text
white_alignment_test.py
color_match_gray.py
```

---

## 実験系

```text
annealing_pack_test.py
hexgrid_density_test.py
```

---

# export/presets の思想

presets は再利用可能なレイアウト設定を格納する。

例：

* A4高密度配置
* ハガキ簡易配置
* ステンシル向けmargin設定

など。

---

# export/templates の思想

templates は汎用的なシート構成テンプレートを格納する。

例：

```text
mono_warning_sheet.py
line_decal_sheet.py
serial_sheet.py
```

---

# exportスクリプト metadata

各 export job は metadata を持つことを推奨する。

例：

```python
EXPORT_NAME = "hg_gm_custom_01"

SHEET_SIZE = A4_MM

TARGET_SCALE = "1/144"

DESCRIPTION = """
HG GM custom decals
"""
```

---

# ファイル命名規則

## 基本方針

ソースコードファイル名には固定パラメータを含めない。

パラメータは export 時の成果物ファイル名に含める。

---

# exportファイル命名規則

生成SVGファイルには、幾何パラメータを含める。

目的：

* 再利用性向上
* 視認性向上
* 自動生成との整合性
* キャッシュしやすさ
* AI補助との相性向上

---

## Line系

### 直線

```text
line_[length]
```

例：

```text
line_20mm.svg
```

---

### 折れ線

```text
polyline_[length1]_[angle]_[length2]
```

例：

```text
polyline_20_60_40.svg
```

---

### 多段折れ線

```text
polyline_[l1]_[a1]_[l2]_[a2]_[l3]
```

---

## Circle系

### 円

```text
circle_r[r]
```

例：

```text
circle_r10.svg
```

---

### 円弧

```text
arc_r[r]_[deg]
```

例：

```text
arc_r10_120deg.svg
```

---

### リング

```text
ring_r[outer]_r[inner]
```

例：

```text
ring_r10_r8.svg
```

---

## Polygon系

### 正多角形

```text
polygon_[n]_r[r]
```

例：

```text
polygon_6_r10.svg
```

---

## Pattern系

### 六角格子

```text
hexgrid_[cell]
```

---

### ドット格子

```text
dotgrid_[pitch]_[r]
```

---

## Stripe系

### 単線

```text
stripe_[length]_[width]
```

---

### 二重線

```text
double_stripe_[length]_[gap]
```

---

### 警告斜線

```text
hazard_[angle]_[pitch]
```

---

# Metadata方針

可能な限り図形メタデータを保持する。

例：

```python
{
    "type": "polyline",
    "lengths": [20, 40],
    "angles": [60],
    "width": 0.4,
}
```

metadata は：

* export
* DB化
* GUI
* 自動配置
* 検索
* 自動分類

などへの利用を想定する。

---

# 配置最適化（Packing / Nesting）

本プロジェクトには、汎用配置最適化機能を実装する。

目的：

* デカール紙の余白最小化
* 面積利用率向上
* 図形同士の衝突回避
* 回転配置対応

対象：

* 任意SVG図形
* 多角形
* 長方形近似
* 将来的な複雑図形

対応予定：

* 回転
* margin
* polygon collision
* rectangle approximation
* 将来的な焼きなまし法
* 将来的なヒューリスティクス最適化

推奨ライブラリ：

* shapely
* numpy
* svgpathtools

---

# export 用スクリプト

最終成果物生成は export スクリプトで行う。

処理フロー：

```text
図形生成関数
↓
図形オブジェクト生成
↓
配置最適化
↓
シート合成
↓
SVG export
```

export スクリプトは：

* 図形生成
* 配置
* レイヤ分離
* シート生成

のみを担当する。

個別図形内部に export 処理を持たせないこと。

---

# SVGルール

SVG生成時：

* mm単位を使用
* ベクター情報を保持
* ラスタライズ禁止
* Cricut / Silhouette 対応
* レーザーカッター対応
* 印刷対応

を基本方針とする。

---

# メンテナンス方針

重視するもの：

* 再利用性
* 拡張性
* 可読性
* 図形生成の独立性
* 責務分離

避けるもの：

* 巨大関数
* export と geometry の密結合
* SVG文字列直書き乱用
* ハードコード座標大量使用
* 状態共有の多用

---

# 将来的な拡張案

* GUI配置エディタ
* 自動白フチ生成
* スケールプリセット
* デカールDB化
* DXF export
* PDF export
* 自動シリアル生成
* プロシージャル迷彩生成
* ステンシル自動生成
* カッティングプロッタ直接出力

---

# スケール対応

基本方針として、制作基準スケールは 1/144 とする。

個別図形の寸法指定や reusable な図形生成関数は、

「1/144 でそのまま出力される模型寸法」

を基準に設計する。

将来的に：

* 1/144
* 1/100
* 1/72
* 1/48

などへのスケール対応を想定する。

可能な限り：

「1/144ベース → 必要に応じて他スケールへ変換」

で扱うこと。

つまり、

* 通常運用は 1/144 をそのまま出力する
* 1/100 などが必要な場合のみ引き延ばす
* 実寸は必要なときにのみ補助的に扱う

方針とする。

---

# 実装方針

推奨：

* dataclass 活用
* 型ヒント使用
* 小さい責務単位
* 純粋関数寄り設計

可能なら：

* テスト可能構造
* deterministic な出力
* geometry と rendering の分離

を維持すること。
