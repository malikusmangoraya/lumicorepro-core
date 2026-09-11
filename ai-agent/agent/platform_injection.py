"""Platform Injection Rules (TRD #2) — runtime architecture mandates.

Injects + verifies the platform's full-stack technical requirements into every
generated project:

Frontend Runtime Architecture (all modes)
    1. Core stack pins  → React 19.2.x, Vite 8.2.x, Tailwind v3.4.x (frontend/package.json).
    2. State topologies  → TanStack React Query cache cluster (server state) +
                           Zustand store wrapper (client state); QueryClientProvider
                           auto-wrapped around the app root.
    3. Optimization      → React.lazy() alternative layout templates (LandingLayout /
                           AppLayout) with Suspense + CLS-safe LayoutSkeleton;
                           CLS guard utilities appended to index.css (budget < 0.1).

Backend Infrastructure Blueprint (enterprise runtime only — conformance verify)
    4. Express decoupled route controllers with predictable HTTP status codes
       (backend/utils/response.js + middleware/errorHandler.js).
    5. Native Sequelize models mapped to PostgreSQL/MySQL schemas (config/db.js).
    6. BullMQ delayed job clusters over protected isolated Redis nodes with
       in-memory fallback (backend/services/cache/redis.client.js isMemory +
       backend/services/queue/queue.service.js).

Outputs PLATFORM-INJECTION.md + a structured conformance report per project.
Idempotent: markers `LUMICORE_PLATFORM` guard all writes.
"""
import os
import re
from typing import Dict, Any, Optional, Tuple

from utils.logger import agent_logger
from utils.file_manager import FileManager

_MARKER = "LUMICORE_PLATFORM"

# TRD pins
PIN_REACT = "^19.2.0"
PIN_REACT_DOM = "^19.2.0"
PIN_QUERY = "^5.59.0"
PIN_ZUSTAND = "^5.0.0"
PIN_VITE = "^8.2.0"
PIN_TAILWIND = "^3.4.7"

# Files that collectively define the canonical backend blueprint
# (paths relative to <project>/backend).
_BACKEND_PIPELINE = {
    "controllers": ("controllers", "user.controller.js"),
    "response_envelope": ("utils", "response.js"),
    "error_handler": ("middleware", "errorHandler.js"),
    "sequelize_models": ("models", "User.js"),
    "queue_service": ("services/queue", "queue.service.js"),
    "redis_protected_fallback": ("services/cache", "redis.client.js"),
}


