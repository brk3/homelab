#!/usr/bin/env bash
# Bump one OCIRepository's ref.tag to the latest tag on its registry, commit, and
# reconcile so Flux applies it now. Needs: crane, flux, kubectl context on dagda.
# Usage: scripts/sync-oci-tag.sh <ocirepository-name>
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# stdin: tag list; stdout: highest version. Junk tags (latest, stable, ...) are dropped.
pick_latest() {
  grep -E '^v?[0-9]+(\.[0-9]+)+' | sort -V | tail -1
}

main() {
  NAME="${1:?usage: $0 <ocirepository-name>}"
  file="$(grep -rl --include=ocirepository.yaml "^  name: ${NAME}\$" "$ROOT/clusters")"
  [ -n "$file" ] || { echo "no ocirepository.yaml named '$NAME' under clusters/" >&2; exit 1; }

  url="$(sed -n 's|^  url: oci://||p' "$file" | head -1)"
  tag="$(sed -n 's|^    tag: ||p' "$file" | head -1)"
  latest="$(crane ls "$url" | pick_latest)"
  [ "$latest" = "$tag" ] && { echo "$NAME already at $tag"; return 0; }

  echo "$NAME: $tag -> $latest"
  sed -i '' "s|^    tag: .*|    tag: $latest|" "$file"
  git -C "$ROOT" add "$file"
  git -C "$ROOT" commit -m "chore(deps): bump $NAME $tag -> $latest"
  git -C "$ROOT" push origin HEAD # Flux reconciles from the remote, not the local commit

  ks="$(basename "$(dirname "$(dirname "$file")")")"
  flux reconcile kustomization "$ks" --with-source # apply the new tag to the cluster
  flux reconcile source oci "$NAME"                # re-pull chart; HelmRelease follows
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
