"""
Project Mode Engine — Client-Only Static Showcase vs Enterprise Full-Stack Hydration
=====================================================================================

Selects one of two STRICT execution modes based on the targeted buyer type and
renders the codebase layout accordingly.

Mode 1 — CLIENT-ONLY STATIC SHOWCASE ("client-static")
    Target buyer: high-performance landing pages with zero server hosting maintenance.
    - Strips backend / docker / nginx artifacts injected by the template pipeline.
    - Injects navigation/state/form interactions purely through the frontend client
      layer: static API mock handlers (frontend/src/services/mockApi.js) and pre-wired
      cloud-edge client hooks (Formspree / Resend webhook for contact forms via client
      actions in frontend/src/services/staticForms.js).
    - Emits an API-less SPA build tree (vercel.json, netlify.toml, _redirects,
      _headers) ready for direct drop into Vercel or Netlify.

Mode 2 — ENTERPRISE FULL-STACK HYDRATION ("enterprise")
    Target buyer: SaaS products, multi-vendor marketplaces, dynamic apps requiring
    persistent databases.
    - Mounts the master-express-backend scaffold and hydrates the generated backend/
      with the canonical backend-library: the 14 Sequelize models (PostgreSQL/MySQL
      ready), the 18 API route groups mapped in server.js, and the Redis/BullMQ
      background jobs (backend/services/queue + backend/workers/worker.js).
    - Frontend Axios instance is pre-configured to communicate with the relative
      /api/* sub-routes through the Nginx gateway (nginx/nginx.conf → upstream).

Strict constraint: the generated bundle always carries a bespoke README.md with
explicit copy-paste setup steps for the selected mode.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

from config.settings import PROJECT_ROOT
from utils.logger import agent_logger
from utils.file_manager import FileManager
from .frontend_journey_generator import generate_frontend_journeys


MODE_CLIENT_STATIC = "client-static"
MODE_ENTERPRISE = "enterprise"

# Explicit buyer-type / deployment-mode aliases (win over website-type heuristics).
BUYER_STATIC_TERMS = ("client-only", "client_only", "static", "showcase", "landing", "brochure")
BUYER_ENTERPRISE_TERMS = ("enterprise", "fullstack", "full-stack", "full_stack", "dynamic")

BACKEND_CANONICAL = "backend"
BACKEND_EXCLUDE_DIRS = ("node_modules", ".git", "coverage", "logs", "tests", "__tests__")
BACKEND_EXCLUDE_FILES = (".env", ".env.production", ".env.staging", "package-lock.json")
BACKEND_COPY_DIRS = (
    "config", "controllers", "middleware", "models",
    "repositories", "routes", "services", "utils", "workers", "scripts",
)
BACKEND_COPY_FILES = ("server.js", "package.json", "Dockerfile", ".env.example")


class ProjectModeEngine:
    """Classifies the buyer type and renders the matching codebase layout."""

    def select_mode(self, spec: Dict[str, Any]) -> str:
        """Resolve the strict execution mode for a spec.

        Explicit `buyer_type` / `deployment_mode` may opt into client-static;
        all new websites otherwise use the full-stack enterprise mode. Website
        type alone never removes backend, database, authentication, or Docker.
        The resolved mode is written back into the spec as `layout_mode`.
        """
        raw = str(spec.get("buyer_type") or spec.get("deployment_mode") or "").strip().lower()
        wtype = str(spec.get("website_type") or "website").strip().lower()

        if raw:
            if any(term in raw for term in BUYER_STATIC_TERMS):
                mode = MODE_CLIENT_STATIC
            else:
                mode = MODE_ENTERPRISE
        else:
            mode = MODE_ENTERPRISE

        spec["layout_mode"] = mode
        spec["deployment_mode"] = mode
        spec["has_api"] = mode == MODE_ENTERPRISE
        spec["runtime_mode"] = "transactional" if mode == MODE_ENTERPRISE else "static"
        agent_logger.info(
            f"ProjectModeEngine: website_type='{wtype}' buyer_type='{raw or 'auto'}' -> "
            f"mode='{mode}'"
        )
        return mode

    def render_layout(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Render the layout for the selected mode and return a report dict."""
        mode = self.select_mode(spec)
        if mode == MODE_CLIENT_STATIC:
            return self.render_static_layout(project_dir, spec)
        return self.render_enterprise_layout(project_dir, spec)

    # ── Mode 1: Client-Only Static Showcase ─────────────────────────────────
    def render_static_layout(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        agent_logger.info("Layout Mode 1 (client-static): stripping backend, wiring client-only layer...")
        spec["layout_mode"] = MODE_CLIENT_STATIC
        spec["deployment_mode"] = MODE_CLIENT_STATIC
        spec["runtime_mode"] = "static"
        spec["has_api"] = False
        root = project_dir
        self._prune_backend_artifacts(root)

        frontend_src = os.path.join(root, "frontend", "src")
        frontend_public = os.path.join(root, "frontend", "public")
        FileManager.ensure_dir(frontend_src)
        FileManager.ensure_dir(frontend_public)

        services_dir = os.path.join(frontend_src, "services")
        FileManager.ensure_dir(services_dir)
        FileManager.write_file(
            os.path.join(services_dir, "staticForms.js"),
            self._static_forms_js(),
        )
        FileManager.write_file(
            os.path.join(services_dir, "mockApi.js"),
            self._mock_api_js(),
        )

        # API-less SPA deployment configs (Vercel / Netlify direct drop).
        self._write_static_deploy_configs(root)

        # Minimal frontend-only env example.
        project = spec.get("project_name", "generated-project")
        FileManager.write_file(
            os.path.join(root, ".env.example"),
            self._static_env_example(project),
        )

        # Bespoke static-mode README (strict constraint).
        FileManager.write_file(
            os.path.join(root, "README.md"),
            self._static_readme(spec),
        )
        license_path = os.path.join(root, "LICENSE.md")
        if not os.path.isfile(license_path):
            FileManager.write_file(
                license_path,
                (
                    f"# License — {project}\n\n"
                    "## Permitted Use\n"
                    "- Host, deploy, and commercially operate this product.\n"
                    "- Modify the source for your own or client projects.\n"
                    "- Resale of this source as a competing template requires a reseller license.\n"
                ),
            )

        # Generation Matrix — era-baseline premium layers.
        matrix_report = self._apply_generation_matrix(spec, root, MODE_CLIENT_STATIC)

        # LumicorePro Platform Injection (TRD #2) — runtime architecture rules.
        platform_report = self._apply_platform_injection(spec, root, MODE_CLIENT_STATIC)

        # LumicorePro Design System (TRD #3) — semantic tokens + layout fidelity.
        design_report = self._apply_design_system(spec, root, MODE_CLIENT_STATIC)

        # LumicorePro Schema Contract (TRD #4) — 14-model FK baseline + row locks.
        schema_report = self._apply_schema_contract(spec, root, MODE_CLIENT_STATIC)

        # LumicorePro SRS Quality Gates (TRD #5) — SEO + i18n functional compliance.
        quality_report = self._apply_functional_compliance(spec, root, MODE_CLIENT_STATIC)

        return {
            "mode": MODE_CLIENT_STATIC,
            "runtime_mode": "static",
            "backend_removed": True,
            "docker_removed": True,
            "nginx_removed": True,
            "form_provider": "formspree|resend-webhook|mock (client-side)",
            "mock_handlers": "frontend/src/services/mockApi.js",
            "client_forms": "frontend/src/services/staticForms.js",
            "platforms": ["vercel", "netlify"],
            "build_tree": "frontend/ (SPA, no /api)",
            "generation_matrix": matrix_report,
            "platform_injection": platform_report,
            "design_system": design_report,
            "schema_contract": schema_report,
            "functional_compliance": quality_report,
        }

    def _prune_backend_artifacts(self, root: str) -> None:
        """Remove every server-side artifact from a project tree (idempotent)."""
        # Explicit paths to remove
        explicit_paths = [
            os.path.join(root, "backend"),
            os.path.join(root, "nginx"),
            os.path.join(root, "nginx.conf"),
            os.path.join(root, "docker-compose.yml"),
            os.path.join(root, "docker-compose.yaml"),
            os.path.join(root, "compose.yml"),
            os.path.join(root, "Dockerfile"),
            os.path.join(root, "backend.Dockerfile"),
            os.path.join(root, "frontend", "Dockerfile"),
            os.path.join(root, "database"),
            os.path.join(root, "scripts"),
            os.path.join(root, ".github", "workflows"),
        ]
        for path in explicit_paths:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        # Recursive sweep for Dockerfile* and .dockerignore anywhere in the tree
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            for fname in filenames:
                if fname.startswith("Dockerfile") or fname == ".dockerignore":
                    fpath = os.path.join(dirpath, fname)
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass
            # Remove empty .github directories
            if os.path.basename(dirpath) == ".github" and not os.listdir(dirpath):
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass

    def _write_static_deploy_configs(self, root: str) -> None:
        frontend_public = os.path.join(root, "frontend", "public")
        FileManager.ensure_dir(frontend_public)

        FileManager.write_file(
            os.path.join(root, "vercel.json"),
            self._static_vercel_json(),
        )
        FileManager.write_file(
            os.path.join(root, "netlify.toml"),
            self._static_netlify_toml(),
        )
        FileManager.write_file(
            os.path.join(frontend_public, "_redirects"),
            "# SPA routing — client-only static showcase\n/*  /index.html  200\n",
        )
        FileManager.write_file(
            os.path.join(frontend_public, "_headers"),
            self._static_headers(),
        )

    def _static_vercel_json(self) -> str:
        return (
            "{\n"
            '  "version": 2,\n'
            '  "framework": "vite",\n'
            '  "rootDirectory": "frontend",\n'
            '  "buildCommand": "npm run build",\n'
            '  "outputDirectory": "dist",\n'
            '  "rewrites": [\n'
            '    { "source": "/(.*)", "destination": "/index.html" }\n'
            '  ],\n'
            '  "headers": [\n'
            '    {\n'
            '      "source": "/(.*)",\n'
            '      "headers": [\n'
            '        { "key": "X-Content-Type-Options", "value": "nosniff" },\n'
            '        { "key": "X-Frame-Options", "value": "SAMEORIGIN" },\n'
            '        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            "}\n"
        )

    def _static_netlify_toml(self) -> str:
        return (
            "# Netlify configuration — client-only static showcase\n\n"
            "[build]\n"
            '  base    = "frontend"\n'
            '  command = "npm run build"\n'
            '  publish = "dist"\n\n'
            "[build.environment]\n"
            '  NODE_VERSION = "20"\n'
            '  NPM_VERSION  = "10"\n\n'
            "[[redirects]]\n"
            '  from   = "/*"\n'
            '  to     = "/index.html"\n'
            '  status = 200\n'
        )

    def _static_headers(self) -> str:
        return (
            "# Security headers — client-only static showcase\n"
            "/*\n"
            "  X-Content-Type-Options: nosniff\n"
            "  X-Frame-Options: SAMEORIGIN\n"
            "  Referrer-Policy: strict-origin-when-cross-origin\n"
            "  Permissions-Policy: camera=(), microphone=(), geolocation=(self)\n\n"
            "/assets/*\n"
            "  Cache-Control: public, max-age=31536000, immutable\n"
        )

    def _static_env_example(self, project: str) -> str:
        return (
            "# Client-only static showcase — VITE_* vars only, no server secrets.\n"
            "# Copy to .env (frontend picks these up at build time).\n\n"
            f"# App\nVITE_APP_NAME={project}\n\n"
            "# Contact forms via cloud-edge client actions.\n"
            "# 1) Formspree (recommended, zero server): create a form at https://formspree.io\n"
            "#    then paste your endpoint:\n"
            "VITE_FORMSPREE_ENDPOINT=\n"
            "#    Optional second formspree form id for the newsletter/subscribe action:\n"
            "VITE_FORMSPREE_NEWSLETTER_ID=\n\n"
            "# 2) Resend / generic webhook (client action): point this at a serverless\n"
            "#    edge function (Vercel/Netlify) or webhook that fans out to Resend.\n"
            "VITE_CONTACT_WEBHOOK_URL=\n\n"
            "# Without either endpoint the forms fall back to a dev mock (no network).\n"
        )

    def _static_forms_js(self) -> str:
        return (
            "/**\n"
            " * Client-only cloud-edge form actions (static showcase mode).\n"
            " * Provider resolution: Formspree endpoint -> generic webhook -> dev mock.\n"
            " * Configure via VITE_FORMSPREE_ENDPOINT, VITE_FORMSPREE_NEWSLETTER_ID,\n"
            " * VITE_CONTACT_WEBHOOK_URL (e.g. a Vercel/Netlify edge function fanning out\n"
            " * to Resend). No backend server is required for any provider.\n"
            " */\n"
            "const FORMSPREE_ENDPOINT = import.meta.env.VITE_FORMSPREE_ENDPOINT || '';\n"
            "const NEWSLETTER_ENDPOINT = import.meta.env.VITE_FORMSPREE_NEWSLETTER_ID\n"
            "  ? `https://formspree.io/f/${import.meta.env.VITE_FORMSPREE_NEWSLETTER_ID}`\n"
            "  : '';\n"
            "const WEBHOOK_URL = import.meta.env.VITE_CONTACT_WEBHOOK_URL || '';\n"
            "\n"
            "export const getFormProvider = () => {\n"
            "  if (FORMSPREE_ENDPOINT) return 'formspree';\n"
            "  if (WEBHOOK_URL) return 'webhook';\n"
            "  return 'mock';\n"
            "};\n"
            "\n"
            "const postJSON = async (url, payload) => {\n"
            "  const res = await fetch(url, {\n"
            "    method: 'POST',\n"
            "    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },\n"
            "    body: JSON.stringify(payload),\n"
            "  });\n"
            "  if (!res.ok) throw new Error(`Endpoint responded with status ${res.status}`);\n"
            "  return res.json();\n"
            "};\n"
            "\n"
            "const mockDelivery = async () => {\n"
            "  await new Promise((resolve) => setTimeout(resolve, 450));\n"
            "  return { ok: true, mock: true };\n"
            "};\n"
            "\n"
            "/** Submit a contact / lead through the resolved cloud-edge provider. */\n"
            "export const submitContact = async (data) => {\n"
            "  const provider = getFormProvider();\n"
            "  const payload = {\n"
            "    _subject: data.subject || 'New website lead',\n"
            "    name: data.name,\n"
            "    email: data.email,\n"
            "    message: data.message,\n"
            "    ...(data.budget ? { budget: data.budget } : {}),\n"
            "  };\n"
            "  if (provider === 'formspree') {\n"
            "    await postJSON(FORMSPREE_ENDPOINT, payload);\n"
            "    return { ok: true, provider };\n"
            "  }\n"
            "  if (provider === 'webhook') {\n"
            "    await postJSON(WEBHOOK_URL, { ...payload, type: 'contact' });\n"
            "    return { ok: true, provider };\n"
            "  }\n"
            "  return mockDelivery();\n"
            "};\n"
            "\n"
            "/** Subscribe an email to the newsletter through the cloud-edge provider. */\n"
            "export const subscribeNewsletter = async (email) => {\n"
            "  const provider = getFormProvider();\n"
            "  if (provider === 'formspree' && NEWSLETTER_ENDPOINT) {\n"
            "    await postJSON(NEWSLETTER_ENDPOINT, { email });\n"
            "    return { ok: true, provider };\n"
            "  }\n"
            "  if (provider === 'webhook') {\n"
            "    await postJSON(WEBHOOK_URL, { email, type: 'newsletter' });\n"
            "    return { ok: true, provider };\n"
            "  }\n"
            "  return mockDelivery();\n"
            "};\n"
        )

    def _mock_api_js(self) -> str:
        return (
            "/**\n"
            " * Static API mock handlers — client-only showcase mode.\n"
            " * Promise-based stand-ins for backend data so the SPA renders and\n"
            " * state/filter interactions work with zero server hosting.\n"
            " */\n"
            "const delay = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));\n"
            "\n"
            "const COLLECTIONS = {\n"
            "  products: [\n"
            "    { id: 1, title: 'Signature Package', tagline: 'Hero offering', price: 149 },\n"
            "    { id: 2, title: 'Growth Package', tagline: 'Best seller', price: 249 },\n"
            "    { id: 3, title: 'Premium Package', tagline: 'Full-service', price: 499 },\n"
            "  ],\n"
            "  testimonials: [\n"
            "    { id: 1, name: 'Ayesha Khan', text: 'Outstanding quality and support.' },\n"
            "    { id: 2, name: 'Omar Farooq', text: 'Modern, fast and beautiful.' },\n"
            "    { id: 3, name: 'Sarah Malik', text: 'Exceeded every expectation.' },\n"
            "  ],\n"
            "  gallery: [\n"
            "    { id: 1, title: 'Project One' },\n"
            "    { id: 2, title: 'Project Two' },\n"
            "    { id: 3, title: 'Project Three' },\n"
            "  ],\n"
            "};\n"
            "\n"
            "export const getMockCollection = async (collection, query = {}) => {\n"
            "  await delay();\n"
            "  const items = [...(COLLECTIONS[collection] || [])];\n"
            "  if (query.q) return items.filter((i) => JSON.stringify(i).toLowerCase().includes(String(query.q).toLowerCase()));\n"
            "  if (query.limit) return items.slice(0, Number(query.limit));\n"
            "  return items;\n"
            "};\n"
            "\n"
            "export const postMockRecord = async (collection, payload) => {\n"
            "  await delay();\n"
            "  return { ok: true, id: `${collection}-${Date.now()}`, ...payload };\n"
            "};\n"
        )

    def _apply_platform_injection(self, spec: Dict[str, Any], root: str, mode: str) -> Dict[str, Any]:
        """TRD #2 runtime-architecture injections (frontend stack/state/optimization + backend conformance)."""
        try:
            from agent.platform_injection import platform_injection
            return platform_injection.generate(spec, root, mode)
        except Exception as exc:  # pragma: no cover — layout render must never be blocked
            agent_logger.warning(f"PlatformInjection skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _apply_generation_matrix(self, spec: Dict[str, Any], root: str, mode: str) -> Dict[str, Any]:
        """Era-baseline premium layers (fluid UI, motion, lead capture, dual runtime)."""
        try:
            from agent.generation_matrix import default_matrix
            return default_matrix.generate(spec, root, mode)
        except Exception as exc:  # pragma: no cover — render must never be blocked by the layer
            agent_logger.warning(f"GenerationMatrix skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _apply_design_system(self, spec: Dict[str, Any], root: str, mode: str) -> Dict[str, Any]:
        """TRD #3 design tokens + layout fidelity (semantic colors, glassmorphism, motion profiles)."""
        try:
            from agent.design_system_injection import design_system_injector
            return design_system_injector.generate(spec, root, mode)
        except Exception as exc:  # pragma: no cover — render must never be blocked by the layer
            agent_logger.warning(f"DesignSystem skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _apply_schema_contract(self, spec: Dict[str, Any], root: str, mode: str) -> Dict[str, Any]:
        """TRD #4 relational contract: 14-model FK baseline + row-lock checkout concurrency."""
        try:
            from agent.schema_contract_injection import schema_contract_injector
            return schema_contract_injector.generate(spec, root, mode)
        except Exception as exc:  # pragma: no cover — render must never be blocked by the layer
            agent_logger.warning(f"SchemaContract skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _apply_functional_compliance(self, spec: Dict[str, Any], root: str, mode: str) -> Dict[str, Any]:
        """TRD #5 SRS quality gates — SEO architecture + i18n/RTL compliance."""
        try:
            from agent.functional_compliance import functional_compliance
            return functional_compliance.generate(spec, root, mode)
        except Exception as exc:  # pragma: no cover — render must never be blocked by the layer
            agent_logger.warning(f"FunctionalCompliance skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _static_readme(self, spec: Dict[str, Any]) -> str:
        from .marketplace_readme import generate_marketplace_readme

        name = str(spec.get("project_name") or "Generated Project").replace("-", " ").title()
        wtype = str(spec.get("website_type") or "website").replace("_", " ").title()
        extra = (
            f"# {name}\n\n"
            f"Client-only static showcase (Mode 1) — `{wtype}` landing experience with "
            f"zero server hosting maintenance. The bundle is an API-less single-page "
            f"app ready for direct drop into **Vercel** or **Netlify**.\n\n"
            f"## What is included\n\n"
            f"- Frontend client layer only — all navigation, state and form interactions "
            f"run in the browser.\n"
            f"- Static API mock handlers: `frontend/src/services/mockApi.js`\n"
            f"- Cloud-edge contact forms via client actions: `frontend/src/services/staticForms.js` "
            f"(Formspree → Resend/generic webhook → dev mock).\n"
            f"- Edge deploy configs: `vercel.json`, `netlify.toml`, `frontend/public/_redirects`, "
            f"`frontend/public/_headers`.\n\n"
            f"## Quick start (local)\n\n"
            f"```bash\n"
            f"cd frontend\n"
            f"npm install\n"
            f"npm run dev        # http://localhost:5173\n"
            f"```\n\n"
            f"## Deploy to Vercel (copy-paste)\n\n"
            f"```bash\n"
            f"npm install -g vercel\n"
            f"vercel            # root of this bundle; rootDirectory: frontend is pre-set in vercel.json\n"
            f"vercel --prod\n"
            f"```\n\n"
            f"Or import the repo at https://vercel.com/new — Vercel auto-detects "
            f"`vercel.json` (Vite, rootDirectory `frontend`).\n\n"
            f"## Deploy to Netlify (copy-paste)\n\n"
            f"```bash\n"
            f"npm install -g netlify-cli\n"
            f"netlify deploy    # base \"frontend\", publish \"dist\" pre-set in netlify.toml\n"
            f"netlify deploy --prod\n"
            f"```\n\n"
            f"Or drag-and-drop the `frontend/dist` folder after `npm run build`.\n\n"
            f"## Contact forms — pick a provider\n\n"
            f"Create `.env` from `.env.example` and set one of:\n\n"
            f"1. **Formspree (zero server):** create a form at https://formspree.io and set\n"
            f"   `VITE_FORMSPREE_ENDPOINT=https://formspree.io/f/your-id`. Optional second form\n"
            f"   id for the newsletter: `VITE_FORMSPREE_NEWSLETTER_ID=your-newsletter-id`.\n"
            f"2. **Resend / webhook (client action):** set\n"
            f"   `VITE_CONTACT_WEBHOOK_URL=https://your-edge-function.example/resend` pointing\n"
            f"   at a Vercel/Netlify edge function (or Resend serverless hook).\n"
            f"3. **Mock (default):** with no vars set, forms resolve to a 450ms mock success "
            f"for demos.\n\n"
            f"Remember to re-run `npm run build` after changing env vars (Vite inlines them).\n\n"
            f"## Custom domain\n\n"
            f"- Vercel: Settings → Domains → add your domain + DNS A/CNAME records.\n"
            f"- Netlify: Domain settings → assign domain + update the registrar nameservers "
            f"to Netlify DNS (or add a CNAME to yoursite.netlify.app).\n\n"
        )
        return generate_marketplace_readme(spec, mode="static", extra_sections=extra)

    # ── Canonical blueprint files ───────────────────────────────────────────
    #: Written into a generated backend ONLY when the mounted scaffold does not
    #: already provide them. Keeps every generated project conformant to the
    #: documented blueprint (Express/Sequelize/BullMQ + in-memory fallbacks)
    #: without overwriting library code.
    _CANONICAL_USER_CONTROLLER = """/**
 * User controller — Express + Sequelize.
 * Generated by the LumiCorePro platform. Replace the demo responses with real
 * business logic; the auth/validation contract stays the same.
 */
const { User } = require('../models');
const { asyncHandler } = require('../utils/response');

/** GET /api/users — paginated list. */
const list = asyncHandler(async (req, res) => {
  const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
  const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
  const offset = (page - 1) * limit;

  const { rows, count } = await User.findAndCountAll({
    attributes: ['id', 'name', 'email', 'role', 'createdAt'],
    order: [['createdAt', 'DESC']],
    limit,
    offset,
  });

  res.status(200).json({ success: true, data: rows, meta: { page, limit, total: count } });
});

/** GET /api/users/:id — single record. */
const getById = asyncHandler(async (req, res) => {
  const user = await User.findByPk(req.params.id, {
    attributes: ['id', 'name', 'email', 'role', 'createdAt'],
  });
  if (!user) {
    return res.status(404).json({ success: false, error: { code: 'NOT_FOUND', message: 'User not found' } });
  }
  return res.status(200).json({ success: true, data: user });
});

/** PATCH /api/users/:id — partial update. */
const update = asyncHandler(async (req, res) => {
  const [updated] = await User.update(req.body || {}, { where: { id: req.params.id } });
  if (!updated) {
    return res.status(404).json({ success: false, error: { code: 'NOT_FOUND', message: 'User not found' } });
  }
  return list(req, res);
});

module.exports = { list, getById, update };
"""

    def _ensure_backend_blueprint_files(self, backend_dir: str) -> List[str]:
        """Create blueprint files that the mounted scaffold is missing.

        Returns the list of files written (empty when the scaffold already
        provides them), and never overwrites an existing file.
        """
        written: List[str] = []
        targets = (
            (os.path.join("controllers", "user.controller.js"), self._CANONICAL_USER_CONTROLLER),
        )
        for relative, content in targets:
            path = os.path.join(backend_dir, relative)
            if os.path.isfile(path):
                continue
            try:
                FileManager.write_file(path, content)
                written.append(relative.replace(os.sep, "/"))
            except Exception as exc:  # noqa: BLE001
                agent_logger.warning(f"Could not write blueprint file {relative}: {exc}")
        if written:
            agent_logger.info(f"ProjectModeEngine: added canonical blueprint file(s): {written}")
        return written

    # ── Mode 2: Enterprise Full-Stack Hydration ─────────────────────────────
    def render_enterprise_layout(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        agent_logger.info(
            "Layout Mode 2 (enterprise): mounting master-express-backend scaffold + "
            "canonical hydration (14 Sequelize models / 18 route groups / Redis+BullMQ)..."
        )
        root = project_dir
        canonical = (PROJECT_ROOT / BACKEND_CANONICAL).resolve()

        # Re-seed backend/ with the ecommerce-base scaffold first.
        backend_dir = os.path.join(root, "backend")
        if os.path.isdir(backend_dir):
            shutil.rmtree(backend_dir, ignore_errors=True)
        FileManager.ensure_dir(backend_dir)
        ecommerce_base = (PROJECT_ROOT / "backend-library" / "ecommerce-base").resolve()
        if ecommerce_base.exists():
            agent_logger.info(f"Copying ecommerce-base scaffold from: {ecommerce_base}")
            FileManager.copy_directory(str(ecommerce_base), str(backend_dir), ignore_patterns=["node_modules", ".git"])

        # Overlay with canonical enterprise scaffold (no secrets).
        mounted = 0
        if canonical.exists():
            for sub in BACKEND_COPY_DIRS:
                src = canonical / sub
                if src.is_dir():
                    dst = os.path.join(backend_dir, sub)
                    FileManager.copy_directory(
                        str(src), dst,
                        ignore_patterns=list(BACKEND_EXCLUDE_DIRS),
                    )
                    mounted += 1
            for fname in BACKEND_COPY_FILES:
                src = canonical / fname
                if src.is_file():
                    FileManager.copy_file(str(src), os.path.join(backend_dir, fname))
                    mounted += 1

        model_count, models = self._list_models(backend_dir)
        route_count, routes = self._list_routes(backend_dir)

        # Blueprint completeness: the overlay only provides what the canonical
        # backend happens to contain. If a library scaffold is missing the
        # controller layer, the generated project would ship a backend with no
        # controllers and the conformance check would (correctly) report a GAP.
        # Writing the canonical file only when it is absent keeps this additive
        # and idempotent — real library code is never overwritten.
        blueprint_files = self._ensure_backend_blueprint_files(backend_dir)

        # Hygiene: strip .env / .env.production / .env.staging that could carry secrets.
        for env_file in ("backend/.env", "backend/.env.production", "backend/.env.staging"):
            env_path = os.path.join(root, env_file)
            if os.path.isfile(env_path):
                try:
                    os.remove(env_path)
                except OSError:
                    pass

        # Postgres/MySQL-ready Sequelize env template.
        project = spec.get("project_name", "generated-project")
        FileManager.ensure_dir(backend_dir)
        FileManager.write_file(
            os.path.join(backend_dir, ".env.example"),
            self._enterprise_env_example(project),
        )

        # Nginx gateway (frontend ↔ backend upstream via /api/*).
        self._write_nginx_gateway(root)

        # Frontend Axios interceptor pre-wired to relative /api/* sub-routes.
        frontend_src = os.path.join(root, "frontend", "src")
        frontend_package = os.path.join(root, "frontend", "package.json")
        if os.path.isfile(frontend_package):
            package_data = json.loads(FileManager.read_file(frontend_package))
            dependencies = package_data.setdefault("dependencies", {})
            if "axios" not in dependencies and "axios" not in package_data.get("devDependencies", {}):
                dependencies["axios"] = "^1.7.9"
                FileManager.write_json(frontend_package, package_data)
        services_dir = os.path.join(frontend_src, "services")
        FileManager.ensure_dir(services_dir)
        FileManager.write_file(os.path.join(services_dir, "apiConfig.js"), self._api_config_js())
        FileManager.write_file(os.path.join(services_dir, "api.js"), self._api_js())
        frontend_journeys = generate_frontend_journeys(
            Path(root) / "frontend",
            str(spec.get("project_name") or "Generated Project"),
        )

        # Bespoke enterprise-mode README (strict constraint).
        FileManager.write_file(
            os.path.join(root, "README.md"),
            self._enterprise_readme(spec, models, routes),
        )

        # Generation Matrix — era-baseline premium layers.
        matrix_report = self._apply_generation_matrix(spec, root, MODE_ENTERPRISE)

        # LumicorePro Platform Injection (TRD #2) — runtime architecture rules.
        platform_report = self._apply_platform_injection(spec, root, MODE_ENTERPRISE)

        # LumicorePro Design System (TRD #3) — semantic tokens + layout fidelity.
        design_report = self._apply_design_system(spec, root, MODE_ENTERPRISE)

        # LumicorePro Schema Contract (TRD #4) — 14-model FK baseline + row locks.
        schema_report = self._apply_schema_contract(spec, root, MODE_ENTERPRISE)

        # LumicorePro SRS Quality Gates (TRD #5) — SEO + i18n functional compliance.
        quality_report = self._apply_functional_compliance(spec, root, MODE_ENTERPRISE)

        return {
            "mode": MODE_ENTERPRISE,
            "runtime_mode": "transactional",
            "scaffold": "master-express-backend hydrated from backend-library",
            "blueprint_files_added": blueprint_files,
            "models_mounted": model_count,
            "models": models,
            "route_groups_mapped": route_count,
            "routes": routes,
            "queue": "Redis + BullMQ (backend/services/queue, backend/workers/worker.js)",
            "axios_interceptor": "frontend/src/services/api.js -> /api/* via nginx gateway",
            "frontend_journeys": frontend_journeys,
            "database": "Sequelize — PostgreSQL/MySQL ready (DATABASE_URL + DB_DIALECT)",
            "generation_matrix": matrix_report,
            "platform_injection": platform_report,
            "design_system": design_report,
            "schema_contract": schema_report,
            "functional_compliance": quality_report,
        }

    def _write_nginx_gateway(self, root: str) -> None:
        nginx_dir = os.path.join(root, "nginx")
        FileManager.ensure_dir(nginx_dir)
        repo_nginx = PROJECT_ROOT / "nginx" / "nginx.conf"
        if repo_nginx.exists():
            FileManager.copy_file(str(repo_nginx), os.path.join(nginx_dir, "nginx.conf"))
        repo_ssl = PROJECT_ROOT / "nginx" / "ssl" / "README.md"
        if repo_ssl.exists():
            ssl_dir = os.path.join(nginx_dir, "ssl")
            FileManager.ensure_dir(ssl_dir)
            FileManager.copy_file(str(repo_ssl), os.path.join(ssl_dir, "README.md"))

    @staticmethod
    def _list_models(backend_dir: str) -> List:
        models_dir = os.path.join(backend_dir, "models")
        names = []
        if os.path.isdir(models_dir):
            for fname in sorted(os.listdir(models_dir)):
                if fname.endswith(".js") and fname != "index.js":
                    names.append(fname.replace(".js", ""))
        return len(names), names

    @staticmethod
    def _list_routes(backend_dir: str) -> List:
        routes_dir = os.path.join(backend_dir, "routes")
        names = []
        if os.path.isdir(routes_dir):
            for fname in sorted(os.listdir(routes_dir)):
                if fname.endswith(".routes.js"):
                    names.append(fname.replace(".routes.js", ""))
        return len(names), names

    def _enterprise_env_example(self, project: str) -> str:
        return (
            "# Environment — copy to .env (never commit .env).\n"
            "NODE_ENV=development\n"
            "PORT=5000\n\n"
            "# Database — Sequelize, PostgreSQL/MySQL ready.\n"
            "# PostgreSQL (default, pg is installed):\n"
            f"DATABASE_URL=postgres://postgres:postgres@localhost:5432/{project.replace('-', '_')}\n"
            "# MySQL: install the driver (`npm i mysql2`) and flip the dialect in\n"
            "# backend/config/database.js to 'mysql', then:\n"
            "# DATABASE_URL=mysql://root:root@localhost:3306/" + project.replace("-", "_") + "\n\n"
            "# Redis / BullMQ background jobs:\n"
            "REDIS_URL=redis://localhost:6379\n"
            "QUEUE_MAIN=lg-generic-jobs\n"
            "QUEUE_EMAIL=lg-email-jobs\n\n"
            "# JWT + CORS + uploads:\n"
            "# Generate: node -e \"console.log(require('crypto').randomBytes(48).toString('hex'))\"\n"
            "# Minimum 32 chars. The backend refuses to start if missing/weak/placeholder.\n"
            "JWT_SECRET=\n"
            "JWT_EXPIRES_15M=15m\n"
            "REFRESH_TOKEN_EXPIRES_DAYS=7\n"
            "CORS_ORIGIN=http://localhost:5173\n"
            "UPLOAD_DIR=uploads\n"
        )

    def _api_config_js(self) -> str:
        return (
            "/**\n"
            " * API configuration — enterprise full-stack mode.\n"
            " * The Axios instance talks to RELATIVE /api/* sub-routes; in production the\n"
            " * Nginx gateway proxies /api/* to the Express upstream (see nginx/nginx.conf).\n"
            " */\n"
            "export const getApiConfig = () => {\n"
            "  const raw = import.meta.env.VITE_API_URL || '/api';\n"
            "  return {\n"
            "    API_URL: raw.endsWith('/') ? raw.slice(0, -1) : raw,\n"
            "    API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 12000,\n"
            "  };\n"
            "};\n"
        )

    def _api_js(self) -> str:
        return (
            "/**\n"
            " * Pre-configured Axios instance — enterprise full-stack mode.\n"
            " * baseURL defaults to the relative /api route served by the Nginx gateway.\n"
            " * Request interceptor attaches the JWT; response interceptor handles 401s.\n"
            " */\n"
            "import axios from 'axios';\n"
            "import { getApiConfig } from './apiConfig';\n"
            "\n"
            "const { API_URL, API_TIMEOUT } = getApiConfig();\n"
            "\n"
            "const api = axios.create({\n"
            "  baseURL: API_URL,\n"
            "  timeout: API_TIMEOUT,\n"
            "  withCredentials: true,\n"
            "  headers: { 'Content-Type': 'application/json' },\n"
            "});\n"
            "\n"
            "api.interceptors.request.use(\n"
            "  (config) => {\n"
            "    if (config.url && config.url.startsWith('/api/')) {\n"
            "      config.url = config.url.replace(/^\\/api/, '');\n"
            "    }\n"
            "    const token = localStorage.getItem('auth_token');\n"
            "    if (token) config.headers.Authorization = `Bearer ${token}`;\n"
            "    return config;\n"
            "  },\n"
            "  (error) => Promise.reject(error)\n"
            ");\n"
            "\n"
            "let refreshRequest;\n"
            "api.interceptors.response.use(\n"
            "  (response) => response,\n"
            "  async (error) => {\n"
            "    const originalRequest = error.config;\n"
            "    const isAuthRequest = originalRequest && /^\\/auth\\/(login|register|refresh|logout)(?:$|\\?)/.test(originalRequest.url || '');\n"
            "    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry || isAuthRequest || typeof window === 'undefined') {\n"
            "      return Promise.reject(error);\n"
            "    }\n"
            "    originalRequest._retry = true;\n"
            "    try {\n"
            "      refreshRequest ||= api.post('/auth/refresh').then((response) => response.data?.data?.accessToken).finally(() => { refreshRequest = null; });\n"
            "      const accessToken = await refreshRequest;\n"
            "      if (!accessToken) throw new Error('The refresh endpoint did not return an access token.');\n"
            "      window.localStorage.setItem('auth_token', accessToken);\n"
            "      originalRequest.headers.Authorization = `Bearer ${accessToken}`;\n"
            "      return api(originalRequest);\n"
            "    } catch (refreshError) {\n"
            "      window.localStorage.removeItem('auth_token');\n"
            "      if (!['/login', '/register'].includes(window.location.pathname)) window.location.assign('/login');\n"
            "      return Promise.reject(refreshError);\n"
            "    }\n"
            "  }\n"
            ");\n"
            "\n"
            "export default api;\n"
        )

    def _enterprise_readme(self, spec: Dict[str, Any], models: List[str], routes: List[str]) -> str:
        name = str(spec.get("project_name") or "Generated Project").replace("-", " ").title()
        wtype = str(spec.get("website_type") or "saas").replace("_", " ").title()
        model_list = "\n".join(f"  - `{m}`" for m in models)
        route_list = "\n".join(f"  - `{r}`" for r in routes)
        core = (
            f"# {name}\n\n"
            f"Enterprise full-stack application — `{wtype}` website with a React frontend, "
            f"Express API, and PostgreSQL persistence.\n\n"
            f"## Architecture\n\n"
            f"```\n"
            f"Browser → Vite SPA (frontend/) → Express API (backend/) → PostgreSQL\n"
            f"Docker: Browser → Nginx frontend proxy → Express API → PostgreSQL\n"
            f"```\n\n"
            f"The frontend Axios instance (`frontend/src/services/api.js`) is pre-configured "
            f"for relative `/api/*` routes. In Docker, Nginx proxies those requests to the API.\n\n"
            f"## Backend and database setup\n\n"
            f"```bash\n"
            f"cd backend\n"
            f"copy .env.example .env      # Windows PowerShell; set DATABASE_URL and JWT_SECRET\n"
            f"# macOS/Linux: cp .env.example .env\n"
            f"npm install\n"
            f"npm run db:migrate          # apply versioned PostgreSQL migrations\n"
            f"npm run dev                 # API on http://localhost:5000\n"
            f"```\n\n"
            f"The API also runs pending migrations at startup and does not listen if database "
            f"connection or migration setup fails. `backend/migrations/` is the canonical schema.\n\n"
            f"## Frontend setup\n\n"
            f"```bash\n"
            f"cd frontend\n"
            f"copy .env.example .env      # set VITE_API_URL=http://localhost:5000\n"
            f"# macOS/Linux: cp .env.example .env\n"
            f"npm install\n"
            f"npm run dev                 # http://localhost:5173\n"
            f"```\n\n"
            f"## Docker Compose\n\n"
            f"```bash\n"
            f"copy .env.example .env      # set POSTGRES_PASSWORD and JWT_SECRET first\n"
            f"docker compose up --build\n"
            f"```\n\n"
            f"Compose waits for PostgreSQL health, backend readiness, then starts the frontend. "
            f"Never use the example secrets in production; configure strong unique values.\n\n"
            f"## Background jobs — Redis + BullMQ\n\n"
            f"Long-running work (emails, webhooks, report builds) runs through BullMQ queues in "
            f"`backend/services/queue` with workers in `backend/workers/worker.js`. Set `REDIS_URL` "
            f"(plus `QUEUE_MAIN`/`QUEUE_EMAIL`) in `backend/.env`; without Redis the queues use the "
            f"in-memory driver for local development.\n\n"
            f"## REST API surface\n\n"
            f"{len(routes)} route groups mapped on `/api/*`:\n"
            f"{route_list}\n\n"
            f"## Data model — Sequelize\n\n"
            f"{len(models)} generated models:\n"
            f"{model_list}\n\n"
            f"## Production build and verification\n\n"
            f"```bash\n"
            f"cd frontend && npm run build\n"
            f"cd ../backend && npm test\n"
            f"```\n"
            f"Configure external database, domain, HTTPS, monitoring, and backups before "
            f"production deployment. Payment routes and credentials are generated only when "
            f"the feature list explicitly requests Stripe payments; live-provider readiness "
            f"must be verified separately.\n\n"
        )
        from .marketplace_readme import generate_marketplace_readme

        return core + "\n" + generate_marketplace_readme(spec, mode="fullstack")

    # ── Finalize (idempotent, safe-invariant run before ZIP) ───────────────
    def finalize_layout(self, project_dir: str, spec: Dict[str, Any]) -> None:
        """Re-assert the selected mode's invariants right before ZIP compilation.

        Later phases (CDN/edge config generation) may recreate server artifacts;
        for client-static mode we prune them and re-emit API-less SPA configs so the
        shipped bundle always matches the buyer's mode.
        """
        mode = spec.get("layout_mode") or self.select_mode(spec)
        if mode == MODE_CLIENT_STATIC:
            self._prune_backend_artifacts(project_dir)
            self._write_static_deploy_configs(project_dir)
        agent_logger.info(
            f"ProjectModeEngine finalize: layout_mode={mode} invariants re-asserted "
            f"for {project_dir}"
        )