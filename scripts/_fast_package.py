"""Fast delivery packaging - creates delivery folders + ZIPs for all projects."""
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "generated-projects"
OUT = ROOT / "delivery-new"

def make_readme(slug, name):
    return f"""# {name}

Full-stack generated project.

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
npm install
cp .env.example .env
npm run dev
```

## Structure
- `frontend/` - React + Vite + Tailwind
- `backend/` - Express + PostgreSQL + Redis
- `database/` - Schema SQL
- `dist/` - Built frontend

## Deployment
See DEPLOY.md for full instructions.
"""

def make_deploy(slug):
    return f"""# Deployment Guide

## Frontend (Vite + React)
```bash
cd frontend
npm run build
# Deploy dist/ to Netlify/Vercel/GitHub Pages
```

## Backend (Express)
```bash
cd backend
npm install
cp .env.example .env
# Set DATABASE_URL, REDIS_URL, JWT_SECRET
npm start
```

## Environment Variables
See `.env.example` for all required variables.
"""

def make_env_example():
    return """# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-secret-key-here
JWT_REFRESH_SECRET=your-refresh-secret-here
JWT_EXPIRE=15m
JWT_REFRESH_EXPIRE=7d

# App
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:5173
"""

def package_project(slug):
    proj = GEN / slug
    if not proj.exists():
        return None
    
    dest = OUT / slug
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    
    # Copy essential directories
    for d in ["frontend/dist", "frontend/src", "backend", "database"]:
        src = proj / d
        if src.exists():
            dst = dest / d.replace("frontend/", "").replace("frontend\\", "")
            if d == "frontend/dist":
                dst = dest / "dist"
            elif d == "frontend/src":
                dst = dest / "src"
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                "node_modules", ".git", "__pycache__", "*.pyc", ".pytest_cache"
            ))
    
    # Write metadata files
    (dest / "README.md").write_text(make_readme(slug, slug.replace("-", " ").title()), encoding="utf-8")
    (dest / "DEPLOY.md").write_text(make_deploy(slug), encoding="utf-8")
    (dest / ".env.example").write_text(make_env_example(), encoding="utf-8")
    (dest / "LIVE-LINK.txt").write_text("", encoding="utf-8")
    
    # Create ZIP
    zip_path = OUT / f"{slug}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in dest.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(dest))
    
    return slug

def main():
    slugs = sys.argv[1:] or [
        d.name for d in sorted(GEN.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    
    OUT.mkdir(exist_ok=True)
    
    ok = 0
    fail = 0
    for i, slug in enumerate(slugs):
        try:
            result = package_project(slug)
            if result:
                ok += 1
                if ok % 10 == 0:
                    print(f"  packaged {ok}/{len(slugs)}...")
            else:
                fail += 1
        except Exception as e:
            print(f"  FAIL {slug}: {e}")
            fail += 1
    
    print(f"\n=== DELIVERY PACKAGING COMPLETE ===")
    print(f"  OK: {ok}")
    print(f"  FAIL: {fail}")
    print(f"  Output: {OUT}")

if __name__ == "__main__":
    main()
