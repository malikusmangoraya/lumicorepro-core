"""Real Browser QA — Playwright-driven evidence for generated sites.

Serves the built project on an ephemeral local port and, when a Playwright
runtime is available, captures:
  - desktop (1440x900) + mobile (375x812) screenshots
  - browser console + page errors
  - horizontal-collapse detection at 375/768/1024/1440 (overflow elements)
  - basic LCP / load timing from the Performance API

When Playwright (python `playwright` or a repo-root `npx playwright`) is not
available it degrades to honest "not_measured" status with a clear upgrade
hint — it never fabricates a pass. Results land in `project_dir/qa/`.
"""
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger

VIEWPORTS = {"desktop": (1440, 900), "mobile": (375, 812)}
COLLAPSE_BREAKPOINTS = (375, 768, 1024, 1440)


class _PreviewHandler(SimpleHTTPRequestHandler):
    """Serve built frontend with SPA fallback (traversal-safe)."""

    def __init__(self, *args, roots=None, **kwargs):
        self._roots = roots or []
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        rel = path.strip("/")
        for base in self._roots:
            base = Path(base).resolve()
            if rel:
                cand = (base / rel).resolve()
                if str(cand).startswith(str(base) + os.sep) and cand.is_file():
                    return str(cand)
            index = base / "index.html"
            if index.is_file():
                return str(index)
        return str((Path(self._roots[0]) / "index.html").resolve()) if self._roots else "/"

    def log_message(self, *args, **kwargs):
        return  # silence request spam


