"""asset_wire — make generated projects self-contained and use their own artwork.

Two jobs, run together via ``wire_assets``:

1. ``localize_images``   — remote hotlinks (Unsplash/Pexels/Picsum) inside
   ``src/**`` + ``index.html`` are downloaded once, stored under
   ``frontend/public/images/local/`` (WebP via Pillow when smaller, else JPEG)
   and every reference is rewritten to the local absolute path. Hotlinked
   images die on rate limits and break offline clones — a sellable project
   must carry its images.
2. ``wire_generated``    — the agent-generated artwork is actually used:
   ``og:image`` points at the local generated OG card, and the first eager
   hero ``<img>`` in the home page gets the generated hero photo.

Never touches real artwork already on disk; only rewrites remote references.
"""
from __future__ import annotations

import hashlib
import io
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # works both as `agent.extensions.asset_wire` and as a direct script
    from agent.extensions.built_with_badge import _brand_name
except ImportError:
    from extensions.built_with_badge import _brand_name

_REMOTE_HOSTS = (
    r"(?:images\.unsplash\.com|images\.pexels\.com|picsum\.photos|"
    r"source\.unsplash\.com|cdn\.pixabay\.com|upload\.wikimedia\.org)"
)
_REMOTE_URL = re.compile(rf"https://{_REMOTE_HOSTS}[^\"'\s)]+", flags=re.I)
_SCAN_EXT = (".jsx", ".tsx", ".js", ".ts", ".html", ".css")
_SKIP_DIRS = {"node_modules", "dist", "build", ".git", "coverage"}
_PUBLIC_SRC = "images/local"
_MAX_BYTES = 8 << 20
_MAX_IMAGES = 48
_UA = "lumicorepro-agent/1.0"


def _scan_files(root: Path) -> List[Path]:
    """Frontend tree only — backend seed URLs are buyer data and cannot serve
    a path that lives inside the frontend's public folder."""
    bases: List[Path] = []
    for cand in ("frontend", "."):
        p = root / cand
        if p.is_dir():
            bases.append(p)
        if cand == "frontend":
            break  # dedicated frontend dir: skip everything beside it
    out: List[Path] = []
    for base in bases:
        for cur, dirs, files in base.walk():
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            for name in files:
                p = cur / name
                if p.suffix.lower() in _SCAN_EXT:
                    out.append(p)
    return out


def _public_dir(root: Path) -> Path:
    cand = root / "frontend" / "public"
    if cand.exists():
        return cand
    p = root / "public"
    return p if p.exists() else (root / "frontend" / "public")


def _download(url: str, timeout: int = 20) -> bytes:
    """Fetch one remote image; returns bytes or raises."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read(_MAX_BYTES)
    if len(data) < 1000 or not data[:4].startswith((b"\xff\xd8", b"\x89PN", b"RIFF")):
        raise ValueError(f"not an image payload ({len(data)} bytes)")
    return data


def _to_webp(data: bytes) -> Optional[bytes]:
    """Pillow WebP transcode; None when Pillow is missing or transcode grows."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=82, method=4)
        webp = buf.getvalue()
        return webp if 0 < len(webp) < len(data) else None
    except Exception:  # noqa: BLE001 — corrupt/animated input: keep original bytes
        return None


def _slug(url: str, seen: Dict[str, str]) -> str:
    if url in seen:
        return seen[url]
    tail = url.rstrip("/?").split("?")[0].rstrip("/").split("/")[-1] or "image"
    tail = re.sub(r"[^A-Za-z0-9._-]", "", tail)[:24] or "image"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    name = f"{tail}-{digest}"
    seen[url] = name
    return name


def localize_images(project_dir: str, timeout: int = 20) -> Dict[str, Any]:
    """Download remote images and rewrite every reference to local paths."""
    root = Path(project_dir)
    if not root.exists():
        return {"status": "failed", "message": "project dir missing"}
    public = _public_dir(root)
    out_dir = public / "images" / "local"
    name_of: Dict[str, str] = {}
    ext_of: Dict[str, str] = {}
    downloaded: List[str] = []
    failed: List[Dict[str, str]] = []
    rewritten = 0

    for path in _scan_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = _REMOTE_URL.findall(text)
        if not hits:
            continue
        new_text = text
        for url in _sorted_unique(hits):
            if "${" in url or "`" in url:
                continue  # inside a template literal — not a real request
            fname = _slug(url, name_of)
            if fname not in ext_of:
                cached = _existing(out_dir, fname)
                if cached:
                    ext_of[fname] = cached  # earlier run: reuse, no re-download
                elif len(downloaded) >= _MAX_IMAGES:
                    name_of.pop(url, None)
                    continue  # cap applies to fresh downloads only
            if fname not in ext_of:
                try:
                    data = _download(url, timeout=timeout)
                except Exception as exc:  # noqa: BLE001
                    failed.append({"url": url[:120], "error": str(exc)[:120]})
                    name_of.pop(url, None)
                    continue
                ext = ".webp"
                payload = _to_webp(data)
                if payload is None:
                    ext, payload = ".jpg", data
                ext_of[fname] = ext
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"{fname}{ext}").write_bytes(payload)
                downloaded.append(f"{fname}{ext}")
            new_text = new_text.replace(url, f"/{_PUBLIC_SRC}/{fname}{ext_of[fname]}")
            rewritten += 1
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    return {
        "status": "ok" if not failed else "partial",
        "downloaded": len(downloaded),
        "rewritten_refs": rewritten,
        "failed": failed,
        "files": downloaded,
    }


