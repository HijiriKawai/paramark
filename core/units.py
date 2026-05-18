"""長さ・シートサイズ・スケールに関する共通定義。"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

Millimeter = float
Degrees = float


def ensure_mm(value: Real) -> Millimeter:
    """長さを mm の float として正規化する。"""

    return float(value)


@dataclass(frozen=True, slots=True)
class SheetSize:
    """出力シートの寸法。"""

    name: str
    width_mm: Millimeter
    height_mm: Millimeter

    def as_tuple(self) -> tuple[Millimeter, Millimeter]:
        return (self.width_mm, self.height_mm)

    @property
    def aspect_ratio(self) -> float:
        return self.width_mm / self.height_mm


@dataclass(frozen=True, slots=True)
class Scale:
    """模型縮尺を表す比率。"""

    numerator: int = 1
    denominator: int = 1

    def __post_init__(self) -> None:
        if self.denominator == 0:
            raise ValueError("縮尺の分母は 0 にできません。")
        if self.numerator <= 0 or self.denominator <= 0:
            raise ValueError("縮尺は正の値で指定してください。")

    @property
    def factor(self) -> float:
        return self.numerator / self.denominator

    def ratio_to(self, target: "Scale | str") -> float:
        """この縮尺から target 縮尺へ変換する倍率。"""

        parsed_target = self.parse(target)
        return parsed_target.factor / self.factor

    @classmethod
    def parse(cls, value: "Scale | str") -> "Scale":
        if isinstance(value, cls):
            return value

        left, separator, right = value.partition("/")
        if separator != "/":
            raise ValueError(f"縮尺は '1/144' のような形式で指定してください: {value}")
        return cls(int(left), int(right))

    def to_text(self) -> str:
        return f"{self.numerator}/{self.denominator}"


POSTCARD = SheetSize(name="postcard", width_mm=100.0, height_mm=148.0)
A4 = SheetSize(name="a4", width_mm=210.0, height_mm=297.0)
BASE_MODEL_SCALE = Scale(1, 144)

POSTCARD_MM = POSTCARD.as_tuple()
A4_MM = A4.as_tuple()


def scaled_length_mm(real_length_mm: Real, scale: Scale | str) -> Millimeter:
    """実寸を指定縮尺の模型寸法へ変換する。"""

    parsed_scale = Scale.parse(scale)
    return ensure_mm(real_length_mm) * parsed_scale.factor


def full_size_length_mm(model_length_mm: Real, scale: Scale | str = BASE_MODEL_SCALE) -> Millimeter:
    """模型寸法を実寸へ戻す。"""

    parsed_scale = Scale.parse(scale)
    return ensure_mm(model_length_mm) / parsed_scale.factor


def rescale_model_length_mm(
    model_length_mm: Real,
    target_scale: Scale | str,
    *,
    source_scale: Scale | str = BASE_MODEL_SCALE,
) -> Millimeter:
    """模型寸法をある縮尺から別の縮尺へ変換する。

    既定では 1/144 ベース寸法から別縮尺へ引き延ばす用途を想定する。
    """

    parsed_source = Scale.parse(source_scale)
    ratio = parsed_source.ratio_to(target_scale)
    return ensure_mm(model_length_mm) * ratio
