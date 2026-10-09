#!/usr/bin/env python3
"""Record the generated Canva logo designs in the product documentation.

Each of the ten logos was generated through the Canva connector and converted
into an editable design, so the colours and geometry can be adjusted in Canva
and re-exported without going back to code.

One deliberate decision: **the shipped `favicon.svg` is not replaced with the
Canva export.** Canva's export formats for these designs are pdf/png/jpg/pptx/
gif/mp4 - there is no SVG. A 16px favicon rasterised from a PNG is visibly
softer than the purpose-drawn vector mark that ships today, and the vector
marks are already verified unique across the catalogue (10 distinct hashes,
minimum pairwise separation 18.36 at 16px). So the Canva designs are recorded
here as the editable marketing source, and the vector mark stays as the
shipped asset. If you want the Canva artwork in the package, export it at
1024px and place it at `frontend/public/brand/canva-mark.png`.

Usage:  python scripts/record_canva_logos.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

# slug -> (canva design id, edit url, view url, design title)
LOGOS = {
    "apex": ("DAHXEt-pa6Y", "https://www.canva.com/d/pKULhF8NY-EPrUQ",
             "https://www.canva.com/d/6cS_ROHPHu0AExZ", "Sleek Modern Chevron Logo"),
    "aurelia-estates": ("DAHXEy8OmBM", "https://www.canva.com/d/9nHcS3y0dGqmXgs",
                        "https://www.canva.com/d/Yg5Em-ihM0gZ_ld",
                        "Precision Logo with Geometric Arched Doorway"),
    "aurum-fitness": ("DAHXE6yPoUQ", "https://www.canva.com/d/cNRAo_w3Mp0qFiM",
                       "https://www.canva.com/d/H3uzNM_0IC3Pj8L",
                       "Bold Barbell Logo with Oval Plates"),
    "claimflow-ai": ("DAHXE5xOU98", "https://www.canva.com/d/89q27pUGFHq6Ho8",
                     "https://www.canva.com/d/0ozlQFbBoBcjTkC",
                     "Pentagonal Gradient Shield Logo with Checkmark"),
    "meridian-capital": ("DAHXE4yWbBM", "https://www.canva.com/d/fX0s4zIrylol9fy",
                         "https://www.canva.com/d/wKSRFgZPEKQ10cc",
                         "Geometric Polygon Globe Logo with Offset Arc"),
    "nuage-events": ("DAHXE5rg6dg", "https://www.canva.com/d/eGJ3APfGFZ7CVS_",
                     "https://www.canva.com/d/9ctBMdd3EYxIGxH",
                     "Cloud Design with Dawn-Like Radiance"),
    "prestige-studio": ("DAHXE6O95MU", "https://www.canva.com/d/nNqCjqQcOXBmRsX",
                        "https://www.canva.com/d/SKl2etW2xps4kQt",
                        "Minimal Vector Logo of Abstract Camera Aperture"),
    "resupro": ("DAHXE0z1FH4", "https://www.canva.com/d/FHzaYmu4eNqn7_K",
                "https://www.canva.com/d/5yJ4MjS4BRZTBr6",
                "Minimalist Logo Design with Document and Career Growth Arrow"),
    "saffron-voyage": ("DAHXE4xkqkA", "https://www.canva.com/d/4XzlOjosZOVapsZ",
                       "https://www.canva.com/d/joIU6byRJruC8BT",
                       "Compass Logo with Lower Left to Upper Right Needle"),
    "studio-lumen": ("DAHXE1DFtZI", "https://www.canva.com/d/Dp3BTpfZqhcVsT1",
                     "https://www.canva.com/d/0QxjB1y66AzEBsJ",
                     "Five-Blade Camera Lens Aperture Logo"),
}

BLOCK = """
## Canva logo source

The mark for this product was generated through Canva and left as an **editable
design**, so colours and geometry can be adjusted and re-exported without
touching code.

| | |
|---|---|
| Canva design | `{title}` |
| Design ID | `{design_id}` |
| Edit | {edit_url} |
| View | {view_url} |

Export supports PNG, JPG, PDF, PPTX, GIF and MP4. **Canva cannot export SVG.**

### Which asset ships

| File | Role |
|---|---|
| `frontend/public/favicon.svg` | The shipped mark. Purpose-drawn vector geometry, so it stays sharp at 16px in a browser tab. |
| `frontend/public/brand/*.svg` | The same geometry at large sizes for the header lockup and Open Graph image. |
| Canva design (above) | Editable source for social cards, pitch decks, print and anything else you export yourself. |

If you want the Canva artwork inside the package, export it at 1024px with a
transparent background and save it as `frontend/public/brand/canva-mark.png`.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = []
    for slug, (design_id, edit_url, view_url, title) in LOGOS.items():
        path = PRODUCTS_DIR / slug / "BRAND_GUIDELINES.md"
        if not path.is_file():
            print(f"  [{slug}] no BRAND_GUIDELINES.md")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        block = BLOCK.format(design_id=design_id, title=title,
                             edit_url=edit_url, view_url=view_url)
        if "## Canva logo source" in text:
            # Replace the existing block rather than appending a second copy.
            head, _, tail = text.partition("## Canva logo source")
            new = head.rstrip("\n") + "\n" + block
            if tail:
                new += ""
        else:
            new = text.rstrip("\n") + "\n" + block
        if new == text:
            continue
        changed.append(slug)
        if not args.dry_run:
            path.write_text(new, encoding="utf-8")
        print(f"  [{slug}] recorded {design_id}")

    verb = "would record" if args.dry_run else "recorded"
    print(f"\n{verb} {len(changed)}/10 products.")
    return 0


if __name__ == "__main__":
    sys.exit(main())