#!/usr/bin/env bash
# Regenerate the backend lockfiles from backend/pyproject.toml, then prove that:
#   - every pin installs from a binary wheel on Linux AND Windows for each supported Python;
#   - no pinned package has a known vulnerability (pip-audit, PyPA/OSV advisory database).
#
# Why two passes:
#   A plain universal resolve "forks" on Python-version markers and picks different
#   versions per Python (e.g. SQLAlchemy 2.0 on 3.10, 2.1 on 3.14). Code tested on one
#   Python could then behave differently on another. So:
#   1. resolve once for the OLDEST supported Python (3.10) on Linux -> one version set;
#   2. resolve universally, constrained to those pins -> same versions everywhere,
#      only genuinely platform-specific packages (colorama/win, uvloop/linux) differ;
#   3. runtime lock is constrained to the dev lock -> runtime pins == dev pins.
#
# Requires uv (https://docs.astral.sh/uv/) and internet access. Only needed when changing
# dependencies; installing from the lockfiles needs plain pip only.
set -euo pipefail

cd "$(dirname "$0")/../backend"

PLATFORMS=(
    "x86_64-manylinux_2_39"    # Linux: Ubuntu 24.04 ships glibc 2.39
    "x86_64-pc-windows-msvc"   # Windows 64-bit
)
PYTHONS=(3.10 3.11 3.12 3.13 3.14)
# Relative names on purpose: uv writes constraint-file paths into the lock's "via"
# comments, and an absolute temp path would leak the local username into the repo.
tmp_pins=".pins-py310.txt"
tmp_all=".pins-all.txt"
trap 'rm -f "$tmp_pins" "$tmp_all"' EXIT

common=(--universal --python-version 3.10 --custom-compile-command "scripts/lock_backend.sh")

# 1. single version set, valid on the oldest Python
uv pip compile pyproject.toml --extra dev --python-version 3.10 \
    --python-platform "${PLATFORMS[0]}" --no-header --no-annotate --quiet -o "$tmp_pins"

# 2. universal locks pinned to that set (--upgrade: ignore old pins in the existing
#    lockfile, so packages only needed on newer Pythons get their latest releases)
uv pip compile pyproject.toml --extra dev -c "$tmp_pins" --upgrade "${common[@]}" -o requirements-dev.lock
uv pip compile pyproject.toml -c requirements-dev.lock --upgrade "${common[@]}" -o requirements.lock

# 3. every pin must install from a binary wheel (no compiler / no internet on the target)
for platform in "${PLATFORMS[@]}"; do
    for py in "${PYTHONS[@]}"; do
        uv pip compile requirements-dev.lock --python-version "$py" \
            --python-platform "$platform" --only-binary :all: --quiet -o "$tmp_pins"   # output discarded
        echo "ok: binary wheels for cp${py/./} on $platform"
    done
done

# 4. no known vulnerabilities in ANY pin (markers stripped, so Linux-only and
#    Windows-only packages are audited too, whatever OS this script runs on)
sed -nE 's/^([A-Za-z0-9._-]+==[^ ;]+).*/\1/p' requirements-dev.lock | sort -u >"$tmp_all"
uvx pip-audit --requirement "$tmp_all" --no-deps --disable-pip --progress-spinner off
echo "ok: pip-audit found no known vulnerabilities"

echo "Lockfiles updated: backend/requirements.lock, backend/requirements-dev.lock"
