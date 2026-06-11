# anki-morphs-sudachi

Companion add-on for [AnkiMorphs](https://github.com/mortii/anki-morphs)
that provides the `AnkiMorphs: Japanese Sudachi` morphemizer.

*Preface: For full transparency, this was basically entirely vibe coded using GPT 5.5 via OpenAI's Codex and a bit of Qwen 3.6 via OpenCode. You might find some oddities here and there!*

End users should install the `.ankiaddon` file and restart Anki. They should
not need to install pip packages, Rust, system Python packages, or Sudachi
dictionaries manually.

The first actual Sudachi tokenization can take a while because AnkiMorphs
extracts the bundled `SudachiDict-full` dictionary from the add-on archive.
The extracted dictionary is treated as rebuildable cache.

## Prerequisites

- Python 3.12 or later
- `pip` (comes with most Python installations)

## Build

From this repository root:

```sh
# 1. Clone the repository (skip if you already have it)
git clone https://github.com/YOUR_USERNAME/anki-morphs-sudachi.git
cd anki-morphs-sudachi

# 2. Download SudachiPy wheels and build the SudachiDict-full archive
python3 scripts/build_vendor.py

# 3. Bundle everything into an .ankiaddon file
python3 scripts/bundle_addon.py

# 4. Verify the package is well-formed
python3 scripts/check_package.py ankimorphs_japanese_sudachi.ankiaddon
```

Step 2 (`build_vendor.py`) downloads official PyPI artifacts, extracts only the
selected SudachiPy wheels, materializes `SudachiDict-full`, writes
`deps/dict/sudachi_full_20260428.tar.xz`, and records checksums plus expected
dictionary paths in `deps/dict/manifest.json`.

Step 3 (`bundle_addon.py`) produces `ankimorphs_japanese_sudachi.ankiaddon`
in the repository root. This file is gitignored and must be rebuilt after any
code change.

Step 4 (`check_package.py`) validates that the `.ankiaddon` contains all
required files for every supported platform and that the package imports
without errors.

## Bundled Runtime

- `SudachiPy==0.6.11`
- `SudachiDict-full==20260428`

SudachiPy is vendored as extracted wheels under:

```text
ankimorphs_japanese_sudachi/deps/sudachipy/<python_tag>/<os_arch>/
```

Supported runtime targets:

- `cpython-312/linux-x86_64`
- `cpython-312/linux-aarch64`
- `cpython-312/windows-amd64`
- `cpython-312/macos-x86_64`
- `cpython-312/macos-arm64`
- `cpython-313/linux-x86_64`
- `cpython-313/linux-aarch64`
- `cpython-313/windows-amd64`
- `cpython-313/macos-x86_64`
- `cpython-313/macos-arm64`
- `cpython-314/linux-x86_64`
- `cpython-314/linux-aarch64`
- `cpython-314/windows-amd64`
- `cpython-314/macos-x86_64`
- `cpython-314/macos-arm64`

Unsupported platforms fail morphemizer discovery with a diagnostic instead of
raising a native import traceback.

## License

This project's own code is released under the Unlicense. See [LICENSE](LICENSE).

Bundled third-party components retain their original licenses. See
[LICENSE-3RD-PARTY.txt](LICENSE-3RD-PARTY.txt) for details.
