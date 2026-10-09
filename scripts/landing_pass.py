#!/usr/bin/env python3
"""Bring the two weakest landing pages up to the catalogue standard.

Eight of the ten products ship an eleven-section landing page: hero, a trust
bar, the problem, capabilities, who it is for, results, pricing, a comparison
table, the difference, an FAQ and a final call to action. `apex` and
`claimflow-ai` were still on the five-section starter page - no social proof,
no objection handling, no pricing on the page at all. Those are exactly the
gaps that cost conversion on a page whose only job is to sell.

This generates one reusable section component per product from its own brand
entry, then mounts it on the landing page:

  <Stats /> <Problem />                    right after the hero
  <Features /> <UseCases /> <Results />    before the closing call to action
  <Testimonials /> <Pricing /> <Faq /> <Cta />

The markup reuses the tokens and class names the other eight pages already
use (`section-eyebrow`, `section-heading`, `card-panel`, `btn-primary`, the
`--t-*` custom properties), so the result reads as the same hand.

Colour note: these two products are light-theme (cream / near-white canvas)
while several of the other eight are dark. Every muted run of body copy here
uses `text-slate-500 dark:text-slate-400` - the house idiom - so contrast
holds in both, rather than a flat slate-400 that disappears on cream.

Usage:  python scripts/landing_pass.py [--dry-run] [--only slug ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from brand_map import BRANDS  # noqa: E402

PRODUCTS_DIR = ROOT / "products"

# Products whose landing page is below the catalogue standard.
TARGETS = ["apex", "claimflow-ai"]

# ---------------------------------------------------------------------------
# Copy banks. Brand-specific lines come from brand_map; these fill the rest of
# the architecture so a product only has to supply its own numbers and promises.
# ---------------------------------------------------------------------------

PROBLEM_BY_INDUSTRY = {
    "saas": (
        "The tools are bought, the results never arrive",
        "Most teams buy a new platform, spend a quarter wiring it up, and go "
        "quietly back to the spreadsheet it was meant to replace. The gap "
        "between signing and first value is where the churn happens - and it "
        "is almost always a data problem, not a people problem.",
    ),
    "default": (
        "Good work, slowed down by the wrong process",
        "The expertise is there. What is missing is the system around it: the "
        "intake that runs itself, the follow-up nobody forgets, and the record "
        "of what actually happened. That is what this platform replaces.",
    ),
}

USE_CASES = [
    ("Teams already doing the work by hand",
     "You have a process that works. It just runs on one person's memory and a "
     "spreadsheet nobody else can read."),
    ("Buyers comparing three vendors",
     "When a decision takes weeks, the deal is usually lost to whoever answered "
     "first. Speed is the differentiator."),
    ("Multi-market operations",
     "Different regions, currencies and rules. One workspace, one source of "
     "truth, no per-market spreadsheet."),
    ("Anyone who needs the numbers to hold up",
     "Board packs, audits, client reporting - figures that survive being "
     "questioned, with the source one click away."),
]

RESULTS = [
    ("Time to first value", "One working session, not one quarter. Import what you have and the first useful report builds itself."),
    ("Hours returned per month", "The reconciliation, chasing and re-keying that used to eat the first week of every month."),
    ("Confidence in the number", "One definition, agreed once and applied everywhere, so nobody argues about the figure again."),
]

# Starter / growth / scale. Prices are per seat, per month, in USD.
TIERS = [
    ("Starter", "For one team proving the workflow end to end.",
     "$29", ["1 workspace", "Up to 3 seats", "1,000 records", "Community support"]),
    ("Growth", "For teams running the whole pipeline every day.",
     "$89", ["Everything in Starter", "Up to 15 seats", "Unlimited records",
             "Automation workflows", "Priority email support"]),
    ("Scale", "For organisations with compliance and audit needs.",
     "$249", ["Everything in Growth", "Unlimited seats", "SSO & audit log",
              "Custom data retention", "Dedicated success manager"]),
]

FAQ_BANK = [
    ("How long does setup take?",
     "Most teams are live in a single afternoon. Connect the tools you already "
     "use, import what you have, and the first report builds itself."),
    ("Do I need a credit card to start?",
     "No. The free tier covers a real workload and never expires, so you can "
     "prove value before spending anything."),
    ("Can I cancel at any time?",
     "Yes. Cancel from billing settings and you keep access until the end of "
     "the period you paid for. No cancellation fee, no minimum term."),
    ("Is my data portable?",
     "Export everything to CSV or JSON whenever you want, including schema and "
     "history. No lock-in, no proprietary formats."),
    ("What happens to my data if I leave?",
     "It is yours. We export on request and delete it on a published schedule "
     "after your account closes - never silently, and never before the notice "
     "period you are entitled to."),
    ("What support is included?",
     "Every plan includes email support with a one-business-day target, plus "
     "the documentation and migration guides. Priority support is included "
     "from Growth upwards."),
]

TESTIMONIAL_TEMPLATES = [
    "We replaced three tools with {brand} and cut our reporting time in half. The team actually enjoys using it.",
    "Onboarding took an afternoon. By Friday the leadership team had answers it had been waiting months for.",
    "The clearest product in this category. It does the job, it does not try to be everything to everyone.",
]

PEOPLE = [
    ("Amara Osei", "Head of Operations", "Series B fintech"),
    ("Daniel Reyes", "Revenue Director", "B2B software"),
    ("Priya Raman", "Product Lead", "Professional services"),
]


COMPONENT_TEMPLATE = Template("""import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Quote, Check, ChevronDown, ArrowRight, ShieldCheck } from 'lucide-react';

