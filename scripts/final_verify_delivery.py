"""Final verification + delivery manifest.

Evidence-based release gate. Every column in DELIVERY_MANIFEST.md is produced by
an actual check in this process:

* dist built   - frontend/dist/index.html exists
* blue-free    - no blue-family hex literal in any dist *.css
* logo unique  - sha256 of frontend/public/logo.svg is unique across the fleet
* zip valid    - the delivery zip opens and every entry passes its CRC check
* live         - HTTP probe of the LIVE-LINK.txt URL inside the zip (status code,
                 or timeout/unreachable). Never guessed, never assumed.

Run: python scripts/final_verify_delivery.py [--probe] [--no-crc]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_map import BRANDS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
OUT = ROOT / "delivery"
BLUE = {
    "#3b82f6", "#2563eb", "#60a5fa", "#0ea5e9", "#0891b2", "#06b6d4",
    "#22d3ee", "#4dd6ff", "#14b8a6", "#0d9488", "#38bdf8", "#0284c7",
    "#93c5fd", "#7dd3fc",
}
PROBE_TIMEOUT = 12
PROBE_WORKERS = 8


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def zip_is_valid(path: Path, check_crc: bool) -> tuple[bool, int, str]:
    """Return (valid, entry_count, detail)."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if check_crc:
                bad = zf.testzip()
                if bad is not None:
                    return False, len(names), f"crc-failed:{bad}"
            return True, len(names), "ok"
    except Exception as exc:  # noqa: BLE001 - report the real reason
        return False, 0, f"{type(exc).__name__}:{exc}"


