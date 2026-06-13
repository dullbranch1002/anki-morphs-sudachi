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
    pytest.param(
        "“ああ　そうなのかも”って",
        [
            ExpectedMorpheme("ああ", "ああ", "感動詞"),
            ExpectedMorpheme("そう", "そう", "副詞"),
            ExpectedMorpheme("だ", "な", "助動詞"),
            ExpectedMorpheme("の", "の", "助詞", "準体助詞"),
            ExpectedMorpheme("かも", "かも", "助詞", "副助詞"),
            ExpectedMorpheme("って", "って", "助詞", "副助詞"),
        ],
        id="quoted sentence with full-width space",
    ),
    pytest.param(
        # Source: ほいじゃ　いくよ
        # Misparse: in this context Sudachi treats "いくよ" as a proper-name
        # noun, but the useful AnkiMorphs units are the verb "いく" plus "よ".
        "ほいじゃ　いくよ",
        [
            ExpectedMorpheme("ほい", "ほい", "代名詞"),
            ExpectedMorpheme("じゃ", "じゃ", "助詞"),
            ExpectedMorpheme("いく", "いく", "動詞"),
            ExpectedMorpheme("よ", "よ", "助詞"),
        ],
        id="kana iku yo after colloquial lead-in",
    ),
    pytest.param(
        # Source: （岡部）ＳＥＲＮ(セルン)にハッキングだ
        # Misparse: "(セルン)" is a kana reading annotation for "ＳＥＲＮ",
        # not a separate morph that should be learned from the sentence.
        "（岡部）ＳＥＲＮ(セルン)にハッキングだ",
        [
            ExpectedMorpheme("岡部", "岡部", "名詞"),
            ExpectedMorpheme("sern", "ＳＥＲＮ", "名詞"),
            ExpectedMorpheme("に", "に", "助詞"),
            ExpectedMorpheme("ハッキング", "ハッキング", "名詞"),
            ExpectedMorpheme("だ", "だ", "助動詞"),
        ],
        id="parenthetical kana reading annotation",
    ),
    pytest.param(
        "いってらっしゃ～い…　ん？",
        [
            ExpectedMorpheme("いく", "いっ", "動詞"),
            ExpectedMorpheme("てらっしゃる", "てらっしゃ～い", "助動詞"),
            ExpectedMorpheme("ん", "ん", "感動詞"),
        ],
        id="wave dash elongated itterasshai",
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
