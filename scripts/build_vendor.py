#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SUDACHIPY_VERSION = "0.6.11"
DICT_VERSION = "20260428"
PYPI_JSON = "https://pypi.org/pypi/{project}/{version}/json"

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "ankimorphs_japanese_sudachi"
SUDACHIPY_DEPS = PACKAGE_ROOT / "deps" / "sudachipy"
DICT_DEPS = PACKAGE_ROOT / "deps" / "dict"

TARGETS = {
    "cpython-312": {
        "wheel_cp": "cp312",
        "os_arches": {
            "linux-x86_64": "manylinux2014_x86_64",
            "linux-aarch64": "manylinux2014_aarch64",
            "windows-amd64": "win_amd64",
            "macos-x86_64": "macosx_10_13_x86_64",
            "macos-arm64": "macosx_11_0_arm64",
        },
    },
    "cpython-313": {
        "wheel_cp": "cp313",
        "os_arches": {
            "linux-x86_64": "manylinux2014_x86_64",
            "linux-aarch64": "manylinux2014_aarch64",
            "windows-amd64": "win_amd64",
            "macos-x86_64": "macosx_10_13_x86_64",
            "macos-arm64": "macosx_11_0_arm64",
        },
    },
    "cpython-314": {
        "wheel_cp": "cp314",
        "os_arches": {
            "linux-x86_64": "manylinux2014_x86_64",
            "linux-aarch64": "manylinux2014_aarch64",
            "windows-amd64": "win_amd64",
            "macos-x86_64": "macosx_10_13_x86_64",
            "macos-arm64": "macosx_11_0_arm64",
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-sudachipy", action="store_true")
    parser.add_argument("--skip-dict", action="store_true")
    args = parser.parse_args()

    if not args.skip_sudachipy:
        vendor_sudachipy()
    if not args.skip_dict:
        vendor_dictionary()


def vendor_sudachipy() -> None:
    metadata = fetch_pypi_metadata("SudachiPy", SUDACHIPY_VERSION)
    urls = metadata["urls"]
    wheels = [url for url in urls if url["packagetype"] == "bdist_wheel"]

    for python_tag, target_config in TARGETS.items():
        wheel_cp = target_config["wheel_cp"]
        os_arches = target_config["os_arches"]
        for os_arch, platform_tag in os_arches.items():
            wheel = select_wheel(wheels, wheel_cp, platform_tag)
            destination = SUDACHIPY_DEPS / python_tag / os_arch
            if destination.exists():
                shutil.rmtree(destination)
            destination.mkdir(parents=True)

            with tempfile.TemporaryDirectory() as temp_dir:
                wheel_path = Path(temp_dir) / wheel["filename"]
                download_file(wheel["url"], wheel_path)
                if sha256_file(wheel_path) != wheel["digests"]["sha256"]:
                    raise RuntimeError(f"Checksum failed for {wheel['filename']}")
                with zipfile.ZipFile(wheel_path) as wheel_zip:
                    wheel_zip.extractall(destination)


def select_wheel(
    wheels: list[dict[str, Any]],
    wheel_cp: str,
    platform_tag: str,
) -> dict[str, Any]:
    matches = [
        wheel
        for wheel in wheels
        if f"-{wheel_cp}-" in wheel["filename"]
        and platform_tag in wheel["filename"]
        and "universal2" not in wheel["filename"]
        and f"{wheel_cp}t" not in wheel["filename"]
    ]
    if len(matches) != 1:
        filenames = "\n".join(wheel["filename"] for wheel in matches)
        raise RuntimeError(
            f"Expected one SudachiPy wheel for {wheel_cp}/{platform_tag}, got "
            f"{len(matches)}:\n{filenames}"
        )
    return matches[0]


def vendor_dictionary() -> None:
    DICT_DEPS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir) / "target"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--target",
                str(target_dir),
                f"SudachiDict-full=={DICT_VERSION}",
                f"SudachiPy=={SUDACHIPY_VERSION}",
            ],
            check=True,
        )
        system_dic = find_system_dic(target_dir)
        archive_path = DICT_DEPS / f"sudachi_full_{DICT_VERSION}.tar.xz"
        with tarfile.open(archive_path, "w:xz") as archive:
            archive.add(
                system_dic,
                arcname=f"sudachi_full_{DICT_VERSION}/system.dic",
                recursive=False,
            )

    system_dic_contents = read_archive_member(
        archive_path, f"sudachi_full_{DICT_VERSION}/system.dic"
    )
    manifest = {
        "dictionary_version": DICT_VERSION,
        "archive": archive_path.name,
        "archive_sha256": sha256_file(archive_path),
        "system_dic": f"sudachi_full_{DICT_VERSION}/system.dic",
        "members": [
            {
                "path": f"sudachi_full_{DICT_VERSION}/system.dic",
                "size": len(system_dic_contents),
                "sha256": hashlib.sha256(system_dic_contents).hexdigest(),
            }
        ],
    }
    (DICT_DEPS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf8",
    )


def find_system_dic(target_dir: Path) -> Path:
    matches = list(target_dir.rglob("system.dic"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one system.dic, got {len(matches)}")
    return matches[0]


def read_archive_member(archive_path: Path, member_name: str) -> bytes:
    with tarfile.open(archive_path, "r:xz") as archive:
        member_file = archive.extractfile(member_name)
        if member_file is None:
            raise RuntimeError(f"Could not read {member_name}")
        return member_file.read()


def fetch_pypi_metadata(project: str, version: str) -> dict[str, Any]:
    with urllib.request.urlopen(PYPI_JSON.format(project=project, version=version)) as response:
        return json.loads(response.read().decode("utf8"))


def download_file(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url) as response, open(destination, "wb") as output:
        shutil.copyfileobj(response, output)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()

