#!/usr/bin/env python3
"""Find every module the ESM tree imports that is not an ES module.

Node lets ESM import CommonJS through the default export, so a default import of
a CJS file works. A *named* import from CJS only works when Node's
cjs-module-lexer can statically detect the names, which it frequently cannot for
generated code. The result at runtime is:

    Named export 'authorize' not found. The requested module
    '../middleware/auth.js' is a CommonJS module, and may not provide a
    named export

which makes the importing route fail to load at all. That is how a whole
feature area ends up silently dead while the server still starts.

This reports the real state: every module reachable from the ESM tree that is
not itself ESM, and whether each importer needs default-only or named access.

    python scripts/import_graph.py --product aurelia-estates
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"
SKIP = {"node_modules", ".git", "dist", "build", "coverage"}

ESM_IMPORT = re.compile(
    r"""import\s+(?P<clause>[^'"]*?)\s*from\s*['"](?P<spec>[^'"]+)['"]""", re.S)
BARE_IMPORT = re.compile(r"""import\s*['"](?P<spec>[^'"]+)['"]""")
EXPORT_FROM = re.compile(
    r"""export\s+(?P<clause>[^'"]*?)\s*from\s*['"](?P<spec>[^'"]+)['"]""")
REQUIRE = re.compile(r"""require\s*\(\s*['"](?P<spec>[^'"]+)['"]\s*\)""")
NAMED = re.compile(r"\{(?P<names>[^}]*)\}")
DEFAULT = re.compile(r"^\s*(?P<name>[A-Za-z_$][\w$]*)\s*(?:,|$)")


def classify(text: str) -> str:
    if re.search(r"^\s*(import|export)\s", text, re.M):
        return "esm"
    if re.search(r"^\s*module\.exports", text, re.M) or "require(" in text:
        return "cjs"
    return "bare"


def specifiers(text: str):
    """Yield (specifier, wants_named) for every import in a module."""
    for rx in (ESM_IMPORT, EXPORT_FROM):
        for m in rx.finditer(text):
            spec = m.group("spec")
            clause = m.group("clause") or ""
            wants_named = bool(NAMED.search(clause))
            yield spec, wants_named
    for m in BARE_IMPORT.finditer(text):
        yield m.group("spec"), False


@dataclass
class Issue:
    target: str          # path relative to backend/
    kind: str            # cjs | bare
    imported_by: list[str] = field(default_factory=list)
    named_importers: list[str] = field(default_factory=list)


def analyse(proj: Path) -> dict:
    be = proj / "backend"
    if not be.is_dir():
        return {"product": proj.name, "error": "no backend directory"}

    styles: dict[Path, str] = {}
    texts: dict[Path, str] = {}
    for f in be.rglob("*.js"):
        if any(part in SKIP for part in f.parts):
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        styles[f] = classify(t)
        texts[f] = t

    esm_files = [f for f, s in styles.items() if s == "esm"]
    issues: dict[str, Issue] = {}

    for f in esm_files:
        for spec, wants_named in specifiers(texts[f]):
            if not spec.startswith("."):
                continue
            target = (f.parent / spec).resolve()
            # tolerate an extensionless or directory import
            if not target.exists():
                for cand in (target.with_suffix(".js"), target / "index.js"):
                    if cand.exists():
                        target = cand
                        break
                else:
                    continue
            kind = styles.get(target)
            if kind is None or kind == "esm":
                continue
            rel = target.relative_to(be.resolve()).as_posix()
            key = rel
            if key not in issues:
                issues[key] = Issue(target=rel, kind=kind)
            importer = f.relative_to(be).as_posix()
            if importer not in issues[key].imported_by:
                issues[key].imported_by.append(importer)
            if wants_named and importer not in issues[key].named_importers:
                issues[key].named_importers.append(importer)

    # A CJS module CAN serve named imports if Node can statically see them.
    def cjs_exports(text: str) -> set[str]:
        names = set()
        for m in re.finditer(r"module\.exports\.([A-Za-z_$][\w$]*)\s*=", text):
            names.add(m.group(1))
        for m in re.finditer(r"module\.exports\s*=\s*\{([^}]*)\}", text, re.S):
            for part in m.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                alias = re.split(r"[:\s]", part)[0].strip()
                if alias:
                    names.add(alias)
        return names

    breaking = []
    for rel, issue in sorted(issues.items()):
        target = be / rel
        exported = cjs_exports(texts.get(target, ""))
        # Only flagged when the importer asks for a name Node cannot see.
        for importer in issue.named_importers:
            itext = texts.get(be / importer, "")
            for m in ESM_IMPORT.finditer(itext):
                if m.group("spec") != target.name and not m.group("spec").endswith(rel.split("/")[-1]):
                    continue
                clause = m.group("clause") or ""
                wanted = [n.split(" as ")[0].strip()
                          for n in (NAMED.search(clause).group("names") if NAMED.search(clause) else "").split(",")
                          if n.strip()]
                missing = [w for w in wanted if w and w not in exported]
                if missing:
                    breaking.append({
                        "target": rel,
                        "kind": issue.kind,
                        "importer": importer,
                        "missing": missing,
                        "cjs_visible_exports": sorted(exported),
                    })
                break

    return {
        "product": proj.name,
        "esm_modules": len(esm_files),
        "non_esm_reachable": len(issues),
        "breaking_named_imports": breaking,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--product")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.product:
        dirs = [q for q in dirs if a.product in q.name]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    results = [analyse(d) for d in dirs]
    if a.json:
        print(json.dumps(results, indent=2))
        return 0

    total = 0
    for r in results:
        if "error" in r:
            print(f"-- {r['product']:20} {r['error']}")
            continue
        breaks = r["breaking_named_imports"]
        total += len(breaks)
        print(f"-- {r['product']:20} esm={r['esm_modules']:<4} "
              f"non-esm reachable={r['non_esm_reachable']:<3} breaking={len(breaks)}")
        for b in breaks[:6]:
            print(f"     {b['importer']}")
            print(f"       -> {b['target']} [{b['kind']}] missing: {', '.join(b['missing'])}")
            if b["cjs_visible_exports"]:
                print(f"          CJS exports Node can see: {', '.join(b['cjs_visible_exports'][:8])}")
    print(f"\n=== {total} breaking named import(s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())