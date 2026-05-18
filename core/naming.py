"""成果物名を deterministic に組み立てるためのユーティリティ。"""

from __future__ import annotations

from numbers import Real


def format_number_token(value: Real, *, precision: int = 4) -> str:
    """ファイル名向けに小数を安全な token へ変換する。"""

    normalized = round(float(value), precision)
    text = f"{normalized:.{precision}f}".rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    return text.replace("-", "n").replace(".", "p")


def format_mm_token(value_mm: Real, *, precision: int = 4) -> str:
    return f"{format_number_token(value_mm, precision=precision)}mm"


def build_parametric_name(
    base_name: str,
    *parts: str | Real | None,
    extension: str | None = None,
) -> str:
    """`line_20mm.svg` のような規則的ファイル名を生成する。"""

    tokens: list[str] = [base_name]
    for part in parts:
        if part is None:
            continue
        if isinstance(part, str):
            token = part.strip("_ ")
        else:
            token = format_number_token(part)
        if token:
            tokens.append(token)

    stem = "_".join(tokens)
    if extension is None:
        return stem

    normalized_extension = extension.lstrip(".")
    return f"{stem}.{normalized_extension}"
