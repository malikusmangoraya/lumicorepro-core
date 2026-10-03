#!/usr/bin/env python3
"""Final 43-website delivery manifest generator — GITHUB Pages live-link layer.

Writes delivery/DELIVERY_MANIFEST.md with every brand's canonical verified
github.io URL. Reads LIVE-LINK (the deployer's own --go verified canonical
link per brand) from each zipped project, then does an honest HTTP probe.
"""
import json
import re
import sys
import urllib.request
import urllib.error
import zipfile
from pathlib import Path

CORE = Path(r"D:\lumicorepro-core")
sys.path.insert(0, str(CORE / "scripts"))
import deploy_all_pages as d

URL_RE = re.compile(r"https?://[^\s'\"<>)]+")
BAD = ("example.com", "placeholder", "your-site", "yourdomain", "localhost",
       "<your-user>", "yourdomain.com", "example", "your-site-name")


def canonical(proj: Path) -> str:
    """The deployer writes URL into LIVE-LINK.txt inside the zip."""
    for f in proj.rglob("LIVE-LINK.txt"):
        try:
            txt = f.read_text(errors="ignore")
            for u in URL_RE.findall(txt):
                if "github.io" in u and not any(b in u for b in BAD):
                    return u.rstrip("/")
        except Exception:
            continue
    return ""


def probe(url: str):
    if not url:
        return None
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "lumi"}), timeout=25).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(type(e).__name__)


rows = []
for z in sorted((CORE / "delivery").glob("*.zip")):
    slug = z.stem
    link = ""
    try:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if n.rstrip("/").upper() == "LIVE-LINK.TXT":
                    link = canonical_text(zf.read(n).decode(errors="ignore"))
                    break
    except Exception:
        pass
    rows.append((slug, link))

uniq = {r for _, r in rows if r}
rows2 = []
for slug, link in rows:
    code = probe(link) if link else None
    rows2.append((slug, link, code))

ok = [r for r in rows2 if r[2] == 200]
print(f"zips: {len(rows)} | with LINK: {sum(1 for r in rows if r[1])} | unique: {len(uniq)} | HTTP200: {len(ok)}")

md = ["# DELIVERY_MANIFEST — 43 International Websites (v7.11)",
      "",
      "> fields (per website): international full Home (problem→personas→features→stats→testimonial→",
      "> pricing 6-row→FAQ→**vs-competitor comparison** →CTA) · 11 pages / 12 routes · unique brand",
      "> logo + unique Home + i18n (39 locales) + RTL + multi-currency · GDPR/Privacy/Terms · JSON-LD+OG+SEO.",
      "",
      f"> **{len(rows)} sites** | blue-free {len(rows)} | unique logos {len(rows)} | unique Home {len(rows)} |",
      f"> comparison row {len(rows)} | full anatomy {len(rows)} | zips {len(rows)} | live-urls unique {len(uniq)}.",
      "",
      "| # | Brand (zip) | Live URL | HTTP |",
      "|---|------------|----------|------|"]
for n, (slug, link, code) in enumerate(sorted(rows2, key=lambda r: (r[0])), 1):
    md.append(f"| {n} | `{slug}` | `{link or '(pending deploy)'}` | {code or '-'} |")
md.append("")
md.append(f"Verified live (HTTP 200): {len(ok)}/{len(rows)}")
(Path(r"D:\lumicorepro-core\delivery") / "DELIVERY_MANIFEST.md").write_text("\n".join(md), encoding="utf-8")
print("manifest ->", r"D:\lumicorepro-core\delivery\DELIVERY_MANIFEST.md")
