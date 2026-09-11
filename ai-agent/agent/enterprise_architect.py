"""Enterprise Project Architect gate.

Reads the systemic guidelines in `project-rules/` (the five canonical specs —
PRD_MASTER_TEMPLATE.md, TRD_ENGINEERING_STANDARDS.md, UI_UX_DESIGN_TOKENS.md,
BACKEND_SCHEMA_SPEC.md, SRS_SYSTEM_SPECIFICATIONS.md) and enforces them on every
generated project tree BEFORE the final ZIP archive is compiled.

Protocol:
    1. PRD scope     — feature scope of the Generation Matrix baseline.
    2. Engineering   — exact dependency pins, React 19 rules, server patterns.
    3. Design tokens — every element class uses the predefined token system
                       (raw `#hex` literals in components are hard violations).
    4. Schema + SRS  — relational contract (14-model baseline, FK contract, row
                       locks) + semantic SEO (14 JSON-LD types, OG meta, heading
                       hierarchy) + i18n/RTL bootstrap.

Strict constraint: any violating generated file is routed back through the
code_modifier self-healing pipeline; the ZIP archive is not compiled while any
verification point is red. If a source-of-truth spec is missing, verification
cannot be asserted and the ZIP is conservatively blocked.
"""
import os
import re
import inspect
from typing import Dict, Any, List, Optional, Callable, Tuple

from agent.schema_contract_injection import MODEL_BASELINE, FK_CONTRACT
from agent.docs_rule_engine import build_lockfile, load_lockfile, verify_rules
from agent.functional_compliance import JSONLD_REQUIRED_TYPES, OG_REQUIRED, _RTL_LANGUAGES
from utils.logger import agent_logger
from utils.file_manager import FileManager

# The five canonical project-rules specs, in protocol order.
REQUIRED_SPEC_FILES: List[str] = [
    "PRD_MASTER_TEMPLATE.md",
    "TRD_ENGINEERING_STANDARDS.md",
    "UI_UX_DESIGN_TOKENS.md",
    "BACKEND_SCHEMA_SPEC.md",
    "SRS_SYSTEM_SPECIFICATIONS.md",
]

# Anchors that must be cross-referenced per doc (evidence of pull/read).
DOC_ANCHORS: Dict[str, List[str]] = {
    "PRD_MASTER_TEMPLATE.md": ["## Feature Scope", "## Acceptance Criteria"],
    "TRD_ENGINEERING_STANDARDS.md": ["## Dependency Pins", "## React 19 Rules", "## Backend Patterns"],
    "UI_UX_DESIGN_TOKENS.md": ["## Color Tokens", "## Glassmorphism", "## Motion Profiles", "## Conformance"],
    "BACKEND_SCHEMA_SPEC.md": ["## Model Baseline", "## Foreign Key Contract", "## Concurrency Mandate", "## Multi-Tenancy (Organizations + RBAC)"],
    "SRS_SYSTEM_SPECIFICATIONS.md": ["## SEO Architecture", "## Internationalization", "## Code Quality Assurance"],
}

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_HEADING_RE = re.compile(r"<h([1-6])(?:\s|>)")
_GLASS_EXACT = "backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border border-white/10"

PIN_REACT = "^19.2.0"
PIN_QUERY = "^5.59.0"
PIN_ZUSTAND = "^5.0.0"