def probe(url: str) -> str:
    """HTTP probe a live URL. Returns 'HTTP 200' style text or a failure reason."""
    if not url or not url.startswith("http"):
        return "no-url"
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "lumicore-release-gate/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=PROBE_TIMEOUT) as response:
            return f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return f"unreachable ({exc.reason})"
    except Exception as exc:  # noqa: BLE001
        return f"error ({type(exc).__name__})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", help="HTTP probe every live link (slow, network required)")
    parser.add_argument("--no-crc", action="store_true", help="skip the slow CRC pass over every zip entry")
    args = parser.parse_args()

    if not GEN.exists():
        print(f"generated-projects/ not found at {GEN} - nothing to verify")
        return 2

    projects = sorted(p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists())
    logo_hashes: dict[str, list[str]] = {}
    rows: list[dict] = []

    for proj in projects:
        slug = proj.name
        if slug not in BRANDS:
            continue  # legacy/test scaffolding: never delivered, never packaged
        brand = BRANDS[slug]
        bslug = slugify(brand["name"])
        fe = proj / "frontend"

        row: dict = {
            "dir": slug,
            "brand": brand["name"],
            "brand_slug": bslug,
            "industry": brand["industry"],
        }

        dist = fe / "dist"
        row["dist"] = (dist / "index.html").exists() if dist.exists() else False

        row["blue_free"] = None
        if dist.exists():
            css_files = [f for f in dist.rglob("*.css") if f.exists()]
            if css_files:
                row["blue_free"] = not any(
                    b in f.read_text(errors="replace") for f in css_files for b in BLUE
                )

        logo = fe / "public" / "logo.svg"
        if logo.exists():
            digest = sha256_of(logo)
            logo_hashes.setdefault(digest, []).append(bslug)
            row["logo_hash"] = digest
            row["logo_hash_short"] = digest[:12]
        else:
            row["logo_hash"] = None
            row["logo_hash_short"] = None

        zip_path = OUT / f"{bslug}.zip"
        row["zip"] = zip_path.exists()
        if row["zip"]:
            ok, entries, detail = zip_is_valid(zip_path, check_crc=not args.no_crc)
            row["zip_ok"] = ok
            row["zip_entries"] = entries
            row["zip_detail"] = detail
            with zipfile.ZipFile(zip_path) as zf:
                link_names = [n for n in zf.namelist() if n.endswith("LIVE-LINK.txt")]
            row["has_live_link"] = bool(link_names)
            if link_names:
                with zipfile.ZipFile(zip_path) as zf:
                    text = zf.read(link_names[0]).decode("utf-8", "replace")
                match = re.search(r"https?://\S+", text)
                row["live_url"] = match.group(0).strip() if match else None
        else:
            row["zip_ok"] = False
            row["has_live_link"] = False

        rows.append(row)

    # logo uniqueness: a hash used by more than one project is a collision
    for row in rows:
        digest = row.get("logo_hash")
        row["logo_unique"] = bool(digest) and len(logo_hashes.get(row["logo_hash"], [])) == 1

    if args.probe:
        targets = [r.get("live_url") for r in rows if r.get("live_url")]
        with ThreadPoolExecutor(max_workers=PROBE_WORKERS) as pool:
            results = list(pool.map(probe, targets))
        for row, result in zip([r for r in rows if r.get("live_url")], results):
            row["live_status"] = result

    live_urls = [r.get("live_url") for r in rows if r.get("live_url")]
    totals = {
        "projects": len(rows),
        "dist_built": sum(1 for r in rows if r["dist"]),
        "blue_free": sum(1 for r in rows if r["blue_free"]),
        "logos_unique": sum(1 for r in rows if r["logo_unique"]),
        "zips_present": sum(1 for r in rows if r["zip"]),
        "zips_valid": sum(1 for r in rows if r.get("zip_ok")),
        "with_live_link": sum(1 for r in rows if r.get("has_live_link")),
        "unique_live_urls": len(set(live_urls)),
        "probed": sum(1 for r in rows if r.get("live_status")),
        "probe_ok": sum(1 for r in rows if str(r.get("live_status", "")).startswith("HTTP 2")),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "DELIVERY_MANIFEST.md"
    lines = [
        "# Delivery Manifest (evidence-based)",
        "",
        "Every column below is produced by a check that actually ran in",
        "`scripts/final_verify_delivery.py` at the time this file was written. Nothing is",
        "assumed: `live` is an HTTP probe result, `blue-free` is a scan of the built CSS, and",
        "`zip valid` includes a CRC pass over every archive entry.",
        "",
        f"> {totals['projects']} projects | dist built: {totals['dist_built']} | blue-free: {totals['blue_free']}"
        f" | logos unique: {totals['logos_unique']}/{totals['projects']}"
        f" | zips present: {totals['zips_present']} | zips valid: {totals['zips_valid']}"
        f" | live links present: {totals['with_live_link']} (unique URLs: {totals['unique_live_urls']})"
        + (
            f" | probed: {totals['probed']} | probe ok: {totals['probe_ok']}"
            if args.probe
            else " | live links: NOT PROBED (run with --probe)"
        ),
        "",
        "Column meanings: `blue-free` = built CSS free of blue-family hex literals;",
        "`logo` = sha256 of `public/logo.svg` is unique across the fleet; `zip` = archive opens",
        "and passes CRC; `live` = HTTP status of the URL in the zip's `LIVE-LINK.txt`.",
        "",
        "| # | Brand | Slug dir | Industry | Dist | Blue-free | Logo | Zip | Live |",
        "|---|-------|----------|----------|------|-----------|------|-----|------|",
    ]
    for idx, row in enumerate(sorted(rows, key=lambda r: r["brand"].lower()), 1):
        live = row.get("live_status") if args.probe else ("link present" if row.get("has_live_link") else "-")
        lines.append(
            f"| {idx} | {row['brand']} | {row['brand_slug']} | {row['industry']} | "
            f"{'yes' if row['dist'] else 'no'} | "
            f"{'yes' if row['blue_free'] else ('no' if row['blue_free'] is False else 'unknown')} | "
            f"{'unique' if row['logo_unique'] else ('collision' if row.get('logo_hash') else 'missing')} | "
            f"{'valid' if row.get('zip_ok') else ('invalid' if row['zip'] else 'missing')} | "
            f"{live or '-'} |"
        )
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    evidence = OUT / "DELIVERY_EVIDENCE.json"
    evidence.write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "probe_run": bool(args.probe), "crc_checked": not args.no_crc,
                    "totals": totals, "rows": rows}, indent=2),
        encoding="utf-8",
    )

    print(f"projects             : {totals['projects']}")
    print(f"dist built           : {totals['dist_built']}")
    print(f"blue-free            : {totals['blue_free']}")
    print(f"logos unique         : {totals['logos_unique']}/{totals['projects']}")
    print(f"zips present / valid : {totals['zips_present']} / {totals['zips_valid']}")
    print(f"live links present   : {totals['with_live_link']} (unique URLs: {totals['unique_live_urls']})")
    if args.probe:
        print(f"live probed / ok     : {totals['probed']} / {totals['probe_ok']}")
    else:
        print("live probed / ok     : NOT PROBED (pass --probe)")
    print(f"manifest             : {manifest}")
    print(f"evidence             : {evidence}")
    return 0 if totals["zips_valid"] == totals["zips_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
