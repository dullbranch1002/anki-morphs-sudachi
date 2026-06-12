from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest


@dataclass(frozen=True)
class Morpheme:
    lemma: str
    inflection: str
    part_of_speech: str
    sub_part_of_speech: str


@dataclass(frozen=True)
class ExpectedMorpheme:
    lemma: str
    inflection: str
    part_of_speech: str | None = None
    sub_part_of_speech: str | None = None


SUDACHI_EXAMPLES = [
    pytest.param(
        "猫が好きです。",
        [
            ExpectedMorpheme("猫", "猫", "名詞"),
            ExpectedMorpheme("が", "が", "助詞"),
            ExpectedMorpheme("好き", "好き", "形状詞"),
            ExpectedMorpheme("です", "です", "助動詞"),
        ],
        id="basic sentence with punctuation",
    ),
    pytest.param(
        "食べる",
        [
            ExpectedMorpheme("食べる", "食べる", "動詞"),
        ],
        id="dictionary form verb",
    ),
    pytest.param(
        "本を読む",
        [
            ExpectedMorpheme("本", "本", "名詞"),
            ExpectedMorpheme("を", "を", "助詞"),
            ExpectedMorpheme("読む", "読む", "動詞"),
        ],
        id="noun particle verb",
    ),
]


def _require_sudachi_runtime(sudachi_wrapper: Any) -> None:
    sudachi_wrapper.setup_sudachi()
    if not sudachi_wrapper.successful_import:
        pytest.skip(
            "vendored Sudachi runtime is unavailable; run "
            "`python3 scripts/build_vendor.py` before these integration tests. "
            f"Last error: {sudachi_wrapper.last_error}"
        )


@pytest.mark.sudachi
@pytest.mark.parametrize(("expression", "expected"), SUDACHI_EXAMPLES)
def test_sudachi_parsing_examples(
    sudachi_wrapper: Any,
    expression: str,
    expected: list[ExpectedMorpheme],
) -> None:
    _require_sudachi_runtime(sudachi_wrapper)

    actual = sudachi_wrapper.get_morphemes_sudachi(expression, Morpheme)

    assert len(actual) == len(expected)
    for actual_morpheme, expected_morpheme in zip(actual, expected, strict=True):
        assert actual_morpheme.lemma == expected_morpheme.lemma
        assert actual_morpheme.inflection == expected_morpheme.inflection
        if expected_morpheme.part_of_speech is not None:
            assert actual_morpheme.part_of_speech == expected_morpheme.part_of_speech
        if expected_morpheme.sub_part_of_speech is not None:
            assert (
                actual_morpheme.sub_part_of_speech
                == expected_morpheme.sub_part_of_speech
            )