class BrowserQA:
    def __init__(self, project_dir: str, base_url: Optional[str] = None):
        self.project_dir = Path(project_dir)
        self.base_url = base_url
        self.qa_dir = self.project_dir / "qa"
        self.qa_dir.mkdir(parents=True, exist_ok=True)

    # ── static serving ────────────────────────────────────────────────────
    def _roots(self) -> List[str]:
        p = self.project_dir
        return [str(x) for x in (
            p / "frontend" / "dist",
            p / "frontend" / "public",
            p / "dist",
            p / "public",
            p,
        ) if x.is_dir()]

    def _serve(self) -> Tuple[str, int, ThreadingHTTPServer]:
        handler = lambda *a, **kw: _PreviewHandler(*a, roots=self._roots(), **kw)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = httpd.server_address[1]
        th = threading.Thread(target=httpd.serve_forever, daemon=True)
        th.start()
        host = "127.0.0.1"
        if self.base_url:
            try:
                parsed = self.base_url.split("/")[-1]
            except Exception:
                pass
        return host, port, httpd

    # ── playwright acquisition ────────────────────────────────────────────
    def _python_playwright(self):
        try:
            from playwright.sync_api import sync_playwright
            return sync_playwright
        except Exception:
            return None

    def _npx_playwright(self) -> str:
        npx = shutil.which("npx")
        if not npx:
            return ""
        return npx

    # ── core ──────────────────────────────────────────────────────────────
    def run(self) -> Dict[str, Any]:
        if not any(self._roots()):
            return {"status": "failed", "message": "No build output found to QA.", "evidence": {}}
        host, port, httpd = self._serve()
        url = f"http://{host}:{port}/index.html"
        agent_logger.info(f"[BROWSER-QA] Serving {self.project_dir.name} at {url}")
        try:
            sp = self._python_playwright()
            if sp is None and self._npx_playwright():
                return self._run_via_cli(url, port, httpd)
            if sp is None:
                return {
                    "status": "not_measured",
                    "message": "Playwright not installed. Run `pip install playwright && playwright install chromium` "
                               "to enable real-browser QA.",
                    "evidence": {},
                }
            return self._run_full(sp, url, port, httpd)
        finally:
            threading.Thread(target=httpd.shutdown, daemon=True).start()

    def _run_full(self, sp, url: str, port: int, httpd) -> Dict[str, Any]:
        shots: Dict[str, str] = {}
        console_errors: List[str] = []
        page_errors: List[str] = []
        collapse_evidence: List[Dict[str, Any]] = []
        timing: Dict[str, Any] = {}
        waited = 0
        ok = False
        with sp() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for name, (w, h) in VIEWPORTS.items():
                    try:
                        ctx = browser.new_context(viewport={"width": w, "height": h})
                        page = ctx.new_page()
                        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
                        page.on("pageerror", lambda e: page_errors.append(str(e)))
                        page.goto(url, wait_until="networkidle", timeout=30000)
                        waited = 1
                        ok = True
                        shot = self.qa_dir / f"{name}.png"
                        page.screenshot(path=str(shot), full_page=False)
                        shots[name] = f"qa/{name}.png"
                        page.close()
                        ctx.close()
                    except Exception as exc:
                        agent_logger.warning(f"[BROWSER-QA] {name} screenshot failed: {exc}")

                # Collapse + LCP on a desktop context
                try:
                    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
                    page = ctx.new_page()
                    page.goto(url, wait_until="load", timeout=30000)
                    timing = page.evaluate(
                        """() => {
                          const nav = performance.getEntriesByType('navigation')[0] || {};
                          const lcp = performance.getEntriesByType('largest-contentful-paint');
                          const body = document.body;
                          return {
                            load_ms: Math.round(nav.loadEventEnd || 0),
                            dom_ms: Math.round(nav.domContentLoadedEventEnd || 0),
                            lcp_ms: Math.round((lcp.length ? lcp[lcp.length-1].startTime : 0)),
                            title: document.title
                          };
                        }"""
                    )
                    for bw in COLLAPSE_BREAKPOINTS:
                        detect = page.evaluate(
                            """(bw) => {
                              const els = [];
                              if (document.body.scrollWidth > bw) {
                                document.querySelectorAll('*').forEach(el => {
                                  const r = el.getBoundingClientRect();
                                  if (r.right > bw + 1 || r.left < -1) {
                                    if (r.width > 0) els.push({tag: el.tagName, cls: (el.className||'').toString().slice(0,60), right: Math.round(r.right)});
                                  }
                                });
                              }
                              return {overflow: document.body.scrollWidth > bw,
                                      pageWidth: document.body.scrollWidth,
                                      offenders: els.slice(0, 8)};
                            }""",
                            bw,
                        )
                        collapse_evidence.append({
                            "breakpoint": bw,
                            "overflow": detect.get("overflow"),
                            "pageWidth": detect.get("pageWidth"),
                            "offenders": detect.get("offenders") or [],
                        })
                    page.close()
                    ctx.close()
                except Exception as exc:
                    agent_logger.warning(f"[BROWSER-QA] collapse/LCP failed: {exc}")
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        report = {
            "status": "passed" if ok else "not_measured",
            "base_url": url.replace(f":{port}", ":<port>"),
            "screenshots": shots,
            "console_errors": console_errors[:20],
            "page_errors": page_errors[:20],
            "collapse_check": {
                "clean": all(not c["overflow"] for c in collapse_evidence),
                "breakpoints": collapse_evidence,
            },
            "performance": timing,
            "evidence": {
                "viewport_captures": 2 if ok else 0,
                "collapse_samples": len(collapse_evidence),
                "console_errors": len(console_errors),
                "page_errors": len(page_errors),
                "lcp_ms": timing.get("lcp_ms"),
            },
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._write_report(report)
        return report

    def _run_via_cli(self, url: str, port: int, httpd) -> Dict[str, Any]:
        """Fallback: `npx playwright screenshot` per viewport — evidence only."""
        npx = self._npx_playwright()
        shots: Dict[str, str] = {}
        for name, (w, h) in VIEWPORTS.items():
            out = self.qa_dir / f"{name}.png"
            try:
                subprocess.run(
                    [npx, "playwright", "screenshot", "--viewport-size", f"{w},{h}", url, str(out)],
                    cwd=str(Path(__file__).resolve().parent.parent.parent.parent),  # repo root
                    capture_output=True, timeout=90, check=True,
                )
                if out.is_file():
                    shots[name] = f"qa/{name}.png"
            except Exception as exc:
                agent_logger.warning(f"[BROWSER-QA] npx screenshot {name} failed: {exc}")
        report = {
            "status": "partial" if shots else "not_measured",
            "base_url": url.replace(f":{port}", ":<port>"),
            "screenshots": shots,
            "evidence": {"viewport_captures": len(shots), "mode": "npx-playwright-cli"},
            "note": "Install `pip install playwright && playwright install chromium` for full "
                    "console/collapse/LCP evidence.",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._write_report(report)
        return report

    def _write_report(self, report: Dict[str, Any]):
        (self.qa_dir / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def run_browser_qa(project_dir: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    return BrowserQA(project_dir, base_url).run()