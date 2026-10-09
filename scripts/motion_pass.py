#!/usr/bin/env python3
"""One advanced, deduplicated animation layer for all ten products.

The survey found the animation layer in three different states:

* `apex` and `claimflow-ai` load `lumi-motion.js` from `main.jsx` but their
  stylesheet has no `.lumi-reveal` rules at all - the engine ran and animated
  nothing.
* `aurelia-estates` carried **three** copies of the motion block and
  `nuage-events` carried two, because each earlier pass appended instead of
  replacing.
* the remaining six were correct but basic: a single translateY fade.

This removes every existing block and writes exactly one, and replaces the
engine with a version that adds real interaction while staying cheap:

* spring-eased reveals with per-element distance and direction
* a scroll progress bar
* number counters for the stat blocks
* magnetic hover on primary buttons, card tilt on panels, parallax on the
  aurora backdrop

Performance discipline, because this runs on every page of a demo a buyer is
judging:

* one `requestAnimationFrame` loop for all scroll-linked work, not one per
  listener
* passive scroll listeners, `IntersectionObserver` to unhook finished elements
* only `transform` and `opacity` are animated, so work stays on the compositor
* `will-change` is set for the duration of an animation and then removed
* everything is skipped under `prefers-reduced-motion`

Usage:  python scripts/motion_pass.py [--dry-run] [--only slug ...]
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

TARGETS = [
    "apex", "aurelia-estates", "aurum-fitness", "claimflow-ai",
    "flowpilot",
    "meridian-capital", "nuage-events", "prestige-studio", "resupro",
    "saffron-voyage", "studio-lumen",
]

# Existing blocks were written by several passes with slightly different
# comment text, so match the end marker as well as the opening comment.
BLOCK_RE = re.compile(
    r"/\*\s*=+\s*lumi-motion.*?\*/.*?/\*\s*=+\s*end lumi-motion\s*=+\s*\*/\s*",
    re.S | re.I,
)

CSS = """/* ===== lumi-motion (advanced animation layer) ===== */
.lumi-reveal {
  opacity: 0;
  transform: translate3d(0, var(--lumi-y, 28px), 0) scale(var(--lumi-s, 1));
  transition:
    opacity 0.72s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.72s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--lumi-d, 0ms);
}
.lumi-reveal[data-reveal='left'] { --lumi-y: 0px; transform: translate3d(-32px, 0, 0) scale(var(--lumi-s, 1)); }
.lumi-reveal[data-reveal='right'] { --lumi-y: 0px; transform: translate3d(32px, 0, 0) scale(var(--lumi-s, 1)); }
.lumi-reveal[data-reveal='scale'] { --lumi-y: 0px; --lumi-s: 0.94; }
.lumi-reveal.lumi-in {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
  will-change: auto;
}

