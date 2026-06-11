#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

REQUIRED_TARGETS = [
    (python_tag, os_arch)
    for python_tag in ("cpython-312", "cpython-313", "cpython-314")
    for os_arch in (
        "linux-x86_64",
        "linux-aarch64",
        "windows-amd64",
        "macos-x86_64",
        "macos-arm64",
    )
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addon", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.addon) as addon:
        names = addon.namelist()
        require("manifest.json" in names, "missing manifest.json")
        require("__init__.py" in names, "missing add-on initializer")
        require("sudachi_morphemizer.py" in names, "missing Sudachi morphemizer")
        require("sudachi_wrapper.py" in names, "missing Sudachi wrapper")
        require(
            "deps/dict/sudachi_full_20260428.tar.xz" in names,
            "missing SudachiDict-full archive",
        )
        require("deps/dict/manifest.json" in names, "missing dictionary manifest")
        require(
            not any("__pycache__" in name or name.endswith((".pyc", ".pyo")) for name in names),
            "package contains Python cache files",
        )
        require(
            not any(name.startswith("user_files/") for name in names),
            "package contains runtime cache files",
        )
        require(
            not all(name.startswith("ankimorphs_japanese_sudachi/") for name in names),
            "package contains an enclosing top-level folder",
        )
        for python_tag, os_arch in REQUIRED_TARGETS:
            prefix = f"deps/sudachipy/{python_tag}/{os_arch}/"
            require(
                any(name.startswith(prefix) and name != prefix for name in names),
                f"missing SudachiPy target {python_tag}/{os_arch}",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            staged_addon = Path(temp_dir) / "ankimorphs_japanese_sudachi"
            staged_addon.mkdir()
            addon.extractall(staged_addon)
            sys.path.insert(0, temp_dir)
            try:
                __import__("ankimorphs_japanese_sudachi")
            finally:
                sys.path.remove(temp_dir)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


if __name__ == "__main__":
    main()
