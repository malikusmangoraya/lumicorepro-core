import sqlite3, os
from pathlib import Path

db_path = Path("ai-agent/database/lumicore_registry.db")
candidates = [db_path] + list(Path("ai-agent").rglob("*.db"))
print("DB candidates:", [str(p) for p in candidates])

conn = None
for p in candidates:
    try:
        t = sqlite3.connect(str(p))
        rows = t.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if any("components" in (r[0] or "") for r in rows):
            conn = t
            print("Using:", p, "| tables:", [r[0] for r in rows])
            break
    except Exception as e:
        pass

if not conn:
    print("NO db found"); raise SystemExit

comp = conn.execute("SELECT name, category, file_path, tags FROM components_index").fetchall()
print(f"REGISTERED COMPONENTS: {len(comp)}")
disk_root = Path("src/components")
missing = []
for name, cat, path, tags in comp:
    rel = (path or "").replace("@/components/", "")
    if not rel:
        rel = f"{cat}/{name}.jsx"
    fpath = disk_root / rel
    if not fpath.exists():
        missing.append((name, cat, rel))
print(f"MISSING ON DISK: {len(missing)}")
for name, cat, rel in sorted(missing, key=lambda x: x[1]):
    print(f"  [{cat:12s}] {rel}")