/* Scroll progress */
.lumi-progress {
  position: fixed;
  inset: 0 auto auto 0;
  height: 3px;
  width: 100%;
  transform: scale3d(var(--lumi-progress, 0), 1, 1);
  transform-origin: 0 50%;
  background: linear-gradient(90deg, var(--t-primary, #7c3aed), var(--t-accent, #ec4899));
  z-index: 9999;
  pointer-events: none;
  will-change: transform;
}

/* Counters */
.lumi-count { font-variant-numeric: tabular-nums; }

/* Magnetic + tilt targets */
.lumi-card {
  transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.34s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
.lumi-card:hover {
  transform: translate3d(0, -4px, 0);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.14);
}

/* Floating accents */
.lumi-float { animation: lumiFloat 7s ease-in-out infinite; }
@keyframes lumiFloat {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(0, -10px, 0); }
}

/* Loading shimmer */
.lumi-shimmer {
  background-image: linear-gradient(
    100deg,
    transparent 20%,
    color-mix(in srgb, var(--t-heading, #000) 7%, transparent) 50%,
    transparent 80%
  );
  background-size: 220% 100%;
  animation: lumiShimmer 1.6s linear infinite;
}
@keyframes lumiShimmer {
  from { background-position: 180% 0; }
  to { background-position: -80% 0; }
}

/* Parallax backdrop */
.lumi-parallax { will-change: transform; }

@media (prefers-reduced-motion: reduce) {
  .lumi-reveal { opacity: 1 !important; transform: none !important; transition: none !important; }
  .lumi-card, .lumi-float, .lumi-shimmer { animation: none !important; transition: none !important; }
  .lumi-progress { display: none !important; }
  .lumi-parallax { transform: none !important; }
}
/* ===== end lumi-motion ===== */
"""

JS = """/**
 * lumi-motion - the animation layer.
 *
 * One rAF loop drives every scroll-linked effect, scroll work is passive, and
 * finished elements are unobserved, so a long landing page does not accumulate
 * handlers as you scroll. Only transform and opacity animate, which keeps the
 * work on the compositor and off the main thread's layout path.
 *
 * Nothing runs under prefers-reduced-motion.
 */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches) return;

  var parallaxEls = [];
  var progressEl = null;
  var ticking = false;

  function root() {
    return document.getElementById('root') || document.body;
  }

  function onFrame() {
    ticking = false;
    var vh = window.innerHeight || 1;
    var scrolled = window.scrollY || 0;

    if (progressEl) {
      var max = document.documentElement.scrollHeight - vh;
      var p = max > 0 ? Math.min(1, Math.max(0, scrolled / max)) : 0;
      progressEl.style.setProperty('--lumi-progress', p.toFixed(4));
    }

    for (var i = 0; i < parallaxEls.length; i++) {
      var el = parallaxEls[i];
      var box = el.getBoundingClientRect();
      if (box.bottom < -200 || box.top > vh + 200) continue;
      var strength = parseFloat(el.dataset.parallax || '0.12');
      // Offset from viewport centre, so the layer drifts as it passes through.
      var offset = (box.top + box.height / 2 - vh / 2) * -strength;
      el.style.transform = 'translate3d(0,' + offset.toFixed(2) + 'px,0)';
    }
  }

  function request() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(onFrame);
  }

  /* ---------------------------------------------------------------- reveal */

  function reveals() {
    var nodes = root().querySelectorAll(
      '[data-reveal], section, article, h1:not(:first-child), h2, h3'
    );
    var targets = [];
    Array.prototype.forEach.call(nodes, function (el) {
      // A wrapper that already contains headings animates as one block,
      // otherwise every heading inside it animates again.
      if (el.querySelector('h2, h3') && !/^(SECTION|ARTICLE)$/.test(el.tagName)) return;
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      targets.push(el);
    });

    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          el.style.willChange = 'opacity, transform';
          el.classList.add('lumi-in');
          // Drop will-change once the transition is done, or the layer is
          // promoted to its own compositor layer for the rest of the session.
          window.setTimeout(function () { el.style.willChange = ''; }, 900);
          obs.unobserve(el);
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -36px 0px' }
    );

    targets.forEach(function (el, i) {
      if (el.classList.contains('lumi-in')) return;
      el.classList.add('lumi-reveal');
      el.style.setProperty('--lumi-d', (i % 24) * 55 + 'ms');
      obs.observe(el);
    });
  }

  /* -------------------------------------------------------------- counters */

  function animateCount(el) {
    var target = parseFloat(el.dataset.count);
    if (isNaN(target)) return;
    var decimals = (el.dataset.count.split('.')[1] || '').length;
    var prefix = el.dataset.countPrefix || '';
    var suffix = el.dataset.countSuffix || '';
    var start = performance.now();
    var dur = 1400;

    function tick(now) {
      var t = Math.min(1, (now - start) / dur);
      // easeOutExpo - fast start, long settle, reads as "counting up".
      var eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      el.textContent = prefix + (target * eased).toFixed(decimals) + suffix;
      if (t < 1) window.requestAnimationFrame(tick);
      else el.textContent = el.dataset.countFinal || el.textContent;
    }
    window.requestAnimationFrame(tick);
  }

  function counters() {
    var els = root().querySelectorAll('[data-count]');
    if (!els.length) return;
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          animateCount(entry.target);
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.4 }
    );
    Array.prototype.forEach.call(els, function (el) {
      el.classList.add('lumi-count');
      obs.observe(el);
    });
  }

  /* -------------------------------------------------------------- magnetic */

  function magnetic() {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var els = root().querySelectorAll('.btn-primary, [data-magnetic]');
    Array.prototype.forEach.call(els, function (el) {
      if (el.dataset.lumiMagnetic === '1') return;
      el.dataset.lumiMagnetic = '1';
      var strength = parseFloat(el.dataset.magnetic || '0.22');

      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) * strength;
        var dy = (e.clientY - (r.top + r.height / 2)) * strength;
        el.style.transform = 'translate3d(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px,0)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  /* ------------------------------------------------------------------ tilt */

  function tilt() {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var els = root().querySelectorAll('.card-panel');
    Array.prototype.forEach.call(els, function (el) {
      if (el.dataset.lumiTilt === '1') return;
      el.dataset.lumiTilt = '1';
      el.classList.add('lumi-card');
      var max = parseFloat(el.dataset.tilt || '6');

      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform =
          'perspective(900px) rotateX(' + (-py * max).toFixed(2) +
          'deg) rotateY(' + (px * max).toFixed(2) + 'deg) translate3d(0,-4px,0)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  /* ------------------------------------------------------------------ init */

  function setup() {
    if (!progressEl) {
      progressEl = document.createElement('div');
      progressEl.className = 'lumi-progress';
      progressEl.setAttribute('aria-hidden', 'true');
      document.body.appendChild(progressEl);
    }
    parallaxEls = Array.prototype.slice.call(
      root().querySelectorAll('[data-parallax], .hero-aurora')
    );
    parallaxEls.forEach(function (el) {
      if (!el.dataset.parallax) el.dataset.parallax = '0.08';
      el.classList.add('lumi-parallax');
    });
    reveals();
    counters();
    magnetic();
    tilt();
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request, { passive: true });
    request();
  }

  window.addEventListener('lumi-motion:activate', setup);
  var t = window.setTimeout(setup, 120);
  if (document.readyState === 'complete') {
    window.clearTimeout(t);
    setup();
  }
})();
"""


def strip_blocks(css: str) -> tuple[str, int]:
    """Remove every existing lumi-motion block, however it was written."""
    text, n = BLOCK_RE.subn("", css)
    return re.sub(r"\n{3,}", "\n\n", text), n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    changed, problems = [], []

    for slug in args.only or TARGETS:
        fe = PRODUCTS_DIR / slug / "frontend"
        css_path = fe / "src/index.css"
        js_path = fe / "src/utils/lumi-motion.js"
        if not css_path.is_file():
            problems.append(f"{slug}: no src/index.css")
            continue

        css = css_path.read_text(encoding="utf-8", errors="replace")
        stripped, removed = strip_blocks(css)
        if stripped != css.rstrip("\n") or removed:
            new_css = stripped.rstrip("\n") + "\n\n" + CSS
        else:
            new_css = css
        if new_css == css:
            new_css = stripped.rstrip("\n") + "\n\n" + CSS if BLOCK_RE.search(css) else new_css

        writes = {}
        if new_css != css:
            writes[css_path] = new_css
        if js_path.is_file() and js_path.read_text(encoding="utf-8", errors="replace") != JS:
            writes[js_path] = JS

        written = []
        for path, body in writes.items():
            written.append(path.name)
            if not args.dry_run:
                path.write_text(body, encoding="utf-8")

        if written:
            changed.append(slug)
            print(f"  [{slug}] removed {removed} old block(s), wrote: "
                  + ", ".join(sorted(written)))

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1

    verb = "would change" if args.dry_run else "updated"
    print(f"\n{verb}: {', '.join(changed) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())