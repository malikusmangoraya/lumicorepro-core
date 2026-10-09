"""Live campaign QA — fetches every deployed GitHub Pages site and reports real defects.

Checks per site (all evidence-based, no taste rules):
  1. root reachable
  2. every referenced JS/CSS asset actually resolves
  3. favicon resolves
  4. og:image resolves
  5. twitter:image resolves
  6. JSON-LD @id/url domain agrees with og:url
  7. mojibake (UTF-8 decoded as cp1252) anywhere in the document
  8. .nojekyll present

Usage:
  python scripts/audit_live_campaigns.py
  python scripts/audit_live_campaigns.py --json out.json
Exit code 1 if any site has blocking defects (missing assets / broken images).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

OWNER = "malikusmangoraya"
SITES = [
    "aurelia-estates",
    "aurum-fitness",
    "ember-salt",
    "maison-noir",
    "meridian-capital",
    "nuage-events",
    "prestige-studio",
    "saffron-voyage",
    "studio-lumen",
    "voltus-atelier",
]

USER_AGENT = "lumicorepro-campaign-audit"
TIMEOUT = 25

# UTF-8 bytes decoded as cp1252: '—' (E2 80 94) -> 'ΓÇö'
MOJIBAKE = re.compile(r"[\u0393\u00c7\u00e2\u0080\u0094\u00c2\u00a0]")


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return 0, b""


def head_status(url: str) -> int:
    return fetch(url)[0]


def resolve(base: str, reference: str) -> str:
    if reference.startswith(("http://", "https://")):
        return reference
    if reference.startswith("//"):
        return "https:" + reference
    root = base.rstrip("/")
    path = reference.lstrip("./")
    return f"{root}/{path}"


def meta(html: str, *patterns: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    return None


def audit_site(site: str) -> dict:
    origin = f"https://{OWNER}.github.io"
    root = f"{origin}/{site}/"
    report: dict = {"site": site, "url": root, "defects": [], "checks": {}}

    status, body = fetch(root)
    report["checks"]["root"] = status
    if status != 200 or not body:
        report["defects"].append(f"root not reachable (http {status})")
        return report

    html = body.decode("utf-8", errors="replace")
    report["checks"]["bytes"] = len(body)

    # 2. referenced assets must resolve
    assets = re.findall(r'(?:src|href)="([^"]+\.(?:js|css))"', html)
    assets = [a for a in assets if not a.startswith(("http://", "https://", "//"))]
    bad_assets = []
    for asset in dict.fromkeys(assets):
        code = head_status(resolve(root, asset))
        if code != 200:
            bad_assets.append(f"{asset} -> {code}")
    report["checks"]["assets"] = len(assets)
    if bad_assets:
        report["defects"].append("broken assets: " + ", ".join(bad_assets))

    # 3. favicon
    favicon = meta(html, r'<link[^>]+rel="icon"[^>]+href="([^"]+)"')
    if favicon:
        code = head_status(resolve(root, favicon))
        report["checks"]["favicon"] = code
        if code != 200:
            report["defects"].append(f"favicon broken ({favicon} -> {code})")

    # 4/5. social images
    for label, patterns in (
        ("og:image", (r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',)),
        ("twitter:image", (r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"',)),
    ):
        url = meta(html, *patterns)
        if not url:
            continue
        code = head_status(url)
        report["checks"][label] = {"url": url, "status": code}
        if code != 200:
            report["defects"].append(f"{label} broken ({code}) {url}")

    # 6. JSON-LD domain must agree with og:url
    og_url = meta(html, r'<meta[^>]+property="og:url"[^>]+content="([^"]+)"')
    ld_ids = re.findall(r'"@id"\s*:\s*"(https?://[^/"]+)', html)
    report["checks"]["og_url"] = og_url
    ld_domains = sorted({re.sub(r"^https?://(www\.)?", "", d) for d in ld_ids})
    report["checks"]["jsonld_domains"] = ld_domains
    if og_url and ld_domains:
        og_domain = re.sub(r"^https?://(www\.)?", "", og_url)
        if og_domain not in ld_domains:
            report["defects"].append(
                f"JSON-LD domain {ld_domains} disagrees with og:url domain {og_domain}"
            )

    # 7. mojibake
    hits = MOJIBAKE.findall(html)
    if hits:
        sample = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        report["checks"]["mojibake"] = len(hits)
        report["defects"].append(
            "mojibake in document"
            + (f' (title: {sample.group(1).strip()[:70]})' if sample else "")
        )

    # 8. .nojekyll
    report["checks"]["nojekyll"] = head_status(f"{origin}/{site}/.nojekyll")

    report["ok"] = not report["defects"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        reports = list(pool.map(audit_site, SITES))

    blocking = 0
    for report in reports:
        status = "PASS" if report["ok"] else "FAIL"
        print(f"[{status}] {report['site']}  {report['url']}")
        for defect in report["defects"]:
            print(f"       - {defect}")
        if not report["ok"]:
            blocking += 1

    print(f"\n{len(reports) - blocking}/{len(reports)} sites clean, {blocking} with defects")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump({"reports": reports}, handle, indent=2)
        print(f"wrote {args.json_out}")

    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())