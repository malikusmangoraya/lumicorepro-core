"""Find existing live GitHub Pages / deploy links across the repo (fast)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_RE = re.compile(r"https?://[^\s'\"><)]+")
SKIP_PARTS = ("node_modules", ".git", "delivery", "/dist", ".zip", ".png", ".jpg", ".svg", ".woff", ".eot", "__pycache__", ".venv", "package-lock", "bundle")
LOOK = (".md", ".txt", ".json", ".html")

FOUND = {}


def walk(base):
    try:
        it = base.rglob("*")
        for f in it:
            sp = str(f)
            if not f.is_file() or any(x in sp for x in SKIP_PARTS):
                continue
            if f.suffix.lower() not in LOOK:
                continue
            yield f
    except Exception:
        return


seen = set()
for base in [ROOT / "generated-projects", ROOT, ROOT / "scripts", ROOT / "docs"]:
    for f in walk(base):
        if id(f) in seen:
            continue
        seen.add(id(f))
        try:
            t = f.read_text(errors="ignore")
        except Exception:
            continue
        for m in URL_RE.findall(t):
            u = m.strip().strip(".,;:)]}")
            if any(k in u for k in ("github.io", "pages.dev", "vercel.app", "netlify.app")):
                rel = f.relative_to(ROOT)
                FOUND.setdefault(str(rel), set()).add(u)

for path, urls in sorted(FOUND.items()):
    for u in sorted(urls):
        print(f"{path} => {u}")
print("total:", sum(len(v) for v in FOUND.values()))