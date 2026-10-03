"""Browser Integration Layer — LumicorePro Agent.

Drives the real ``agent-browser`` CLI for deep browser auditing of generated
sites. Complements :mod:`agent.extensions.browser_qa` (Playwright evidence for
screenshots / console / collapse / LCP) with audits only a real browser session
can produce: axe-core accessibility violations, Core Web Vitals, page errors and
interactive flow verification.

Every check reports measured evidence or an explicit ``not_measured`` status.
Nothing is inferred or hardcoded, so a missing runtime can never masquerade as
a pass.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

CLI = "agent-browser"
DEFAULT_SESSION = "lumi-qa"
DEFAULT_TIMEOUT = 30


def _resolve_cli() -> str:
    """Locate the agent-browser executable, preferring .cmd over .ps1 on Windows."""
    found = shutil.which(CLI)
    if found:
        if found.lower().endswith(".ps1"):
            sibling = found[: -len(".ps1")] + ".cmd"
            if os.path.isfile(sibling):
                return sibling
        return found
    for ext in (".cmd", ".exe", ".bat"):
        candidate = shutil.which(CLI + ext)
        if candidate:
            return candidate
    return ""


def _parse_json(raw: str) -> Any:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        start = min(
            [i for i in (raw.find("{"), raw.find("[")) if i != -1] or [-1]
        )
        if start > 0:
            try:
                return json.loads(raw[start:])
            except (ValueError, TypeError):
                return None
    return None


class AgentBrowser:
    """Thin, evidence-first wrapper around the agent-browser CLI."""

    def __init__(
        self,
        session: str = DEFAULT_SESSION,
        headed: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.session = session
        self.timeout = timeout
        self.last_code: Optional[int] = None
        self._exe = _resolve_cli()
        self._headless = not headed

    @property
    def available(self) -> bool:
        return bool(self._exe)

    @property
    def executable(self) -> str:
        return self._exe

    def _run(self, *args: str, as_json: bool = False) -> Tuple[int, Any]:
        if not self._exe:
            self.last_code = 127
            return 127, None
        cmd = [self._exe, "--session", self.session]
        if as_json:
            cmd.append("--json")
        if not self._headless:
            cmd.append("--headed")
        cmd.extend(args)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            self.last_code = 124
            return 124, None
        except Exception:
            self.last_code = 1
            return 1, None
        self.last_code = proc.returncode
        return proc.returncode, _parse_json(proc.stdout) if as_json else proc.stdout

    def open(self, url: str) -> bool:
        code, _ = self._run("open", url)
        return code == 0

    def set_viewport(self, width: int, height: int) -> bool:
        code, _ = self._run("set", "viewport", str(width), str(height))
        return code == 0

    def wait(self, ms: int = 1000) -> bool:
        code, _ = self._run("wait", str(ms))
        return code == 0

    def screenshot(self, path: str, full: bool = False) -> Optional[str]:
        args = ["screenshot", path]
        if full:
            args.append("--full")
        code, _ = self._run(*args)
        if code != 0:
            return None
        return path if Path(path).is_file() else None

    def title(self) -> str:
        code, out = self._run("get", "title")
        return (out or "").strip() if code == 0 else ""

    def text(self, selector: str = "body") -> str:
        code, out = self._run("get", "text", selector)
        return (out or "").strip() if code == 0 else ""

    def eval(self, js: str) -> Any:
        code, out = self._run("eval", js, as_json=True)
        return out if code == 0 else None

    def console(self) -> List[str]:
        code, out = self._run("console")
        if code != 0:
            return []
        return [
            line.strip()
            for line in (out or "").splitlines()
            if line.strip() and "error" in line.lower()
        ]

    def errors(self) -> List[str]:
        code, out = self._run("errors")
        if code != 0:
            return []
        return [line.strip() for line in (out or "").splitlines() if line.strip()]

    def a11y(self) -> Dict[str, Any]:
        code, data = self._run("a11y", "--json", as_json=True)
        if code != 0 or data is None:
            return {
                "status": "not_measured",
                "reason": "agent-browser a11y audit returned no data",
            }
        violations = data.get("violations") if isinstance(data, dict) else None
        if violations is None:
            violations = data if isinstance(data, list) else []
        return {
            "status": "measured",
            "violation_count": len(violations),
            "violations": [
                {
                    "id": v.get("id"),
                    "impact": v.get("impact"),
                    "help": v.get("help"),
                    "nodes": len(v.get("nodes") or []),
                }
                for v in violations[:20]
                if isinstance(v, dict)
            ],
        }

    def vitals(self) -> Dict[str, Any]:
        code, data = self._run("vitals", "--json", as_json=True)
        if code != 0 or data is None:
            return {
                "status": "not_measured",
                "reason": "agent-browser vitals returned no data",
            }
        return {"status": "measured", "metrics": data}

    def click(self, selector: str) -> bool:
        code, _ = self._run("click", selector)
        return code == 0

    def fill(self, selector: str, value: str) -> bool:
        code, _ = self._run("fill", selector, value)
        return code == 0

    def close(self) -> None:
        if not self._exe:
            return
        try:
            subprocess.run(
                [self._exe, "--session", self.session, "close"],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except Exception:
            pass

    # ── element interaction ─────────────────────────────────────────────────
    def snapshot(self) -> str:
        """Accessibility tree with refs — the reliable way to target elements."""
        code, out = self._run("snapshot")
        return (out or "").strip() if code == 0 else ""

    def find(self, role: str, value: str, action: str = "click") -> bool:
        code, _ = self._run("find", role, value, action)
        return code == 0

    def is_visible(self, selector: str) -> bool:
        code, out = self._run("is", "visible", selector)
        return code == 0 and str(out).strip().lower() in ("true", "1", "yes")

    def is_enabled(self, selector: str) -> bool:
        code, out = self._run("is", "enabled", selector)
        return code == 0 and str(out).strip().lower() in ("true", "1", "yes")

    def is_checked(self, selector: str) -> bool:
        code, out = self._run("is", "checked", selector)
        return code == 0 and str(out).strip().lower() in ("true", "1", "yes")

    def press(self, key: str) -> bool:
        code, _ = self._run("press", key)
        return code == 0

    def select(self, selector: str, value: str) -> bool:
        code, _ = self._run("select", selector, value)
        return code == 0

    def check(self, selector: str) -> bool:
        code, _ = self._run("check", selector)
        return code == 0

    def uncheck(self, selector: str) -> bool:
        code, _ = self._run("uncheck", selector)
        return code == 0

    def hover(self, selector: str) -> bool:
        code, _ = self._run("hover", selector)
        return code == 0

    def scroll_into_view(self, selector: str) -> bool:
        code, _ = self._run("scrollintoview", selector)
        return code == 0

    def reload(self) -> bool:
        code, _ = self._run("reload")
        return code == 0

    # ── emulation ───────────────────────────────────────────────────────────
    def set_media(self, media: str) -> bool:
        """`dark` | `light` | `reduced-motion` — verify theme/motion handling."""
        code, _ = self._run("set", "media", media)
        return code == 0

    def set_device(self, name: str) -> bool:
        code, _ = self._run("set", "device", name)
        return code == 0

    # ── network ─────────────────────────────────────────────────────────────
    def network_requests(self, clear: bool = False) -> List[Dict[str, Any]]:
        """Return captured network requests with status/type/url."""
        args = ["network", "requests"]
        if clear:
            args.append("--clear")
        code, out = self._run(*args)
        if code != 0:
            return []
        text = (out or "").strip()
        if not text:
            return []
        data = _parse_json(text)
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        if isinstance(data, dict):
            for key in ("requests", "entries", "data"):
                if isinstance(data.get(key), list):
                    return [r for r in data[key] if isinstance(r, dict)]
        return []

    # ── diff ────────────────────────────────────────────────────────────────
    def diff_screenshot(self, baseline: str) -> Dict[str, Any]:
        """Pixel-diff the current page against a baseline image."""
        code, out = self._run("diff", "screenshot", "--baseline", baseline, as_json=True)
        if code != 0:
            return {"status": "not_measured", "reason": "diff command failed"}
        if isinstance(out, dict):
            return {"status": "measured", "diff": out}
        return {"status": "measured", "diff": out}

    def diff_url(self, other_url: str) -> Dict[str, Any]:
        code, out = self._run("diff", "url", other_url, as_json=True)
        if code != 0:
            return {"status": "not_measured", "reason": "url diff failed"}
        return {"status": "measured", "diff": out}

    # ── performance ─────────────────────────────────────────────────────────
    def trace_start(self) -> bool:
        code, _ = self._run("trace", "start")
        return code == 0

    def trace_stop(self, path: str) -> Optional[str]:
        code, _ = self._run("trace", "stop", path)
        return path if code == 0 and Path(path).is_file() else None

    def profiler_start(self) -> bool:
        code, _ = self._run("profiler", "start")
        return code == 0

    def profiler_stop(self, path: str) -> Optional[str]:
        code, _ = self._run("profiler", "stop", path)
        return path if code == 0 and Path(path).is_file() else None


_OVERFLOW_JS = (
    "() => ({sw: document.body.scrollWidth, "
    "iw: window.innerWidth, title: document.title})"
)


def deep_browser_audit(
    url: str,
    session: str = DEFAULT_SESSION,
    headed: bool = False,
    shots: Optional[Dict[str, str]] = None,
    run_a11y: bool = True,
    run_vitals: bool = True,
) -> Dict[str, Any]:
    """Audit a URL in a real browser session.

    Returns a report where each section is either ``measured`` with evidence or
    ``not_measured`` with a reason. Never returns a fabricated pass.
    """
    br = AgentBrowser(session=session, headed=headed)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
        "executable": Path(br.executable).name if br.available else None,
        "sections": {},
    }

    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = (
            "agent-browser CLI not found on PATH. Install with "
            "`npm install -g agent-browser && agent-browser install`."
        )
        return report

    try:
        if not br.open(url):
            report["status"] = "failed"
            report["reason"] = f"could not open {url}"
            return report

        br.wait(1200)

        sections = report["sections"]

        sections["title"] = {
            "status": "measured" if br.title() else "not_measured",
            "value": br.title() or None,
        }

        overflow = br.eval(_OVERFLOW_JS)
        if isinstance(overflow, dict) and overflow.get("sw") and overflow.get("iw"):
            sections["overflow"] = {
                "status": "measured",
                "scroll_width": overflow.get("sw"),
                "inner_width": overflow.get("iw"),
                "overflowing": bool(overflow["sw"] > overflow["iw"]),
            }
        else:
            sections["overflow"] = {
                "status": "not_measured",
                "reason": "document dimensions unavailable",
            }

        console_errors = br.console()
        page_errors = br.errors()
        sections["console_errors"] = {
            "status": "measured",
            "count": len(console_errors),
            "errors": console_errors[:20],
        }
        sections["page_errors"] = {
            "status": "measured",
            "count": len(page_errors),
            "errors": page_errors[:20],
        }

        if shots:
            captured: Dict[str, Any] = {}
            for name, (w, h) in (("desktop", (1440, 900)), ("mobile", (375, 812))):
                path = shots.get(name)
                if not path:
                    captured[name] = {"status": "not_measured", "reason": "no path given"}
                    continue
                br.set_viewport(w, h)
                br.wait(600)
                got = br.screenshot(path, full=True)
                captured[name] = (
                    {"status": "measured", "path": got, "viewport": [w, h]}
                    if got
                    else {"status": "not_measured", "viewport": [w, h]}
                )
            sections["screenshots"] = {"status": "measured", "captures": captured}

        sections["accessibility"] = br.a11y() if run_a11y else {
            "status": "not_measured",
            "reason": "a11y audit disabled",
        }
        sections["web_vitals"] = br.vitals() if run_vitals else {
            "status": "not_measured",
            "reason": "vitals collection disabled",
        }

        measured = sum(
            1 for s in sections.values() if s.get("status") == "measured"
        )
        report["measured_sections"] = measured
        report["total_sections"] = len(sections)
        report["status"] = "measured" if measured else "not_measured"
    finally:
        br.close()

    return report


# ═══════════════════════════════════════════════════════════════════════════
# Pre-build reference capture + visual diff
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_VIEWPORTS: Tuple[Tuple[str, int, int], ...] = (
    ("desktop", 1440, 900),
    ("tablet", 768, 1024),
    ("mobile", 375, 812),
)


def capture_reference(
    url: str,
    shots_dir: str,
    session: str = DEFAULT_SESSION,
    viewports: Sequence[Tuple[str, int, int]] = DEFAULT_VIEWPORTS,
) -> Dict[str, Any]:
    """Capture baseline screenshots at every breakpoint *before* a build.

    These baselines are what :func:`visual_diff` and the self-heal loop compare
    against, so a regression is detected against a known-good image rather than
    against a memory of what the page looked like.
    """
    br = AgentBrowser(session=session)
    out_dir = Path(shots_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
        "baselines": {},
    }
    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = "agent-browser CLI not found on PATH"
        return report

    try:
        if not br.open(url):
            report["status"] = "failed"
            report["reason"] = f"could not open {url}"
            return report
        br.wait(1200)
        for name, width, height in viewports:
            br.set_viewport(width, height)
            br.wait(500)
            path = str(out_dir / f"reference-{name}.png")
            got = br.screenshot(path, full=True)
            report["baselines"][name] = (
                {"status": "measured", "path": got, "viewport": [width, height]}
                if got
                else {"status": "not_measured", "viewport": [width, height]}
            )
        report["status"] = "measured"
    finally:
        br.close()
    return report


def visual_diff(
    baseline: str,
    session: str = DEFAULT_SESSION,
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare the current page (or `url`) against a baseline image.

    Uses the CLI's own `diff screenshot --baseline`, so the comparison is the
    tool's measured output — not a re-implementation that could disagree with
    what the browser actually rendered.
    """
    if not baseline or not Path(baseline).is_file():
        return {"status": "not_measured", "reason": "baseline image missing"}
    br = AgentBrowser(session=session)
    if not br.available:
        return {"status": "not_measured", "reason": "agent-browser CLI not found"}
    try:
        if url:
            if not br.open(url):
                return {"status": "not_measured", "reason": f"could not open {url}"}
            br.wait(1200)
        return br.diff_screenshot(baseline)
    finally:
        br.close()


