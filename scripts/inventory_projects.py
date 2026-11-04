"""Inventory every generated/delivered product and classify what is really there."""

import json
import os
import re
from pathlib import Path

PREMIUM = Path(r"D:/lumicorepro-core-premium-delivery")
ORIGINAL = Path(r"D:/lumicorepro-core")

SKIP_DIRS = {"node_modules", "frontend_node_modules_old", ".git", ".expo", ".next",
             "coverage", "test-results", "playwright-report", ".vercel", ".turbo",
             "build", "dist", ".cache", "__pycache__"}

FRONTEND_EXT = {".jsx", ".tsx", ".css", ".vue", ".svelte"}
BACKEND_EXT = {".js", ".ts", ".py", ".php", ".go", ".cs", ".rb"}


def count_files(root: Path) -> dict:
    """Count source files, split by area. Skips build output and deps."""
    out = {"frontend": 0, "backend": 0, "tests": 0, "docs": 0, "other": 0}
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel = Path(dirpath).relative_to(root)
        parts = rel.parts
        depth = len(parts)
        if depth > 6:
            dirnames[:] = []
            continue
        area = "other"
        if parts and parts[0] in ("frontend", "src", "app", "pages", "components"):
            area = "frontend"
        elif parts and parts[0] in ("backend", "server", "api"):
            area = "backend"
        for name in filenames:
            suffix = Path(name).suffix.lower()
            lowered = name.lower()
            if "test" in lowered or "spec" in lowered:
                out["tests"] += 1
                continue
            if suffix in (".md", ".txt") and area == "other":
                out["docs"] += 1
                continue
            if suffix in FRONTEND_EXT:
                out["frontend"] += 1
            elif suffix in BACKEND_EXT:
                if area == "backend":
                    out["backend"] += 1
                elif area == "frontend":
                    out["frontend"] += 1
                else:
                    out["other"] += 1
            else:
                out["other"] += 1
    return out


def flags(root: Path) -> dict:
    if not root.is_dir():
        return {}
    return {
        "package_json": any((root / p / "package.json").is_file() for p in ("", "frontend", "backend")),
        "frontend_pkg": (root / "frontend" / "package.json").is_file() or (root / "package.json").is_file(),
        "backend_pkg": (root / "backend" / "package.json").is_file(),
        "dist": any((root / p / "dist" / "index.html").is_file() for p in ("", "frontend")),
        "src_index": any((root / p / "index.html").is_file() for p in ("", "frontend")),
        "readme": (root / "README.md").is_file(),
        "license": (root / "LICENSE.md").is_file() or (root / "LICENSE").is_file(),
        "env_example": bool(list(root.glob(".env.example")) + list(root.glob("*/.env.example"))),
        "vercel": (root / "vercel.json").is_file(),
    }


def classify(root: Path) -> tuple[str, dict]:
    f = flags(root)
    if not f:
        return "MISSING", {}
    c = count_files(root)
    has_fe = c["frontend"] >= 5
    has_be = c["backend"] >= 3
    has_src = has_fe or c["backend"] >= 1
    if not has_src and not f.get("dist"):
        return "EMPTY", c
    if not has_src and f.get("dist"):
        return "DIST_ONLY", c
    if has_fe and has_be:
        return "FULL_STACK", c
    if has_fe and not has_be:
        return "FRONTEND_ONLY", c
    if has_be and not has_fe:
        return "BACKEND_ONLY", c
    return "SCAFFOLD", c


def parse_manifest(path: Path) -> list[dict]:
    rows = []
    if not path.is_file():
        return rows
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
                     r"\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
                     line)
        if not m:
            continue
        rows.append({
            "n": int(m.group(1)),
            "brand": m.group(2),
            "slug": m.group(3),
            "industry": m.group(4),
            "dist": m.group(5),
            "blue_free": m.group(6),
            "logo": m.group(7),
            "zip": m.group(8),
            "live": m.group(9),
        })
    return rows


def locate(slug: str) -> tuple[str, Path | None]:
    """Where does this project actually exist? Prefer real source over build output."""
    candidates = [
        ("premium/products", PREMIUM / "products" / "sell-today" / slug),
        ("premium/delivery", PREMIUM / "delivery" / slug),
        ("original/products", ORIGINAL / "products" / "sell-today" / slug),
        ("original/delivery", ORIGINAL / "delivery" / slug),
        ("original/generated", ORIGINAL / "generated-projects" / slug),
        ("premium/generated", PREMIUM / "generated-projects" / slug),
    ]
    for label, path in candidates:
        if path.is_dir():
            return label, path
    return "nowhere", None


def main() -> None:
    manifest = parse_manifest(PREMIUM / "delivery" / "DELIVERY_MANIFEST.md")
    print(f"manifest rows parsed: {len(manifest)}\n")

    records = []
    for row in manifest:
        where, path = locate(row["slug"])
        status, counts = classify(path) if path else ("MISSING", {})
        records.append({**row, "where": where, "path": str(path) if path else "",
                        "status": status, **counts})

    # Extra projects not in the manifest
    extras = []
    for label, root in [
        ("premium/products/sell-today", PREMIUM / "products" / "sell-today"),
        ("premium/generated-projects", PREMIUM / "generated-projects"),
        ("original/generated-projects", ORIGINAL / "generated-projects"),
    ]:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if any(r["slug"] == child.name for r in records):
                continue
            if any(e["slug"] == child.name for e in extras):
                continue
            status, counts = classify(child)
            extras.append({"slug": child.name, "where": label, "path": str(child),
                           "status": status, **counts})

    out = {"manifest": records, "extras": extras}
    (PREMIUM / "docs" / "superpowers" / "reports" / "project-inventory.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    # Summary
    from collections import Counter
    print("=== MANIFEST PROJECTS (95) ===")
    print(Counter(r["status"] for r in records))
    print(Counter(r["where"] for r in records))
    print("\n=== EXTRAS ===")
    print(Counter(e["status"] for e in extras))
    print(f"\nwrote docs/superpowers/reports/project-inventory.json")


if __name__ == "__main__":
    main()
