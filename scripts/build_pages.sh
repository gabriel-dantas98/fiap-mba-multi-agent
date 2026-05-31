#!/usr/bin/env bash
# Stage the GitHub Pages site into ./_site
#
# The published site is the AI Business Strategy deliverable at the root, plus the global
# brand/ design system copied alongside it (so the page can load brand assets at runtime
# without committing duplicates). Used by both local preview and the Pages workflow.
#
#   ./scripts/build_pages.sh && (cd _site && python3 -m http.server 8137)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/_site"
SITE="$ROOT/apps/static-web-apps/ai-business-strategy"

rm -rf "$OUT"
mkdir -p "$OUT"

# 1) the deliverable site at the published root
cp -R "$SITE/." "$OUT/"

# 2) the global brand assets, available at /brand
mkdir -p "$OUT/brand"
cp -R "$ROOT/brand/." "$OUT/brand/"

echo "Staged site -> $OUT"