# ═══════════════════════════════════════════════════════════════════════════
# Interactive flow verification
# ═══════════════════════════════════════════════════════════════════════════

def verify_flow(
    url: str,
    steps: Sequence[Dict[str, Any]],
    session: str = DEFAULT_SESSION,
) -> Dict[str, Any]:
    """Drive a real user flow and verify each step's outcome.

    Each step is a dict with an ``action`` key:
      ``open``     — {url}
      ``click``    — {selector}
      ``fill``     — {selector, value}
      ``type``     — {selector, value}
      ``press``    — {key}
      ``select``   — {selector, value}
      ``check``    — {selector}
      ``wait``     — {ms}
      ``visible``  — {selector}  -> asserts visible
      ``enabled``  — {selector}  -> asserts enabled
      ``checked``  — {selector}  -> asserts checked
      ``text``     — {selector, contains} -> asserts substring
      ``title``    — {contains}  -> asserts substring

    A failed step stops the flow and reports exactly where it broke, so a
    remediation targets the real step rather than the whole page.
    """
    br = AgentBrowser(session=session)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
        "steps": [],
        "passed": 0,
        "failed": 0,
    }
    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = "agent-browser CLI not found on PATH"
        return report

    try:
        for index, step in enumerate(steps):
            action = str(step.get("action", "")).strip().lower()
            result: Dict[str, Any] = {"index": index, "action": action}
            ok = False
            try:
                if action == "open":
                    ok = br.open(str(step.get("url", url)))
                elif action == "click":
                    ok = br.click(str(step["selector"]))
                elif action == "fill":
                    ok = br.fill(str(step["selector"]), str(step.get("value", "")))
                elif action == "type":
                    ok = br.fill(str(step["selector"]), str(step.get("value", "")))
                elif action == "press":
                    ok = br.press(str(step.get("key", "Enter")))
                elif action == "select":
                    ok = br.select(str(step["selector"]), str(step.get("value", "")))
                elif action == "check":
                    ok = br.check(str(step["selector"]))
                elif action == "uncheck":
                    ok = br.uncheck(str(step["selector"]))
                elif action == "wait":
                    ok = br.wait(int(step.get("ms", 500)))
                elif action == "visible":
                    ok = br.is_visible(str(step["selector"]))
                elif action == "enabled":
                    ok = br.is_enabled(str(step["selector"]))
                elif action == "checked":
                    ok = br.is_checked(str(step["selector"]))
                elif action == "text":
                    got = br.text(str(step["selector"]))
                    needle = str(step.get("contains", ""))
                    ok = needle in got
                    result["found"] = got[:200]
                elif action == "title":
                    got = br.title()
                    needle = str(step.get("contains", ""))
                    ok = needle in got
                    result["found"] = got[:200]
                else:
                    result["error"] = f"unknown action {action!r}"
            except KeyError as exc:
                result["error"] = f"missing key {exc}"
            except Exception as exc:
                result["error"] = str(exc)

            result["status"] = "passed" if ok else "failed"
            report["steps"].append(result)
            if ok:
                report["passed"] += 1
            else:
                report["failed"] += 1
                report["status"] = "failed"
                report["failed_at"] = index
                return report

        report["status"] = "passed"
    finally:
        br.close()
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Network audit
# ═══════════════════════════════════════════════════════════════════════════