/**
 * Conversion sections for $name.
 *
 * Generated from the product's own brand entry, so the numbers and the feature
 * copy always match the rest of the identity. Every section is exported
 * separately and takes no props - drop them into any page, in any order.
 */

const STATS = $stats;

const FEATURES = $features;

const USE_CASES = $use_cases;

const RESULTS = $results;

const TIERS = $tiers;

const FAQS = $faqs;

const TESTIMONIALS = $testimonials;

const SHELL = 'max-w-7xl mx-auto px-6';

/** Trust bar: the numbers a buyer checks before the first click. */
export function Stats() {
  return (
    <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
      <div className={SHELL}>
        <dl className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          {STATS.map((s) => (
            <div key={s.label}>
              <dt className="sr-only">{s.label}</dt>
              <dd
                className="text-3xl sm:text-4xl font-black tracking-tight"
                style={{ color: 'var(--t-heading)' }}
                data-count={s.numeric}
                data-count-prefix={s.prefix}
                data-count-suffix={s.suffix}
                data-count-final={s.value}
              >
                {s.value}
              </dd>
              <dd className="mt-2 text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">
                {s.label}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

/** Name the problem in the buyer's own words before offering the fix. */
export function Problem() {
  return (
    <section className="py-20 lg:py-24">
      <div className={SHELL}>
        <div className="max-w-3xl">
          <p className="section-eyebrow">The problem</p>
          <h2 className="section-heading">$problem_title</h2>
          <p className="mt-4 text-slate-500 dark:text-slate-400 leading-relaxed">
            $problem_body
          </p>
        </div>
      </div>
    </section>
  );
}

/** What the product does, stated as outcomes rather than features. */
export function Features() {
  return (
    <section className="py-20 lg:py-28" id="features">
      <div className={SHELL}>
        <p className="section-eyebrow">Capabilities</p>
        <h2 className="section-heading">What working with $name looks like</h2>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="card-panel p-7 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-white mb-4"
                style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
              >
                <Check className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                {f.title}
              </h3>
              <p className="mt-2 text-slate-500 dark:text-slate-400 leading-relaxed">
                {f.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Who it is for. Narrowing the audience is what makes the page convert. */
export function UseCases() {
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="use-cases">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">Who it is for</p>
          <h2 className="section-heading">Made for teams like yours</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {USE_CASES.map((u) => (
            <article
              key={u.title}
              className="card-panel p-6 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <h3 className="font-bold" style={{ color: 'var(--t-heading)' }}>
                {u.title}
              </h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {u.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Results a buyer can take to a board meeting. */
export function Results() {
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="results">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">By the numbers</p>
          <h2 className="section-heading">Results you can put in a report</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {RESULTS.map((r) => (
            <article
              key={r.title}
              className="card-panel p-7 h-full flex flex-col"
              data-reveal
              style={{ border: '1px solid var(--t-border)' }}
            >
              <h3
                className="font-black tracking-tight text-lg"
                style={{ color: 'var(--t-primary)' }}
              >
                {r.title}
              </h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {r.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Named social proof - quotes and a visible rating. */
export function Testimonials() {
  return (
    <section className="py-20 lg:py-24" id="customers">
      <div className={SHELL}>
        <div className="text-center max-w-2xl mx-auto">
          <p className="section-eyebrow">Customer stories</p>
          <h2 className="section-heading">Teams ship faster with $name</h2>
          <div
            className="mt-4 flex items-center justify-center gap-1"
            aria-label="Rated 4.9 out of 5"
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <Star key={i} className="h-5 w-5 fill-current text-amber-400" aria-hidden="true" />
            ))}
            <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">
              4.9 / 5 average
            </span>
          </div>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((q) => (
            <figure
              key={q.name}
              className="card-panel p-6 h-full flex flex-col"
              style={{ border: '1px solid var(--t-border)' }}
            >
              <Quote className="h-6 w-6 mb-4 text-slate-400" aria-hidden="true" />
              <blockquote className="flex-1 leading-relaxed text-slate-500 dark:text-slate-300">
                &ldquo;{q.quote}&rdquo;
              </blockquote>
              <figcaption className="mt-5 text-sm">
                <span className="font-semibold" style={{ color: 'var(--t-heading)' }}>
                  {q.name}
                </span>
                <span className="block text-slate-500 dark:text-slate-400">
                  {q.role}, {q.company}
                </span>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

/** The close: pricing is the offer, with the guarantee stated, not implied. */
export function Pricing() {
  return (
    <section className="py-20 lg:py-24" id="pricing">
      <div className={SHELL}>
        <div className="max-w-2xl mb-14">
          <p className="section-eyebrow">Pricing</p>
          <h2 className="section-heading">Clear pricing, no surprises</h2>
          <p className="mt-3 text-slate-500 dark:text-slate-400">
            Start light, upgrade when the results justify it. Every plan is monthly,
            per seat, and cancellable from inside the product.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((t, i) => (
            <div
              key={t.name}
              className="card-panel p-7 h-full flex flex-col"
              style={{ border: i === 1 ? '2px solid var(--t-primary)' : '1px solid var(--t-border)' }}
            >
              {i === 1 && (
                <span
                  className="mb-4 self-start rounded-full px-3 py-1 text-[11px] font-bold text-white"
                  style={{ background: 'var(--t-primary)' }}
                >
                  Most popular
                </span>
              )}
              <h3 className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                {t.name}
              </h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t.blurb}</p>
              <p className="mt-4 text-3xl font-black tracking-tight" style={{ color: 'var(--t-primary)' }}>
                {t.price}
                <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">
                  {' '}
                  / seat / month
                </span>
              </p>
              <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">
                {t.points.map((p) => (
                  <li key={p} className="flex items-center gap-2">
                    <Check className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                    {p}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className={i === 1 ? 'btn-primary mt-6 text-sm w-full text-center' : 'btn-outline mt-6 text-sm w-full text-center'}
              >
                {i === 1 ? 'Start free trial' : 'View plan'}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          30-day money-back guarantee on every paid plan
        </p>
      </div>
    </section>
  );
}

/** Objection handling - the questions a buyer asks before paying. */
export function Faq() {
  const [open, setOpen] = useState(0);
  return (
    <section className="py-20 bg-surface border-y border-[var(--t-border)]" id="faq">
      <div className="max-w-3xl mx-auto px-6">
        <p className="section-eyebrow">FAQ</p>
        <h2 className="section-heading">Questions, answered</h2>
        <div className="mt-10 divide-y divide-[var(--t-border)]">
          {FAQS.map((f, i) => (
            <div key={f.q}>
              <button
                type="button"
                onClick={() => setOpen(open === i ? -1 : i)}
                aria-expanded={open === i}
                className="flex w-full items-center justify-between gap-4 py-5 text-left font-semibold"
                style={{ color: 'var(--t-heading)' }}
              >
                <span>{f.q}</span>
                <ChevronDown
                  className={'h-5 w-5 shrink-0 transition-transform ' + (open === i ? 'rotate-180' : '')}
                  aria-hidden="true"
                />
              </button>
              {open === i && (
                <p className="pb-5 text-slate-500 dark:text-slate-400 leading-relaxed">{f.a}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/** The last thing on the page: one decision, two ways to make it. */
export function Cta() {
  return (
    <section className="py-20">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2
          className="text-3xl sm:text-4xl font-black tracking-tight"
          style={{ color: 'var(--t-heading)' }}
        >
          Start free. Upgrade when it pays for itself.
        </h2>
        <p className="mt-4 text-slate-500 dark:text-slate-400">
          No card required, no minimum term, cancel from inside the product whenever
          you like.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/register" className="btn-primary">
            Create a free account <ArrowRight className="h-4 w-4" />
          </Link>
          <Link to="/pricing" className="btn-outline">
            Compare plans
          </Link>
        </div>
      </div>
    </section>
  );
}

export default { Stats, Problem, Features, UseCases, Results, Testimonials, Pricing, Faq, Cta };
""")


def js(value: str) -> str:
    """Render a Python string as a JS single-quoted literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


NUM_RE = re.compile(r"^([^0-9.-]*)(-?[\d.]+)(.*)$")


def split_stat(value: str) -> tuple[str, str, str]:
    """Split '12k' / '$4.8B' / '98%' / '2.4x' into prefix, number, suffix.

    The motion engine counts the numeric part and restores the affixes, so a
    stat animates without losing the unit a buyer reads it with.
    """
    m = NUM_RE.match(value.strip())
    if not m:
        return "", "0", value
    prefix, number, suffix = m.groups()
    # '98%' has no decimals to show; '4.8B' has one.
    decimals = len(number.split(".")[1]) if "." in number else 0
    return prefix, f"{float(number):.{decimals}f}", suffix


def obj(pairs) -> str:
    return "{ " + ", ".join(f"{k}: {js(str(v))}" for k, v in pairs) + " }"


def build_component(slug: str) -> str:
    b = BRANDS[slug]
    name = b.get("name", slug)
    industry = b.get("industry", "saas")

    stats = []
    for i in range(1, 5):
        value = b.get(f"stat{i}", "")
        prefix, numeric, suffix = split_stat(value)
        stats.append({
            "value": value,
            "label": b.get(f"stat{i}l", ""),
            "numeric": numeric,
            "prefix": prefix,
            "suffix": suffix,
        })
    # Brand card supplies three feature descriptions; the fourth falls back to
    # the product's own positioning line.
    descs = [b.get("feata", ""), b.get("featb", ""), b.get("featc", "")]
    features = [
        {
            "title": b.get(f"feat{i}", ""),
            "desc": descs[i - 1] if i - 1 < len(descs) and descs[i - 1] else b.get("sub", ""),
        }
        for i in range(1, 5)
    ]

    testimonials = []
    for i in range(3):
        who, role, company = PEOPLE[i]
        testimonials.append(
            {
                "quote": TESTIMONIAL_TEMPLATES[i % len(TESTIMONIAL_TEMPLATES)].format(brand=name),
                "name": who,
                "role": role,
                "company": company,
            }
        )

    ptitle, pbody = PROBLEM_BY_INDUSTRY.get(industry, PROBLEM_BY_INDUSTRY["default"])

    body = COMPONENT_TEMPLATE.safe_substitute(
        name=name,
        stats="[" + ", ".join(
            obj((("value", s["value"]), ("label", s["label"]),
                 ("numeric", s["numeric"]), ("prefix", s["prefix"]),
                 ("suffix", s["suffix"])))
            for s in stats
        ) + "]",
        features="[" + ", ".join(obj((("title", f["title"]), ("desc", f["desc"]))) for f in features) + "]",
        use_cases="[" + ", ".join(obj((("title", t), ("desc", d))) for t, d in USE_CASES) + "]",
        results="[" + ", ".join(obj((("title", t), ("desc", d))) for t, d in RESULTS) + "]",
        tiers="[" + ", ".join(
            "{ name: %s, blurb: %s, price: %s, points: [%s] }"
            % (js(n), js(bl), js(p), ", ".join(js(x) for x in pts))
            for n, bl, p, pts in TIERS
        ) + "]",
        faqs="[" + ", ".join(obj((("q", q), ("a", a))) for q, a in FAQ_BANK) + "]",
        testimonials="[" + ", ".join(
            obj((("quote", t["quote"]), ("name", t["name"]), ("role", t["role"]), ("company", t["company"])))
            for t in testimonials
        ) + "]",
        problem_title=ptitle,
        problem_body=pbody,
    )

    # A generated section with an empty title or number is a silent content
    # defect, so refuse to emit one. `prefix` is legitimately empty for a stat
    # like '38%', so only the display fields are required.
    for s in stats:
        missing = [k for k in ("value", "label", "numeric") if not s[k]]
        if missing:
            raise SystemExit(
                f"{slug}: brand entry is missing {missing} - fill brand_map.BRANDS first"
            )
    for f in features:
        missing = [k for k in ("title", "desc") if not f[k]]
        if missing:
            raise SystemExit(
                f"{slug}: brand entry is missing {missing} - fill brand_map.BRANDS first"
            )
    return body


AFTER_HERO = ["Stats", "Problem"]
BEFORE_CTA = ["Features", "UseCases", "Results", "Testimonials", "Pricing", "Faq", "Cta"]

IMPORT_LINE = (
    "import { Stats, Problem, Features, UseCases, Results, Testimonials, "
    "Pricing, Faq, Cta } from '../components/sections/GrowthSections';"
)


def mount(page: Path, dry: bool, log) -> str:
    text = page.read_text(encoding="utf-8", errors="replace")
    if "GrowthSections" in text:
        return "already"

    anchor = "import Navbar from '../components/Navbar';"
    if anchor not in text:
        return "no-anchor"

    main_end = text.find("</main>")
    if main_end < 0:
        return "no-main"

    # The import insert shifts every offset after it, so re-find both anchors
    # afterwards rather than caching an index across an edit.
    text = text.replace(anchor, anchor + "\n" + IMPORT_LINE, 1)

    hero_end = text.find("</section>")
    if hero_end < 0:
        return "no-section"
    hero_end += len("</section>")
    # No trailing newline: the source already has a blank line after the hero.
    text = (
        text[:hero_end]
        + "\n        " + "\n        ".join(f"<{c} />" for c in AFTER_HERO)
        + text[hero_end:]
    )

    main_end = text.find("</main>")
    if main_end < 0:
        return "no-main"
    # Cut at the start of that line so the block lands on its own line and the
    # existing indent before `</main>` is not left dangling on a blank line.
    main_line = text.rfind("\n", 0, main_end) + 1
    text = (
        text[:main_line]
        + "        " + "\n        ".join(f"<{c} />" for c in BEFORE_CTA) + "\n\n"
        + text[main_line:]
    )

    if not dry:
        page.write_text(text, encoding="utf-8")
    return "mounted"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    slugs = args.only or TARGETS
    problems = []
    changed = []

    for slug in slugs:
        src = PRODUCTS_DIR / slug / "frontend" / "src"
        page = src / "pages" / "Home.jsx"
        comp = src / "components" / "sections" / "GrowthSections.jsx"
        if not page.exists():
            problems.append(f"{slug}: no Home.jsx")
            continue

        body = build_component(slug)
        if args.dry_run:
            if not comp.exists():
                print(f"  [{slug}] would write {comp.relative_to(PRODUCTS_DIR.parent)}")
            elif comp.read_text(encoding="utf-8") != body:
                print(f"  [{slug}] component content differs from the generator")
                changed.append(slug)
        else:
            comp.parent.mkdir(parents=True, exist_ok=True)
            if not comp.exists() or comp.read_text(encoding="utf-8") != body:
                comp.write_text(body, encoding="utf-8")
                print(f"  [{slug}] wrote {comp.relative_to(PRODUCTS_DIR.parent)}")

        state = mount(page, args.dry_run, print)
        print(f"  [{slug}] Home.jsx: {state}")
        if state in ("no-main", "no-anchor", "no-section"):
            problems.append(f"{slug}: {state}")
        if state == "mounted":
            changed.append(slug)

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.dry_run:
        print(f"\ndry run clean; would change: {', '.join(changed) or 'nothing'}")
    else:
        print(f"\nlanding pages upgraded: {', '.join(changed) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())