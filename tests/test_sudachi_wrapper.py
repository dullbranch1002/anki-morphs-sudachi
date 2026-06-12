from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Morpheme:
    lemma: str
    inflection: str
    part_of_speech: str
    sub_part_of_speech: str


class FakeToken:
    def __init__(
        self,
        *,
        surface: str,
        dictionary_form: str,
        part_of_speech: tuple[str, ...],
    ) -> None:
        self._surface = surface
        self._dictionary_form = dictionary_form
        self._part_of_speech = part_of_speech

    def surface(self) -> str:
        return self._surface

    def dictionary_form(self) -> str:
        return self._dictionary_form

    def part_of_speech(self) -> tuple[str, ...]:
        return self._part_of_speech


class FakeTokenizer:
    def __init__(self, tokens: list[FakeToken]) -> None:
        self._tokens = tokens
        self.last_expression = ""

    def tokenize(self, expression: str) -> list[FakeToken]:
        self.last_expression = expression
        return self._tokens


def test_get_morphemes_sudachi_filters_tokens_before_ankimorphs(
    sudachi_wrapper: Any,
    monkeypatch: Any,
) -> None:
    tokenizer = FakeTokenizer(
        [
            FakeToken(
                surface="猫",
                dictionary_form="猫",
                part_of_speech=("名詞", "普通名詞"),
            ),
            FakeToken(
                surface="123",
                dictionary_form="123",
                part_of_speech=("名詞", "数詞"),
            ),
            FakeToken(
                surface="。",
                dictionary_form="。",
                part_of_speech=("補助記号", "句点"),
            ),
            FakeToken(
                surface="未知語",
                dictionary_form="*",
                part_of_speech=("名詞", "普通名詞"),
            ),
        ]
    )
    monkeypatch.setattr(sudachi_wrapper, "_get_tokenizer", lambda: tokenizer)

    morphemes = sudachi_wrapper.get_morphemes_sudachi("猫\x00123。未知語", Morpheme)

    assert tokenizer.last_expression == "猫123。未知語"
    assert morphemes == [
        Morpheme(
            lemma="猫",
            inflection="猫",
            part_of_speech="名詞",
            sub_part_of_speech="普通名詞",
        ),
        Morpheme(
            lemma="未知語",
            inflection="未知語",
            part_of_speech="名詞",
            sub_part_of_speech="普通名詞",
        ),
    ]


def test_get_morphemes_sudachi_composes_kamo(
    sudachi_wrapper: Any,
    monkeypatch: Any,
) -> None:
    tokenizer = FakeTokenizer(
        [
            FakeToken(
                surface="か",
                dictionary_form="か",
                part_of_speech=("助詞", "副助詞"),
            ),
            FakeToken(
                surface="も",
                dictionary_form="も",
                part_of_speech=("助詞", "係助詞"),
            ),
        ]
    )
    monkeypatch.setattr(sudachi_wrapper, "_get_tokenizer", lambda: tokenizer)

    morphemes = sudachi_wrapper.get_morphemes_sudachi("かも", Morpheme)

    assert morphemes == [
        Morpheme(
            lemma="かも",
            inflection="かも",
            part_of_speech="助詞",
            sub_part_of_speech="副助詞",
        ),
    ]