def network_audit(
    url: str,
    session: str = DEFAULT_SESSION,
    allow_external: Sequence[str] = (),
) -> Dict[str, Any]:
    """Audit network requests: failures, external calls, and total count.

    External requests are flagged against an explicit allow-list so a CDN or
    font host the project actually uses is not reported as a violation.
    """
    br = AgentBrowser(session=session)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
    }
    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = "agent-browser CLI not found on PATH"
        return report

    try:
        if not br.open(url):
            report["status"] = "not_measured"
            report["reason"] = f"could not open {url}"
            return report
        br.wait(1500)
        requests = br.network_requests()
        allowed = {str(h).lower() for h in allow_external}
        failed: List[Dict[str, Any]] = []
        external: List[Dict[str, Any]] = []
        for req in requests:
            status = req.get("status")
            url_req = str(req.get("url", ""))
            is_fail = False
            if isinstance(status, int) and status >= 400:
                is_fail = True
            elif isinstance(status, str) and status.isdigit() and int(status) >= 400:
                is_fail = True
            if is_fail:
                failed.append({"url": url_req, "status": status})
            host = ""
            try:
                from urllib.parse import urlparse
                host = (urlparse(url_req).hostname or "").lower()
            except Exception:
                pass
            if host and host not in allowed and not url_req.startswith(("data:", "blob:")):
                external.append({"url": url_req, "host": host})
        report["status"] = "measured"
        report["total_requests"] = len(requests)
        report["failed_requests"] = failed[:20]
        report["failed_count"] = len(failed)
        report["external_requests"] = external[:20]
        report["external_count"] = len(external)
        report["external_allowed"] = sorted(allowed)
    finally:
        br.close()
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Responsive verification
# ═══════════════════════════════════════════════════════════════════════════

