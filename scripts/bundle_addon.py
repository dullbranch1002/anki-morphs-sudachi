#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "ankimorphs-japanese-sudachi"
OUTPUT_FILE = PACKAGE_DIR.parent / "ankimorphs-japanese-sudachi.ankiaddon"

PYTHON_TAGS = ["cpython-312", "cpython-313", "cpython-314"]
OS_ARCHES = ["linux-x86_64", "linux-aarch64", "windows-amd64", "macos-x86_64", "macos-arm64"]


def main() -> None:
    os.chdir(PACKAGE_DIR)

    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
        for f in files:
            if f.endswith((".pyc", ".pyo")):
                os.remove(os.path.join(root, f))

    dict_dir = Path("deps/dict/sudachi_full_20260428")
    if dict_dir.exists():
        shutil.rmtree(dict_dir)

    user_files = Path("user_files")
    if user_files.exists():
        shutil.rmtree(user_files)

    assert (PACKAGE_DIR / "manifest.json").is_file(), "missing manifest.json"
    assert (PACKAGE_DIR / "deps/dict/sudachi_full_20260428.tar.xz").is_file(), "missing dictionary archive"
    assert (PACKAGE_DIR / "deps/dict/manifest.json").is_file(), "missing dict manifest.json"

    for python_tag in PYTHON_TAGS:
        for os_arch in OS_ARCHES:
            target = PACKAGE_DIR / "deps" / "sudachipy" / python_tag / os_arch
            assert target.is_dir(), f"missing deps/sudachipy/{python_tag}/{os_arch}"

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    with zipfile.ZipFile(OUTPUT_FILE, "w", compression=zipfile.ZIP_DEFLATED) as addon:
        for root, _dirs, files in os.walk("."):
            for filename in files:
                path = os.path.join(root, filename)
                arcname = os.path.relpath(path, ".")
                addon.write(path, arcname)


if __name__ == "__main__":
    main()
