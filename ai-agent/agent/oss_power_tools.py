"""OSS power-up pack â€” internet-run, keyless quality/security tools.

Tools (all degrade gracefully; nothing requires local models or paid keys):
  secrets_scan()     â€” planted-credential regex audit of a project tree
  npm_audit()        â€” `npm audit --json` vulnerability summary
  license_report()   â€” npm registry license lookup per dependency (cached)
  lint_project()     â€” oxlint via npx (Rust-fast, free) with summary parsing
  a11y_audit()       â€” axe-core on a live URL through the repo's Playwright
  mermaid_doc()      â€” architecture.mmd blueprint for a generated project

The Ollama/vLLM/llama.cpp local runtimes are intentionally NOT here: the
operator runs no local GPU stack (see providers/openweight_provider.py).
"""
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

_SKIP_DIRS = {
    "node_modules", "dist", "build", ".git", "venv", "__pycache__",
    ".pytest_cache", "coverage", ".venv", ".next", "out",
}
_MAX_FILE_BYTES = 1_000_000  # skip huge minified bundles

_SECRETS = [
    tuple(("github_pat", re.compile(r"github_pat_[0-9A-Za-z_]{22,255}"))),
    tuple(("github_token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,255}\b"))),
    tuple(("openai_key", re.compile(r"\bsk-(?:proj-)?[0-9A-Za-z\-_]{20,200}\b"))),
    tuple(("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"))),
    tuple(("google_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"))),
    tuple(("slack_token", re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b"))),
    tuple(("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"))),
    tuple(("jwt", re.compile(r"\beryJ[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{15,}\b"))),
    tuple(("stripe_key", re.compile(r"\b(?:sk|pk)_(?:live|test)_[0-9A-Za-z]{20,}\b"))),
    tuple(("npm_token", re.compile(r"npm_[0-9A-Za-z]{36}"))),
]  # type: List[tuple]
_SECRETS = [(k, v) for k, v in _SECRETS]

_GITKEEP_HINTS = ("example", "placeholder", "sample", "xxxxx", "your_api_key", "your_", "<key>")

# licenses barred from commercial resale kits
_COPYLEFT = ("gpl", "agpl", "sspl", "eula", "unlicense")


def _iter_files(project_dir: str, exts: List[str] = None) -> List[Path]:
    root = Path(project_dir)
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".vercel")]
        for name in filenames:
            if name.endswith((".png", ".jpg", ".webp", ".svg", ".gif", ".woff", ".woff2", ".ttf", ".ico", ".pdf", ".zip")):
                continue
            if exts and not name.endswith(tuple(exts)):
                continue
            p = Path(dirpath) / name
            try:
                if p.stat().st_size <= _MAX_FILE_BYTES:
                    out.append(p)
            except OSError:
                continue
    return out


def secrets_scan(project_dir: str) -> Dict[str, Any]:
    """Scan every text file for planted credentials. Findings carry file+line+redacted match."""
    findings: List[Dict[str, Any]] = []
    files = _iter_files(project_dir)
    scanned = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned += 1
        low = text.lower()
        for kind, rx in _SECRETS:
            for m in rx.finditer(text):
                ctx = low[max(0, m.start() - 40):m.start()]
                if any(h in ctx or h in m.group(0).lower() for h in _GITKEEP_HINTS):
                    continue  # documented example, not a live secret
                line = text.count("\n", 0, m.start()) + 1
                val = m.group(0)
                findings.append({
                    "kind": kind,
                    "file": str(p.relative_to(project_dir)).replace("\\", "/"),
                    "line": line,
                    "match": val[:6] + "*" * 8 + val[-4:] if len(val) > 12 else "****",
                })
    return {"status": "passed" if not findings else "failed",
            "checked_files": scanned, "findings": findings[:50],
            "total_findings": len(findings)}


def npm_audit(project_dir: str, runner=None) -> Dict[str, Any]:
    """Vulnerability summary from `npm audit --json` (free, internet)."""
    frontend = _frontend_dir(project_dir)
    if not (frontend / "package-lock.json").exists():
        return {"status": "skipped", "reason": "no package-lock.json"}
    cmd = _win_cmd(["npm", "audit", "--json"])
    if runner:
        proc = runner(cmd, str(frontend))
        rc, out, err = proc
    else:
        try:
            proc = subprocess.run(cmd, cwd=str(frontend), capture_output=True,
                                  text=True, timeout=180, encoding="utf-8", errors="replace",
                                  shell=os.name == "nt")
        except (subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "message": str(exc)[:200]}
        rc, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
    try:
        data = json.loads(out)
    except ValueError:
        return {"status": "failed", "message": (err or out)[:200] or "npm audit produced no JSON"}
    counts = (data.get("metadata") or {}).get("vulnerabilities") or {}
    vulns = []
    for name, v in (data.get("vulnerabilities") or {}).items():
        vulns.append({"package": name, "severity": v.get("severity"),
                      "fix_available": bool((v.get("fixAvailable") is not True and v.get("fixAvailable")) or v.get("fixAvailable"))})
    return {"status": "passed" if not counts.get("total") else "warn",
            "counts": {k: counts.get(k, 0) for k in ("info", "low", "moderate", "high", "critical", "total")},
            "vulnerabilities": vulns[:30]}


