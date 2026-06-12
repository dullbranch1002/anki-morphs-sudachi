from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ADDON_PACKAGE_NAME = "ankimorphs_japanese_sudachi"
ADDON_ROOT = Path(__file__).resolve().parents[1] / "ankimorphs-japanese-sudachi"


def _load_addon_package() -> ModuleType:
    package = sys.modules.get(ADDON_PACKAGE_NAME)
    if package is not None:
        return package

    spec = importlib.util.spec_from_file_location(
        ADDON_PACKAGE_NAME,
        ADDON_ROOT / "__init__.py",
        submodule_search_locations=[str(ADDON_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load add-on package from {ADDON_ROOT}")

    package = importlib.util.module_from_spec(spec)
    sys.modules[ADDON_PACKAGE_NAME] = package
    spec.loader.exec_module(package)
    return package


@pytest.fixture(scope="session")
def addon_package() -> ModuleType:
    return _load_addon_package()


@pytest.fixture(scope="session")
def sudachi_wrapper(addon_package: ModuleType) -> ModuleType:
    return importlib.import_module(f"{addon_package.__name__}.sudachi_wrapper")
