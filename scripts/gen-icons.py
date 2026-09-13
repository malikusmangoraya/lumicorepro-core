"""Generate original UI icon SVGs into src/icons/ and refresh registry/icons.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, "src", "icons")
os.makedirs(ICON_DIR, exist_ok=True)

ICONS = {
    "smartphone": '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
    "laptop": '<rect x="4" y="4" width="16" height="11" rx="2"/><path d="M2 19h20l-2-2H4z"/>',
    "headphones": '<path d="M4 14v-3a8 8 0 0 1 16 0v3"/><rect x="2" y="14" width="5" height="7" rx="1.5"/><rect x="17" y="14" width="5" height="7" rx="1.5"/>',
    "smartwatch": '<rect x="6" y="6" width="12" height="12" rx="2.5"/><path d="M9 2h6l-1 4M9 22h6l-1-4"/><path d="M11 11l2 2 3-3"/>',
    "television": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 3l3 3 3-3"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2z"/><circle cx="12" cy="14" r="4"/>',
    "speaker": '<rect x="7" y="2" width="10" height="20" rx="2"/><circle cx="12" cy="8" r="2"/><path d="M12 15a2 2 0 1 0 0 .01"/>',
    "gamepad": '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 11v4M5 13h4"/><circle cx="16" cy="12" r="0.6" fill="currentColor"/><circle cx="18.5" cy="14" r="0.6" fill="currentColor"/>',
    "shopping-cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h2l2.5 12h11l2-8H5"/>',
    "heart": '<path d="M12 20s-7-4.5-9-9a5 5 0 0 1 9-3.5A5 5 0 0 1 21 11c-2 4.5-9 9-9 9z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.5-6 8-6s8 2 8 6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/>',
    "shield-check": '<path d="M12 2l7 3v6c0 5-3.5 8.5-7 11-3.5-2.5-7-6-7-11V5z"/><path d="M9 12l2 2 4-4"/>',
    "truck": '<path d="M2 6h12v10H2zM14 10h4l4 4v2h-4"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
}

entries = []
for name, body in ICONS.items():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
        f"  {body}\n"
        "</svg>\n"
    )
    p = os.path.join(ICON_DIR, f"{name}.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    industry = "electronics" if name in ("smartphone", "laptop", "headphones", "smartwatch", "television", "camera", "speaker", "gamepad") else "general"
    entries.append(
        {
            "name": name.replace("-", " ").title() + " Icon",
            "type": "icon",
            "category": "ecommerce" if industry == "electronics" else "general",
            "industry": industry,
            "tags": [name, "icon", "ui", "vector"],
            "file_path": os.path.join("src", "icons", f"{name}.svg").replace(os.sep, "/"),
        }
    )

with open(os.path.join(ROOT, "registry", "icons.json"), "w", encoding="utf-8") as fh:
    json.dump(entries, fh, indent=2)

print(f"wrote {len(entries)} icons to src/icons/ and registry/icons.json")