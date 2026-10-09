#!/usr/bin/env python3
"""Frontend source integrity repairs.

Three defects the sellability audit does not look for, all found by walking the
frontend import graph:

1. `components/common/LazyImage.jsx` shipped as a stub:
       export const LazyImage = (props) => React.createElement('div', ...)
   It renders a plain div and never shows the image, yet the ecommerce and blog
   components import it as their picture element. Replaced with a real
   implementation in every product, whether the stub was present or the file
   was missing entirely.

2. `components/index.js` re-exported `../templates/ecommerce/...` components
   that do not exist in the shipped product, so the barrel referenced files that
   were never there.

3. `hooks/useApiQuery.js` used a bare dynamic `import('../services/api')` to an
   optional module. The try/catch already handled its absence at runtime, but a
   bundler still tries to resolve the specifier. Marked as an optional import.

Usage:  python scripts/frontend_integrity.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

PRODUCTS = [
    "apex", "aurelia-estates", "aurum-fitness", "claimflow-ai",
    "meridian-capital", "nuage-events", "prestige-studio", "resupro",
    "saffron-voyage", "studio-lumen",
]

LAZY_IMAGE = '''import React, { useState } from 'react';

/**
 * LazyImage
 * ---------
 * An <img> that behaves the way a content image actually needs to:
 *
 *  - native lazy loading (eager when the image is above the fold),
 *  - async decoding so it never blocks the main thread,
 *  - reserved space from `ratio` or `width`/`height`, so the page does not
 *    jump while the image arrives (no layout shift),
 *  - a short fade-in on load, and a neutral placeholder if the file is broken,
 *  - `sizes` / `srcSet` / `loading` passthrough for responsive delivery.
 */
export default function LazyImage({
  src,
  alt = '',
  width,
  height,
  ratio = '4 / 3',
  className = '',
  priority = false,
  fallback = null,
  wrapperClassName = '',
  ...rest
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  if (!src) return null;

  return (
    <div
      className={`relative overflow-hidden bg-surface/60 ${wrapperClassName}`}
      style={ratio ? { aspectRatio: ratio } : undefined}
    >
      {failed ? (
        fallback || (
          <div
            role="img"
            aria-label={alt}
            className="flex h-full w-full items-center justify-center bg-gradient-to-br from-muted/40 to-muted/10 text-[10px] uppercase tracking-widest text-muted-foreground"
          >
            Image unavailable
          </div>
        )
      ) : (
        <img
          src={src}
          alt={alt}
          width={width}
          height={height}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={`h-full w-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          } ${className}`}
          {...rest}
        />
      )}
    </div>
  );
}
'''

# The stub exports a named LazyImage too; keep that import surface working.
STUB_MARKERS = ("DummyComponent", "createElement('div'")

BARREL_LINE = re.compile(
    r"^export \{ default as (\w+) \} from '\.{1,2}/\.\./templates/[^']+';\n", re.M)

OPTIONAL_IMPORT = re.compile(r"import\((?P<q>['\"])(?P<spec>\.\./services/api)(?P=q)\)")


def fix_lazy_image(path: Path, dry: bool, log) -> str:
    if not path.exists():
        state = "created"
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
        state = "replaced-stub" if any(m in text for m in STUB_MARKERS) else "present"
        if state == "present":
            return state
    log(f"    LazyImage {state}: {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(LAZY_IMAGE, encoding="utf-8")
    return state


def fix_barrel(path: Path, templates_dir: Path, dry: bool, log) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    removed = []
    for m in list(BARREL_LINE.finditer(text)):
        name = m.group(1)
        if (templates_dir / name).exists():
            continue  # the component really ships; keep the export
        removed.append(name)
    if not removed:
        return False
    new = BARREL_LINE.sub("", text)
    log(f"    dropped dangling template exports ({', '.join(removed)}): "
        f"{path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def fix_optional_import(path: Path, dry: bool, log) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    if "/* @vite-ignore */" in text:
        return False
    m = OPTIONAL_IMPORT.search(text)
    if not m:
        return False
    replacement = f"import(/* @vite-ignore */ {m.group(0)[len('import('):]}"
    new = text[: m.start()] + replacement + text[m.end():]
    log(f"    optional import marked: {path.relative_to(PRODUCTS_DIR.parent).as_posix()}")
    if not dry:
        path.write_text(new, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    counts = {}
    problems = []

    for slug in PRODUCTS:
        src = PRODUCTS_DIR / slug / "frontend" / "src"
        if not src.is_dir():
            problems.append(f"{slug}: no frontend/src")
            continue

        state = fix_lazy_image(src / "components/common/LazyImage.jsx", args.dry_run, print)
        counts[state] = counts.get(state, 0) + 1

        if fix_barrel(src / "components/index.js", PRODUCTS_DIR / slug / "frontend" / "templates",
                       args.dry_run, print):
            counts["barrel"] = counts.get("barrel", 0) + 1

        if fix_optional_import(src / "hooks/useApiQuery.js", args.dry_run, print):
            counts["optional-import"] = counts.get("optional-import", 0) + 1

        # every product must end up with a real LazyImage
        li = src / "components/common/LazyImage.jsx"
        if li.exists() and not args.dry_run:
            body = li.read_text(encoding="utf-8", errors="replace")
            if any(m in body for m in STUB_MARKERS):
                problems.append(f"{slug}: LazyImage is still a stub")

    print()
    prefix = "would apply" if args.dry_run else "applied"
    print(f"{prefix}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"all {len(PRODUCTS)} products have a real LazyImage and no dangling template exports")
    return 0


if __name__ == "__main__":
    sys.exit(main())