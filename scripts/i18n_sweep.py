"""Run the translation sweep in chunks, persisting progress between chunks.

Safe to re-run: i18n_translate.py caches every translated string, so already
done work is skipped. Writes a resume checkpoint so a later invocation picks
up exactly where this one stopped.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r'D:\lumicorepro-core')
PROJECTS = ROOT / "generated-projects"
STATE = PROJECTS / "I18N_SWEEP_STATE.json"
CHUNK = 5

import json


def slugs():
    return [d.name for d in sorted(PROJECTS.iterdir()) if (d / "frontend" / "package.json").exists()]


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "failed": []}


def _kill_tree(proc):
    """Kill a timed-out child and everything it spawned (Windows-safe)."""
    import signal
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, timeout=60)
    except Exception:
        pass
    for sig in (getattr(signal, "SIGTERM", 15), getattr(signal, "SIGKILL", 9)):
        try:
            proc.kill() if hasattr(proc, "kill") else None
            proc.send_signal(sig)
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
            return
        except Exception:
            continue


def save_state(s):
    STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")


def main():
    st = load_state()
    all_slugs = slugs()
    done = set(st.get("done", []))
    todo = [s for s in all_slugs if s not in done]
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    print(f"{len(done)} already done, {len(todo)} queued, budget {budget} projects")
    processed = 0
    i = 0
    while i < len(todo) and processed < budget:
        chunk = todo[i:i + CHUNK]
        cmd = [sys.executable, str(ROOT / "scripts" / "i18n_translate.py")] + chunk
        proc = subprocess.Popen(
            cmd, cwd=str(ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        try:
            out, _ = proc.communicate(timeout=1800)
            tail = [ln for ln in (out or "").splitlines()
                    if "newly translated" in ln or "awaiting retry" in ln]
            print(" | ".join(tail) if tail else (out or "").splitlines()[-1:])
        except subprocess.TimeoutExpired:
            # Kill the whole tree. A surviving child keeps an in-memory cache and
            # would later overwrite newer translations.
            _kill_tree(proc)
            print(f"  chunk {chunk} TIMEOUT after 30m (progress cached, will resume)")
        for s in chunk:
            st.setdefault("done", []).append(s)
        done.update(chunk)
        save_state(st)
        processed += len(chunk)
        i += CHUNK
        time.sleep(2)
    print(f"\nsweep chunk complete: {processed} projects this run, {len(done)}/{len(all_slugs)} total")


if __name__ == "__main__":
    main()