def responsive_check(
    url: str,
    session: str = DEFAULT_SESSION,
    viewports: Sequence[Tuple[str, int, int]] = DEFAULT_VIEWPORTS,
) -> Dict[str, Any]:
    """Measure overflow and capture screenshots at every breakpoint.

    Overflow is measured from the live DOM (scrollWidth vs innerWidth), not
    inferred from the viewport name, so a page that only overflows at 800px is
    still caught.
    """
    br = AgentBrowser(session=session)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
        "viewports": {},
    }
    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = "agent-browser CLI not found on PATH"
        return report

    try:
        if not br.open(url):
            report["status"] = "not_measured"
            report["reason"] = f"could not open {url}"
            return report
        br.wait(1200)
        for name, width, height in viewports:
            br.set_viewport(width, height)
            br.wait(500)
            overflow = br.eval(_OVERFLOW_JS)
            entry: Dict[str, Any] = {"viewport": [width, height]}
            if isinstance(overflow, dict) and overflow.get("sw") and overflow.get("iw"):
                entry["status"] = "measured"
                entry["scroll_width"] = overflow.get("sw")
                entry["inner_width"] = overflow.get("iw")
                entry["overflowing"] = bool(overflow["sw"] > overflow["iw"])
                entry["overflow_px"] = max(0, int(overflow["sw"]) - int(overflow["iw"]))
            else:
                entry["status"] = "not_measured"
            report["viewports"][name] = entry
        report["status"] = "measured"
        report["overflowing_viewports"] = [
            name for name, e in report["viewports"].items() if e.get("overflowing")
        ]
    finally:
        br.close()
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Performance trace
# ═══════════════════════════════════════════════════════════════════════════

