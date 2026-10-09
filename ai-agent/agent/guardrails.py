"""Output guardrails — the safety pass every generated project goes through.

Three independent checks, each idempotent and fail-open (a guardrail bug must
never kill a build; it degrades to a recorded warning):

1. ``scrub_prompt_injection`` — user prompts are screened before the
   orchestrator sees them: classic instruction-override patterns are
   neutralized so a buyer prompt can't hijack the master prompt.
2. ``redact_project_pii`` — generated files are scanned for accidental PII
   (emails, phone numbers, long digit runs like card/account numbers) and
   hard secrets (AWS/GCP/private keys, bearer tokens) before packaging.
   Secrets are REPLACED with placeholders; emails/phones only in
   demo/content strings via config markers (see redact_report).
3. ``inject_csp`` — every generated ``index.html`` gets a strict
   Content-Security-Policy meta tag (script-src 'self' + inline styles only),
   plus a Netlify ``_headers`` file so the deployed site ships the header.

The combined ``apply_guardrails`` pass returns a report that is embedded in
the run report and folded into the quality gate.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import agent_logger

# ── 1. Prompt-injection scrubbing ───────────────────────────────────────────
_INJECTION_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?|rules?)", re.I),
     "instruction override"),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior|your)\s+(instructions|rules?)", re.I),
     "instruction override"),
    (re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.I), "persona hijack"),
    (re.compile(r"(reveal|print|output)\s+(your\s+)?(system\s+)?(prompt|instructions)", re.I),
     "prompt exfiltration"),
    (re.compile(r"system\s*:\s*", re.I), "fake system message"),
    (re.compile(r"<\|?(im_start|system|endoftext)\|?>", re.I), "chat template injection"),
]


def scan_prompt_injection(prompt: str) -> List[str]:
    hits = []
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(prompt or ""):
            hits.append(label)
    return hits


def scrub_prompt_injection(prompt: str) -> Dict[str, Any]:
    """Neutralize injection attempts. Returns {text, scrubbed, flags}.

    Strategy: replace the matched phrase with a harmless marker instead of
    dropping the whole prompt (buyers often phrase requirements awkwardly).
    """
    text = prompt or ""
    flags: List[str] = []
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append(label)
            text = pattern.sub("[scrubbed]", text)
    return {"text": text, "scrubbed": bool(flags), "flags": flags}


# ── 2. Secret / PII scanning ────────────────────────────────────────────────
_SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_access_key", "AWS_ACCESS_KEY_PLACEHOLDER"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "google_api_key", "GOOGLE_API_KEY_PLACEHOLDER"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "openai_style_key", "API_KEY_PLACEHOLDER"),
    (re.compile(r"ghp_[A-Za-z0-9]{36,}"), "github_pat", "GITHUB_TOKEN_PLACEHOLDER"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private_key", "PRIVATE_KEY_PLACEHOLDER"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "slack_token", "SLACK_TOKEN_PLACEHOLDER"),
]

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@(?:[A-Za-z0-9\-]+\.)+[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<![\w\-])(?:\+?\d[\d\- ().]{7,}\d)(?![\w\-])")


def scan_text_for_secrets(text: str) -> List[Dict[str, str]]:
    found = []
    for pattern, label, _placeholder in _SECRET_PATTERNS:
        if pattern.search(text):
            found.append({"type": label})
    return found


def redact_text(text: str, redact_contacts: bool = False) -> str:
    out = text or ""
    for pattern, _label, placeholder in _SECRET_PATTERNS:
        out = pattern.sub(placeholder, out)
    if redact_contacts:
        out = _EMAIL_RE.sub("user@example.com", out)
        out = _PHONE_RE.sub("+1-000-000-0000", out)
    return out


_SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", ".venv", "venv", "__pycache__"}
_TEXT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".md",
                  ".py", ".yml", ".yaml", ".env", ".txt", ".toml", ".cfg", ".svg", ".prisma"}


def redact_project_pii(project_dir: str, redact_contacts: bool = False,
                       max_files: int = 4000) -> Dict[str, Any]:
    """Scrub secrets (always) and contact PII (optional) from generated files."""
    root = Path(project_dir)
    report: Dict[str, Any] = {"scanned_files": 0, "redacted_files": [], "secrets_found": []}
    if not root.is_dir():
        report["error"] = f"not a directory: {project_dir}"
        return report
    for path in sorted(root.rglob("*")):
        if report["scanned_files"] >= max_files:
            break
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        report["scanned_files"] += 1
        cleaned = redact_text(text, redact_contacts=redact_contacts)
        secrets_here = scan_text_for_secrets(text)
        if secrets_here:
            report["secrets_found"].extend({"file": str(path.relative_to(root)), **s} for s in secrets_here)
        if cleaned != text:
            try:
                path.write_text(cleaned, encoding="utf-8")
                report["redacted_files"].append(str(path.relative_to(root)))
            except OSError:
                agent_logger.warning("Guardrails: could not rewrite %s", path)
    return report


# ── 3. Mandatory CSP ────────────────────────────────────────────────────────
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data: https:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

CSP_META = f'<meta http-equiv="Content-Security-Policy" content="{CSP_POLICY}">'


def inject_csp(project_dir: str) -> Dict[str, Any]:
    """Ensure every generated index.html carries a CSP meta tag; also write a
    Netlify _headers file so the deployed site enforces the header."""
    root = Path(project_dir)
    report: Dict[str, Any] = {"csp_injected": [], "already_present": [], "headers_file": None}
    if not root.is_dir():
        report["error"] = f"not a directory: {project_dir}"
        return report

    for index_html in root.rglob("index.html"):
        try:
            text = index_html.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "Content-Security-Policy" in text:
            report["already_present"].append(str(index_html.relative_to(root)))
            continue
        if "<head>" in text:
            patched = text.replace("<head>", f"<head>\n    {CSP_META}", 1)
        elif "<head " in text:
            patched = re.sub(r"(<head[^>]*>)", r"\1\n    " + CSP_META.replace("\\", "\\\\"), text, count=1)
        else:
            continue
        index_html.write_text(patched, encoding="utf-8")
        report["csp_injected"].append(str(index_html.relative_to(root)))

    headers_path = root / "_headers"
    if not headers_path.exists():
        headers_path.write_text(
            "/*\n"
            f"  Content-Security-Policy: {CSP_POLICY}\n"
            "  X-Content-Type-Options: nosniff\n"
            "  X-Frame-Options: SAMEORIGIN\n"
            "  Referrer-Policy: strict-origin-when-cross-origin\n",
            encoding="utf-8",
        )
        report["headers_file"] = str(headers_path)
    return report


# ── Combined pass ───────────────────────────────────────────────────────────
def apply_guardrails(project_dir: str, scrub_contacts: Optional[bool] = None) -> Dict[str, Any]:
    """Run the full output guardrail pass over a generated project."""
    if scrub_contacts is None:
        scrub_contacts = (os.getenv("GUARDRAILS_REDACT_CONTACTS", "true").strip().lower()
                          not in ("0", "false", "no", "off"))
    pii = redact_project_pii(project_dir, redact_contacts=scrub_contacts)
    csp = inject_csp(project_dir)
    ok = "error" not in pii and "error" not in csp
    return {
        "passed": ok,
        "pii": {"scanned_files": pii.get("scanned_files", 0),
                "redacted_count": len(pii.get("redacted_files", [])),
                "secrets_found": pii.get("secrets_found", [])},
        "csp": {"injected": len(csp.get("csp_injected", [])),
                "already_present": len(csp.get("already_present", [])),
                "headers_file": csp.get("headers_file")},
    }


def guardrail_penalty(report: Dict[str, Any]) -> float:
    """Quality-gate penalty (0–10) derived from the guardrail report."""
    if not report:
        return 0.0
    secrets_found = len(report.get("pii", {}).get("secrets_found", []))
    penalty = min(5.0, secrets_found * 2.5)
    if report.get("csp", {}).get("injected", 0) == 0 and not report.get("csp", {}).get("already_present", 0):
        penalty += 2.0
    return round(penalty, 2)
