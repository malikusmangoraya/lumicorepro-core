#!/usr/bin/env python3
"""Give every product its own real, local, industry-correct imagery.

The 11 products hotlink 20 shared Unsplash photo IDs (3 avatar photos appear
in ALL 11 sites; apex and flowpilot share 5 scenic photos; a kettlebell photo
serves an insurance site). This script:

  1. downloads verified replacements per product into
     `products/<p>/frontend/public/images/` (scenic at w=1600, portraits w=256),
  2. enforces global uniqueness - a photo ID is never used by two products,
  3. rewrites every `images.unsplash.com` URL in `frontend/src` to the local
     file, so buyers ship zero hotlinks,
  4. records everything in `docs/audit/product_image_manifest.json`.

A candidate that does not return HTTP 200 with an image content-type is
skipped for the next candidate. Slots with no resolvable candidate are
reported, never silently hotlinked.

    python scripts/fetch_product_images.py                 # everything
    python scripts/fetch_product_images.py --product apex   # one product
    python scripts/fetch_product_images.py --rewrite-only  # no downloads
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "audit" / "product_image_manifest.json"
URL_RE = re.compile(r"https://images\.unsplash\.com/(photo-[0-9a-f\-]+)[^\"'\s\)]*")

AVATAR_IDS = {
    "photo-1494790108377-be9c29b29330",
    "photo-1507003211169-0a1dd7228f2d",
    "photo-1534528741775-53994a69daeb",
}

# 33 unique portraits, 3 per product in listed order.
PORTRAITS = [
    "photo-1544005313-94ddf0286df2",
    "photo-1506794778202-cad84cf45f1d",
    "photo-1531123897727-8f129e1688ce",
    "photo-1519085360753-af0119f7cbe7",
    "photo-1580489944761-15a19d654956",
    "photo-1633332755192-727a05c4013d",
    "photo-1599566150163-29194dcaad36",
    "photo-1607746882042-944635dfe10e",
    "photo-1472099645785-5658abf4ff4e",
    "photo-1438761681033-6461ffad8d80",
    "photo-1500648767791-00dcc994a43e",
    "photo-1573496359142-b8d87734a5a2",
    "photo-1560250097-0b93528c311a",
    "photo-1547425260-76bcadfb4f2c",
    "photo-1552058544-f2b08422138a",
    "photo-1492562080023-ab3db95bfbce",
    "photo-1531384441138-2736e62e0919",
    "photo-1521119989659-a83eee488004",
    "photo-1519345182560-3f2917c472ef",
    "photo-1463453091185-61582044d556",
    "photo-1489424731084-a5d8b219a5bb",
    "photo-1487412720507-e7ab37603c6f",
    "photo-1492106087820-71f1a00d2b11",
    "photo-1508214751196-bcfd4ca60f91",
    "photo-1524504388940-b1c1722653e1",
    "photo-1529626455594-4ff0802cfb7e",
    "photo-1542909168-82c3e7fdca5c",
    "photo-1520813792240-56fc4a3765a7",
    "photo-1521146764736-56c929d59c83",
    "photo-1589156280159-27698a70f29e",
    "photo-1619895862022-09114b41f16f",
    "photo-1628157588553-5eeea00af15c",
    "photo-1567532939604-b6b5b0db2604",
]

PRODUCT_ORDER = [
    "apex",
    "aurelia-estates",
    "aurum-fitness",
    "claimflow-ai",
    "flowpilot",
    "meridian-capital",
    "nuage-events",
    "prestige-studio",
    "resupro",
    "saffron-voyage",
    "studio-lumen",
]

# old scenic photo ID -> ordered candidate replacements (first resolvable wins).
# Products not listed keep their scenic IDs (downloaded locally instead).
REPLACE = {
    "apex": {
        # photo-1551434675 (the old hero) returns HTTP 404 - the live hero is
        # broken today. Replaced with a verified developers-at-work photo.
        "photo-1551434675-a141877074ae": [
            "photo-1573164713988-8665fc963095",
            "photo-1498050108023-c5249f4df085",
            "photo-1587620962725-abab7fe55159",
        ],
        "photo-1600585154526-990dced4db0d": ["photo-1460925895917-afdab827c52f"],
        "photo-1553729459-efe14ef6055d": ["photo-1551288049-bebda4e38f71"],
        "photo-1533750349088-cd871a92f312": ["photo-1522071820081-009f0129c71c"],
        "photo-1547658719-da2b51169166": ["photo-1552664730-d307ca884978"],
        "photo-1466692476868-aef1dfb1e735": ["photo-1553877522-43269d4ea984"],
    },
    "flowpilot": {
        "photo-1454165804606-c3d57bc81466": ["photo-1518186285589-2f7649de83e0"],
        "photo-1600585154526-990dced4db0d": ["photo-1485827404703-89b55fcc595e"],
        "photo-1553729459-efe14ef6055d": ["photo-1555255707-c07966088b7b"],
        "photo-1533750349088-cd871a92f312": ["photo-1677442136019-21780ecad995"],
        "photo-1547658719-da2b51169166": ["photo-1620712943543-bcc4688e7485"],
        "photo-1466692476868-aef1dfb1e735": ["photo-1526374965328-7f61d4dc18c5"],
    },
    "aurelia-estates": {
        "photo-1600596542815-ffad4c15dcb0": ["photo-1600596542815-ffad4c1539a9"],
    },
    "aurum-fitness": {
        "photo-1517836357463-d25dfeac3438": ["photo-1571019613454-1cb2f99b2d8b"],
    },
    "claimflow-ai": {
        "photo-1571019613454-1cb2f99b2d8b": ["photo-1450101499163-c8848c66ca85"],
        "photo-1476480862126-209bfaa8edc8": ["photo-1521791136064-7986c2920216"],
        "photo-1517836357463-d25dfeac3438": ["photo-1454165804606-c3d57bc86b40"],
    },
    "resupro": {
        "photo-1441986300917-64674bd600d8": ["photo-1542744173-8e7e53415bb0"],
    },
}

# Extra gallery images per product for the new sections (2-3 each).
EXTRA = {
    "apex": ["photo-1556761175-4b46a572b786", "photo-1600880292089-90a7e086ee0c", "photo-1551434678-e076c223a692"],
    "aurelia-estates": ["photo-1600607687939-ce8a6c25118c", "photo-1512917774080-9991f1c4c750", "photo-1600566753086-00f18fb6b3ea"],
    "aurum-fitness": ["photo-1583454110551-21f2fa2afe61", "photo-1571902943202-507ec2618e38", "photo-1526506118085-60ce8714f8c5"],
    "claimflow-ai": ["photo-1556742049-0cfed4f6a45d", "photo-1423666639041-f56000c27a9a", "photo-1600880292203-757bb62b4baf"],
    "flowpilot": ["photo-1518709268805-4e9042af9f23", "photo-1550751827-4bd374c3f58b", "photo-1531297484001-80022131f5a1"],
    "meridian-capital": ["photo-1611974789855-9c2a0a7236a3", "photo-1486406146926-c627a92ad1ab", "photo-1560472354-b33ff0c44a43"],
    "nuage-events": ["photo-1511578314322-379afb476865", "photo-1492684223066-81342ee5ff30", "photo-1540575467063-178a50c2df87"],
    "prestige-studio": ["photo-1561070791-2526d30994b5", "photo-1542038784456-1ea8e935640e", "photo-1524758631624-e2822e304c36"],
    "resupro": ["photo-1521737604893-d14cc237f11d", "photo-1556761175-b413da4baf72", "photo-1573497019940-1c28c88b4f3e"],
    "saffron-voyage": ["photo-1488646953014-85cb44e25828", "photo-1476514525535-07fb3b4ae5f1", "photo-1500835556837-99ac94a94552"],
    "studio-lumen": ["photo-1493809842364-78817add7ffb", "photo-1522708323590-d24dbb6b0267", "photo-1513506003901-1e6a229e2d15"],
}


def fetch(url: str, dest: pathlib.Path, timeout: int = 30) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LumicorePro/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"
            ctype = resp.headers.get("Content-Type", "")
            if not ctype.startswith("image/"):
                return False, f"content-type {ctype}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
            return True, f"{dest.stat().st_size} bytes {ctype}"
    except Exception as exc:  # noqa: BLE001 - report, then try next candidate
        return False, f"{type(exc).__name__}: {exc}"


def pick(candidates: list[str], used: set[str], width: int) -> tuple[str | None, str]:
    for pid in candidates:
        if pid in used:
            continue
        url = f"https://images.unsplash.com/{pid}?q=80&w={width}&auto=format&fit=crop"
        return pid, url
    return None, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", help="limit to one product")
    ap.add_argument("--rewrite-only", action="store_true")
    args = ap.parse_args()

    products = [args.product] if args.product else PRODUCT_ORDER
    used: set[str] = set()
    manifest: dict = {}
    failures: list[str] = []

    for index, prod in enumerate(products):
        fe = ROOT / "products" / prod / "frontend"
        imgdir = fe / "public" / "images"
        mapping: dict[str, str] = {}  # old photo ID -> local web path

        # 1. Portraits: 3 unique per product.
        trio = PORTRAITS[index * 3 : index * 3 + 3]
        for n, pid in enumerate(trio, 1):
            local = f"/images/avatar-{n}.jpg"
            dest = imgdir / f"avatar-{n}.jpg"
            if not args.rewrite_only and not dest.exists():
                url = f"https://images.unsplash.com/{pid}?q=80&w=256&auto=format&fit=crop"
                ok, detail = fetch(url, dest)
                print(f"[{prod}] avatar-{n} {pid[:22]}... -> {'OK ' + detail if ok else 'FAIL ' + detail}")
                if not ok:
                    failures.append(f"{prod}/avatar-{n} {pid}: {detail}")
                    continue
            used.add(pid)
            manifest.setdefault(prod, {})[f"avatar-{n}"] = {"photo_id": pid, "local": local}
        # Each of the three shared avatar IDs maps to a different new portrait.
        avatar_winner = {
            old: f"/images/avatar-{i + 1}.jpg" for i, old in enumerate(sorted(AVATAR_IDS))
        }
        mapping.update(avatar_winner)

        # 2. Scenic: every old scenic ID currently referenced.
        src = fe / "src"
        old_ids: set[str] = set()
        for f in src.rglob("*.jsx"):
            for m in URL_RE.finditer(f.read_text(encoding="utf-8", errors="replace")):
                if m.group(1) not in AVATAR_IDS:
                    old_ids.add(m.group(1))

        repl = REPLACE.get(prod, {})
        n = 0
        for old in sorted(old_ids):
            n += 1
            cands = list(repl.get(old, [])) + [old]
            winner: str | None = None
            for cand in cands:
                if cand in used and cand != old:
                    continue
                dest = imgdir / f"scene-{n}.jpg"
                local = f"/images/scene-{n}.jpg"
                if not args.rewrite_only and not dest.exists():
                    url = f"https://images.unsplash.com/{cand}?q=80&w=1600&auto=format&fit=crop"
                    ok, detail = fetch(url, dest)
                    print(f"[{prod}] scene-{n} {cand[:22]}... -> {'OK ' + detail if ok else 'FAIL ' + detail}")
                    if not ok:
                        dest.unlink(missing_ok=True)
                        continue
                winner = cand
                used.add(cand)
                manifest.setdefault(prod, {})[f"scene-{n}"] = {
                    "photo_id": cand,
                    "local": local,
                    "replaces": old,
                }
                break
            if winner is None:
                failures.append(f"{prod}/scene-{n} (replaces {old}): no candidate resolved")
            else:
                mapping[old] = f"/images/scene-{n}.jpg"

        # 3. Extras for the new sections.
        for e, pid in enumerate(EXTRA.get(prod, []), 1):
            if pid in used:
                continue
            dest = imgdir / f"extra-{e}.jpg"
            local = f"/images/extra-{e}.jpg"
            if not args.rewrite_only and not dest.exists():
                url = f"https://images.unsplash.com/{pid}?q=80&w=1600&auto=format&fit=crop"
                ok, detail = fetch(url, dest)
                print(f"[{prod}] extra-{e} {pid[:22]}... -> {'OK ' + detail if ok else 'FAIL ' + detail}")
                if not ok:
                    dest.unlink(missing_ok=True)
                    failures.append(f"{prod}/extra-{e} {pid}: {detail}")
                    continue
            used.add(pid)
            manifest.setdefault(prod, {})[f"extra-{e}"] = {"photo_id": pid, "local": local}

        # 4. Rewrite hotlinks to local paths.
        rewrites = 0
        for f in src.rglob("*.jsx"):
            text = f.read_text(encoding="utf-8", errors="replace")

            def sub(m: re.Match) -> str:
                pid = m.group(1)
                return mapping.get(pid, m.group(0))

            new, count = URL_RE.subn(sub, text)
            if count:
                f.write_text(new, encoding="utf-8", newline="\n")
                rewrites += count
        print(f"[{prod}] rewrote {rewrites} hotlinked refs -> local files")

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps({"products": manifest, "failures": failures}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"failures: {len(failures)}")
    for fl in failures:
        print("  FAIL:", fl)
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
