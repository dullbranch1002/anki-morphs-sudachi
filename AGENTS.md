# Agent Notes

## AnkiMorphs Verification

When asked whether a morph was picked up by AnkiMorphs, is known, or was manually
added, check the Anki profile data directly.

Default local test profile is under the current user's Anki data directory.
Commands below assume:

```sh
ANKI_PROFILE="${ANKI_PROFILE:-$HOME/.local/share/Anki2/Test}"
ANKI_ADDONS="${ANKI_ADDONS:-$HOME/.local/share/Anki2/addons21}"
```

- Profile folder: `$ANKI_PROFILE`
- AnkiMorphs DB: `$ANKI_PROFILE/ankimorphs.db`
- Anki collection DB: `$ANKI_PROFILE/collection.anki2`
- Known morphs folder: `$ANKI_PROFILE/known-morphs`
- Profile settings: `$ANKI_PROFILE/ankimorphs_profile_settings.json`
- Installed AnkiMorphs add-on: `$ANKI_ADDONS/472573498`

Anki may keep `collection.anki2` locked. For read-only collection checks, use
SQLite immutable mode:

```sh
sqlite3 -readonly "file:$ANKI_PROFILE/collection.anki2?immutable=1" '...'
```

AnkiMorphs DB schema currently has only these tables:

- `Morphs`
- `Cards`
- `Card_Morph_Map`
- `Seen_Morphs`

There is no separate manually-known morph table. Manual knowledge enters through:

- The configured manual-known note tag, currently
  `_card-status::i+0-manually` in `ankimorphs_profile_settings.json`.
- CSV files under `known-morphs/`, when `read_known_morphs_folder` is true.

During recalculation, AnkiMorphs:

- Rebuilds `ankimorphs.db`.
- Parses configured card fields into morphs.
- Sets morph learning intervals from card interval/stability.
- Treats cards tagged with `tag_known_automatically` or `tag_known_manually` as
  known by assigning `interval_for_known_morphs`.
- Imports CSV rows from `known-morphs/` into `Morphs` with
  `interval_for_known_morphs`.

Useful source files in the installed add-on:

- `ankimorphs_db.py`: table definitions and known/seen queries.
- `recalc/caching.py`: DB rebuild, known-morphs CSV import, known interval logic.
- `reviewing_utils.py`: "Set known and skip" adds `tag_known_manually`.
- `recalc/anki_data_utils.py`: reads card/note tags into recalc data.

Checklist for a morph, replacing `かも` with the target:

1. Check whether the morph exists and whether its intervals meet the known
   threshold:

```sh
sqlite3 -header -column "$ANKI_PROFILE/ankimorphs.db" \
  "SELECT lemma, inflection, highest_lemma_learning_interval, highest_inflection_learning_interval
   FROM Morphs
   WHERE lemma = 'かも' OR inflection = 'かも'
   ORDER BY lemma, inflection;"
```

2. Check whether it was seen today:

```sh
sqlite3 -header -column "$ANKI_PROFILE/ankimorphs.db" \
  "SELECT lemma, inflection
   FROM Seen_Morphs
   WHERE lemma = 'かも' OR inflection = 'かも'
   ORDER BY lemma, inflection;"
```

3. Check whether any cards contain it:

```sh
sqlite3 -header -column "$ANKI_PROFILE/ankimorphs.db" \
  "SELECT cmm.card_id, cmm.morph_lemma, cmm.morph_inflection, c.tags
   FROM Card_Morph_Map cmm
   JOIN Cards c ON c.card_id = cmm.card_id
   WHERE cmm.morph_lemma = 'かも' OR cmm.morph_inflection = 'かも'
   ORDER BY cmm.card_id;"
```

4. Check for manually-known tagged notes/cards:

```sh
sqlite3 -readonly "file:$ANKI_PROFILE/collection.anki2?immutable=1" \
  "SELECT COUNT(*)
   FROM notes
   WHERE tags LIKE '%_card-status::i+0-manually%';"
```

If there are tagged notes, join cards and then compare card IDs to
`Card_Morph_Map`:

```sh
sqlite3 -readonly "file:$ANKI_PROFILE/collection.anki2?immutable=1" \
  "SELECT c.id AS card_id, n.id AS note_id, n.tags, n.flds
   FROM cards c
   JOIN notes n ON n.id = c.nid
   WHERE n.tags LIKE '%_card-status::i+0-manually%'
   LIMIT 50;"
```

5. Check known-morphs CSV imports. Use exact-line or CSV-aware checks where
possible; avoid substring-only conclusions because files may contain words like
`かもね`.

```sh
rg -n '^かも$|^かも,|,かも$' "$ANKI_PROFILE/known-morphs"
```

