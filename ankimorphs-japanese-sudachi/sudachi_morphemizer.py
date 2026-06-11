from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from . import MORPHEMIZER_DESCRIPTION
from . import sudachi_wrapper


def build_sudachi_morphemizer(morpheme_class: Any, morphemizer_base: Any) -> Any:
    class SudachiMorphemizer(morphemizer_base):
        def __init__(self) -> None:
            super().__init__()
            sudachi_wrapper.setup_sudachi()

        def init_successful(self) -> bool:
            return sudachi_wrapper.successful_import

        def get_morphemes(self, sentences: list[str]) -> Iterator[list[Any]]:
            for sentence in sentences:
                yield sudachi_wrapper.get_morphemes_sudachi(sentence, morpheme_class)

        def get_description(self) -> str:
            return MORPHEMIZER_DESCRIPTION

    return SudachiMorphemizer
