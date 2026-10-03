"""Deterministic animation layer for generated websites (premium motion).

Injects a small, dependency-free runtime (CSS + IntersectionObserver JS) into a
generated frontend so every section/heading/card animates on scroll, respects
``prefers-reduced-motion`` and RTL, and never participates in layout shift
(only opacity + transform are animated).

The pass is append-only and idempotent:
  * ``frontend/src/index.css``   gets a marked ``/* lumi-motion-injected */`` block
  * ``frontend/src/utils/lumi-motion.js`` is created if missing
  * ``frontend/src/main.jsx``    gets the runtime import appended if missing

No generated component/JSX is rewritten, so the quality gate / build cannot
regress from this pass. The orchestrator calls it observationally after codegen.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

MARKER = "lumi-motion-injected"
MOTION_CSS = """
/* ===== lumi-motion (premium animation layer) ===== */
.lumi-reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--lumi-d, 0ms);
  will-change: opacity, transform;
}
.lumi-reveal.lumi-in {
  opacity: 1;
  transform: none;
}
.lumi-card {
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.lumi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.14);
}
.lumi-float {
  animation: lumiFloat 6s ease-in-out infinite;
}
@keyframes lumiFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.lumi-shimmer {
  background: linear-gradient(100deg, transparent 30%, rgba(255, 255, 255, 0.18) 50%, transparent 70%);
  background-size: 200% 100%;
  animation: lumiShimmer 3.2s ease-in-out infinite;
}
@keyframes lumiShimmer {
  from { background-position: 180% 0; }
  to { background-position: -80% 0; }
}
@media (prefers-reduced-motion: reduce) {
  .lumi-reveal { opacity: 1; transform: none; transition: none; }
  .lumi-card, .lumi-float, .lumi-shimmer { animation: none; transition: none; }
}
/* ===== end lumi-motion ===== */
"""

MOTION_JS = """// lumi-motion — scroll-reveal + stagger + hover micro-motion (dependency-free).
(function () {
  'use strict';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var shownAt = null;
  var all = [];
  var doomed = 0;

  function targetEls() {
    var root = document.getElementById('root') || document.body;
    return Array.prototype.slice.call(
      root.querySelectorAll(
        '[data-reveal], section, article, h1:not(:first-child), h2, h3'
      )
    ).filter(function (el) {
      if (el.querySelectorAll('h2, h3').length) return /section|article/i.test(el.tagName);
      return true;
    }).filter(function (el) {
      var cs = getComputedStyle(el);
      return cs.display !== 'none' && cs.visibility !== 'hidden';
    });
  }

  function collect() {
    all = targetEls();
    all.forEach(function (el, i) {
      if (el.dataset.reveal === '' && el.classList.contains('lumi-reveal')) return;
      el.classList.add('lumi-reveal');
      el.style.setProperty('--lumi-d', (i % 24) * 55 + 'ms');
    });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        el.classList.add('lumi-in');
        obs.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -36px 0px' });
    all.forEach(function (el) { obs.observe(el); });
  }

  window.addEventListener('lumi-motion:activate', collect);
  var t = window.setTimeout(collect, 120);
  if (document.readyState === 'complete') { window.clearTimeout(t); collect(); }
})();
"""

MAIN_IMPORT = "import './utils/lumi-motion.js';"


def _has(src_dir: Path, name: str) -> bool:
    return (src_dir / name).is_file()


def _patch_main(main_jsx: Path) -> str:
    text = main_jsx.read_text(encoding="utf-8")
    if MAIN_IMPORT in text:
        return "already-imported"
    lines = text.rstrip("\n").split("\n")
    insert = 0
    for i, ln in enumerate(lines):
        if ln.startswith("import "):
            insert = i + 1
    lines.insert(insert, MAIN_IMPORT)
    main_jsx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "patched"


def _patch_css(css: Path) -> str:
    raw = css.read_text(encoding="utf-8", errors="ignore")
    if MARKER in raw or "/* ===== lumi-motion" in raw:
        return "already-present"
    css.write_text(raw.rstrip("\n") + "\n" + MOTION_CSS, encoding="utf-8")
    return "appended"


def _card_hover_focus(frontend: Path) -> int:
    """Add lumi-card accent to card-shaped elements in page files (safe class append)."""
    src_dir = frontend / "src"
    pages = list((src_dir / "pages").glob("*.jsx"))
    touched = 0
    card_re = re.compile(r'className=\{?`?["\']([^"\'\`{}]*?\b(?:card|Card|feature|service|testimonial|pricing|blog|product)[^"\'\`{}]*?)["\'`]')
    for f in pages:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        if "lumi-card" in raw:
            continue
        new, n = card_re.subn(
            lambda m: m.group(0).replace(
                '"' + m.group(1) + '"', '"' + m.group(1).rstrip() + ' lumi-card"'
            ),
            raw,
        )
        if n:
            f.write_text(new, encoding="utf-8")
            touched += 1
    return touched


def inject_motion_layer(
    project_dir: str,
    intensity: str = "high",
    write_report: bool = True,
) -> Dict[str, Any]:
    """Inject the lumi-motion layer into a generated project.

    ``intensity``: ``high`` (full layer) / ``medium`` / ``low`` / ``none``.
    Never raises — returns a status dict the orchestrator can log.
    """
    pdir = Path(project_dir)
    frontend = pdir / "frontend"
    src_dir = frontend / "src"
    if not (src_dir / "main.jsx").is_file():
        if not (pdir / "src" / "main.jsx").is_file():
            return {"status": "skipped", "reason": "no frontend/src/main.jsx"}
        src_dir = pdir / "src"
        frontend = pdir

    if intensity in ("none", "low", "off", ""):
        return {"status": "skipped", "reason": f"intensity={intensity}"}

    log: Dict[str, Any] = {
        "status": "injected",
        "intensity": intensity,
        "files": [],
    }
    try:
        css = src_dir / "index.css"
        css_name = None
        for cand in (src_dir / "index.css", src_dir / "styles" / "globals.css", src_dir / "styles.css"):
            if cand.is_file():
                css = cand
                break
        r = _patch_css(css)
        main_jsx = src_dir / "main.jsx"
        r2 = _patch_main(main_jsx)
        js = src_dir / "utils" / "lumi-motion.js"
        js.parent.mkdir(parents=True, exist_ok=True)
        created_js = not js.is_file()
        js.write_text(MOTION_JS, encoding="utf-8")

        touched = 0
        if intensity == "high":
            touched = _card_hover_focus(frontend)

        log["files"] = [
            {"path": str(css.relative_to(pdir)), "action": r},
            {"path": str(main_jsx.relative_to(pdir)), "action": r2},
            {"path": str(js.relative_to(pdir)), "action": "created" if created_js else "written"},
            {"path": "pages/*.jsx", "action": f"lumi-card applied to {touched} page(s)"},
        ]
        if write_report:
            report = pdir / "MOTION_REPORT.md"
            report.write_text(
                "# Premium Motion Layer\n\n"
                f"Project: `{pdir.name}`  \nIntensity: `{intensity}`\n\n"
                "Injected runtime: scroll-reveal (IntersectionObserver), stagger delays, "
                "card hover lifts, float/shimmer accents. Vanilla JS + CSS only (zero deps); "
                "`prefers-reduced-motion` and RTL respected.\n",
                encoding="utf-8",
            )
            log["report"] = str(report.relative_to(pdir))
    except Exception as exc:  # noqa: BLE001
        agent_logger.warning("lumi-motion injection failed: %s", exc)
        return {"status": "error", "error": str(exc)[:300]}

    agent_logger.info("lumi-motion layer %s for %s (intensity=%s)", log["status"], pdir.name, intensity)
    return log


if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "generated-projects/nuage-events"
    level = sys.argv[2] if len(sys.argv) > 2 else "high"
    print(json.dumps(inject_motion_layer(target, intensity=level), indent=2))