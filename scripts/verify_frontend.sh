#!/usr/bin/env bash
# Install and production-build the frontend of every product in products/.
#
# This is the proof that the live demo actually builds: `npm ci` against the
# committed lockfile, then `vite build` with the same VITE_BASE_PATH the Pages
# workflow uses. It also asserts that the post-build step produced
# dist/404.html, because without it every deep link 404s on GitHub Pages.
#
# Usage: bash scripts/verify_frontend.sh [product ...]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ "$#" -gt 0 ]; then
  TARGETS=()
  for arg in "$@"; do
    for d in products/*/; do
      [ "$(basename "$d")" = "$arg" ] && TARGETS+=("$d")
    done
  done
else
  mapfile -t TARGETS < <(find products -maxdepth 1 -mindepth 1 -type d | sort)
fi

pass=0
fail=0
declare -a FAILED

for d in "${TARGETS[@]}"; do
  name="$(basename "$d")"
  fe="$d/frontend"
  if [ ! -f "$fe/package.json" ]; then
    echo "[SKIP] $name — no frontend/package.json"
    continue
  fi

  echo "=== $name ==="

  if [ ! -d "$fe/node_modules" ]; then
    echo "  npm ci ..."
    if ! (cd "$fe" && npm ci --no-audit --no-fund) > "/tmp/${name}-npmci.log" 2>&1; then
      echo "  [FAIL] npm ci failed — see /tmp/${name}-npmci.log"
      tail -12 "/tmp/${name}-npmci.log" | sed 's/^/     /'
      fail=$((fail + 1)); FAILED+=("$name"); continue
    fi
  fi

  # Same base path the Pages deploy workflow sets, so the built asset URLs are
  # the ones that will actually be requested in production.
  #
  # MSYS_NO_PATHCONV matters on Git Bash: without it the shell rewrites the
  # leading-slash value into a Windows path (e.g. /studio-lumen/ becomes
  # D:/Git/studio-lumen/) before handing it to the native node binary, and the
  # build then emits those bogus absolute asset URLs.
  repo_name="$name"
  if ! (cd "$fe" && MSYS_NO_PATHCONV=1 VITE_BASE_PATH="/${repo_name}/" npm run build) > "/tmp/${name}-build.log" 2>&1; then
    echo "  [FAIL] build failed — see /tmp/${name}-build.log"
    tail -18 "/tmp/${name}-build.log" | sed 's/^/     /'
    fail=$((fail + 1)); FAILED+=("$name"); continue
  fi

  if [ ! -f "$fe/dist/404.html" ]; then
    echo "  [FAIL] dist/404.html missing — deep links would 404 on Pages"
    fail=$((fail + 1)); FAILED+=("$name"); continue
  fi

  files=$(find "$fe/dist" -type f | wc -l)
  size=$(du -sh "$fe/dist" 2>/dev/null | cut -f1)
  echo "  [PASS] built $files files ($size), 404.html present"
  grep -oE 'src="[^"]*index-[^"]*\.js"' "$fe/dist/index.html" | head -1 | sed 's/^/     entry /'
  pass=$((pass + 1))
done

echo
echo "======================================================"
echo "FRONTEND BUILDS: $pass passed, $fail failed"
[ "$fail" -gt 0 ] && echo "failed: ${FAILED[*]}"
echo "======================================================"
[ "$fail" -eq 0 ]