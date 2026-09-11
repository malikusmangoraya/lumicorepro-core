"""
Rebuild registry/images.json from the real local stock library.

Scans src/assets/images/{category}/ for every jpg/png/webp and produces a
registry entry with category mapping, industry keywords, and tag tokens.
Run: python ai-agent/scratch/rebuild_image_registry.py
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = PROJECT_ROOT / "src" / "assets" / "images"
REGISTRY = PROJECT_ROOT / "registry" / "images.json"

# category -> industry + tag keywords
CATEGORY_META = {
    "business": {"industries": ["business", "corporate", "saas", "agency"], "keywords": ["team", "meeting", "office", "corporate", "growth", "office", "executive", "workspace"]},
    "dashboard": {"industries": ["software", "saas", "dashboard"], "keywords": ["analytics", "dashboard", "user", "hero"]},
    "ecommerce": {"industries": ["ecommerce", "electronics", "shopping"], "keywords": ["product", "iphone", "macbook", "headphones", "laptop", "phone", "watch", "camera", "shopping"]},
    "education": {"industries": ["education", "lms", "course"], "keywords": ["student", "course", "library", "learning", "online"]},
    "fitness": {"industries": ["fitness", "gym"], "keywords": ["gym", "trainer", "workout", "class", "personal"]},
    "healthcare": {"industries": ["healthcare", "medical", "hospital"], "keywords": ["doctor", "hospital", "medical", "consult", "patient"]},
    "portfolio": {"industries": ["portfolio", "personal", "developer"], "keywords": ["workspace", "portfolio", "project", "code", "developer", "designer", "avatar"]},
    "realestate": {"industries": ["realestate", "property"], "keywords": ["house", "villa", "property", "interior", "agent", "home"]},
    "restaurant": {"industries": ["restaurant", "cafe", "food"], "keywords": ["dish", "chef", "dining", "food", "restaurant", "interior"]},
    "travel": {"industries": ["travel", "hotel", "tourism"], "keywords": ["travel", "destination", "resort", "beach", "mountain", "tour", "flight"]},
    "creative": {"industries": ["creative", "studio"], "keywords": ["studio", "team", "agency", "creative", "art"]},
}

# Keep the original premium remote products as well (they enrich electronics rows)
def build_entries(category_dir: Path, category: str) -> list:
    meta = CATEGORY_META.get(category, {"industries": [category], "keywords": []})
    entries = []
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    pool = []
    for ext in exts:
        pool.extend(sorted(category_dir.glob(ext)))
    for img in sorted(pool, key=lambda p: p.name):
        stem = img.stem.replace("_", "-")
        name = " ".join(img.stem.replace("_", " ").replace("-", " ").strip().title().split())
        tags = list(meta["keywords"])
        for tok in re.split(r"[-_ ]", stem):
            tok = tok.lower().strip()
            if tok and len(tok) > 2 and tok not in tags:
                tags.append(tok)
        rel = f"src/assets/images/{category}/{img.name}"
        entries.append({
            "name": name,
            "type": "image",
            "category": category,
            "industry": meta["industries"][0],
            "industries": meta["industries"],
            "tags": tags[:16],
            "file_path": rel,
            "width": 0,
            "height": 0,
        })
    return entries


def main() -> None:
    if not IMAGES_DIR.exists():
        print(f"Images dir not found: {IMAGES_DIR}")
        sys.exit(1)

    all_entries = []
    for category_dir in sorted(IMAGES_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        entries = build_entries(category_dir, category_dir.name)
        all_entries.extend(entries)
        print(f"{category_dir.name}: {len(entries)} images")

    # Keep the high-quality remote Unsplash products at the front (they get
    # streamed/downloaded at build time via ImageService)
    registry_path = REGISTRY
    if registry_path.exists():
        try:
            old = json.loads(registry_path.read_text(encoding="utf-8"))
            remote = [e for e in old if str(e.get("file_path", "")).startswith("http")]
            all_entries = remote + all_entries
        except Exception:
            pass

    REGISTRY.write_text(json.dumps(all_entries, indent=2), encoding="utf-8")
    print(f"\nTotal registry entries: {len(all_entries)}")
    print(f"Written: {REGISTRY}")
    print(f"Local (copyable) entries: {sum(1 for e in all_entries if not str(e['file_path']).startswith('http'))}")


if __name__ == "__main__":
    main()