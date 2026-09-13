"""
ImageService — unified image provisioning for generated projects.

Resolution order (best → worst):
  1. Local stock library (src/assets/images/{category}/) — pre-downloaded real photos
  2. Registry remote URLs — cached download into the project at build time
  3. AI image generation — Gemini/Imagen if an image key is configured
  4. Deterministic SVG placeholder — original vector art (no external dependency)

Each generated project therefore always ends up with real, local image files
in frontend/src/assets/images/ — never dangling remote URLs.
"""
import os
import re
import time
import hashlib
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config.settings import PROJECT_ROOT, ASSETS_DIR
from utils.logger import agent_logger
from utils.file_manager import FileManager

# ── Industry → local stock category mapping ──────────────────────────────────
INDUSTRY_CATEGORY_MAP = {
    "business": "business",
    "corporate": "business",
    "agency": "business",
    "consulting": "business",
    "lawfirm": "business",
    "nonprofit": "business",
    "ecommerce": "ecommerce",
    "electronics": "ecommerce",
    "fashion": "ecommerce",
    "electronics": "ecommerce",
    "realestate": "realestate",
    "property": "realestate",
    "restaurant": "restaurant",
    "cafe": "restaurant",
    "food": "restaurant",
    "portfolio": "portfolio",
    "personal": "portfolio",
    "education": "education",
    "lms": "education",
    "course": "education",
    "healthcare": "healthcare",
    "medical": "healthcare",
    "hospital": "healthcare",
    "fitness": "fitness",
    "gym": "fitness",
    "travel": "travel",
    "agency-travel": "travel",
    "creative": "creative",
    "studio": "creative",
    "saas": "saas",
    "dashboard": "dashboard",
    "software": "saas",
    "fintech": "fintech",
    "ai": "ai",
    "ml": "ai",
    "artificial-intelligence": "ai",
}

# Total count of files in the stock library
STOCK_CATEGORIES = [
    "business", "dashboard", "ecommerce", "education", "fitness",
    "healthcare", "portfolio", "realestate", "restaurant", "travel", "creative",
    "ai", "saas", "fintech",
]


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()


def _download(url: str, dst: Path, timeout: int = 20) -> bool:
    """Download a remote image to a local path with a browser User-Agent."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=timeout).read()
        if not data:
            return False
        FileManager.ensure_dir(str(dst.parent))
        dst.write_bytes(data)
        agent_logger.info(f"ImageService: downloaded {dst.name} ({len(data)} bytes)")
        return True
    except Exception as exc:
        agent_logger.warning(f"ImageService: download failed {url}: {exc}")
        return False


def _svg_placeholder(frontend_dir: Path, title: str, hue: str = "#6366f1") -> Tuple[str, str]:
    """Deterministic original SVG fallback. Returns (rel_path, abs_path)."""
    assets_dir = frontend_dir / "src" / "assets" / "images" / "placeholders"
    FileManager.ensure_dir(str(assets_dir))
    seed = int(hashlib.sha1(title.encode("utf-8")).hexdigest()[:8], 16)
    h1 = f"#{seed:06x}"
    h2 = f"{int(h1[1:3], 16):02x}{int(h1[3:5], 16):02x}ff"
    safe = _slugify(title)[:40] or "placeholder"
    fname = f"{safe}.svg"
    content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{h1}"/>
      <stop offset="100%" stop-color="#{h2}"/>
    </linearGradient>
    <radialGradient id="s" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="800" fill="url(#g)"/>
  <rect width="1200" height="800" fill="url(#s)"/>
  <circle cx="940" cy="150" r="120" fill="#ffffff" opacity="0.08"/>
  <circle cx="250" cy="680" r="180" fill="#000000" opacity="0.08"/>
  <text x="600" y="410" text-anchor="middle" font-family="Arial, Helvetica, sans-serif"
        font-size="56" font-weight="600" fill="#ffffff" opacity="0.92">{title}</text>
  <text x="600" y="460" text-anchor="middle" font-family="Arial, Helvetica, sans-serif"
        font-size="24" fill="#ffffff" opacity="0.6">LumiCorePro Generated Asset</text>
</svg>"""
    abs_path = assets_dir / fname
    FileManager.write_file(str(abs_path), content)
    return f"assets/images/placeholders/{fname}", str(abs_path)


