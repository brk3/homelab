#!/usr/bin/env bash
# Self-check: pick_latest ignores junk tags and version-sorts the rest.
set -euo pipefail

. "$(dirname "$0")/sync-oci-tag.sh"

out="$(printf 'latest\nv1.9.0\nv1.21.1\nv1.21.0-alpha.0\nstable\n0.87.0\n' | pick_latest)"
[ "$out" = "v1.21.1" ] || { echo "FAIL: got '$out', want v1.21.1" >&2; exit 1; }
echo "OK"