def license_report(project_dir: str, runner=None, _cache: Dict[str, str] = {}) -> Dict[str, Any]:
    """License of each direct dependency via `npm view <pkg> license` (free)."""
    frontend = _frontend_dir(project_dir)
    pkg = frontend / "package.json"
    if not pkg.exists():
        return {"status": "skipped", "reason": "no package.json"}
    try:
        deps = list(json.loads(pkg.read_text(encoding="utf-8")).get("dependencies") or {})
    except (ValueError, OSError) as exc:
        return {"status": "failed", "message": str(exc)[:150]}

    def run_npm_view(name: str):
        cmd = _win_cmd(["npm", "view", name, "license"])
        if runner:
            return runner(cmd, str(frontend))
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=_LICENSE_TIMEOUT,
                                  encoding="utf-8", errors="replace", shell=os.name == "nt")
            return proc.returncode, proc.stdout or "", proc.stderr or ""
        except (subprocess.TimeoutExpired, OSError) as exc:
            return 1, "", str(exc)

    entries, flagged = [], []
    for dep in deps:
        if dep in _cache:
            lic = _cache[dep]
        else:
            rc, out, err = run_npm_view(dep)
            lic = (out or "").strip().splitlines()[0].strip() if rc == 0 and out.strip() else "UNKNOWN"
            _cache[dep] = lic
        if lic == "UNKNOWN":
            cached_err = True
            lic = None
            if runner is None:
                rc, out, err = run_npm_view(dep)
                lic = (out or "").strip().splitlines()[0].strip() if rc == 0 and out.strip() else None
                if lic:
                    _cache[dep] = lic
        lic_s = lic or "unknown"
        bad = any(t in lic_s.lower() for t in _COPYLEFT)
        entries.append({"package": dep, "license": lic_s, "commercial_ok": not bad})
        if bad:
            flagged.append(dep)
    return {"status": "passed", "dependencies": entries,
            "copyleft_risk": flagged, "checked": len(entries)}


_LICENSE_TIMEOUT = 30
_LINT_TIMEOUT = 240


def _win_cmd(cmd: List[str]) -> List[str]:
    """Windows: npm/npx ship as .cmd â€” append .cmd so CreateProcess finds them."""
    if os.name == "nt" and cmd and cmd[0] in ("npm", "npx") and not cmd[0].endswith(".cmd"):
        return [cmd[0] + ".cmd"] + cmd[1:]
    return cmd


def lint_project(project_dir: str, runner=None) -> Dict[str, Any]:
    """Run oxlint through npx (downloads once, then near-instant; Apache-2.0)."""
    frontend = _frontend_dir(project_dir)
    if not (frontend / "package.json").exists():
        return {"status": "skipped", "reason": "no package.json"}
    # oxlint's directory walk honours ancestor .gitignore files — the mono-repo
    # ignores `generated-projects/`, so explicit relative file paths are passed
    # (explicit file args bypass the walk). Windows caps the command line at
    # ~32,767 chars; 400 short paths leave comfortable headroom.
    targets = [
        str(p.relative_to(frontend)).replace("\\", "/")
        for p in _iter_files(frontend, exts=[".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"])
    ][:400]
    if not targets:
        return {"status": "skipped", "reason": "no lintable files"}
    cmd = _win_cmd(["npx", "-y", "oxlint@latest", "--format", "json"] + targets)
    if runner:
        rc, out, err = runner(cmd, str(frontend))
    else:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=_LINT_TIMEOUT,
                                  encoding="utf-8", errors="replace", cwd=str(frontend),
                                  shell=os.name == "nt")
            rc, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
        except (subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "message": str(exc)[:200]}
    try:
        payload = json.loads(out or "{}")
    except ValueError:
        return {"status": "failed", "message": (err or out)[:200] or "oxlint produced no JSON"}
    if isinstance(payload, dict):
        payload = payload.get("diagnostics") or []
    rule_hits: Dict[str, int] = {}
    files_hit: Dict[str, int] = {}
    for diag in payload:
        if not isinstance(diag, dict):
            continue
        rule = diag.get("rule") or diag.get("code") or "unknown"
        rule_hits[rule] = rule_hits.get(rule, 0) + 1
        fp = str(diag.get("file") or "?").replace("\\", "/")
        files_hit[fp] = files_hit.get(fp, 0) + 1
    total = sum(rule_hits.values())
    return {"status": "passed" if total == 0 else "warn",
            "issues": total, "by_rule": dict(sorted(rule_hits.items(), key=lambda kv: -kv[1])[:15]),
            "worst_files": dict(sorted(files_hit.items(), key=lambda kv: -kv[1])[:10])}