class ImageService:
    """Provides real, local image files for generated projects."""

    def __init__(self, spec: Optional[Dict[str, Any]] = None, can_generate_ai: bool = False):
        self.spec = spec or {}
        self.can_generate_ai = can_generate_ai

    # ── Stock library ─────────────────────────────────────────────────────────
    def stock_category(self) -> str:
        industry = (self.spec.get("industry") or "general").lower().strip()
        category = INDUSTRY_CATEGORY_MAP.get(industry)
        if category:
            return category
        for key, cat in INDUSTRY_CATEGORY_MAP.items():
            if key in industry:
                return cat
        return "business"

    def list_stock_images(self, category: Optional[str] = None) -> List[Path]:
        cat = category or self.stock_category()
        cat_dir = ASSETS_DIR / "images" / cat
        if not cat_dir.exists():
            cat_dir = ASSETS_DIR / "images" / "business"
        images = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            images.extend(list(cat_dir.glob(ext)))
        images.sort(key=lambda p: p.name)
        return images

    def pick_stock(self, count: int = 6, category: Optional[str] = None) -> List[Path]:
        """Deterministically pick popular (stable-order) stock photos."""
        images = self.list_stock_images(category)
        if not images:
            return []
        seed = int(hashlib.sha1((self.spec.get("project_name") or "site").encode()).hexdigest()[:8], 16)
        stride = max(1, len(images) // max(1, count))
        picked = []
        for i in range(min(count, len(images))):
            idx = (seed + i * stride) % len(images)
            if images[idx] not in picked:
                picked.append(images[idx])
        return picked or images[:count]

    # ── Registry resolution ───────────────────────────────────────────────────
    def resolve_registry_item(self, item: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Given a registry asset dict, return (copy_src, filename).
        Handles local paths AND remote URLs. Returns None if unusable."""
        file_path = (item.get("file_path") or "").strip()
        if not file_path:
            return None
        filename = item.get("name") or os.path.basename(file_path.split("?")[0])
        filename = _slugify(os.path.splitext(filename)[0]) + ".jpg"
        if file_path.startswith(("http://", "https://")):
            return file_path, filename  # marker: needs download
        src = (PROJECT_ROOT / file_path).resolve()
        if src.exists():
            return str(src), src.name
        return None

    # ── AI generation (optional) ──────────────────────────────────────────────
    def ai_generate(self, prompt: str, filename: str, frontend_dir: Path) -> Optional[str]:
        """Generate an image via Gemini image API if configured. Returns rel path or None."""
        key = os.getenv("GEMINI_IMAGE_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            return None
        try:
            import urllib.parse
            from config.settings import GEMINI_MODEL
            model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.0-flash-preview-image-generation")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
                f":generateContent?key={key}"
            )
            body = {
                "contents": [{"parts": [{"text": prompt + " (photorealistic, high quality, no text overlay)"}]}],
                "generationConfig": {"responseModalities": ["IMAGE"]},
            }
            import json as _json
            payload = _json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = _json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
            parts = (
                resp.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            for part in parts:
                if "inlineData" in part:
                    import base64
                    img_bytes = base64.b64decode(part["inlineData"]["data"])
                    dst = frontend_dir / "src" / "assets" / "images" / "generated" / filename
                    FileManager.ensure_dir(str(dst.parent))
                    dst.write_bytes(img_bytes)
                    agent_logger.info(f"ImageService: AI-generated {filename} ({len(img_bytes)} bytes)")
                    return f"assets/images/generated/{filename}"
        except Exception as exc:
            agent_logger.warning(f"ImageService: AI generation failed ({exc})")
        return None

    # ── Main provisioning ─────────────────────────────────────────────────────
    def provision(self, plan: Dict[str, Any], frontend_dir: Path) -> Dict[str, Any]:
        """Copy real images into the generated frontend. Returns manifest.

        Manifest shape:
          {
            "copied":     [ {"name": ..., "file": "assets/images/..."} ],
            "downloaded": [ {"name": ..., "file": "assets/images/..."} ],
            "generated":  [ {"name": ..., "file": "assets/images/..."} ],
            "fallbacks":  [ {"name": ..., "file": "assets/images/..."} ],
            "images_dir": "src/assets/images",
          }
        """
        assets = plan.get("assets", {})
        registry_images = assets.get("images", [])
        target = frontend_dir / "src" / "assets" / "images"
        target_rel = "src/assets/images"
        result: Dict[str, List[Dict[str, str]]] = {
            "copied": [], "downloaded": [], "generated": [], "fallbacks": [],
        }

        # ── Layer 1+2: bounded registry copies (category-matched, up to 8) ───
        category = self.stock_category()
        category_items = [i for i in registry_images if (i.get("category") or "") == category]
        if len(category_items) < 4:
            category_items = registry_images  # fall back to all registrations
        for item in category_items[:12]:
            resolved = self.resolve_registry_item(item)
            if not resolved:
                continue
            src, fname = resolved
            dst = target / fname
            if src.startswith(("http://", "https://")):
                if _download(src, dst):
                    result["downloaded"].append({"name": fname, "file": f"{target_rel}/{fname}"})
            else:
                try:
                    FileManager.ensure_dir(str(target))
                    if Path(src).exists() and not dst.exists():
                        FileManager.copy_file(src, str(dst))
                    result["copied"].append({"name": fname, "file": f"{target_rel}/{fname}"})
                except Exception as exc:
                    agent_logger.warning(f"ImageService: copy failed {src} ({exc})")

        # ── Layer 1b: backfill with the real local stock library ─────────────
        if len(result["copied"]) + len(result["downloaded"]) < 4:
            for stock in self.pick_stock(6):
                dst = target / stock.name
                FileManager.copy_file(str(stock), str(dst))
                result["copied"].append({"name": stock.stem, "file": f"{target_rel}/{stock.name}"})

        # ── Layer 3: AI generation for missing hero imagery ──────────────────
        if self.can_generate_ai and not result["generated"]:
            industry = self.spec.get("industry", "modern business website")
            prompt = f"High-quality hero image for a {industry} website, photorealistic, professional, 16:9"
            gen = self.ai_generate(prompt, f"ai-hero-{int(time.time())}.jpg", frontend_dir)
            if gen:
                result["generated"].append({"name": "ai-hero", "file": gen})

        # ── Layer 4: deterministic SVG fallbacks (always present) ────────────
        hero_title = (self.spec.get("project_name") or "Welcome").replace("-", " ").title()
        rel, _ = _svg_placeholder(frontend_dir, hero_title or "Welcome")
        result["fallbacks"].append({"name": "hero-fallback", "file": rel})

        counts = {k: len(v) for k, v in result.items()}
        agent_logger.info(f"ImageService: provisioned -> {counts}")
        result["images_dir"] = target_rel
        return result


def provision_images(plan: Dict[str, Any], frontend_dir: Path, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience wrapper — defaults spec to plan so industry selection works."""
    svc = ImageService(spec or plan)
    return svc.provision(plan, frontend_dir)