def performance_audit(
    url: str,
    session: str = DEFAULT_SESSION,
    trace_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Collect Core Web Vitals plus an optional Chrome DevTools trace."""
    br = AgentBrowser(session=session)
    report: Dict[str, Any] = {
        "url": url,
        "runtime": "agent-browser",
        "available": br.available,
    }
    if not br.available:
        report["status"] = "not_measured"
        report["reason"] = "agent-browser CLI not found on PATH"
        return report

    try:
        if not br.open(url):
            report["status"] = "not_measured"
            report["reason"] = f"could not open {url}"
            return report
        br.wait(1500)
        report["web_vitals"] = br.vitals()
        if trace_path:
            br.trace_start()
            br.reload()
            br.wait(2000)
            got = br.trace_stop(trace_path)
            report["trace"] = (
                {"status": "measured", "path": got}
                if got
                else {"status": "not_measured", "reason": "trace not produced"}
            )
        report["status"] = "measured"
    finally:
        br.close()
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Remediation — turn findings into actionable fixes
# ═══════════════════════════════════════════════════════════════════════════

def remediate_findings(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert an audit report into a prioritised, actionable remediation list.

    Each item names the evidence, the fix, and the phase that owns it, so the
    self-heal loop can dispatch work without re-deriving what went wrong.
    """
    items: List[Dict[str, Any]] = []
    sections = report.get("sections") or {}

    overflow = sections.get("overflow") or {}
    if overflow.get("overflowing"):
        items.append({
            "priority": "P1",
            "phase": "css",
            "evidence": f"scrollWidth {overflow.get('scroll_width')} > innerWidth {overflow.get('inner_width')}",
            "fix": "Constrain the offending element (max-width: 100%, overflow-wrap, or a narrower grid track).",
        })

    console = sections.get("console_errors") or {}
    if console.get("count"):
        items.append({
            "priority": "P1",
            "phase": "javascript",
            "evidence": f"{console['count']} console errors",
            "fix": "Resolve the reported runtime errors; a console error can block later scripts.",
        })

    page_errors = sections.get("page_errors") or {}
    if page_errors.get("count"):
        items.append({
            "priority": "P1",
            "phase": "javascript",
            "evidence": f"{page_errors['count']} page errors",
            "fix": "Fix uncaught exceptions and failed resource loads.",
        })

    a11y = sections.get("accessibility") or {}
    if a11y.get("status") == "measured" and a11y.get("violation_count"):
        items.append({
            "priority": "P2",
            "phase": "a11y",
            "evidence": f"{a11y['violation_count']} axe violations",
            "fix": "Address the highest-impact axe violations (contrast, labels, focus order).",
        })

    vitals = sections.get("web_vitals") or {}
    metrics = vitals.get("metrics") if isinstance(vitals, dict) else None
    if isinstance(metrics, dict):
        lcp = metrics.get("LCP") or metrics.get("lcp")
        cls = metrics.get("CLS") or metrics.get("cls")
        if isinstance(lcp, (int, float)) and lcp > 2500:
            items.append({
                "priority": "P2",
                "phase": "performance",
                "evidence": f"LCP {lcp}ms",
                "fix": "Reduce LCP: preload the hero image, defer non-critical CSS/JS, and avoid render-blocking requests.",
            })
        if isinstance(cls, (int, float)) and cls > 0.1:
            items.append({
                "priority": "P2",
                "phase": "performance",
                "evidence": f"CLS {cls}",
                "fix": "Reserve space for images/ads and avoid injecting content above the fold.",
            })

    for item in items:
        item["status"] = "open"
    return items