"""Built-with LumicorePro proof badge — ships inside every generated project.

Proof surface the operator asked for: each generated website carries a small,
tasteful fixed-position card (bottom-right) that shows the project's own
logo/preview image with the project name, a "Built with LumicorePro" line and
— once the project has a live URL — a "View live" link directly beneath.

Design constraints honored:
  * vanilla HTML < imgsrc > — survives React/Vite S purges because it lives
    outside the app root div in ``index.html``
  * idempotent — the ``id="built-with-lumicorepro"`` marker blocks re-injection
  * project image = first available brand asset (og-image / logo / favicon),
    copied next to the entry HTML as ``built-with-thumb.svg`` so the relative
    reference always resolves
  * no external requests at runtime except the optional link itself
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

MARKER = "built-with-lumicorepro"

_ENTRY_CANDIDATES = (
    "frontend/index.html",
    "frontend/dist/index.html",
    "index.html",
    "dist/index.html",
    "public/index.html",
)

_IMAGE_CANDIDATES = (
    "og-image.svg",
    "logo.svg",
    "favicon.svg",
    "public/og-image.svg",
    "public/logo.svg",
    "public/favicon.svg",
    "frontend/public/og-image.svg",
    "frontend/public/logo.svg",
    "frontend/public/favicon.svg",
)

_FALLBACK_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="none"/>'
    '<defs><linearGradient id="bwg" x1="0" y1="0" x2="64" y2="64">'
    '<stop offset="0" stop-color="#0ea5a4"/><stop offset="1" stop-color="#6366f1"/>'
    "</linearGradient></defs>"
    '<polygon points="32,4 56,18 56,46 32,60 8,46 8,18" fill="url(#bwg)"/>'
    '<path d="M26 22v20h14" stroke="#fff" stroke-width="5" fill="none" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg>"
)

_STYLE = """
#%(marker)s{position:fixed;right:14px;bottom:14px;z-index:2147483647;
font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
max-width:210px;background:rgba(15,23,42,.92);color:#e2e8f0;border-radius:14px;
padding:10px 12px;box-shadow:0 10px 30px rgba(15,23,42,.35);
border:1px solid rgba(148,163,184,.25);backdrop-filter:blur(6px)}
#%(marker)s img,#%(marker)s .bw-fallback{display:block;width:40px;height:40px;
border-radius:10px;margin-bottom:6px;object-fit:cover}
#%(marker)s .bw-name{font-size:12px;font-weight:650;color:#fff;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:186px}
#%(marker)s .bw-brand{font-size:10.5px;color:#94a3b8;margin-top:1px}
#%(marker)s .bw-brand a{color:#38bdf8;text-decoration:none;font-weight:600}
#%(marker)s .bw-brand a:hover{text-decoration:underline}
@media (max-width:640px){#%(marker)s{max-width:160px}}
"""


def _brand_name(project_dir: str) -> str:
    raw = Path(project_dir).name.replace("-", " ").replace("_", " ").strip()
    if not raw:
        return "LumiCorePro Project"
    return " ".join(w[:1].upper() + w[1:] for w in raw.split())[:48]


def find_entries(project_dir: str) -> List[Path]:
    base = Path(project_dir)
    return [base / rel for rel in _ENTRY_CANDIDATES if (base / rel).is_file()]


def _pick_image(project_dir: str) -> Optional[Path]:
    base = Path(project_dir)
    for rel in _IMAGE_CANDIDATES:
        p = base / rel
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def inject_built_with(
    project_dir: str,
    live_url: Optional[str] = None,
    link_label: str = "View live",
) -> Dict[str, Any]:
    """Inject the proof badge into every entry HTML of ``project_dir``.

    Idempotent: files already carrying the marker are left untouched. Returns
    ``{"status", "injected", "skipped", "entries", "live_url", "brand_name"}``.
    """
    project_dir = str(project_dir or "").strip()
    if not Path(project_dir).is_dir():
        return {"status": "failed", "message": "Project directory not found"}

    entries = find_entries(project_dir)
    if not entries:
        return {"status": "failed", "message": "No index.html found for badge injection"}

    image = _pick_image(project_dir)
    injected, skipped = 0, 0
    touched: List[str] = []
    for entry in entries:
        html = entry.read_text(encoding="utf-8", errors="replace")
        if MARKER in html:
            skipped += 1
            continue
        if image is not None:
            thumb = entry.parent / "built-with-thumb.svg"
            try:
                shutil.copyfile(image, thumb)
            except OSError:
                thumb = None
            img_tag = (
                f'<img src="{thumb.name}" alt="{_brand_name(project_dir)} logo">'
                if thumb
                else f'<div class="bw-fallback">{_FALLBACK_LOGO}</div>'
            )
        else:
            img_tag = f'<div class="bw-fallback">{_FALLBACK_LOGO}</div>'

        if live_url:
            link = f'<a href="{live_url}" target="_blank" rel="noopener">{link_label} →</a>'
        else:
            link = '<a href="#" title="Live URL available after deployment" onclick="return false">Pending deploy</a>'
        brand = _brand_name(project_dir)
        chip = (
            f'<div id="{MARKER}" role="complementary" aria-label="Built with LumicorePro">'
            f"{img_tag}"
            f'<div class="bw-name">{brand}</div>'
            f'<div class="bw-brand">Built with '
            f'<a href="https://github.com/malikusmangoraya/lumicorepro-core" target="_blank" rel="noopener">LumiCorePro</a>'
            f"</div>"
            f'<div class="bw-brand">{link}</div>'
            f"</div>"
        )
        style = _STYLE % {"marker": MARKER}
        block = f"<style data-{MARKER}>{style}</style>{chip}"
        if re.search(r"</body\s*>", html, re.I):
            html = re.sub(r"(</body\s*>)", block + r"\1", html, count=1, flags=re.I)
        else:
            html += block
        entry.write_text(html, encoding="utf-8")
        injected += 1
        touched.append(str(entry.relative_to(Path(project_dir))))

    return {
        "status": "ok",
        "injected": injected,
        "skipped": skipped,
        "entries": touched,
        "live_url": live_url or "",
        "brand_name": _brand_name(project_dir),
    }


def update_live_link(project_dir: str, live_url: str) -> Dict[str, Any]:
    """Point an already-injected badge at the final live URL (e.g. post-deploy)."""
    from urllib.parse import urlparse

    if not live_url or not urlparse(live_url).netloc:
        return {"status": "failed", "message": "A valid live URL is required"}
    updated = 0
    for entry in find_entries(project_dir):
        html = entry.read_text(encoding="utf-8", errors="replace")
        if MARKER not in html:
            continue
        html = html.replace(
            '<a href="#" title="Live URL available after deployment" onclick="return false">Pending deploy</a>',
            f'<a href="{live_url}" target="_blank" rel="noopener">View live →</a>',
        )
        entry.write_text(html, encoding="utf-8")
        updated += 1
    return {"status": "ok" if updated else "no-op", "updated": updated, "live_url": live_url}
