"""asset_gen — keyless free image generation for generated projects.

Pollinations Image (GET image.pollinations.ai/prompt/…) returns a JPEG with no
API key. Generated projects get brand-grade imagery only where something is
missing: OG share image, hero/background image, favicon raster fallback.

All functions are honest about failures and never overwrite real artwork.
"""
from __future__ import annotations

import os
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

try:  # works both as `agent.asset_gen` and as a direct script
    from agent.extensions.built_with_badge import _brand_name  # reuse brand slug
except ImportError:
    from extensions.built_with_badge import _brand_name

IMAGE_BASE = os.getenv("POLLINATIONS_IMAGE_BASE", "https://image.pollinations.ai")
_RETRIEVE_TIMEOUT = 180


def image_url(prompt: str, width: int = 1200, height: int = 630, seed: int = None) -> str:
    """Deterministic keyless image URL — fetch it to obtain the JPEG bytes."""
    from urllib.parse import quote
    q = f"?width={int(width)}&height={int(height)}&nologo=true"
    if seed is not None:
        q += f"&seed={int(seed)}"
    return f"{IMAGE_BASE}/prompt/{quote(prompt)}{q}"


_IMAGE_RETRIES = 3          # free tier serves ~1 image per short window;
_IMAGE_RETRY_WAIT = 30      # HTTP 402 means "rate window" — wait and retry


def _fetch(url: str, out: Path) -> Dict[str, Any]:
    for attempt in range(_IMAGE_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lumicorepro-agent/1.0"})
            with urllib.request.urlopen(req, timeout=_RETRIEVE_TIMEOUT) as resp:
                data = resp.read(8 << 20)
            if len(data) < 2000 or not data[:3].startswith((b"\xff\xd8", b"\x89PN")):
                return {"status": "failed", "message": f"unexpected image payload ({len(data)} bytes)"}
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            return {"status": "ok", "file": str(out), "bytes": len(data)}
        except Exception as exc:  # noqa: BLE001
            if "402" in str(exc) and attempt < _IMAGE_RETRIES - 1:
                time.sleep(_IMAGE_RETRY_WAIT)
                continue
            return {"status": "failed", "message": str(exc)[:160]}
    return {"status": "failed", "message": "image generation exhausted retries"}


def generate_image(prompt: str, out_path: str, width: int = 1200,
                   height: int = 630, seed: int = None) -> Dict[str, Any]:
    """One keyless image into ``out_path`` (JPEG)."""
    if not prompt or len(prompt) < 8:
        return {"status": "failed", "message": "prompt too short"}
    return _fetch(image_url(prompt, width, height, seed), Path(out_path))


def _public_dir(project_dir: Path) -> Path:
    for cand in ("frontend/public", "public"):
        p = project_dir / cand
        if p.exists():
            return p / "images" / "generated" if cand.startswith("frontend") else p / "images" / "generated"
    return project_dir / "public" / "images"


def gen_project_images(project_dir: str, brand: str = None,
                       industry: str = "modern business", force: bool = False) -> Dict[str, Any]:
    """Fill the project's image gaps with generated (keyless, free) imagery.

    Targets (only when missing unless force=True):
      og-image.jpg   1200×630  social share card
      hero.jpg       1600×900  landing hero backdrop
      og-image.png equivalent NOT reused — extensions decide display.
    """
    root = Path(project_dir)
    if not root.exists():
        return {"status": "failed", "message": "project dir missing"}
    brand = brand or _brand_name(str(root))
    public = _public_dir(root)
    stamps: List[Dict[str, Any]] = []
    seed_base = int(time.time()) % 10_000

    wants = [
        ("og-image.jpg", f"Professional {industry} brand image for {brand}, premium website share card, elegant colors, no text", 1200, 630),
        ("hero.jpg", f"High-end {industry} hero photograph for {brand}, modern workspace, cinematic light, no text", 1200, 630),
    ]  # 1200×630 = Pollinations free tier ceiling; larger sizes answer HTTP 402
    total_ok = 0
    for i, (name, prompt, w, h) in enumerate(wants):
        target = public / name
        if target.exists() and not force:
            stamps.append({"target": name, "status": "skipped", "reason": "exists"})
            continue
        out = _fetch(image_url(prompt, w, h, seed=seed_base + i), target)
        stamps.append({"target": name, **out})
        if out["status"] == "ok":
            total_ok += 1
            agent_logger.info("asset_gen: %s → %s (%s bytes)", target.name, root.name, out.get("bytes"))
    return {"status": "passed" if total_ok or any(s.get("status") == "skipped" for s in stamps) else "failed",
            "generated": total_ok, "results": stamps, "dir": str(public)}
