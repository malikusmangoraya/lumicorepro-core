#!/usr/bin/env python3
"""Repair generation defects found in the shipped product source.

Two classes of defect, both invisible to the content audit but obvious to any
buyer who opens the source:

1. Reasoning leak - a couple of generated components were written with the
   generator's own "<think> ... </think>" scratchpad in front of the code. The
   scratchpad is stripped from every shipped source file.

2. Truncation - the same two files were cut off mid-statement, leaving
   unparseable JavaScript. Their remaining markup is completed here and the
   import lists are trimmed to what is actually used.

The resupro hero also shipped ecommerce copy ("dream store", "Curated Product
Showcase") inside a resume product; its copy is corrected to the brand.

Usage:  python scripts/repair_generated_defects.py [--dry-run]
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

SOURCE_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs"}

# Brand copy corrections for the resupro hero (source of an off-brand component).
RESUPRO_COPY = [
    ("Build your", "Your next role is"),
    ("dream store", "one resume away"),
    ("in minutes", "before you apply"),
    ("The all-in-one ecommerce platform that turns your vision into a\n              high-converting storefront. No code required.",
     "ResuPro writes resumes that pass applicant tracking systems, then\n              coaches you through the interviews that follow."),
    ("Start Building Free", "Build My Resume"),
    ("New Collection Live", "ATS Scoring Live"),
    ("2.4x Conversion", "92% Match Score"),
    ("Curated Product Showcase", "Resume, tailored to the role"),
    ("AI-powered layout suggestions that maximize your revenue\n                      per visitor.",
     "Every line rewritten against the job description you are targeting."),
    ("Modern ecommerce storefront displaying curated product collection",
     "Tailored resume preview scored against a job description"),
    ("Monthly Revenue", "Interviews Won"),
]

AURELIA_TAIL = '''                    <h3 className="font-semibold text-lg text-foreground leading-snug line-clamp-2">
                      {product.name}
                    </h3>
                    {product.price ? (
                      <span className="shrink-0 text-sm font-semibold text-primary">
                        {formatPrice(product.price)}
                      </span>
                    ) : null}
                  </div>

                  {product.location && (
                    <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4 shrink-0" aria-hidden="true" />
                      <span className="truncate">{product.location}</span>
                    </p>
                  )}

                  {product.specs && (
                    <ul className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                      {product.specs.beds != null && (
                        <li className="flex items-center gap-1.5">
                          <BedDouble className="w-4 h-4" aria-hidden="true" />
                          {product.specs.beds} {product.specs.beds === 1 ? 'bed' : 'beds'}
                        </li>
                      )}
                      {product.specs.baths != null && (
                        <li className="flex items-center gap-1.5">
                          <Bath className="w-4 h-4" aria-hidden="true" />
                          {product.specs.baths} {product.specs.baths === 1 ? 'bath' : 'baths'}
                        </li>
                      )}
                      {product.specs.area && (
                        <li className="flex items-center gap-1.5">
                          <Square className="w-4 h-4" aria-hidden="true" />
                          {product.specs.area}
                        </li>
                      )}
                    </ul>
                  )}

                  {product.rating ? (
                    <div className="mt-3">
                      <RatingStars
                        rating={product.rating}
                        size="sm"
                        showValue
                        reviewCount={product.reviewCount}
                      />
                    </div>
                  ) : null}
                </div>

                <div className="flex items-center gap-2 px-5 pb-5">
                  <Button
                    variant="primary"
                    className="flex-1"
                    onClick={() => handleView(product)}
                  >
                    <Eye className="mr-2 h-4 w-4" aria-hidden="true" />
                    View residence
                  </Button>
                  {onAddToCart && (
                    <Button
                      variant="outline"
                      onClick={() => onAddToCart(product)}
                      aria-label={`Enquire about ${product.name}`}
                    >
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  )}
                </div>
              </Card>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
'''

RESUPRO_TAIL = '''                    <div className="mt-4 flex items-baseline gap-2">
                      <AnimatedNumber
                        value={248}
                        suffix="k"
                        className="text-4xl font-bold text-foreground"
                      />
                      <span className="text-sm text-muted-foreground">this month</span>
                    </div>
                  </div>
                </div>
              </Card>
            </Reveal>

            {/* Match score */}
            <Reveal delay={200} direction="up">
              <Card
                className="h-full min-h-[200px] rounded-2xl p-6 hover:-translate-y-1 transition-all duration-200"
                hoverable
                onMouseEnter={() => handleCardHover('score')}
                onMouseLeave={handleCardLeave}
              >
                <div className="flex h-full flex-col justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Zap className="w-4 h-4 text-primary" aria-hidden="true" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground">
                      Match Score
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <AnimatedNumber
                      value={92}
                      suffix="%"
                      className="text-4xl font-bold text-foreground"
                    />
                    <span className="text-sm text-muted-foreground">average</span>
                  </div>
                </div>
              </Card>
            </Reveal>

            {/* Privacy */}
            <Reveal delay={300} direction="up">
              <Card className="h-full min-h-[200px] rounded-2xl p-6" hoverable>
                <div className="flex h-full flex-col justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Shield className="w-4 h-4 text-primary" aria-hidden="true" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground">
                      Privacy First
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Your documents stay yours. Nothing is shared with employers
                    or third parties.
                  </p>
                </div>
              </Card>
            </Reveal>
          </BentoGrid>
        </StaggerGroup>
      </div>
    </section>
  );
}
'''

TRUNCATED_LINE = '<h3 className="font-semibold text-lg text-foreground leading-snug\n'
RESUPRO_CUT = "                    <\n"


# Instructions that tell a buyer to paste a literal placeholder value. Copying
# these puts a well-known credential into production, so each is replaced with
# the command that actually generates a strong value.
JWT_GENERATE = (
    "railway variables set JWT_SECRET='"
    "<node -e \"console.log(require('crypto').randomBytes(48).toString('hex'))\">'"
)

SECRET_WORDING_FIXES = [
    ("railway variables set JWT_SECRET='your_secret'", JWT_GENERATE),
    ("INTERNAL_WEBHOOK_SECRET=your_secret",
     "INTERNAL_WEBHOOK_SECRET=<generate with: openssl rand -hex 32>"),
    ("Add your API key here to activate this feature",
     "Add the provider API key here to activate this feature"),
]

DOC_SUFFIXES = {".md", ".example"}


def fix_secret_wording(root: Path, touched, dry: bool) -> int:
    """Replace literal placeholder values in shipped instructions and templates."""
    n = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in DOC_SUFFIXES:
            continue
        if "node_modules" in path.parts or path.name == "CHANGELOG.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        new = text
        for old, replacement in SECRET_WORDING_FIXES:
            new = new.replace(old, replacement)
        if new != text:
            n += 1
            touched.append((path, "placeholder value replaced with a generation command"))
            if not dry:
                path.write_text(new, encoding="utf-8")
    return n


def strip_reasoning(text: str) -> str:
    """Remove a leading generator scratchpad, if present."""
    m = re.search(r"^\s*<think>.*?</think>\s*", text, re.S)
    if not m:
        return text
    return text[m.end():]


def trim_imports(text: str, unused: list) -> str:
    """Drop named imports that the finished component no longer uses."""
    for name in unused:
        text = re.sub(rf"^\s*{re.escape(name)},\n", "", text, flags=re.M)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    touched = []
    for slug_dir in sorted(p for p in PRODUCTS_DIR.iterdir() if p.is_dir()):
        fix_secret_wording(slug_dir, touched, args.dry_run)

    # --- 1. reasoning leak, everywhere in shipped source --------------------
    for path in sorted(PRODUCTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<think>" not in text:
            continue
        cleaned = strip_reasoning(text)
        if cleaned != text:
            touched.append((path, "reasoning stripped"))
            if not args.dry_run:
                path.write_text(cleaned, encoding="utf-8")

    # --- 2. complete the truncated components --------------------------------
    aurelia = PRODUCTS_DIR / "aurelia-estates/frontend/src/components/atoms/ProductGrid.jsx"
    if aurelia.exists():
        text = strip_reasoning(aurelia.read_text(encoding="utf-8", errors="replace"))
        if text.rstrip().endswith(TRUNCATED_LINE.rstrip()):
            text = text[: text.rindex(TRUNCATED_LINE.rstrip())] + AURELIA_TAIL
            text = trim_imports(text, ["Filter", "IconWrapper", "Grid"])
            touched.append((aurelia, "component completed"))
            if not args.dry_run:
                aurelia.write_text(text, encoding="utf-8")

    resupro = PRODUCTS_DIR / "resupro/frontend/src/components/atoms/HeroSection.jsx"
    if resupro.exists():
        text = strip_reasoning(resupro.read_text(encoding="utf-8", errors="replace"))
        if text.rstrip().endswith(RESUPRO_CUT.rstrip()):
            text = text[: text.rindex(RESUPRO_CUT.rstrip())] + RESUPRO_TAIL
            text = trim_imports(text, ["Sparkles", "ShoppingBag", "Star", "Package",
                                       "Truck", "CreditCard", "ChevronRight",
                                       "BorderBeam", "TiltCard", "TextMorph"])
            for old, new in RESUPRO_COPY:
                text = text.replace(old, new)
            touched.append((resupro, "component completed + copy corrected"))
            if not args.dry_run:
                resupro.write_text(text, encoding="utf-8")

    for path, what in touched:
        print(f"{path.relative_to(ROOT).as_posix()}: {what}")
    print(f"\n{len(touched)} file(s) {'would be ' if args.dry_run else ''}repaired")


if __name__ == "__main__":
    main()