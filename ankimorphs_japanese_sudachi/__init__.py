from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from typing import Any

ADDON_ROOT = Path(__file__).resolve().parent

MORPHEMIZER_DESCRIPTION = "AnkiMorphs: Japanese Sudachi"
_MORPHEMIZER_UTILS_SUFFIX = ".morphemizers.morphemizer_utils"
_original_import: Any | None = None
_installing_hook = False


def _install_ankimorphs_hook() -> None:
    global _installing_hook

    if _installing_hook:
        return

    _installing_hook = True
    try:
        for morphemizer_utils in _get_morphemizer_utils_modules():
            _patch_morphemizer_utils(morphemizer_utils)
    finally:
        _installing_hook = False


def _patch_morphemizer_utils(morphemizer_utils: Any) -> None:
    if getattr(morphemizer_utils, "_sudachi_morphemizer_patched", False):
        return

    package_root = morphemizer_utils.__name__.removesuffix(_MORPHEMIZER_UTILS_SUFFIX)
    morpheme_module = importlib.import_module(f"{package_root}.morpheme")
    morphemizer_module = importlib.import_module(
        f"{package_root}.morphemizers.morphemizer"
    )

    from .sudachi_morphemizer import build_sudachi_morphemizer

    SudachiMorphemizer = build_sudachi_morphemizer(
        morpheme_module.Morpheme,
        morphemizer_module.Morphemizer,
    )

    original_get_all_morphemizers = morphemizer_utils.get_all_morphemizers

    def get_all_morphemizers() -> list[Any]:
        morphemizers = original_get_all_morphemizers()
        if MORPHEMIZER_DESCRIPTION in morphemizer_utils.morphemizers_by_description:
            return morphemizers

        sudachi_morphemizer = SudachiMorphemizer()
        if sudachi_morphemizer.init_successful():
            morphemizers.append(sudachi_morphemizer)
            morphemizer_utils.morphemizers_by_description[
                MORPHEMIZER_DESCRIPTION
            ] = sudachi_morphemizer
        return morphemizers

    morphemizer_utils.get_all_morphemizers = get_all_morphemizers
    morphemizer_utils._sudachi_morphemizer_patched = True

    if morphemizer_utils.available_morphemizers is not None:
        get_all_morphemizers()


def _get_morphemizer_utils_modules() -> list[Any]:
    return [
        module
        for name, module in sys.modules.items()
        if name.endswith(_MORPHEMIZER_UTILS_SUFFIX)
    ]


def _install_import_hook() -> None:
    global _original_import

    if _get_morphemizer_utils_modules():
        _install_ankimorphs_hook()
        return

    if getattr(builtins.__import__, "_sudachi_import_hook", False):
        return

    _original_import = builtins.__import__

    def import_hook(
        name: str,
        globals_: dict[str, Any] | None = None,
        locals_: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        assert _original_import is not None
        module = _original_import(name, globals_, locals_, fromlist, level)
        if _get_morphemizer_utils_modules():
            _install_ankimorphs_hook()
            if all(
                getattr(module, "_sudachi_morphemizer_patched", False)
                for module in _get_morphemizer_utils_modules()
            ):
                builtins.__import__ = _original_import
        return module

    import_hook._sudachi_import_hook = True
    builtins.__import__ = import_hook


def debug_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "addon_root": str(ADDON_ROOT),
        "morphemizer_description": MORPHEMIZER_DESCRIPTION,
        "morphemizer_utils_modules": [
            module.__name__ for module in _get_morphemizer_utils_modules()
        ],
        "patched": False,
        "registered": False,
        "available_morphemizers": None,
        "sudachi_successful_import": None,
        "sudachi_last_error": None,
    }

    morphemizer_utils_modules = _get_morphemizer_utils_modules()
    if morphemizer_utils_modules:
        morphemizer_utils = morphemizer_utils_modules[0]
        status["patched"] = getattr(
            morphemizer_utils,
            "_sudachi_morphemizer_patched",
            False,
        )
        descriptions = list(
            getattr(morphemizer_utils, "morphemizers_by_description", {}).keys()
        )
        status["registered"] = MORPHEMIZER_DESCRIPTION in descriptions
        status["available_morphemizers"] = descriptions

    try:
        from . import sudachi_wrapper

        sudachi_wrapper.setup_sudachi()
        status["sudachi_successful_import"] = sudachi_wrapper.successful_import
        status["sudachi_last_error"] = sudachi_wrapper.last_error
    except Exception as error:
        status["sudachi_successful_import"] = False
        status["sudachi_last_error"] = f"{type(error).__name__}: {error}"

    return status


_install_ankimorphs_hook()
_install_import_hook()
