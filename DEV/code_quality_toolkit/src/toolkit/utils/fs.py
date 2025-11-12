"""Filesystem helpers for discovering files to analyze."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def match_any(path: str, patterns: Iterable[str]) -> bool:
    rel_path = Path(path)
    for pattern in patterns:
        if rel_path.match(pattern):
            return True
        if pattern.startswith("**/") and rel_path.match(pattern[3:]):
            return True
    return False


# EXTENSION-POINT: substituir por implementação assíncrona ou com cache de glob.


def discover_files(
    root: str | Path, include: Iterable[str], exclude: Iterable[str]
) -> List[Path]:
    """Return a sorted list of files under root matching include patterns."""

    root_path = Path(root)
    files: List[Path] = []
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(root_path).as_posix()
        if include and not match_any(relative, include):
            continue
        if exclude and match_any(relative, exclude):
            continue
        files.append(file_path)
    files.sort()
    return files


# TODO(alunos): ignorar ficheiros binários ou parametrizar por extensões suportadas.
