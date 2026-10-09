import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(r"C:\Users\AZAM COMPUTERS\OneDrive\Desktop\lumicorepro-core")
AGENT = ROOT / "ai-agent"
OUT = ROOT / "generated-projects"
sys.path.insert(0, str(AGENT))

from agent.gh_token import clean_token  # noqa: E402  (path set above)

for env_file in [(ROOT / ".env"), (AGENT / ".env")]:
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GITHUB_TOKEN="):
            os.environ.setdefault("GITHUB_TOKEN", clean_token(line.split("=", 1)[1]))

SLUGS = [
    "aurelia-estates", "maison-noir", "ember-salt", "saffron-voyage",
    "prestige-studio", "meridian-capital", "voltus-atelier",
    "aurum-fitness", "studio-lumen", "nuage-events",
]


def rezip(pdir: Path):
    zpath = OUT / f"{pdir.name}.zip"
    with ZipFile(zpath, "w", ZIP_DEFLATED) as zf:
        for f in pdir.rglob("*"):
            if f.is_file() and not any(
                part in {".git", "node_modules", "__pycache__", ".history"} for part in f.parts
            ):
                zf.write(f, f.relative_to(pdir))
    return zpath


def main():
    state_path = OUT / "campaign-results.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    projects = state.get("projects", {})
    for slug in SLUGS:
        pdir = OUT / slug
        proj = projects.get(next((k for k, v in projects.items() if v.get("project_name") == slug), ""), {})
        if not pdir.exists():
            print(f"SKIP {slug}: dir missing")
            continue
        t0 = time.time()
        from agent.extensions.animation_injector import inject_motion_layer
        inj = inject_motion_layer(str(pdir), intensity="high")
        if inj.get("status") != "injected":
            print(f"INJECT FAIL {slug}: {inj.get('reason', inj)}")
            continue
        build = subprocess.run(
            "npm run build",
            cwd=str(pdir / "frontend"),
            capture_output=True,
            text=True,
            timeout=600,
            shell=True,
        )
        built = "error during build" not in (build.stderr or "") and (pdir / "frontend" / "dist" / "index.html").exists()
        print(f"BUILD {slug}: ok={built} ({round(time.time()-t0,1)}s)")
        if built:
            zpath = rezip(pdir)
            from agent.deploy_engine import _github_pages_deploy
            dep = _github_pages_deploy(str(pdir))
            print(f"DEPLOY {slug}: {dep.get('status')} {dep.get('url') or dep.get('message')}")
            if proj:
                proj["motion"] = "lumi-mode-high"
                proj["zip"] = str(zpath)
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            print(f"DEPLOY SKIP {slug}: build failed\n{(build.stdout or build.stderr)[-600:]}")
    print("ALL DONE")


if __name__ == "__main__":
    main()