#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import lzma
import os
import shutil
import tarfile
import time
import zipfile
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "ankimorphs-japanese-sudachi"
OUTPUT_FILE = PACKAGE_DIR.parent / "ankimorphs-japanese-sudachi.ankiaddon"
DICT_VERSION = "20260428"
DICT_DIR_NAME = f"sudachi_full_{DICT_VERSION}"
DICT_DEPS = PACKAGE_DIR / "deps" / "dict"
DICT_DIR = DICT_DEPS / DICT_DIR_NAME
SYSTEM_DIC = DICT_DIR / "system.dic"
ARCHIVE_PATH = DICT_DEPS / f"{DICT_DIR_NAME}.tar.xz"
MANIFEST_PATH = DICT_DEPS / "manifest.json"

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

    user_files = Path("user_files")
    if user_files.exists():
        shutil.rmtree(user_files)

    assert (PACKAGE_DIR / "manifest.json").is_file(), "missing manifest.json"
    create_dictionary_archive()
    assert ARCHIVE_PATH.is_file(), "missing dictionary archive"
    assert MANIFEST_PATH.is_file(), "missing dict manifest.json"

    for python_tag in PYTHON_TAGS:
        for os_arch in OS_ARCHES:
            target = PACKAGE_DIR / "deps" / "sudachipy" / python_tag / os_arch
            assert target.is_dir(), f"missing deps/sudachipy/{python_tag}/{os_arch}"

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    with zipfile.ZipFile(OUTPUT_FILE, "w", compression=zipfile.ZIP_DEFLATED) as addon:
        for root, dirs, files in os.walk("."):
            root_path = Path(root)
            if (
                (root_path / DICT_DIR_NAME).resolve() == DICT_DIR.resolve()
                and DICT_DIR_NAME in dirs
            ):
                dirs.remove(DICT_DIR_NAME)
            for filename in files:
                path = os.path.join(root, filename)
                arcname = os.path.relpath(path, ".")
                addon.write(path, arcname)


def create_dictionary_archive() -> None:
    assert SYSTEM_DIC.is_file(), f"missing dictionary file: {SYSTEM_DIC}"

    file_size = SYSTEM_DIC.stat().st_size
    print("[dict] Compressing dictionary for add-on archive...")
    print(
        f"[dict] Source: {SYSTEM_DIC.relative_to(PACKAGE_DIR)} "
        f"({file_size / 1024 / 1024:.2f} MB)"
    )

    start_time = time.time()
    last_report = 0.0
    progress_interval = 2.0

    class ProgressFile:
        def __init__(self, path: Path, total_size: int):
            self._file = open(path, "rb")
            self._total = total_size
            self._read = 0

        def read(self, size: int = -1) -> bytes:
            nonlocal last_report
            data = self._file.read(size)
            if data:
                self._read += len(data)
                now = time.time()
                if now - last_report >= progress_interval:
                    pct = self._read / self._total * 100
                    elapsed = now - start_time
                    eta = elapsed / self._read * (self._total - self._read)
                    speed = self._read / elapsed / 1024 / 1024
                    print(
                        f"[dict] Progress: {pct:.1f}% | "
                        f"{self._read / 1024 / 1024:.2f}/{self._total / 1024 / 1024:.2f} MB | "
                        f"{speed:.2f} MB/s | ETA: {eta:.0f}s"
                    )
                    last_report = now
            return data

        def close(self) -> None:
            self._file.close()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

        @property
        def name(self) -> str:
            return self._file.name

    tarinfo = tarfile.TarInfo(name=f"{DICT_DIR_NAME}/system.dic")
    tarinfo.size = file_size
    tarinfo.mtime = int(SYSTEM_DIC.stat().st_mtime)

    with tarfile.open(
        ARCHIVE_PATH,
        "w:xz",
        preset=9 | lzma.PRESET_EXTREME,
        format=tarfile.PAX_FORMAT,
    ) as tar:
        with ProgressFile(SYSTEM_DIC, file_size) as dictionary_file:
            tar.addfile(tarinfo, dictionary_file)

    archive_size = ARCHIVE_PATH.stat().st_size
    elapsed = time.time() - start_time
    print(f"[dict] Archive created: {ARCHIVE_PATH.relative_to(PACKAGE_DIR)}")
    print(f"[dict] Compressed size: {archive_size / 1024 / 1024:.2f} MB")
    print(f"[dict] Compression ratio: {archive_size / file_size * 100:.1f}%")
    print(f"[dict] Compression completed in {elapsed:.1f}s")

    manifest = {
        "dictionary_version": DICT_VERSION,
        "archive": ARCHIVE_PATH.name,
        "archive_sha256": sha256_file(ARCHIVE_PATH),
        "system_dic": f"{DICT_DIR_NAME}/system.dic",
        "members": [
            {
                "path": f"{DICT_DIR_NAME}/system.dic",
                "size": file_size,
                "sha256": sha256_file(SYSTEM_DIC),
            }
        ],
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