6. Check settings that affect known status:

```sh
rg -n '"interval_for_known_morphs"|"evaluate_morph_lemma"|"evaluate_morph_inflection"|"read_known_morphs_folder"|"tag_known_manually"' \
  "$ANKI_PROFILE/ankimorphs_profile_settings.json"
```

Interpretation:

- With `evaluate_morph_lemma: true`, known status is generally evaluated by lemma.
- A morph is known when its relevant interval is at least
  `interval_for_known_morphs`.
- A priority-file match does not mean the morph is known; it only affects
  priority.
- If a composed morph such as `かも` is newly emitted by a morphemizer, existing
  known rows for separate `か` and `も` do not imply `かも` is known.

## Random Deck Parse Audit

When given a deck name and a number of random cards to analyse, audit the
AnkiMorphs parse quality for that sample. The goal is to find real parser or
composition misses, add regression coverage for them, and intentionally leave
the tests failing. Do not fix implementation code during this workflow.

Use the default Test profile paths from the AnkiMorphs Verification section
unless the user specifies another profile.

1. Find the deck id.

Plain SQLite does not load Anki's custom `unicase` collation, so avoid `WHERE`
or `ORDER BY` on deck names. Print all deck rows and match the requested deck
name manually:

```sh
sqlite3 -readonly "file:$ANKI_PROFILE/collection.anki2?immutable=1" \
  "SELECT id, quote(name) FROM decks;"
```

2. Sample the requested number of random cards from that deck.

The first note field is usually the sentence field for local test decks. Confirm
field layout if the sampled text does not look like sentences.

```sh
sqlite3 -readonly "file:$ANKI_PROFILE/collection.anki2?immutable=1" \
  "SELECT c.id AS card_id,
          n.id AS note_id,
          substr(n.flds, 1, instr(n.flds, char(31))-1) AS sentence
   FROM cards c
   JOIN notes n ON n.id = c.nid
   WHERE c.did = DECK_ID
   ORDER BY random()
   LIMIT SAMPLE_COUNT;"
```

3. Pull AnkiMorphs' stored morphs for the sampled card ids.

```sh
sqlite3 -header -column "$ANKI_PROFILE/ankimorphs.db" \
  "SELECT cmm.card_id, cmm.morph_lemma, cmm.morph_inflection
   FROM Card_Morph_Map cmm
   WHERE cmm.card_id IN (CARD_IDS)
   ORDER BY cmm.card_id, cmm.morph_lemma, cmm.morph_inflection;"
```

4. Reproduce this repo's wrapper output for each sampled sentence.

Use the "Sentence Morph Validation" reproduction command below, replacing the
sentence each time. Compare wrapper output to the DB morphs. Speaker labels,
known status, card tags, and AnkiMorphs filtering can explain why some wrapper
tokens do not appear in the card's DB morph list.

5. Inspect raw Sudachi tokenization for suspicious sentences.

Use the raw Sudachi A/B/C command below. This distinguishes upstream Sudachi
boundaries from wrapper filtering or composition behavior.

6. Decide whether a sampled card reveals a misparse.

Treat these as misparses worth regression coverage:

- A useful fixed expression is fragmented into less useful morphs.
- An elongated, quoted, punctuated, or whitespace-adjacent form breaks a morph
  that is parsed well in a normalized nearby form.
- Japanese content yields no morphs, or content words/particles/auxiliaries are
  lost due to wrapper filtering.
- The wrapper differs from raw Sudachi in a way that removes useful AnkiMorphs
  units.

Do not count these as misparses by themselves:

- A morph is absent only because it is already known, manually known, or filtered
  by AnkiMorphs status behavior.
- The installed Anki add-on is stale or the AnkiMorphs DB has not been
  recalculated since the repo code changed.
- Raw Sudachi, this wrapper, and the DB all agree and the result is merely
  surprising rather than harmful to AnkiMorphs.

7. Add failing regression tests for each discovered misparse.

- Put real sentence regressions in `tests/test_sudachi_parsing_examples.py`.
- Put fake-token wrapper rule regressions in `tests/test_sudachi_wrapper.py`.
- Add a short comment next to every new regression test stating the source
  sentence and why the observed output is a misparse. Do not include deck,
  note, card, or other source metadata in the comment.
- Set the expected morphs to the useful behavior AnkiMorphs should eventually
  provide.
- Run a focused pytest command to confirm the new test fails for the expected
  reason.
- Do not change parser code or make the new test pass.

After adding a failing regression, continue auditing the remaining sampled
cards. In the final response, list the sampled card ids/sentences at a high
level, identify any failing tests added, and report the focused test result.

## Sentence Morph Validation

