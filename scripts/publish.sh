#!/usr/bin/env bash
# Manual publish for the DRA public site.
#
# Wraps the full local workflow into one command:
#   1. (optional) regenerate docs/ratings.json by running the snapshot
#   2. commit any regenerated snapshot file
#   3. push commits to the dra-core source repo
#   4. subtree-split docs/ and force-push to the org Pages repo
#   5. wait for GitHub Pages to rebuild and report status
#
# Usage:
#   ./scripts/publish.sh                  # split & push the current docs/ state
#   ./scripts/publish.sh --snapshot       # regenerate ratings.json first
#   ./scripts/publish.sh --snapshot --no-wait
#
# Required local git remotes (set up once with `git remote add`):
#   core -> https://github.com/DefiRiskAlliance/dra-core.git
#   dra  -> https://github.com/DefiRiskAlliance/defiriskalliance.github.io.git
#
# Requires `gh` CLI authenticated for the optional Pages-status wait.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

REGEN=0
WAIT=1
for arg in "$@"; do
  case "$arg" in
    --snapshot) REGEN=1 ;;
    --no-wait)  WAIT=0 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg" >&2
      exit 2
      ;;
  esac
done

# 1. Optional: regenerate the snapshot.
if [ "$REGEN" = "1" ]; then
  echo "==> Regenerating docs/ratings.json"
  python3 -m examples.dra_site_snapshot

  if ! git diff --quiet -- docs/ratings.json examples/dra_site_snapshot.py; then
    echo "==> Committing regenerated snapshot"
    git add docs/ratings.json examples/dra_site_snapshot.py
    git commit -m "ratings: regenerate snapshot"
  else
    echo "==> No snapshot changes"
  fi
fi

# 2. Safety: refuse to publish if anything is uncommitted under docs/.
if ! git diff --quiet -- docs/ || ! git diff --cached --quiet -- docs/; then
  echo "ERROR: uncommitted changes under docs/. Commit (or stash) before publishing." >&2
  git status -- docs/
  exit 1
fi

# 3. Push the source repo first so docs/ state on github matches what we ship.
echo "==> Pushing to core (dra-core)"
git push core main

# 4. Subtree-split docs/ and push to the Pages repo.
echo "==> Subtree-splitting docs/"
git branch -D dra-publish >/dev/null 2>&1 || true
git subtree split --prefix=docs -b dra-publish >/dev/null
SHA="$(git rev-parse dra-publish)"
echo "    -> $SHA"

echo "==> Pushing to dra (defiriskalliance.github.io)"
git push dra dra-publish:main

# 5. Optionally wait for Pages to rebuild.
if [ "$WAIT" = "1" ] && command -v gh >/dev/null 2>&1; then
  echo "==> Waiting for GitHub Pages build"
  until [ "$(gh api repos/DefiRiskAlliance/defiriskalliance.github.io/pages/builds/latest --jq .status 2>/dev/null)" != "building" ]; do
    sleep 5
  done
  gh api repos/DefiRiskAlliance/defiriskalliance.github.io/pages/builds/latest \
    --jq '{status, commit, updated_at}'
fi

echo ""
echo "Done. Live at https://defiriskalliance.github.io/"
