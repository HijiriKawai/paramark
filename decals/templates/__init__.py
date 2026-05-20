"""Decals の「テンプレ登録制」カタログ。

このパッケージは、UI などから安全・確実に列挙できる生成単位を提供する。
`decals/` の生成関数を直接列挙するのではなく、ここで登録されたテンプレのみを対象にする。
"""

from .registry import DecalTemplate, TEMPLATES, resolve_decal_template

__all__ = [
    "DecalTemplate",
    "TEMPLATES",
    "resolve_decal_template",
]