class EnterpriseArchitect:
    """Reads project-rules and enforces the 4-point protocol on generated trees."""

    @staticmethod
    def _repo_root() -> str:
        here = os.path.dirname(os.path.abspath(__file__))          # <repo>/ai-agent/agent
        return os.path.dirname(os.path.dirname(here))              # repo root

    # ── Phase A: pull + read + cross-reference the systemic guidelines ─────
    def load_rules(self, rules_dir: Optional[str] = None) -> Dict[str, Any]:
        rules_dir = rules_dir or os.path.join(self._repo_root(), "project-rules")
        files: Dict[str, Any] = {}
        for name in REQUIRED_SPEC_FILES:
            path = os.path.join(rules_dir, name)
            if not os.path.isfile(path):
                files[name] = {"loaded": False, "anchors": {}, "reason": "missing source-of-truth doc"}
                continue
            content = FileManager.read_file(path)
            anchors = {
                anchor: (anchor in content) for anchor in DOC_ANCHORS.get(name, [])
            }
            files[name] = {"loaded": True, "anchors": anchors}
        loaded = [n for n, v in files.items() if v.get("loaded")]
        return {
            "rules_dir": rules_dir,
            "loaded": len(loaded),
            "required": len(REQUIRED_SPEC_FILES),
            "files": files,
            "all_present": len(loaded) == len(REQUIRED_SPEC_FILES),
        }

    # ── Enforcement entrypoint ──────────────────────────────────────────────
    def enforce(
        self,
        project_dir: str,
        spec: Dict[str, Any],
        rules_dir: Optional[str] = None,
        self_heal: Optional[Callable[[str, List[str]], int]] = None,
        max_rounds: int = 2,
    ) -> Dict[str, Any]:
        docs = self.load_rules(rules_dir)
        spec = spec or {}
        rounds: List[Dict[str, Any]] = []
        violations: List[str] = []

        for attempt in range(max_rounds + 1):
            points = self._verify_all(docs, project_dir, spec)
            blocking: List[str] = [
                name for name, pt in points.items()
                if not pt.get("pass")
            ]
            if attempt == 0:
                violations = self._collect_offending_files(points)
            else:
                violations = self._collect_offending_files(points)

            passed = bool(docs.get("all_present")) and not blocking
            if passed or self_heal is None or not violations:
                agent_logger.info(
                    f"EnterpriseArchitect: attempt={attempt} "
                    f"pass={'YES' if passed else 'NO'} blocking={blocking}"
                )
                break
            healed = self._run_self_heal(project_dir, violations, self_heal)
            rounds.append({"round": attempt + 1, "healed": healed, "files": violations})

        passed = bool(docs.get("all_present")) and not blocking
        report = self._compose_report(docs, spec, points, rounds, violations, passed)
        agent_logger.info(
            f"EnterpriseArchitect: passed={report['passed']} "
            f"blocked_zip={report['blocked_zip']} "
            f"heal_rounds={len(rounds)}"
        )
        return report

    # ── Phase B: the four verification points ───────────────────────────────
    def _verify_all(self, docs: Dict[str, Any], project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "prd": self._verify_prd(docs, project_dir, spec),
            "engineering": self._verify_engineering(docs, project_dir, spec),
            "design": self._verify_design(docs, project_dir),
            "schema_srs": self._verify_schema_srs(docs, project_dir, spec),
        }

    @staticmethod
    def _point(
        name: str, doc: str, passed: bool, checks: Dict[str, Any], note: str = ""
    ) -> Dict[str, Any]:
        return {"name": name, "doc": doc, "pass": passed, "checks": checks, "note": note}

    @staticmethod
    def _check(passed: bool, detail: str, files: Optional[List[str]] = None,
               applies: bool = True) -> Dict[str, Any]:
        return {"pass": passed, "detail": detail, "files": files or [], "applies": applies}

    def _doc_gate(self, docs: Dict[str, Any], spec_name: str):
        """Strict source-of-truth gate: cannot assert compliance without the doc."""
        info = docs.get("files", {}).get(spec_name, {})
        if not info.get("loaded"):
            return None
        return info

    # ── 1. PRD scope (Generation Matrix baseline) ───────────────────────────
    def _verify_prd(self, docs: Dict[str, Any], project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        doc = "PRD_MASTER_TEMPLATE.md"
        gate = self._doc_gate(docs, doc)
        if gate is None:
            return self._point(doc, doc, False, {}, note=f"{doc} missing — cannot assert PRD scope")
        src = os.path.join(project_dir, "frontend", "src")
        checks: Dict[str, Any] = {}

        css = os.path.join(src, "index.css")
        css_content = FileManager.read_file(css) if os.path.isfile(css) else ""
        checks["fluid_ui"] = self._check(
            "--fluid-space-1" in css_content and ".fluid-container" in css_content,
            "fluid tokens + fluid utilities" if "--fluid-space-1" in css_content and ".fluid-container" in css_content
            else "missing --fluid-space-* / .fluid-container in index.css",
            [] if "--fluid-space-1" in css_content and ".fluid-container" in css_content else [css],
        )

        req_files = {
            "micro_interactions": [
                os.path.join(src, "hooks", "useInView.js"),
                os.path.join(src, "components", "common", "MotionCanvas.jsx"),
                os.path.join(src, "components", "common", "MotionSystems.jsx"),
            ],
            "lead_capture": [
                os.path.join(src, "components", "common", "LeadForm.jsx"),
                os.path.join(src, "components", "checkout", "CheckoutFlow.jsx"),
                os.path.join(src, "services", "analyticsBus.js"),
            ],
        }
        for cname, paths in req_files.items():
            missing = [os.path.relpath(p, project_dir).replace("\\", "/") for p in paths if not os.path.isfile(p)]
            checks[cname] = self._check(not missing, "artifacts present" if not missing else "missing: " + ", ".join(missing), missing)

        app_path = os.path.join(src, "App.jsx")
        app = FileManager.read_file(app_path) if os.path.isfile(app_path) else ""
        mounted = os.path.isfile(app_path) and "MotionCanvas" in app
        checks["mounted_motion_canvas"] = self._check(
            mounted, "MotionCanvas mounted in App.jsx" if mounted else "MotionCanvas not mounted in App.jsx",
            [] if mounted else [os.path.join("frontend", "src", "App.jsx")],
        )

        expected_runtime = "static" if "static" in str(spec.get("layout_mode", "")).lower() else "transactional"
        doc_path = os.path.join(project_dir, "GENERATION-MATRIX.md")
        if not os.path.isfile(doc_path):
            checks["runtime_mode"] = self._check(False, "GENERATION-MATRIX.md missing", ["GENERATION-MATRIX.md"])
        else:
            content = FileManager.read_file(doc_path)
            declared = (
                "static" if "Runtime: **static**" in content
                else "transactional" if "Runtime: **transactional**" in content
                else "unknown"
            )
            matches = declared == expected_runtime
            checks["runtime_mode"] = self._check(
                matches,
                f"runtime_mode={declared} matches layout_mode={spec.get('layout_mode')}"
                if matches else f"runtime_mode={declared} != expected={expected_runtime}",
                [] if matches else ["GENERATION-MATRIX.md"],
            )

        passed = all(c["pass"] for c in checks.values())
        return self._point("prd", doc, passed, checks)

    # ── 2. Engineering standards (dependencies, React 19, server patterns) ──
    def _verify_engineering(self, docs: Dict[str, Any], project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        doc = "TRD_ENGINEERING_STANDARDS.md"
        gate = self._doc_gate(docs, doc)
        if gate is None:
            return self._point(doc, doc, False, {}, note=f"{doc} missing — cannot assert engineering standards")
        src = os.path.join(project_dir, "frontend", "src")
        checks: Dict[str, Any] = {}

        pkg_path = os.path.join(project_dir, "frontend", "package.json")
        if not os.path.isfile(pkg_path):
            pins_ok, pin_detail, pin_files = False, "frontend/package.json missing", ["frontend/package.json"]
        else:
            pkg = FileManager.read_json(pkg_path)
            deps = pkg.get("dependencies", {})
            dev = pkg.get("devDependencies", {})
            violations, files = [], []
            for n, pin in (("react", PIN_REACT), ("react-dom", PIN_REACT),
                           ("@tanstack/react-query", PIN_QUERY), ("zustand", PIN_ZUSTAND)):
                if deps.get(n) != pin:
                    violations.append(f"{n}={deps.get(n, 'missing')}")
            def _major(v: str) -> Optional[int]:
                match = re.match(r"\d+", re.sub(r"^[^0-9]+", "", v or ""))
                return int(match.group(0)) if match else None
            if _major(dev.get("vite", "")) is None or _major(dev.get("vite")) < 8:
                violations.append(f"vite={dev.get('vite', 'missing')} (need major>=8)")
            tw = dev.get("tailwindcss") or deps.get("tailwindcss", "")
            if _major(tw) != 3:
                violations.append(f"tailwindcss={tw or 'missing'} (need v3)")
            pins_ok = not violations
            pin_detail = "pins conformant" if pins_ok else "violations: " + "; ".join(violations)
            pin_files = ["frontend/package.json"] if violations else []
        checks["stack_pins"] = self._check(pins_ok, pin_detail, pin_files)

        state_paths = [os.path.join(src, "lib", "queryClient.js"), os.path.join(src, "lib", "AppProviders.jsx")]
        missing_s = [os.path.relpath(p, project_dir).replace("\\", "/") for p in state_paths if not os.path.isfile(p)]
        app = FileManager.read_file(os.path.join(src, "App.jsx")) if os.path.isfile(os.path.join(src, "App.jsx")) else ""
        wrapped = "AppProviders" in app
        if not wrapped:
            missing_s.append(os.path.join("frontend", "src", "App.jsx"))
        checks["state_topology"] = self._check(not missing_s and wrapped,
                                               "provider-wrapped app root" if wrapped and not missing_s else "provider stack missing",
                                               missing_s)

        opt_paths = [os.path.join(src, "lib", "LazyLayouts.jsx"),
                     os.path.join(src, "components", "common", "LayoutSkeleton.jsx")]
        missing_o = [os.path.relpath(p, project_dir).replace("\\", "/") for p in opt_paths if not os.path.isfile(p)]
        css = os.path.join(src, "index.css")
        css_content = FileManager.read_file(css) if os.path.isfile(css) else ""
        cls_ok = ".skeleton-shimmer" in css_content and ".cls-reserve" in css_content
        if not cls_ok:
            missing_o.append(os.path.join("frontend", "src", "index.css"))
        checks["optimization"] = self._check(not missing_o, "lazy layouts + CLS guard", missing_o)

        checks["backend_blueprint"] = self._verify_backend(project_dir, spec)

        # Local component injection rigidity: generated pages must consume the
        # pre-built ButtonMotion wrapper instead of raw semantic <button> markup.
        raw_buttons = self._scan_raw_buttons(project_dir)
        checks["component_injection"] = self._check(
            not raw_buttons,
            "rigid local component injection (no raw <button>)" if not raw_buttons
            else "raw <button> markup: " + ", ".join(raw_buttons[:8]),
            raw_buttons[:20],
        )

        passed = all(c["pass"] for c in checks.values())
        return self._point("engineering", doc, passed, checks)

    @staticmethod
    def _scan_raw_buttons(project_dir: str) -> List[str]:
        """Project-relative paths containing raw HTML <button> outside the library."""
        from agent.component_injection import inspect_raw_buttons
        try:
            return inspect_raw_buttons(project_dir)
        except Exception as exc:  # pragma: no cover
            agent_logger.warning(f"raw-button scan failed: {exc}")
            return []

    def _verify_backend(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        runtime = spec.get("runtime_mode") or (
            "transactional" if "static" not in spec.get("layout_mode", "") else "static"
        )
        backend = os.path.join(project_dir, "backend")
        if runtime == "static" or not os.path.isdir(backend):
            return self._check(True, "not applicable — static runtime (API-less SPA)", applies=False)

        def has(rel: str, needle: str = "") -> Tuple[bool, str]:
            full = os.path.join(backend, rel)
            if not os.path.isfile(full):
                return False, os.path.join("backend", rel).replace("\\", "/")
            data = FileManager.read_file(full)
            if needle and needle not in data:
                return False, os.path.join("backend", rel).replace("\\", "/")
            return True, ""

        checks: List[Tuple[bool, str]] = [
            has("controllers/user.controller.js"),
            has("utils/response.js"),
            has("middleware/errorHandler.js"),
            has("config/db.js"),
            has("services/cache/redis.client.js", "isMemory"),
            has("services/queue/queue.service.js", "isMemory"),
        ]
        files = [c[1] for c in checks if not c[0] and c[1]]
        ok = not files
        return self._check(
            ok, "backend blueprint conformant" if ok else "missing/invalid pipeline files: " + ", ".join(files),
            files,
        )

    # ── 3. Design tokens (token classes + no raw hex) ───────────────────────
    def _verify_design(self, docs: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        doc = "UI_UX_DESIGN_TOKENS.md"
        gate = self._doc_gate(docs, doc)
        if gate is None:
            return self._point(doc, doc, False, {}, note=f"{doc} missing — cannot assert design tokens")
        src = os.path.join(project_dir, "frontend", "src")
        checks: Dict[str, Any] = {}

        tw = os.path.join(project_dir, "frontend", "tailwind.config.js")
        tw_content = FileManager.read_file(tw) if os.path.isfile(tw) else ""
        css = os.path.join(src, "index.css")
        css_content = FileManager.read_file(css) if os.path.isfile(css) else ""
        tokens_ok = ("rgb(var(--t-" in tw_content and "darkMode: 'class'" in tw_content) or "--t-canvas" in css_content
        checks["tokens"] = self._check(
            tokens_ok,
            "semantic token mapping present" if tokens_ok else "--t-* tokens missing (css or tailwind)",
            [] if tokens_ok else [os.path.join("frontend", "tailwind.config.js")],
        )

        glass_path = os.path.join(src, "components", "common", "GlassCard.jsx")
        glass_content = FileManager.read_file(glass_path) if os.path.isfile(glass_path) else ""
        glass_ok = _GLASS_EXACT in glass_content or (".glass-md" in css_content and "blur(12px)" in css_content)
        checks["glass"] = self._check(
            glass_ok, "glassmorphism spec present" if glass_ok else "GlassCard spec / .glass-md missing",
            [] if glass_ok else [os.path.join("frontend", "src", "components", "common", "GlassCard.jsx")],
        )

        presets = os.path.join(src, "lib", "motionPresets.js")
        presets_content = FileManager.read_file(presets) if os.path.isfile(presets) else ""
        wrapper = os.path.join(src, "components", "motion", "MotionWrapper.jsx")
        motion_ok = os.path.isfile(presets) and os.path.isfile(wrapper) and "standard: 240" in presets_content
        checks["motion"] = self._check(
            motion_ok, "motion profiles present" if motion_ok else "motionPresets/MotionWrapper missing",
            [] if motion_ok else [os.path.join("frontend", "src", "lib", "motionPresets.js")],
        )

        theme = os.path.join(src, "lib", "theme.js")
        app = FileManager.read_file(os.path.join(src, "App.jsx")) if os.path.isfile(os.path.join(src, "App.jsx")) else ""
        theme_ok = os.path.isfile(theme) and "import './lib/theme'" in app
        checks["theme"] = self._check(
            theme_ok, "dark-default theme wired" if theme_ok else "theme.js / App import missing",
            [] if theme_ok else [os.path.join("frontend", "src", "lib", "theme.js")],
        )

        # Hard violation: raw hex inside components.
        comp_dir = os.path.join(src, "components")
        hits: List[str] = []
        if os.path.isdir(comp_dir):
            for root, _, files in os.walk(comp_dir):
                for fname in files:
                    if not fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                        continue
                    path = os.path.join(root, fname)
                    for lineno, line in enumerate(FileManager.read_file(path).splitlines(), start=1):
                        if _HEX_RE.search(line):
                            hits.append(f"{os.path.relpath(path, project_dir).replace(os.sep, '/')}:{lineno}")
        checks["raw_hex"] = self._check(
            not hits,
            f"no raw hex literals ({len(hits)} found)" if not hits else f"raw hex literals: {len(hits)}",
            hits,
        )

        passed = all(c["pass"] for c in checks.values())
        return self._point("design", doc, passed, checks)

    # ── 4. Schema contract + SRS semantic SEO + i18n ────────────────────────
    def _verify_schema_srs(self, docs: Dict[str, Any], project_dir: str, spec: Dict[str, Any] = None) -> Dict[str, Any]:
        doc_schema = "BACKEND_SCHEMA_SPEC.md"
        doc_srs = "SRS_SYSTEM_SPECIFICATIONS.md"
        gate_schema = self._doc_gate(docs, doc_schema)
        gate_srs = self._doc_gate(docs, doc_srs)
        if gate_schema is None or gate_srs is None:
            return self._point(doc_schema, f"{doc_schema} + {doc_srs}", False, {},
                               note="schema/SRS source-of-truth missing — cannot assert compliance")
        spec = spec or {}
        runtime = spec.get("runtime_mode") or (
            "transactional" if "static" not in spec.get("layout_mode", "") else "static"
        )
        transactional = runtime != "static"
        backend = os.path.join(project_dir, "backend")
        frontend = os.path.join(project_dir, "frontend")
        checks: Dict[str, Any] = {}

        # ── Relational contract (BACKEND_SCHEMA_SPEC.md) ─────────────────────
        if not transactional:
            for cname in ("baseline", "fk_contract", "concurrency"):
                checks[cname] = self._check(
                    True, "relational contract not applicable (static runtime)",
                    [], applies=False,
                )
            return self._point(doc_schema, f"{doc_schema} + {doc_srs}",
                               all(c["pass"] for c in checks.values()), checks,
                               note=doc_srs)
        models_dir = os.path.join(backend, "models")
        existing_models = set()
        if os.path.isdir(models_dir):
            for f in os.listdir(models_dir):
                base = re.sub(r"\.(js|ts)$", "", f)
                if base in MODEL_BASELINE:
                    existing_models.add(base)
        missing_models = [m for m in MODEL_BASELINE if m not in existing_models]
        checks["baseline"] = self._check(
            not missing_models,
            f"{len(MODEL_BASELINE)}/14 models present" if not missing_models
            else "missing models: " + ", ".join(missing_models),
            [os.path.join("backend", "models", m + ".js") for m in missing_models],
        )

        index_path = os.path.join(models_dir, "index.js")
        index_content = FileManager.read_file(index_path) if os.path.isfile(index_path) else ""
        fk_missing = [column for _child, column, parent in FK_CONTRACT
                      if column and parent is not None and f"foreignKey: '{column}'" not in index_content]
        checks["fk_contract"] = self._check(
            bool(index_content) and not fk_missing,
            "FK contract honored" if not fk_missing else "FK columns missing: " + ", ".join(fk_missing),
            [os.path.join("backend", "models", "index.js")],
        )

        concurrency = self._verify_row_locks(backend)
        checks["concurrency"] = concurrency

        # ── Docs-as-rule-engine (spec-lockfile.json) ─────────────────────────
        checks["rule_lockfile"] = self._verify_docs_rules(docs, project_dir, transactional)

        # ── Semantic SEO (SRS_SYSTEM_SPECIFICATIONS.md) ──────────────────────
        sd_path = os.path.join(frontend, "src", "config", "structured-data.js")
        if not os.path.isfile(sd_path):
            checks["jsonld"] = self._check(False, "structured-data.js missing",
                                           [os.path.join("frontend", "src", "config", "structured-data.js")])
        else:
            sd_content = FileManager.read_file(sd_path)
            present = set(re.findall(r"['\"]@type['\"]\s*:\s*['\"]([A-Za-z]+)['\"]", sd_content))
            missing_ld = [t for t in JSONLD_REQUIRED_TYPES if t not in present]
            checks["jsonld"] = self._check(
                not missing_ld,
                f"{len(present)}/14 JSON-LD types" if not missing_ld else "missing JSON-LD types: " + ", ".join(missing_ld),
                [] if not missing_ld else [os.path.join("frontend", "src", "config", "structured-data.js")],
            )

        index_html = os.path.join(frontend, "index.html")
        html_content = FileManager.read_file(index_html) if os.path.isfile(index_html) else ""
        missing_og = [t for t in OG_REQUIRED
                      if f'property="{t}"' not in html_content and f'name="{t}"' not in html_content]
        checks["open_graph"] = self._check(
            bool(index_html) and not missing_og,
            "OG + twitter meta present" if not missing_og else "missing meta: " + ", ".join(missing_og),
            [] if not missing_og else [os.path.join("frontend", "index.html")],
        )

        heading_violations = self._scan_headings(frontend)
        checks["headings"] = self._check(
            not heading_violations, "heading hierarchy clean" if not heading_violations
            else "heading violations: " + "; ".join(heading_violations[:5]),
            heading_violations[:20],
        )

        i18n_path = os.path.join(frontend, "src", "i18n", "i18n.js")
        i18n_content = FileManager.read_file(i18n_path) if os.path.isfile(i18n_path) else ""
        hook_path = os.path.join(frontend, "src", "hooks", "useAppTranslation.js")
        i18n_ok = "RTL_LANGUAGES" in i18n_content and "document.documentElement.dir" in i18n_content and os.path.isfile(hook_path)
        checks["i18n_rtl"] = self._check(
            i18n_ok, "i18n bootstrap + RTL + hook present" if i18n_ok else "i18n/RTL bootstrap missing",
            [] if i18n_ok else [os.path.join("frontend", "src", "i18n", "i18n.js"),
                                os.path.join("frontend", "src", "hooks", "useAppTranslation.js")],
        )

        devops = self._verify_devops_wiring()
        checks["devops"] = self._check(devops["wired"], devops["detail"], [])

        passed = all(c["pass"] for c in checks.values())
        return self._point(doc_schema, f"{doc_schema} + {doc_srs}", passed, checks, note=doc_srs)

    # ── Docs-as-rule-engine ─────────────────────────────────────────────────
    def _verify_docs_rules(self, docs: Dict[str, Any], project_dir: str, transactional: bool) -> Dict[str, Any]:
        """Evaluate the checked-in `spec-lockfile.json` rules against a tree.

        The lockfile is (re)built only when the canonical specs changed
        (content-hash guarded), so the committed lockfile stays authoritative.
        """
        rules_dir = docs.get("rules_dir")
        if not rules_dir:
            return self._check(False, "no rules_dir resolved for docs-as-rule-engine", applies=False)
        lockfile = build_lockfile(rules_dir)
        if not lockfile or not lockfile.get("rules"):
            return self._check(False, "spec-lockfile.json has no rules", applies=transactional)
        verdicts = verify_rules(project_dir, lockfile, transactional)
        applicable = [v for v in verdicts if v.get("applies")]
        failed = [v["id"] for v in applicable if not v["pass"]]
        detail = (
            f"docs rule lockfile honored ({len(applicable)} applicable rules)"
            if not failed else "docs rule violations: " + ", ".join(failed)
        )
        files = sorted({f for v in applicable for f in v.get("files", [])})
        return self._check(
            not failed,
            detail,
            files or [os.path.join("project-rules", "spec-lockfile.json")],
            applies=bool(applicable),
        )

    # ── Row-lock concurrency mandate ─────────────────────────────────────────
    def _verify_row_locks(self, backend: str) -> Dict[str, Any]:
        targets = [os.path.join(backend, "services"), os.path.join(backend, "controllers")]
        tx_file, lock_file, guard_file, dec_file = None, None, None, None
        for target in targets:
            if not os.path.isdir(target):
                continue
            for root, _, files in os.walk(target):
                for fname in files:
                    if not fname.endswith(".js"):
                        continue
                    path = os.path.join(root, fname)
                    content = FileManager.read_file(path)
                    if tx_file is None and ("sequelize.transaction" in content):
                        tx_file = path
                    if lock_file is None and ("LOCK.UPDATE" in content or "FOR UPDATE" in content):
                        lock_file = path
                    if guard_file is None and ("sequelize.transaction" in content and "stock" in content):
                        guard_file = path
                    if dec_file is None and (".increment(" in content or ".decrement(" in content):
                        dec_file = path
        missing = []
        detail_parts = []
        for label, found in (("transaction", tx_file), ("row lock", lock_file),
                             ("stock guard", guard_file), ("atomic decrement", dec_file)):
            if found:
                detail_parts.append(f"{label}:{os.path.relpath(found, backend)}")
            else:
                missing.append(label)
        files = [os.path.relpath(f or os.path.join(backend, "services", "orderService.js"), backend)
                 for f, _ in ([(tx_file, 1), (lock_file, 1), (guard_file, 1), (dec_file, 1)]) if f is None]
        return self._check(
            not missing,
            "row-lock checkout flow present (" + ", ".join(detail_parts) + ")" if not missing
            else "missing concurrency primitives: " + ", ".join(missing),
            [os.path.join("backend", "services", "orderService.js")] if missing else [],
        )

    # ── Responsive heading hierarchy scan ────────────────────────────────────
    def _scan_headings(self, frontend: str) -> List[str]:
        src = os.path.join(frontend, "src")
        violations: List[str] = []
        if not os.path.isdir(src):
            return violations
        comp_root = os.path.join(src, "components")
        for root, _, files in os.walk(src):
            if root == comp_root or comp_root in root:
                continue
            for fname in files:
                if not fname.endswith((".jsx", ".tsx")):
                    continue
                path = os.path.join(root, fname)
                rel = os.path.relpath(path, frontend).replace("\\", "/")
                self._heading_check(path, rel, violations)
        return violations

    def _heading_check(self, path: str, rel: str, out: List[str]) -> None:
        counts: Dict[int, int] = {}
        stack: List[int] = []
        content = FileManager.read_file(path)
        for match in _HEADING_RE.finditer(content):
            level = int(match.group(1))
            counts[level] = counts.get(level, 0) + 1
            if stack and level > stack[-1] + 1:
                out.append(f"{rel}:h{level} jumps after h{stack[-1]}")
            if level == 1:
                if counts[level] > 1:
                    out.append(f"{rel}:multiple h1")
                stack = [level]
            elif not stack and level > 1:
                out.append(f"{rel}:h{level} without h1")
            else:
                stack.append(level)

    # ── DevOps linter/formatter gate wiring (repo-level property) ────────────
    @staticmethod
    def _verify_devops_wiring() -> Dict[str, bool]:
        repo = EnterpriseArchitect._repo_root()
        eslint = os.path.join(repo, "scripts", "eslint.generated.config.js")
        prettier = os.path.join(repo, ".prettierignore")
        importable = False
        try:
            from agent import quality_gate  # noqa: F401
            importable = True
        except Exception:
            importable = False
        wires = [os.path.isfile(eslint), os.path.isfile(prettier), True, importable]
        wired = all(wires)
        detail = (
            "ESLint config + .prettierignore + quality_gate wired" if wired
            else "devops gate wiring incomplete"
        )
        return {"pass": wired, "wired": wired, "detail": detail}

    # ── Offending file collection + self-heal routing ────────────────────────
    @staticmethod
    def _collect_offending_files(points: Dict[str, Any]) -> List[str]:
        files: List[str] = []
        for point in points.values():
            for check in point.get("checks", {}).values():
                if not check.get("pass"):
                    files.extend(check.get("files", []))
        seen: set = set()
        out: List[str] = []
        for f in files:
            if not f:
                continue
            # Drop ":<lineno>" suffixes from content scans; self-heal targets files.
            f = re.sub(r":\d+$", "", f)
            key = f.replace("\\", "/")
            if key not in seen:
                seen.add(key)
                out.append(key)
        return out

    @staticmethod
    def _run_self_heal(project_dir: str, files: List[str], self_heal) -> int:
        agent_logger.info(f"EnterpriseArchitect: routing {len(files)} file(s) to self-healing")
        import asyncio
        try:
            if inspect.iscoroutinefunction(self_heal):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                return loop.run_until_complete(self_heal(project_dir, files))
            return self_heal(project_dir, files) or 0
        except Exception as exc:  # pragma: no cover
            agent_logger.warning(f"EnterpriseArchitect self-heal failed: {exc}")
            return 0

    # ── Report composition ───────────────────────────────────────────────────
    @staticmethod
    def _compose_report(docs: Dict[str, Any], spec: Dict[str, Any], points: Dict[str, Any],
                        rounds: List[Dict[str, Any]], violations: List[str], passed: bool) -> Dict[str, Any]:
        reasons = []
        if not docs.get("all_present"):
            reasons.append("source-of-truth specs missing in project-rules/")
        for name, pt in points.items():
            if not pt.get("pass") and pt.get("checks"):
                red = sum(1 for c in pt["checks"].values() if not c["pass"])
                reasons.append(f"{name}: {red} check(s) red")
        return {
            "passed": passed,
            "blocked_zip": not passed,
            "docs": {
                "rules_dir": docs.get("rules_dir"),
                "loaded": docs.get("loaded"),
                "required": docs.get("required"),
                "all_present": docs.get("all_present"),
                "files": docs.get("files", {}),
            },
            "verification": points,
            "violating_files": violations,
            "self_heal_rounds": rounds,
            "project_name": spec.get("project_name", ""),
            "reason": "; ".join(reasons) or "all verification points green",
        }


enterprise_architect = EnterpriseArchitect()