When given a sentence plus the morphs shown in Anki, validate whether the morphs
make sense before changing code. The goal is to distinguish:

- Expected Sudachi tokenization.
- Expected AnkiMorphs filtering/composition.
- Known-word status effects.
- A genuine morphemizer bug that needs a regression test and implementation fix.

Use this workflow:

1. Reproduce this add-on's output for the exact sentence.

```sh
.venv/bin/python - <<'PY'
from dataclasses import dataclass
import importlib
import importlib.util
import sys
from pathlib import Path

@dataclass(frozen=True)
class Morpheme:
    lemma: str
    inflection: str
    part_of_speech: str
    sub_part_of_speech: str

repo = Path.cwd()
addon_root = repo / "ankimorphs-japanese-sudachi"
name = "ankimorphs_japanese_sudachi"
spec = importlib.util.spec_from_file_location(
    name, addon_root / "__init__.py", submodule_search_locations=[str(addon_root)]
)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
assert spec.loader is not None
spec.loader.exec_module(module)
wrapper = importlib.import_module(f"{name}.sudachi_wrapper")
wrapper.setup_sudachi()
if not wrapper.successful_import:
    raise SystemExit(wrapper.last_error)

sentence = "REPLACE_SENTENCE_HERE"
for morph in wrapper.get_morphemes_sudachi(sentence, Morpheme):
    print(morph)
PY
```

2. Inspect raw Sudachi tokenization for the same sentence, including split modes
   A/B/C. This shows whether Sudachi itself emitted the odd boundary.

```sh
.venv/bin/python - <<'PY'
import importlib.util
import sys
from pathlib import Path

repo = Path.cwd()
addon_root = repo / "ankimorphs-japanese-sudachi"
name = "ankimorphs_japanese_sudachi"
spec = importlib.util.spec_from_file_location(
    name, addon_root / "__init__.py", submodule_search_locations=[str(addon_root)]
)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
assert spec.loader is not None
spec.loader.exec_module(module)
wrapper = __import__(f"{name}.sudachi_wrapper", fromlist=["*"])
wrapper.setup_sudachi()
if not wrapper.successful_import:
    raise SystemExit(wrapper.last_error)

from sudachipy import Dictionary, SplitMode

sentence = "REPLACE_SENTENCE_HERE"
dictionary = Dictionary(dict=str(wrapper._ensure_system_dic()))
for mode_name in ["A", "B", "C"]:
    tokenizer = dictionary.create(getattr(SplitMode, mode_name))
    print(mode_name)
    for token in tokenizer.tokenize(sentence):
        print(
            repr(token.surface()),
            repr(token.dictionary_form()),
            token.part_of_speech(),
            repr(token.normalized_form()),
        )
PY
```

3. Compare against Anki's displayed morphs.

- If raw Sudachi and this wrapper both match Anki, the behavior is probably
  expected tokenizer output unless the composition would be more useful for
  AnkiMorphs.
- If raw Sudachi is reasonable but this wrapper drops or splits incorrectly,
  inspect `_POS_BLACKLIST`, `_SUB_POS_BLACKLIST`, lemma fallback, and local
  composition rules in `sudachi_wrapper.py`.
- If this wrapper output differs from Anki, check whether the installed add-on
  in Anki is current. Rebuild/reinstall the `.ankiaddon` before assuming the DB
  reflects repo code.
- If the displayed morphs are affected by known status, use the AnkiMorphs
  verification checklist above to check `Morphs`, `Card_Morph_Map`,
  `Seen_Morphs`, manual-known tags, and `known-morphs/` CSV imports.

4. Decide whether a test and fix are warranted.

Add a regression test and fix when:

- The wrapper returns no morphs for Japanese content that should produce morphs.
- Useful fixed expressions are split into less useful morphs, such as `か` + `も`
  where the intended AnkiMorphs unit is `かも`.
- Punctuation, whitespace, quotes, or control characters cause meaningful tokens
  to be lost.
- A filtered POS/sub-POS removes content words, auxiliaries, or particles that
  should be available to AnkiMorphs.

Do not change code when:

- The difference is only known/unknown status, not parsing.
- The morph is only present in a priority file.
- Anki is showing stale output from an old add-on build or an unrecalculated DB.

5. Test placement.

- Real Sudachi sentence regressions go in
  `tests/test_sudachi_parsing_examples.py`.
- Wrapper behavior that can be expressed with fake tokens goes in
  `tests/test_sudachi_wrapper.py`.
- Prefer adding a fast fake-token test for any new wrapper composition/filtering
  rule, plus a real Sudachi parsing example when the bug depends on actual
  Sudachi tokenization.

6. Verification command.

```sh
.venv/bin/python -m pytest -q
```