def _frontend_dir(project_dir: str) -> Path:
    p = Path(project_dir)
    cand = p / "frontend"
    return cand if (cand / "package.json").exists() or cand.exists() else p


def a11y_audit(url: str, node_bin: str = None, script: Path = None, runner=None) -> Dict[str, Any]:
    """axe-core run against a live page (repo-local Playwright, axe from CDN)."""
    helper = script or (Path(__file__).resolve().parent.parent / "utils" / "a11y_audit.cjs")
    if not helper.exists():
        return {"status": "skipped", "reason": "a11y helper missing"}
    cmd = [node_bin or "node", str(helper), url]
    if runner:
        rc, out, err = runner(cmd, str(Path(__file__).resolve().parent))
    else:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                  encoding="utf-8", errors="replace",
                                  cwd=str(helper.resolve().parent))
            rc, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
        except (subprocess.TimeoutExpired, OSError) as exc:
            return {"status": "failed", "message": str(exc)[:200]}
    t0 = out.find("{")
    if t0 < 0:
        return {"status": "failed", "message": (err or out)[:220] or "no a11y JSON output"}
    try:
        data = json.loads(out[t0:out.rfind("}") + 1])
    except ValueError:
        return {"status": "failed", "message": (err or out)[:220] or "bad a11y JSON"}
    if data.get("status") != "ok":
        return {"status": data.get("status", "failed"), "message": data.get("message", "")[:200]}
    violations = [
        {"id": v.get("id"), "impact": v.get("impact"), "nodes": v.get("nodes"),
         "help": v.get("help")}
        for v in data.get("violations", [])
        if v.get("impact") in (None, "serious", "critical", "moderate", "minor")
    ]
    counts: Dict[str, int] = {}
    for v in violations:
        counts[v["impact"] or "unknown"] = counts.get(v["impact"] or "unknown", 0) + v["nodes"]
    return {"status": "passed" if not data.get("violations") else "warn",
            "url": data.get("url", url), "violations": violations[:20],
            "node_counts": counts, "passes": data.get("passes", 0)}


_MERMAID_SECTIONS = {
    "frontend": ("React app (Vite)", "src/** components, hooks, services"),
    "backend": ("Express API", "routes â†’ middleware â†’ models"),
    "ai-agent": ("FastAPI agent", "providers â†’ pipeline â†’ QA gates"),
}


def mermaid_doc(project_dir: str, name: str = None) -> Dict[str, Any]:
    """Write docs/architecture.mmd describing the generated project's layers."""
    root = Path(project_dir)
    name = name or root.name or "project"
    edges = [("U", "F", "browser"), ("F", "B", "REST /api/v1"), ("B", "D", "SQL"), ("B", "R", "cache")]
    nodes = [("U", "Visitor"), ("D", "PostgreSQL"), ("R", "Redis")]
    nodes.append(("F", _MERMAID_SECTIONS["frontend"][0] if (root / "frontend").exists() else "Static frontend"))
    nodes.append(("B", _MERMAID_SECTIONS["backend"][0] if (root / "backend").exists() else "Backend services"))
    if (root / "ai-agent").exists() or (root / "agent").exists():
        nodes.append(("A", _MERMAID_SECTIONS["ai-agent"][0]))
        nodes.append(("G", "Internet LLMs"))
        edges.append(("F", "A", "REST /api"))
        edges.append(("A", "G", "LLM providers"))
    lines = [f"graph LR", f'  subgraph "{name}"']
    lines += [f'    {nid}["{label}"]' for nid, label in nodes]
    lines.append("  end")
    lines += [f"  {a} -->|{lbl}| {b}" for a, b, lbl in edges]
    doc = "\n".join(lines) + "\n"
    out = root / "docs"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "architecture.mmd"
    target.write_text(doc, encoding="utf-8")
    return {"status": "ok", "file": str(target), "nodes": len(nodes),
            "mermaid": doc}
