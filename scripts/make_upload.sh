#!/usr/bin/env bash
# Build qa-studio-upload.zip from the last COMMIT.
#
# `git archive HEAD` exports tracked files only, so .git, venvs, node_modules,
# caches, build output and every gitignored file are excluded by construction.
# The zip contents are then checked anyway (defence in depth): if anything
# forbidden is found, or the zip exceeds 10 MB, the zip is deleted and we fail.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

OUT="qa-studio-upload.zip"
MAX_BYTES=$((10 * 1024 * 1024))

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "WARNING: uncommitted changes are NOT included (the archive is built from HEAD)." >&2
fi

rm -f "$OUT"
git archive --format=zip --prefix=qa-studio/ -o "$OUT" HEAD

fail() {
    echo "FAIL: $*" >&2
    rm -f "$OUT"
    exit 1
}

# --- list entries (unzip may be missing on minimal systems: fall back to Python)
if command -v unzip >/dev/null 2>&1; then
    unzip -l "$OUT"
    entries="$(unzip -Z1 "$OUT")"
else
    py="$(command -v python3 || command -v python)"
    "$py" -m zipfile -l "$OUT"
    entries="$("$py" -c 'import sys, zipfile; print("\n".join(zipfile.ZipFile(sys.argv[1]).namelist()))' "$OUT")"
fi

# --- forbidden paths (matched on any path segment)
forbidden_patterns=(
    '(^|/)\.git(/|$)'
    '(^|/)CLAUDE(\.local)?\.md$'
    '(^|/)AGENTS\.md$'
    '(^|/)\.claude(/|$)'
    '(^|/)docs(/|$)'
    '(^|/)node_modules(/|$)'
    '(^|/)\.?venv(/|$)'
    '(^|/)__pycache__(/|$)'
    '(^|/)\.next(/|$)'
)
found=""
for pattern in "${forbidden_patterns[@]}"; do
    matches="$(grep -E "$pattern" <<<"$entries" || true)"
    [[ -n "$matches" ]] && found+="$matches"$'\n'
done
# .env and .env.* are forbidden, except the .env.example templates
env_matches="$(grep -E '(^|/)\.env(\.[^/]*)?$' <<<"$entries" | grep -vE '\.env\.example$' || true)"
[[ -n "$env_matches" ]] && found+="$env_matches"$'\n'

if [[ -n "${found//$'\n'/}" ]]; then
    printf '%s' "$found" >&2
    fail "forbidden paths found in $OUT (listed above)"
fi

# --- size limit
bytes="$(wc -c <"$OUT" | tr -d ' ')"
size_mb="$(awk -v b="$bytes" 'BEGIN { printf "%.2f", b / 1048576 }')"
count="$(grep -c . <<<"$entries")"
echo
echo "Zip: $OUT  entries: $count  size: $bytes bytes ($size_mb MB)"
((bytes <= MAX_BYTES)) || fail "zip is larger than 10 MB"

echo "OK: no forbidden paths, under 10 MB."