def _existing(out_dir: Path, fname: str) -> Optional[str]:
    """Extension of a previously downloaded copy, or None."""
    for ext in (".webp", ".jpg"):
        if (out_dir / f"{fname}{ext}").exists():
            return ext
    return None


def _sorted_unique(hits: List[str]) -> List[str]:
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def _find_generated(public: Path) -> Dict[str, str]:
    """Locate existing generated artwork (og card / hero photo)."""
    found: Dict[str, str] = {}
    for rel, keys in (
        ("images/generated/og-image.jpg", ("og",)),
        ("og.jpg", ("og",)),
        ("og-image.svg", ("og",)),
        ("images/generated/hero.jpg", ("hero",)),
    ):
        p = public / rel
        if p.exists() and not found.get("og" if "og" in keys else "hero"):
            found.setdefault("og" if "og" in keys else "hero", f"/{rel}")
    return found


def _rewire_og(html_path: Path, og_url: str, brand: str) -> bool:
    html = html_path.read_text(encoding="utf-8", errors="replace")
    orig = html
    if 'property="og:image"' in html or "property='og:image'" in html:
        html = re.sub(
            r'(<meta\s+property=["\']og:image["\']\s+content=["\'])[^"\']*(["\'])',
            lambda m: f"{m.group(1)}{og_url}{m.group(2)}",
            html, flags=re.I)
    else:
        html = html.replace("</head>",
            f'    <meta property="og:image" content="{og_url}"/>\n'
            f'    <meta property="og:title" content="{brand}"/>\n'
            f'    <meta property="og:description" content="{brand} — production-ready '
            'full-stack project"/>\n    <meta property="og:type" content="website"/>\n'
            "  </head>", 1)
    if html != orig:
        html_path.write_text(html, encoding="utf-8")
        return True
    return False


def _rewire_hero(page: Path, hero_url: str) -> bool:
    """Swap the first eager hero <img>'s src for the generated photo."""
    m = re.search(r"<img\b[^>]*loading=[\"']eager[\"'][^>]*>", page.read_text(
        encoding="utf-8", errors="replace"), flags=re.I)
    if not m:
        return False
    tag = m.group(0)
    if "src=" not in tag:
        return False
    new_tag, n = re.subn(r"src=(\"|')[^\"']*\1", f'src="{hero_url}"', tag, count=1)
    if n != 1:
        return False
    text = page.read_text(encoding="utf-8", errors="replace")
    if new_tag in text:
        return False  # already wired
    page.write_text(text.replace(tag, new_tag, 1), encoding="utf-8")
    return True


def _home_page(root: Path) -> Optional[Path]:
    pages = sorted((root / "frontend" / "src" / "pages").glob("*ome*.jsx"))
    if not pages:
        pages = sorted((root / "src" / "pages").glob("*ome*.jsx"))
    for p in pages:
        if p.exists() and p.suffix == ".jsx":
            return p
    return None


def wire_generated(project_dir: str) -> Dict[str, Any]:
    """Point og:image and the hero <img> at the project's own generated art."""
    root = Path(project_dir)
    if not root.exists():
        return {"status": "failed", "message": "project dir missing"}
    public = _public_dir(root)
    art = _find_generated(public)
    actions: List[str] = []
    index = None
    for cand in ("frontend/index.html", "index.html"):
        p = root / cand
        if p.exists():
            index = p
            break
    if art.get("og") and index:
        if _rewire_og(index, art["og"], _brand_name(str(root))):
            actions.append(f"og:image={art['og']}")
    if art.get("hero"):
        page = _home_page(root)
        if page and _rewire_hero(page, art["hero"]):
            actions.append(f"hero={art['hero']}")
    return {"status": "ok", "art": art, "wired": actions,
            "message": "; ".join(actions) if actions else "art already wired or absent"}


def wire_assets(project_dir: str, timeout: int = 20) -> Dict[str, Any]:
    """One-shot: localize remote images, then wire generated artwork."""
    local = localize_images(project_dir, timeout=timeout)
    wired = wire_generated(project_dir)
    return {"status": "ok" if local.get("status") == "ok" else "partial",
            "localize": local, "wire": wired}
