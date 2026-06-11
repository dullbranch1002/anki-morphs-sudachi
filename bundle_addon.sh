#!/bin/sh
set -eu

PACKAGE_DIR="ankimorphs_japanese_sudachi"
OUTPUT_FILE="ankimorphs_japanese_sudachi.ankiaddon"

cd "$PACKAGE_DIR"

find . -depth -regex '^.*\(__pycache__\|\.py[co]\)$' -delete
rm -rf deps/dict/sudachi_full_20260428
rm -rf user_files

test -f manifest.json
test -f deps/dict/sudachi_full_20260428.tar.xz
test -f deps/dict/manifest.json

for python_tag in cpython-312 cpython-313 cpython-314; do
  for os_arch in linux-x86_64 linux-aarch64 windows-amd64 macos-x86_64 macos-arm64; do
    test -d "deps/sudachipy/$python_tag/$os_arch"
  done
done

rm -f "../$OUTPUT_FILE"
if command -v zip >/dev/null 2>&1; then
  zip -r "../$OUTPUT_FILE" ./*
else
  python3 - "$OUTPUT_FILE" <<'PY'
import os
import sys
import zipfile

output_file = os.path.join("..", sys.argv[1])
with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as addon:
    for root, _dirs, files in os.walk("."):
        for filename in files:
            path = os.path.join(root, filename)
            arcname = os.path.relpath(path, ".")
            addon.write(path, arcname)
PY
fi

cd ..
