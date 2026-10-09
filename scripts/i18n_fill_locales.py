#!/usr/bin/env python3
"""Fill untranslated UI strings in every product locale.

A generated product advertises 14 locales, but the locale files carried a block
of ~144 UI strings that were still English in all 13 non-English locales — an
Arabic, Urdu or Japanese visitor saw English buttons ("Save", "Delete", "Next",
"Read More") inside an otherwise translated page. This closes that gap using
the reviewed table in scripts/i18n_locale_pack.py.

It only replaces a value when it is byte-identical to the English string, so a
hand-corrected translation is never overwritten. Formatting (indent width and
line ending) is detected per file and preserved, so the diff stays reviewable.

    python scripts/i18n_fill_locales.py            # report only
    python scripts/i18n_fill_locales.py --apply     # write changes
    python scripts/i18n_fill_locales.py --check      # exit 1 if any gap remains

Exit codes
----------
0  clean (or, with --apply, every gap that the pack covers was filled)
1  gaps remain that the pack does not cover, or a locale file failed to parse
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from i18n_locale_pack import (  # noqa: E402
    LOCALES,
    NON_TRANSLATABLE,
    SAME_AS_ENGLISH,
    TOTAL_STRINGS,
    TRANSLATIONS,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTS_DIR = REPO_ROOT / "products"


def locales_dir(product: pathlib.Path) -> pathlib.Path:
    return product / "frontend" / "src" / "i18n" / "locales"


def flatten(node, prefix: str = ""):
    """Yield (dotted_key, value) for every leaf in a nested JSON object."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else key
            yield from flatten(value, child)
    else:
        yield prefix, node


def read_raw(path: pathlib.Path) -> str:
    """Read text WITHOUT universal-newline translation.

    path.read_text() turns CRLF into LF, which silently rewrites every line
    ending in the file when it is written back. The product locale files are
    CRLF, so the raw bytes decide the format.
    """
    return path.read_bytes().decode("utf-8")


def detect_format(raw: str) -> tuple[str, str]:
    """Return (newline, indent_string) as used by the file on disk."""
    newline = "\r\n" if "\r\n" in raw else "\n"
    indent = "  "
    for line in raw.splitlines():
        stripped = line.lstrip(" \t")
        if stripped.startswith('"') and len(line) - len(stripped) > 0:
            indent = line[: len(line) - len(stripped)]
            break
    return newline, indent


def walk_and_fill(node, locale, english_flat, path="", stats=None):
    if stats is None:
        stats = {"filled": 0, "allowed": 0, "untranslatable": 0, "uncovered": []}
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                walk_and_fill(value, locale, english_flat, child, stats)
            elif isinstance(value, str):
                node[key] = _maybe_translate(value, locale, english_flat, child, stats)
    return stats


def _maybe_translate(value, locale, english_flat, path, stats):
    stripped = value.strip()
    if not stripped:
        return value
    english = english_flat.get(path)
    if english is None or stripped != str(english).strip():
        return value  # already localised (or not an English mirror)
    if stripped in NON_TRANSLATABLE:
        stats["untranslatable"] += 1
        return value
    if (locale, stripped) in SAME_AS_ENGLISH:
        stats["allowed"] += 1
        return value
    replacement = TRANSLATIONS.get(locale, {}).get(stripped)
    if replacement is None:
        stats["uncovered"].append(f"{locale}:{path}={stripped!r}")
        return value
    if replacement.strip() == stripped:
        # The reviewed translation is itself spelled like English (French
        # "Contact", Spanish "No", German "Filter"). Correct, not an oversight.
        stats["allowed"] += 1
        return value
    stats["filled"] += 1
    # Preserve surrounding whitespace exactly.
    lead = value[: len(value) - len(value.lstrip())]
    trail = value[len(value.rstrip()) :]
    return f"{lead}{replacement}{trail}"


def process(product: pathlib.Path, apply: bool, eol: str = "preserve") -> dict:
    directory = locales_dir(product)
    result = {
        "product": product.name, "filled": 0, "allowed": 0,
        "untranslatable": 0, "uncovered": [], "files": 0,
    }
    if not directory.is_dir():
        result["uncovered"].append(f"{product.name}: no locales directory")
        return result

    en_path = directory / "en.json"
    if not en_path.is_file():
        result["uncovered"].append(f"{product.name}: no en.json")
        return result
    english_flat = dict(flatten(json.loads(en_path.read_text(encoding="utf-8"))))

    for locale in LOCALES:
        path = directory / f"{locale}.json"
        if not path.is_file():
            result["uncovered"].append(f"{product.name}: missing {locale}.json")
            continue
        raw = read_raw(path)
        detected, indent = detect_format(raw)
        newline = {"preserve": detected, "crlf": "\r\n", "lf": "\n"}[eol]
        data = json.loads(raw)
        stats = walk_and_fill(data, locale, english_flat)
        result["filled"] += stats["filled"]
        result["allowed"] += stats["allowed"]
        result["untranslatable"] += stats["untranslatable"]
        result["uncovered"].extend(f"{product.name}:{item}" for item in stats["uncovered"])
        if apply:
            text = json.dumps(data, ensure_ascii=False, indent=len(indent))
            # json.dumps always uses \n; restore the file's own convention.
            if newline == "\r\n":
                text = text.replace("\n", "\r\n")
            text += newline
            # Compare raw bytes so a line-ending drift is repaired too, not
            # only a translated value.
            if text.encode("utf-8") != path.read_bytes():
                path.write_bytes(text.encode("utf-8"))
                result["files"] += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the fixes to disk")
    parser.add_argument("--check", action="store_true", help="exit 1 if any uncovered gap remains")
    parser.add_argument("--products", default=str(PRODUCTS_DIR), help="products directory")
    parser.add_argument(
        "--eol",
        choices=("preserve", "crlf", "lf"),
        default="preserve",
        help=(
            "line ending to write. 'preserve' (default) keeps whatever each file "
            "already uses. Use 'crlf' once to migrate files that were rewritten "
            "by an older build of this script."
        ),
    )
    args = parser.parse_args()

    root = pathlib.Path(args.products)
    products = sorted(
        p for p in root.iterdir() if p.is_dir() and (p / "frontend").is_dir()
    )
    if not products:
        print(f"no products found under {root}", file=sys.stderr)
        return 1

    print(f"=== i18n fill: {len(products)} product(s), {TOTAL_STRINGS} strings x {len(LOCALES)} locales")
    total_filled = total_allowed = total_untranslatable = 0
    uncovered: list[str] = []
    for product in products:
        result = process(product, args.apply, args.eol)
        total_filled += result["filled"]
        total_allowed += result["allowed"]
        total_untranslatable += result["untranslatable"]
        uncovered.extend(result["uncovered"])
        verb = "filled" if args.apply else "to fill"
        print(
            f"  {result['product']:<18} {result['filled']:>5} {verb:<8} "
            f"{result['allowed']:>4} verified-cognate  {result['files']:>3} file(s) written"
        )

    print()
    print(f"total: {total_filled} value(s) {'written' if args.apply else 'need writing'}")
    print(f"       {total_allowed} value(s) verified correct as English (pack-reviewed cognates)")
    print(f"       {total_untranslatable} value(s) deliberately untranslatable (brands, addresses, e-mails, numerals)")
    if uncovered:
        print(f"\nNOT COVERED by the pack ({len(uncovered)}):")
        for item in uncovered[:40]:
            print("  -", item)
        if len(uncovered) > 40:
            print(f"  ... and {len(uncovered) - 40} more")
        return 1
    print("every English-mirrored value is covered by the pack")
    if args.check and not args.apply:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