class PlatformInjection:
    """Injects TRD-mandated runtime architecture into a generated project tree."""

    def generate(self, spec: Dict[str, Any], project_dir: str, mode: str = "") -> Dict[str, Any]:
        mode = mode or spec.get("layout_mode", "") or ""
        report: Dict[str, Any] = {
            "runtime_mode": spec.get("runtime_mode", "transactional" if "static" not in mode else "static"),
            "artifacts": [],
        }

        report["frontend_stack"] = self._enforce_frontend_stack(project_dir)
        report["state_topology"] = self._inject_state_topology(project_dir)
        report["lazy_layouts"] = self._inject_lazy_layouts(project_dir)
        report["cls_budget"] = self._inject_cls_guard_css(project_dir)
        report["backend_blueprint"] = self._verify_backend_blueprint(project_dir, spec)

        report["doc"] = self._write_injection_doc(project_dir, spec, report)
        report["artifacts"] = self._collect_artifacts(report)

        agent_logger.info(
            f"PlatformInjection: runtime='{report['runtime_mode']}' "
            f"stack={report['frontend_stack'].get('status')} "
            f"provider_wrapped={report['state_topology'].get('provider_wrapped')}"
        )
        return report

    # ── 1. Core stack pins (React 19.2.x / Vite 8.2.x / Tailwind v3.4.x) ──
    def _enforce_frontend_stack(self, project_dir: str) -> Dict[str, Any]:
        pkg_path = os.path.join(project_dir, "frontend", "package.json")
        if not os.path.isfile(pkg_path):
            return {"status": "skip", "reason": "frontend/package.json missing"}
        pkg = FileManager.read_json(pkg_path)
        deps = pkg.setdefault("dependencies", {})
        dev = pkg.setdefault("devDependencies", {})
        muted: Dict[str, Any] = {"status": "ok", "pins": {}, "notes": []}

        def set_pin(bucket: Dict[str, str], name: str, pin: str) -> None:
            current = bucket.get(name)
            if current != pin:
                bucket[name] = pin
                muted["pins"][name] = f"{current or '-'} -> {pin}"
                muted["notes"].append(f"{name}: {pin}")

        if "react" in deps or "react-dom" in deps:
            set_pin(deps, "react", PIN_REACT)
            set_pin(deps, "react-dom", PIN_REACT_DOM)

        set_pin(deps, "@tanstack/react-query", PIN_QUERY)
        set_pin(deps, "zustand", PIN_ZUSTAND)

        vite_major = self._major(dev.get("vite", ""))
        if vite_major is None or vite_major < 8:
            set_pin(dev, "vite", PIN_VITE)
        tailwind_major = self._major(dev.get("tailwindcss") or deps.get("tailwindcss", ""))
        if tailwind_major is None or tailwind_major != 3:
            set_pin(dev, "tailwindcss", PIN_TAILWIND)

        FileManager.write_json(pkg_path, pkg)
        return muted

    @staticmethod
    def _major(version: str) -> Optional[int]:
        parsed = re.match(r"\s*[\^~>=]*\s*(\d+)", version)
        return int(parsed.group(1)) if parsed else None

    # ── 2. State topologies (React Query cache cluster + Zustand) ──────────
    def _inject_state_topology(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"status": "skip", "reason": "frontend/src missing"}
        artifacts: Dict[str, str] = {}

        artifacts["queryClient"] = self._write(
            src, "lib", "queryClient.js",
            """/**
 * Server-state cache cluster (TanStack React Query).
 * Platform TRD: single QueryClient — staleTime 5m, gcTime 30m, retry 2.
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export default queryClient;
""",
        )

        artifacts["useApiQuery"] = self._write(
            src, "hooks", "useApiQuery.js",
            """/**
 * useApiQuery — server-state hook bound to the platform Axios client.
 * Dynamic import keeps static (API-less) builds green: falls back to a
 * relative fetch when the enterprise api.js interceptor is not present.
 */
import { useQuery } from '@tanstack/react-query';

const loadRequester = async () => {
  try {
    const mod = await import('../services/api');
    return mod.api || mod.default;
  } catch (e) {
    return {
      async get(path, cfg) {
        const res = await fetch(`/api${path}`, cfg);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      },
    };
  }
};

export default function useApiQuery(queryKey, path, options = {}) {
  return useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const api = await loadRequester();
      const data = await api.get(path, { signal });
      return data?.data ?? data;
    },
    ...options,
  });
}
""",
        )

        artifacts["AppProviders"] = self._write(
            src, "lib", "AppProviders.jsx",
            """/**
 * AppProviders — platform provider stack (QueryClientProvider root).
 * Platform TRD: server state must live on the TanStack cache cluster.
 */
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';

export default function AppProviders({ children }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
""",
        )

        artifacts["zustand_store"] = self._write(
            src, "store", "useAppStore.js",
            """/**
 * Client-state store wrapper (Zustand).
 * Platform TRD: lightweight store wrapper for UI/fragment state —
 * server state stays in the React Query cache cluster.
 */
import { create } from 'zustand';

export const useAppStore = create((set) => ({
  ui: { sidebarOpen: false },
  toggleSidebar: () => set((s) => ({ ui: { ...s.ui, sidebarOpen: !s.ui.sidebarOpen } })),
  cart: [],
  addItem: (item) => set((s) => ({ cart: [...s.cart, item] })),
  removeItem: (id) => set((s) => ({ cart: s.cart.filter((i) => i.id !== id) })),
  clearCart: () => set({ cart: [] }),
}));

export default useAppStore;
""",
        )

        wrapped = self._wrap_provider(src)
        return {
            "status": "ok",
            "artifacts": artifacts,
            "provider_wrapped": bool(wrapped),
            "app_path": wrapped or None,
        }

    def _wrap_provider(self, src: str) -> Optional[str]:
        """Replace `export default App;` with a provider-wrapped default export."""
        app_path = os.path.join(src, "App.jsx")
        if not os.path.isfile(app_path):
            return None
        content = FileManager.read_file(app_path)
        if _MARKER in content:
            return None  # already wrapped

        lines = content.splitlines()
        out: list = []
        replaced = False
        for line in lines:
            stripped = line.strip()
            if not replaced and stripped == "export default App;":
                out.append("export default function AppWithProviders() {")
                out.append("  return (")
                out.append("    <AppProviders>")
                out.append("      <App />")
                out.append("    </AppProviders>")
                out.append("  );")
                out.append("}")
                replaced = True
            else:
                out.append(line)

        if not replaced:
            return None  # unknown template shape — skip silently

        # Inject the AppProviders import after the first import line.
        import_line = f"import AppProviders from './lib/AppProviders'; // {_MARKER}\n"
        if replaced:
            text = "\n".join(out)
            if "import AppProviders" not in text:
                idx = text.index("import ")
                nl = text.index("\n", idx)
                text = text[: nl + 1] + import_line + text[nl + 1:]
            # No raw-text markers may leak into module scope.
            FileManager.write_file(app_path, text)
            return app_path
        return None

    # ── 3. Optimization (React.lazy layouts + CLS safety) ──────────────────
    def _inject_lazy_layouts(self, project_dir: str) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        if not os.path.isdir(src):
            return {"status": "skip", "reason": "frontend/src missing"}
        artifacts: Dict[str, str] = {}

        artifacts["layout_landing"] = self._write(
            src, "layouts", "LandingLayout.jsx",
            """/**
 * LandingLayout — alternative public landing layout template.
 * Code-split: loaded via React.lazy() (Platform TRD optimization mandate).
 */
export default function LandingLayout({ children }) {
  return (
    <div className="fluid-container min-h-screen py-fluid-6">
      <header className="flex items-center justify-between">
        <span className="text-lg font-bold">Brand</span>
        <nav className="flex gap-fluid-4" aria-label="Primary">Placeholders</nav>
      </header>
      <main>{children}</main>
      <footer className="mt-fluid-6 border-t border-slate-800 pt-fluid-3 text-sm opacity-70">© {new Date().getFullYear()} Brand. All rights reserved.</footer>
    </div>
  );
}
""",
        )
        artifacts["layout_app"] = self._write(
            src, "layouts", "AppLayout.jsx",
            """/**
 * AppLayout — authenticated/application layout template.
 * Code-split: loaded via React.lazy() (Platform TRD optimization mandate).
 */
export default function AppLayout({ children }) {
  return (
    <div className="fluid-container min-h-screen py-fluid-6">
      <header className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/60 px-fluid-3 py-fluid-2">
        <span className="font-bold">Console</span>
        <span className="text-sm opacity-60">Signed in</span>
      </header>
      <main className="mt-fluid-4 grid gap-fluid-5 lg:grid-cols-[220px_1fr]">
        <aside className="space-y-2 text-sm" aria-label="Navigation">Nav</aside>
        <section>{children}</section>
      </main>
    </div>
  );
}
""",
        )
        artifacts["layout_skeleton"] = self._write(
            src, "components", "common", "LayoutSkeleton.jsx",
            """/**
 * LayoutSkeleton — CLS-safe placeholder (reserved height, no layout shift).
 * Platform TRD: zero unhandled layout shifts, CLS budget < 0.1.
 */
export default function LayoutSkeleton({ minHeight = '70vh', shimmer = true }) {
  return (
    <div aria-hidden="true" className={shimmer ? 'skeleton-shimmer' : undefined} style={{ minHeight, width: '100%' }} />
  );
}
""",
        )
        artifacts["lazy_layout_registry"] = self._write(
            src, "lib", "LazyLayouts.jsx",
            """/**
 * LazyLayouts — React.lazy() registry for alternative layout templates.
 * Platform TRD: strict dynamic lazy loading for alternative layouts;
 * each template ships its own Suspense boundary with a CLS-safe skeleton.
 */
import React, { Suspense } from 'react';
import LayoutSkeleton from '../components/common/LayoutSkeleton';

export const LandingLayout = React.lazy(() => import('../layouts/LandingLayout'));
export const AppLayout = React.lazy(() => import('../layouts/AppLayout'));

export function withLayout(Layout) {
  return function LazyLayout(props) {
    return (
      <Suspense fallback={<LayoutSkeleton />}>
        <Layout {...props} />
      </Suspense>
    );
  };
}

export default { LandingLayout, AppLayout, withLayout };
""",
        )

        return {"status": "ok", "artifacts": artifacts}

    def _inject_cls_guard_css(self, project_dir: str) -> Dict[str, Any]:
        css_path = os.path.join(project_dir, "frontend", "src", "index.css")
        if not os.path.isfile(css_path):
            return {"status": "skip", "reason": "index.css missing"}
        existing = FileManager.read_file(css_path)
        if _MARKER in existing:
            return {"status": "skip", "reason": "already-present"}
        block = """
/* ── Platform TRD: CLS guard (budget < 0.1) ────────────────── */
/* LUMICORE_PLATFORM:cls_budget */
@layer utilities {
  img, video, iframe { max-width: 100%; display: block; }
  .cls-reserve { width: 100%; aspect-ratio: var(--cls-ar, 16 / 9); }
  .skeleton-shimmer { position: relative; overflow: hidden; background: rgb(148 163 184 / 0.12); }
  .skeleton-shimmer::after {
    content: ''; position: absolute; inset: 0; transform: translateX(-100%);
    background: linear-gradient(90deg, transparent, rgb(148 163 184 / 0.18), transparent);
    animation: lc-shimmer 1.6s infinite;
  }
}
@media (prefers-reduced-motion: reduce) {
  .skeleton-shimmer::after { animation: none; }
}
@keyframes lc-shimmer { to { transform: translateX(100%); } }
/* ── End Platform TRD CLS guard ──────────────────────────────── */
"""
        FileManager.write_file(css_path, existing.rstrip("\n") + "\n" + block)
        return {"status": "ok", "file": "frontend/src/index.css"}

    # ── 4. Backend blueprint conformance (enterprise only) ─────────────────
    def _verify_backend_blueprint(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        runtime = spec.get("runtime_mode", "transactional")
        backend_dir = os.path.join(project_dir, "backend")
        if runtime != "transactional" or not os.path.isdir(backend_dir):
            return {
                "runtime": runtime,
                "applies": False,
                "reason": "API-less static runtime — backend blueprint not mounted (by design)",
            }

        checks: Dict[str, Any] = {}
        for key, (subdir, fname) in _BACKEND_PIPELINE.items():
            full = os.path.join(backend_dir, subdir, fname)
            ok = os.path.isfile(full)
            extra = ""
            if ok and key in ("queue_service", "redis_protected_fallback"):
                content = FileManager.read_file(full)
                extra = (
                    "in-memory fallback present"
                    if "isMemory" in content
                    else "isMemory fallback missing"
                )
            elif ok and key in ("response_envelope", "error_handler"):
                content = FileManager.read_file(full)
                extra = "status-code helpers present" if "status" in content else "no status helpers"
            checks[key] = {"pass": ok, "hint": extra}

        queue_fb = checks["queue_service"]["pass"] and checks["queue_service"]["hint"] == "in-memory fallback present"
        redis_fb = checks["redis_protected_fallback"]["pass"] and checks["redis_protected_fallback"]["hint"] == "in-memory fallback present"
        conformant = all(c["pass"] for c in checks.values()) and queue_fb and redis_fb
        checks["conformant"] = conformant
        checks["runtime"] = runtime
        checks["applies"] = True
        return checks

    # ── Documentation report ────────────────────────────────────────────────
    def _write_injection_doc(self, project_dir: str, spec: Dict[str, Any], report: Dict[str, Any]) -> str:
        project = spec.get("project_name", "This project")
        runtime = report["runtime_mode"]
        body = f"""# Platform Injection Rules (TRD #2) — {project}

> Runtime architecture mandates applied to every generated project.
> Runtime: **{runtime}** pipeline.

## Frontend Runtime Architecture
- **Core stack pins:** React ^19.2.0 / React-DOM ^19.2.0, Vite ^8.2.0, Tailwind CSS v3.4.x.
- **State topologies:** server state → TanStack React Query cache cluster
  (`src/lib/queryClient.js` mounted via `src/lib/AppProviders.jsx`); client state →
  lightweight Zustand store wrapper (`src/store/useAppStore.js`). `src/hooks/useApiQuery.js`
  binds queries to the platform Axios client (graceful relative-fetch fallback on static).
- **Optimization budgets:** alternate layout templates loaded strictly via
  `React.lazy()` (`src/lib/LazyLayouts.jsx` → `LandingLayout` / `AppLayout`) with
  Suspense + CLS-safe `LayoutSkeleton`; CLS guard utilities in `index.css`
  (img/video sizing, `.cls-reserve` aspect-ratio, shimmer skeleton).
  **CLS budget < 0.1, zero unhandled layout shifts.**

## Backend Infrastructure Blueprint (transactional runtime)
- Express decoupled route controllers (`backend/controllers/*`) with predictable
  HTTP status codes via `backend/utils/response.js` + `backend/middleware/errorHandler.js`.
- Native Sequelize models mapped to PostgreSQL/MySQL schemas (`backend/config/db.js`).
- BullMQ delayed job clusters over protected isolated Redis nodes
  (`backend/services/cache/redis.client.js`: lazy connect, retry disabled, offline queue
  off, connect timeout) with **in-memory fallback** (`connection.isMemory` →
  `backend/services/queue/queue.service.js` in-process dispatch).
- Static runtime: backend blueprint intentionally not mounted (API-less SPA).

## Conformance
- State topology: {report["state_topology"].get("status", "n/a")} —
  provider wrapped: {report["state_topology"].get("provider_wrapped", False)}.
- Lazy layouts: {report["lazy_layouts"].get("status", "n/a")}.
- CLS guard: {report["cls_budget"].get("status", "n/a")}.
- Backend blueprint:
  {self._render_backend_conformance(report["backend_blueprint"])}
"""
        path = os.path.join(project_dir, "PLATFORM-INJECTION.md")
        FileManager.write_file(path, body)
        return path

    @staticmethod
    def _render_backend_conformance(blueprint: Dict[str, Any]) -> str:
        if not blueprint.get("applies"):
            return f"not applicable ({blueprint.get('reason', 'static runtime')})."
        rows = [f"- {k}: {'PASS' if v.get('pass') else 'FAIL'} ({v.get('hint', '')})"
                for k, v in blueprint.items() if k not in ("conformant", "runtime", "applies")]
        rows.append(f"- **overall: {'CONFORMANT' if blueprint.get('conformant') else 'GAPS'}**")
        return "\n  ".join(rows)

    @classmethod
    def _collect_artifacts(cls, report: Dict[str, Any]) -> list:
        out: list = []
        if report["cls_budget"].get("file"):
            out.append(report["cls_budget"]["file"])
        out.extend(report["state_topology"].get("artifacts", {}).values())
        out.extend(report["lazy_layouts"].get("artifacts", {}).values())
        out.append(report["doc"])
        return out

    def _write(self, src: str, *rel_pos: str) -> str:
        if len(rel_pos) < 2:
            raise ValueError("_write requires at least (dir, filename, content)")
        content = rel_pos[-1]
        target = os.path.join(src, *rel_pos[:-1])
        FileManager.ensure_dir(os.path.dirname(target))
        FileManager.write_file(target, content)
        return target.replace("\\", "/")


platform_injection = PlatformInjection()