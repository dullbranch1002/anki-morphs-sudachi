from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class Morpheme:
    lemma: str
    inflection: str
    part_of_speech: str
    sub_part_of_speech: str


class MorphemizerBase:
    def __init__(self) -> None:
        self.initialized = True


def test_built_morphemizer_hands_sudachi_results_to_ankimorphs(
    addon_package: ModuleType,
    monkeypatch: Any,
) -> None:
    sudachi_morphemizer = importlib.import_module(
        f"{addon_package.__name__}.sudachi_morphemizer"
    )
    sudachi_wrapper = importlib.import_module(
        f"{addon_package.__name__}.sudachi_wrapper"
    )

    def get_morphemes_sudachi(
        expression: str,
        morpheme_class: type[Morpheme],
    ) -> list[Morpheme]:
        return [
            morpheme_class(
                lemma=f"{expression}:lemma",
                inflection=expression,
                part_of_speech="名詞",
                sub_part_of_speech="普通名詞",
            )
        ]

    monkeypatch.setattr(sudachi_wrapper, "successful_import", True)
    monkeypatch.setattr(sudachi_wrapper, "setup_sudachi", lambda: None)
    monkeypatch.setattr(
        sudachi_wrapper,
        "get_morphemes_sudachi",
        get_morphemes_sudachi,
    )

    morphemizer_class = sudachi_morphemizer.build_sudachi_morphemizer(
        Morpheme,
        MorphemizerBase,
    )
    morphemizer = morphemizer_class()

    assert morphemizer.initialized
    assert morphemizer.init_successful()
    assert list(morphemizer.get_morphemes(["猫", "本"])) == [
        [
            Morpheme(
                lemma="猫:lemma",
                inflection="猫",
                part_of_speech="名詞",
                sub_part_of_speech="普通名詞",
            )
        ],
        [
            Morpheme(
                lemma="本:lemma",
                inflection="本",
                part_of_speech="名詞",
                sub_part_of_speech="普通名詞",
            )
        ],
    ]
