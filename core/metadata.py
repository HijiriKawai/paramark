"""図形や export に付与するメタデータの共通定義。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

MetadataScalar: TypeAlias = str | int | float | bool | None
MetadataValue: TypeAlias = (
    MetadataScalar | tuple["MetadataValue", ...] | list["MetadataValue"] | dict[str, "MetadataValue"]
)
MetadataDict: TypeAlias = dict[str, MetadataValue]


def metadata_dict(initial: Mapping[str, MetadataValue] | None = None, **extra: MetadataValue) -> MetadataDict:
    """メタデータ辞書を安全に生成する。"""

    data: MetadataDict = {}
    if initial:
        data.update(dict(initial))
    if extra:
        data.update(extra)
    return data


def merge_metadata(*sources: Mapping[str, MetadataValue] | None, **extra: MetadataValue) -> MetadataDict:
    """複数のメタデータ辞書を後勝ちで統合する。"""

    merged: MetadataDict = {}
    for source in sources:
        if source:
            merged.update(dict(source))
    if extra:
        merged.update(extra)
    return merged


def prefixed_metadata(
    prefix: str,
    values: Mapping[str, MetadataValue] | None = None,
    **extra: MetadataValue,
) -> MetadataDict:
    """名前空間を明示したメタデータを作る。"""

    combined = merge_metadata(values, **extra)
    return {f"{prefix}.{key}": value for key, value in combined.items()}
