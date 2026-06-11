from __future__ import annotations

import json
import platform
import re
import sys
import tarfile
from functools import cache
from pathlib import Path
from typing import Any

from . import ADDON_ROOT

_POS_BLACKLIST = {
    "記号",
    "補助記号",
    "空白",
}
_SUB_POS_BLACKLIST = {
    "数詞",
}
_CONTROL_CHARS_RE = re.compile("[\x00-\x1f\x7f-\x9f]")

_SUDACHIPY_ROOT = ADDON_ROOT / "deps" / "sudachipy"
_DICT_ROOT = ADDON_ROOT / "deps" / "dict"
_USER_FILES_ROOT = ADDON_ROOT / "user_files"
_DICT_CACHE_ROOT = _USER_FILES_ROOT / "dict"

successful_import = False
last_error = ""


def setup_sudachi() -> None:
    global last_error
    global successful_import

    if successful_import:
        return

    try:
        vendor_path = _get_vendor_path()
        if str(vendor_path) not in sys.path:
            sys.path.insert(0, str(vendor_path))

        import sudachipy  # noqa: F401

        _get_dict_manifest()
    except Exception as error:
        last_error = f"{type(error).__name__}: {error}"
        successful_import = False
        return

    last_error = ""
    successful_import = True


def get_morphemes_sudachi(expression: str, morpheme_class: Any) -> list[Any]:
    expression = _CONTROL_CHARS_RE.sub("", expression)
    morphs = []

    for token in _get_tokenizer().tokenize(expression):
        pos = token.part_of_speech()
        part_of_speech = pos[0] if len(pos) > 0 else ""
        sub_part_of_speech = pos[1] if len(pos) > 1 else ""

        if part_of_speech in _POS_BLACKLIST:
            continue
        if sub_part_of_speech in _SUB_POS_BLACKLIST:
            continue

        lemma = token.dictionary_form().strip()
        inflection = token.surface().strip()
        if not lemma or lemma == "*":
            lemma = inflection
        if lemma and inflection:
            morphs.append(
                morpheme_class(
                    lemma=lemma,
                    inflection=inflection,
                    part_of_speech=part_of_speech,
                    sub_part_of_speech=sub_part_of_speech,
                )
            )

    return morphs


@cache
def _get_tokenizer() -> Any:
    from sudachipy import Dictionary, SplitMode

    return Dictionary(dict=str(_ensure_system_dic())).create(SplitMode.A)


def _get_vendor_path() -> Path:
    python_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
    os_arch = _get_os_arch()
    vendor_path = _SUDACHIPY_ROOT / python_tag / os_arch

    if not vendor_path.exists():
        raise RuntimeError(
            f"unsupported runtime target {python_tag}/{os_arch}; "
            f"expected vendored SudachiPy at {vendor_path}"
        )
    return vendor_path


def _get_os_arch() -> str:
    machine = platform.machine().lower()
    is_arm64 = machine in {"arm64", "aarch64"}

    if sys.platform.startswith("linux"):
        return "linux-aarch64" if is_arm64 else "linux-x86_64"
    if sys.platform == "darwin":
        return "macos-arm64" if is_arm64 else "macos-x86_64"
    if sys.platform.startswith("win"):
        return "windows-amd64"

    raise RuntimeError(f"unsupported platform {sys.platform}/{machine}")


def _ensure_system_dic() -> Path:
    manifest = _get_dict_manifest()
    system_dic = _DICT_CACHE_ROOT / manifest["system_dic"]
    expected_member = _get_expected_member(manifest)

    if system_dic.exists() and system_dic.stat().st_size == expected_member["size"]:
        return system_dic

    archive_path = _DICT_ROOT / manifest["archive"]
    if not archive_path.exists():
        raise RuntimeError(f"missing Sudachi dictionary archive: {archive_path}")

    _DICT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:xz") as archive:
        member = archive.getmember(expected_member["path"])
        _safe_extract_member(archive, member, _DICT_CACHE_ROOT)

    if system_dic.stat().st_size != expected_member["size"]:
        raise RuntimeError(f"extracted Sudachi dictionary has the wrong size: {system_dic}")

    return system_dic


@cache
def _get_dict_manifest() -> dict[str, Any]:
    manifest_path = _DICT_ROOT / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def _get_expected_member(manifest: dict[str, Any]) -> dict[str, Any]:
    for member in manifest["members"]:
        if member["path"] == manifest["system_dic"]:
            return member
    raise RuntimeError("dictionary manifest does not describe system_dic")


def _safe_extract_member(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    destination: Path,
) -> None:
    if not member.isfile():
        raise RuntimeError(f"dictionary archive member is not a file: {member.name}")

    target = (destination / member.name).resolve()
    destination_resolved = destination.resolve()
    if destination_resolved not in target.parents:
        raise RuntimeError(f"unsafe dictionary archive member path: {member.name}")

    archive.extract(member, destination)
