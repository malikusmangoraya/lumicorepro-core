import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from config.settings import PROJECT_ROOT, GENERATED_PROJECTS_DIR
from utils.logger import agent_logger
from utils.file_manager import FileManager
from .generation_contract import resolve_generation_contract

class ProjectBuilder:
    """Assembles template, components, assets, backend, and database schema into a generated project with NPM auto-fixing & design system injection."""

    # Template path mapping: registry "file_path" -> actual project directory
    TEMPLATE_PATH_MAP = {
        # Business
        "src/templates/business/corporate-template-01": "src/templates/business/corporate-template-01",
        # E-commerce
        "src/templates/ecommerce/electronics/electronics-template-01": "src/templates/ecommerce/electronics/electronics-template-01",
        "src/templates/ecommerce/electronics/electronics-template-02": "src/templates/ecommerce/electronics/electronics-template-02",
        "src/templates/ecommerce/electronics/electronics-template-03": "src/templates/ecommerce/electronics/electronics-template-03",
        # Real estate
        "src/templates/realestate/property-template-01": "src/templates/realestate/property-template-01",
        # Restaurant
        "src/templates/restaurant/cafe-template-01": "src/templates/restaurant/cafe-template-01",
        # Portfolio
        "src/templates/portfolio/personal-template-01": "src/templates/portfolio/personal-template-01",
        # Education
        "src/templates/education/lms-template-01": "src/templates/education/lms-template-01",
        # Healthcare
        "src/templates/healthcare/medical-template-01": "src/templates/healthcare/medical-template-01",
        # Fitness
        "src/templates/fitness/gym-template-01": "src/templates/fitness/gym-template-01",
        # Travel
        "src/templates/travel/agency-template-01": "src/templates/travel/agency-template-01",
        # Creative
        "src/templates/creative/studio-template-01": "src/templates/creative/studio-template-01",
        # Marketplace
        "src/templates/marketplace/marketplace-01": "src/templates/marketplace/marketplace-01",
        "src/templates/ecommerce/marketplace-global-01": "src/templates/ecommerce/marketplace-global-01",
    }

    # Fallback template per category (first available in that category)
    CATEGORY_FALLBACK_TEMPLATES = {
        "business": "src/templates/business/corporate-template-01",
        "ecommerce": "src/templates/ecommerce/electronics/electronics-template-01",
        "realestate": "src/templates/realestate/property-template-01",
        "restaurant": "src/templates/restaurant/cafe-template-01",
        "portfolio": "src/templates/portfolio/personal-template-01",
        "education": "src/templates/education/lms-template-01",
        "healthcare": "src/templates/healthcare/medical-template-01",
        "fitness": "src/templates/fitness/gym-template-01",
        "travel": "src/templates/travel/agency-template-01",
        "creative": "src/templates/creative/studio-template-01",
        "saas": "src/templates/business/corporate-template-01",
        "dashboard": "src/templates/business/corporate-template-01",
        "fintech": "src/templates/business/corporate-template-01",
        "social": "src/templates/business/corporate-template-01",
        "fashion": "src/templates/ecommerce/electronics/electronics-template-01",
        "marketplace": "src/templates/marketplace/marketplace-01",
    }

    PACKAGE_VERSION_MAP = {
        "react": "^19.2.8",
        "react-dom": "^19.2.8",
        "react-router-dom": "^6.22.0",
        "lucide-react": "^1.31.0",
        "framer-motion": "^11.18.2",
        "recharts": "^2.12.0",
        "axios": "^1.6.7",
        "tailwindcss": "^3.4.1",
        "autoprefixer": "^10.4.18",
        "postcss": "^8.4.35",
        "express": "^4.19.2",
        "cors": "^2.8.5",
        "dotenv": "^16.4.5",
        "pg": "^8.11.5",
        "jsonwebtoken": "^9.0.2",
        "bcryptjs": "^2.4.3",
        "express-validator": "^7.0.1"
    }

    @staticmethod
    def _is_project_template(path: Path) -> bool:
        """A usable frontend template must be a real Vite project root.

        Guards against section-level folders (LandingPage.jsx, ServicesPage,
        etc.) being copied raw into frontend/ — which produced broken builds
        where no package.json/index.html existed. Also refuses the monorepo
        root / template library root themselves (they are not templates).
        """
        try:
            resolved = path.resolve()
            templates_root = (PROJECT_ROOT / 'src' / 'templates').resolve()
            if resolved == PROJECT_ROOT or resolved == templates_root:
                return False
            try:
                resolved.relative_to(templates_root)  # must live inside src/templates
            except ValueError:
                return False
            if not (resolved / 'package.json').exists():
                return False
            if not (resolved / 'index.html').exists():
                return False
        except OSError:
            return False
        return True

    def _resolve_template_path(self, template_info: Dict[str, Any]) -> Path:
        """Resolve template directory path using mapping, with fallback logic.

        Only real project templates (dir containing package.json + index.html)
        are accepted. Anything else signals the caller to use the default
        Vite scaffold, guaranteeing a valid buildable frontend every time.
        """
        rel_path = template_info.get("file_path", "") if template_info else ""
        # Use the mapping if available, otherwise use rel_path directly
        mapped = self.TEMPLATE_PATH_MAP.get(rel_path, rel_path)
        resolved = (PROJECT_ROOT / mapped).resolve()
        if self._is_project_template(resolved):
            return resolved
        # Try mapping without the "src/templates/" prefix
        alt_path = "src/templates/" + rel_path.replace("src/templates/", "")
        alt_resolved = (PROJECT_ROOT / alt_path).resolve()
        if self._is_project_template(alt_resolved):
            return alt_resolved
        # Try every known template path as fallback
        for known in self.TEMPLATE_PATH_MAP.values():
            candidate = (PROJECT_ROOT / known).resolve()
            if self._is_project_template(candidate):
                agent_logger.warning(f"Template {rel_path} not found, falling back to {known}")
                return candidate
        # Return a path that certainly does not exist → default scaffold builds
        return resolved.with_name(resolved.name + ".__missing__")

    def build_project(self, plan: Dict[str, Any]) -> str:
        """Execute assembly plan and return path of generated project."""
        spec = plan.get("spec") or {}
        contract = plan.get("generation_contract") or resolve_generation_contract(spec)
        plan["generation_contract"] = contract
        plan["layout_mode"] = contract["layout_mode"]
        plan["features"] = contract["features"]
        project_name = self._safe_project_name(plan.get("project_name", "generated-app"))

        # Idempotent regeneration: never overwrite an existing project dir.
        # Re-running the same spec gets a unique `-002`, `-003`, ... suffix so
        # previous generations keep their preview/dev history intact.
        generated_root = Path(GENERATED_PROJECTS_DIR).resolve(strict=False)
        target_dir = (generated_root / project_name).resolve(strict=False)
        if target_dir.exists():
            base_name = project_name
            counter = 2
            while (generated_root / f"{base_name}-{counter:03d}").exists():
                counter += 1
            project_name = f"{base_name}-{counter:03d}"
            target_dir = (generated_root / project_name).resolve(strict=False)

        plan["project_name"] = project_name
        try:
            target_dir.relative_to(generated_root)
        except ValueError:
            pass
        agent_logger.info(f"Building project '{project_name}' at: {target_dir}")

        FileManager.ensure_dir(str(target_dir), str(GENERATED_PROJECTS_DIR))
        frontend_dir = target_dir / "frontend"
        backend_dir = target_dir / "backend"
        database_dir = target_dir / "database"

        # 1. Copy Frontend Template
        template_info = plan.get("template", {})
        template_src = self._resolve_template_path(template_info)

        if template_src.exists():
            agent_logger.info(f"Copying frontend template from: {template_src}")
            FileManager.copy_directory(str(template_src), str(frontend_dir), ignore_patterns=["node_modules", "dist", ".git"])
        else:
            agent_logger.warning(f"Template path {template_src} not found. Creating default scaffold.")
            FileManager.ensure_dir(str(frontend_dir / "src"))
            FileManager.ensure_dir(str(frontend_dir / "src" / "pages"))
            # Create default package.json & App.jsx with routing + pages
            default_pkg = {
                "name": project_name,
                "private": True,
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "react": "^19.2.0",
                    "react-dom": "^19.2.0",
                    "@tanstack/react-query": "^5.59.0",
                    "zustand": "^5.0.0",
                    "react-router-dom": "^6.22.0",
                    "lucide-react": "^1.31.0",
                    "framer-motion": "^11.18.2",
                    "i18next": "^25.0.0",
                    "react-i18next": "^16.0.0",
                    "axios": "^1.6.0"
                },
                "devDependencies": {
                    "@vitejs/plugin-react": "^6.0.4",
                    "vite": "^8.2.0",
                    "tailwindcss": "^3.4.0",
                    "autoprefixer": "^10.4.0",
                    "postcss": "^8.4.0"
                }
            }
            FileManager.write_json(str(frontend_dir / "package.json"), default_pkg)

            # Vite config
            vite_config = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
});
"""
            FileManager.write_file(str(frontend_dir / "vite.config.js"), vite_config)

            # Tailwind config
            tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#06b6d4', foreground: '#ffffff' },
        secondary: { DEFAULT: '#8b5cf6', foreground: '#ffffff' },
        accent: { DEFAULT: '#f59e0b', foreground: '#000000' },
        muted: { DEFAULT: '#1e293b', foreground: '#94a3b8' },
        card: { DEFAULT: '#0f172a', foreground: '#e2e8f0' },
        border: '#1e293b',
      },
    },
  },
  plugins: [],
};
"""
            FileManager.write_file(str(frontend_dir / "tailwind.config.js"), tailwind_config)

            # PostCSS config
            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
            FileManager.write_file(str(frontend_dir / "postcss.config.js"), postcss_config)

            # index.html
            index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name}</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>"""
            FileManager.write_file(str(frontend_dir / "index.html"), index_html)

            # main.jsx
            main_jsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
            FileManager.write_file(str(frontend_dir / "src" / "main.jsx"), main_jsx)

            # index.css
            index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-slate-950 text-slate-100 font-sans antialiased;
  }
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "index.css"), index_css)

            # App.jsx — proper routing + page components + commercial studio + cookie banner
            default_app = f"""import React, {{ Suspense, lazy }} from 'react';
import {{ BrowserRouter, Routes, Route }} from 'react-router-dom';
import CookieConsent from './components/common/CookieConsent';
import ThemeCustomizer from './components/common/ThemeCustomizer';
import ContactBanner from './components/common/ContactBanner';
import Sidebar from './components/Sidebar';

const Home = lazy(() => import('./pages/Home'));
const Pricing = lazy(() => import('./pages/Pricing'));
const About = lazy(() => import('./pages/About'));
const Services = lazy(() => import('./pages/Services'));
const Contact = lazy(() => import('./pages/Contact'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const Billing = lazy(() => import('./pages/Billing'));

function Loader() {{
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
    </div>
  );
}}

function AppShell() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <main className="ml-0 md:ml-72 pb-8">
        <Suspense fallback={{<Loader />}}>
          <Routes>
            <Route path="/" element={{<Home />}} />
            <Route path="/dashboard" element={{<Dashboard />}} />
            <Route path="/profile" element={{<Profile />}} />
            <Route path="/billing" element={{<Billing />}} />
            <Route path="/pricing" element={{<Pricing />}} />
            <Route path="/about" element={{<About />}} />
            <Route path="/services" element={{<Services />}} />
            <Route path="/contact" element={{<Contact />}} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}}

export default function App() {{
  return (
    <BrowserRouter>
      <ContactBanner />
      <AppShell />
      <CookieConsent />
      <ThemeCustomizer />
    </BrowserRouter>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "App.jsx"), default_app)

            default_sidebar = """import React, { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { BarChart3, CreditCard, Home, Menu, Settings, User, X } from 'lucide-react';

const navItems = [
  { label: 'Overview', to: '/', icon: Home },
  { label: 'Dashboard', to: '/dashboard', icon: BarChart3 },
  { label: 'Billing', to: '/billing', icon: CreditCard },
  { label: 'Profile', to: '/profile', icon: User },
  { label: 'Settings', to: '/profile', icon: Settings },
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        aria-label="Open navigation menu"
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-50 flex h-11 w-11 items-center justify-center rounded-xl border border-slate-700 bg-slate-900 text-slate-100 md:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      <aside className="hidden w-72 border-r border-slate-800 bg-slate-950/90 p-5 md:flex md:flex-col md:fixed md:inset-y-0 md:left-0">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-violet-500 text-lg font-bold text-white">P</div>
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Portal</p>
            <h2 className="text-lg font-semibold text-white">Workspace</h2>
          </div>
        </div>

        <nav className="space-y-2">
          {navItems.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => [
                'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                isActive ? 'bg-cyan-500/10 text-cyan-300' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
              ].join(' ')}
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 bg-slate-950/80 md:hidden" onClick={() => setOpen(false)}>
          <div className="absolute inset-y-0 left-0 w-72 border-r border-slate-800 bg-slate-950 p-5" onClick={(event) => event.stopPropagation()}>
            <div className="mb-8 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-violet-500 text-lg font-bold text-white">P</div>
                <h2 className="text-base font-semibold text-white">Workspace</h2>
              </div>
              <button type="button" aria-label="Close navigation" onClick={() => setOpen(false)} className="rounded-lg border border-slate-700 p-1.5 text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>
            <nav className="space-y-2">
              {navItems.map(({ label, to, icon: Icon }) => (
                <Link key={to} to={to} onClick={() => setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white">
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "Sidebar.jsx"), default_sidebar)

            default_dashboard = """import React from 'react';

const stats = [
  { label: 'Revenue', value: '$48.2K', change: '+12.4%' },
  { label: 'Orders', value: '1,284', change: '+8.1%' },
  { label: 'Conversion', value: '6.8%', change: '+1.2%' },
  { label: 'Retention', value: '92%', change: '+4.7%' },
];

export default function Dashboard() {
  return (
    <div className="p-4 md:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-cyan-300">Overview</p>
            <h1 className="text-3xl font-bold text-white">Operations dashboard</h1>
          </div>
          <button type="button" className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-200">
            Export report
          </button>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {stats.map((item) => (
            <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg shadow-slate-950/20">
              <p className="text-sm text-slate-400">{item.label}</p>
              <div className="mt-4 flex items-end justify-between">
                <span className="text-2xl font-bold text-white">{item.value}</span>
                <span className="text-xs font-medium text-emerald-400">{item.change}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-semibold text-white">Sales trend</h2>
            <div className="mt-5 h-56 rounded-xl bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 p-4">
              <div className="flex h-full items-end gap-3">
                {[30, 55, 48, 72, 67, 82, 96].map((height, index) => (
                  <div key={index} className="flex-1 rounded-t-xl bg-gradient-to-t from-cyan-500 to-violet-500" style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-semibold text-white">Recent activity</h2>
            <ul className="mt-4 space-y-4 text-sm text-slate-300">
              <li className="flex items-center justify-between rounded-xl bg-slate-800/60 p-3"><span>New customer</span><span className="text-cyan-300">+24</span></li>
              <li className="flex items-center justify-between rounded-xl bg-slate-800/60 p-3"><span>Refund requests</span><span className="text-amber-300">3</span></li>
              <li className="flex items-center justify-between rounded-xl bg-slate-800/60 p-3"><span>Open tickets</span><span className="text-violet-300">7</span></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Dashboard.jsx"), default_dashboard)

            default_profile = """import React from 'react';

export default function Profile() {
  return (
    <div className="p-4 md:p-8">
      <div className="mx-auto max-w-4xl space-y-6 rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl shadow-slate-950/20">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 text-xl font-bold text-white">A</div>
          <div>
            <h1 className="text-2xl font-bold text-white">Alex Morgan</h1>
            <p className="text-sm text-slate-400">Product lead</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Full name
            <input defaultValue="Alex Morgan" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none" />
          </label>
          <label className="text-sm text-slate-300">
            Email
            <input defaultValue="alex@acme.com" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none" />
          </label>
        </div>

        <div className="flex gap-3">
          <button type="button" className="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-white">Save changes</button>
          <button type="button" className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200">Change password</button>
        </div>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Profile.jsx"), default_profile)

            default_billing = """import React from 'react';

export default function Billing() {
  return (
    <div className="p-4 md:p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <p className="text-xs uppercase tracking-[0.22em] text-cyan-300">Payments</p>
          <h1 className="mt-2 text-2xl font-bold text-white">Billing & subscriptions</h1>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">Current plan</p>
            <p className="mt-2 text-2xl font-bold text-white">Pro</p>
            <p className="mt-3 text-sm text-emerald-400">Next invoice in 6 days</p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-sm text-slate-400">Payment method</p>
            <p className="mt-2 text-lg font-semibold text-white">Visa •••• 4242</p>
            <p className="mt-3 text-sm text-slate-400">Sandbox mode enabled</p>
          </div>
        </div>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Billing.jsx"), default_billing)

            # Common UI utility — `cn` + `getAnimationClass` helpers used across pro components.
            default_utils = """export const ANIMATIONS = {
  none: '',
  fade: 'animate-fade-in',
  'fade-up': 'animate-fade-in-up',
  'fade-down': 'animate-fade-in-down',
  'fade-left': 'animate-fade-in-left',
  'fade-right': 'animate-fade-in-right',
  scale: 'animate-scale-in',
  'bounce-in': 'animate-bounce-in',
  'slide-up': 'animate-slide-in-up',
  'slide-left': 'animate-slide-in-left',
  'slide-right': 'animate-slide-in-right',
  shake: 'animate-shake',
  float: 'animate-float',
};

export const ANIMATION_DELAYS = {
  0: '',
  75: 'delay-75',
  100: 'delay-100',
  150: 'delay-150',
  200: 'delay-200',
  300: 'delay-300',
  500: 'delay-500',
  700: 'delay-700',
  1000: 'delay-1000',
};

export function getAnimationClass(animate, delay = 0) {
  if (!animate || animate === 'none') return '';
  const anim = ANIMATIONS[animate] || '';
  const delayClass = ANIMATION_DELAYS[delay] || '';
  return [anim, delayClass].filter(Boolean).join(' ');
}

export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "utils.js"), default_utils)

            for feature_dir in [
                "auth",
                "dashboard",
                "profile",
                "payments",
            ]:
                FileManager.ensure_dir(str(frontend_dir / "src" / "features" / feature_dir))
            FileManager.ensure_dir(str(frontend_dir / "src" / "lib"))
            FileManager.write_file(
                str(frontend_dir / "src" / "lib" / "paymentProvider.js"),
                """export class MockPaymentProvider {\n  async createCheckoutSession({ amount, currency, customerId }) {\n    return {\n      id: 'mock-checkout-session',\n      amount,\n      currency: currency || 'USD',\n      customerId: customerId || 'demo-customer',\n      status: 'pending',\n      provider: 'mock',\n    };\n  }\n\n  async verifyWebhook(event) {\n    return {\n      ok: true,\n      provider: 'mock',\n      eventType: event?.type || 'payment.succeeded',\n      id: event?.id || 'demo-event',\n    };\n  }\n}\n\nexport const paymentProvider = new MockPaymentProvider();\nexport default paymentProvider;\n""",
            )
            FileManager.write_file(
                str(frontend_dir / "src" / "features" / "auth" / "index.js"),
                """export const authFeature = { name: 'auth', defaultRoute: '/login' };\nexport default authFeature;\n""",
            )
            FileManager.write_file(
                str(frontend_dir / "src" / "features" / "dashboard" / "index.js"),
                """export const dashboardFeature = { name: 'dashboard', defaultRoute: '/dashboard' };\nexport default dashboardFeature;\n""",
            )
            FileManager.write_file(
                str(frontend_dir / "src" / "features" / "profile" / "index.js"),
                """export const profileFeature = { name: 'profile', defaultRoute: '/profile' };\nexport default profileFeature;\n""",
            )
            FileManager.write_file(
                str(frontend_dir / "src" / "features" / "payments" / "index.js"),
                """export const paymentsFeature = { name: 'payments', defaultRoute: '/billing' };\nexport default paymentsFeature;\n""",
            )

            # Default CookieConsent banner — always present so the mount never breaks.
            # ComplianceGenerator may overwrite this with a region-specific variant.
            FileManager.ensure_dir(str(frontend_dir / "src" / "components" / "common"))
            default_cookie_consent = """import React, { useEffect, useState } from 'react';

const STORAGE_KEY = 'cookie_consent';

function getStoredConsent() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch (e) {
    return null;
  }
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!getStoredConsent()) setVisible(true);
  }, []);

  const decide = (value) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    setVisible(false);
    window.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: value }));
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      aria-live="polite"
      className="fixed bottom-4 left-4 right-4 z-50 max-w-md mx-auto p-4 rounded-xl bg-slate-900 text-slate-200 border border-slate-800 shadow-2xl font-sans"
    >
      <p className="mb-3 text-xs leading-relaxed text-slate-300">
        We use cookies to make our site work and, where you agree, to analyse traffic
        and personalise content. Essential cookies are always active.
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => decide({ essential: true, analytics: true, marketing: false })}
          className="flex-1 py-2 px-3 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-white text-xs font-semibold transition-colors"
        >
          Accept All
        </button>
        <button
          type="button"
          onClick={() => decide({ essential: true, analytics: false, marketing: false })}
          className="flex-1 py-2 px-3 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition-colors"
        >
          Essential Only
        </button>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "CookieConsent.jsx"), default_cookie_consent)

            # ── Modular UI & Navigation Components ───────────────────────────
            unique_logo_comp = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';

export default function UniqueLogo({{ name = '{project_name}', size = 'md' }}) {{
  const sz = {{ sm: 24, md: 32, lg: 40 }}[size] || 32;
  const words = name.split(/(?=[A-Z])|\\s+/).filter(Boolean);
  const primaryWord = words[0] || name;
  const accentWord = words.slice(1).join('') || '';

  return (
    <Link to="/" className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90">
      <svg viewBox="0 0 48 48" width={{sz}} height={{sz}} className="shrink-0" fill="none">
        <defs>
          <linearGradient id="brand-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgb(6, 182, 212)" />
            <stop offset="100%" stopColor="rgb(139, 92, 246)" />
          </linearGradient>
        </defs>
        <polygon points="24,4 42,14 42,34 24,44 6,34 6,14" fill="url(#brand-grad)" opacity="0.95" />
        <polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9" />
        <polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="url(#brand-grad)" />
      </svg>
      <span className="font-extrabold text-xl tracking-tight text-white font-sans">
        {{primaryWord}}
        {{accentWord && <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent ml-0.5">{{accentWord}}</span>}}
      </span>
    </Link>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "UniqueLogo.jsx"), unique_logo_comp)

            # Navbar Component
            selected_mode = str(
                plan.get("layout_mode")
                or (plan.get("spec") or {}).get("layout_mode")
                or (plan.get("spec") or {}).get("buyer_type")
                or (plan.get("spec") or {}).get("deployment_mode")
                or ""
            ).lower()
            static_mode_terms = ("client-only", "client_only", "static", "showcase", "landing", "brochure")
            account_links = (
                "    { path: '/login', label: 'Sign in' },\n"
                "    { path: '/register', label: 'Create account' },\n"
                if not any(term in selected_mode for term in static_mode_terms)
                else ""
            )
            navbar_comp = f"""import React, {{ useState }} from 'react';
import {{ Link, useLocation }} from 'react-router-dom';
import {{ Menu, X, Sparkles, ArrowRight }} from 'lucide-react';
import UniqueLogo from './UniqueLogo';

export default function Navbar() {{
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const links = [
    {{ path: '/', label: 'Home' }},
    {{ path: '/about', label: 'About' }},
    {{ path: '/services', label: 'Services' }},
    {{ path: '/contact', label: 'Contact' }},
{account_links.rstrip()}
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <UniqueLogo name="{project_name}" size="md" />

        <div className="hidden md:flex items-center gap-8">
          <div className="flex items-center gap-6">
            {{links.map((link) => (
              <Link
                key={{link.path}}
                to={{link.path}}
                className={{location.pathname === link.path ? "text-sm font-semibold text-cyan-400" : "text-sm font-medium text-slate-300 hover:text-white transition-colors"}}
              >
                {{link.label}}
              </Link>
            ))}}
          </div>
          <Link
            to="/pricing"
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all active:scale-95"
          >
            Get in touch <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <button
          onClick={{() => setMobileOpen(!mobileOpen)}}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          aria-label="Toggle menu"
        >
          {{mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}}
        </button>
      </div>

      {{mobileOpen && (
        <div className="md:hidden mt-4 pt-4 border-t border-slate-800 flex flex-col gap-3">
          {{links.map((link) => (
            <Link
              key={{link.path}}
              to={{link.path}}
              onClick={{() => setMobileOpen(false)}}
              className="px-2 py-1.5 text-slate-300 hover:text-cyan-400 font-medium"
            >
              {{link.label}}
            </Link>
          ))}}
          <Link
            to="/contact"
            onClick={{() => setMobileOpen(false)}}
            className="mt-2 text-center rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-white"
          >
            Get Started
          </Link>
        </div>
      )}}
    </nav>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "Navbar.jsx"), navbar_comp)

            # Modern Multi-Column Professional Footer
            footer_comp = f"""import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Sparkles, Mail, CheckCircle2, Zap, ArrowUp }} from 'lucide-react';
import UniqueLogo from './UniqueLogo';

export default function Footer() {{
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e) => {{
    e.preventDefault();
    if (email) {{
      setSubscribed(true);
    }}
  }};

  const scrollToTop = () => {{
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }};

  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-5">
          <div className="lg:col-span-2 space-y-4">
            <UniqueLogo name="{project_name}" size="lg" />
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              Empowering next-generation digital experiences. Built with performance, security, and world-class design in mind.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              All systems operational &bull; 99.99%
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/pricing" className="hover:text-cyan-400 transition-colors">Pricing &amp; Plans</Link></li>
              <li><Link to="/services" className="hover:text-cyan-400 transition-colors">Features &amp; Solutions</Link></li>
              <li><Link to="/about" className="hover:text-cyan-400 transition-colors">Case Studies</Link></li>
              <li><Link to="/contact" className="hover:text-cyan-400 transition-colors">Enterprise SLA</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/about" className="hover:text-cyan-400 transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-cyan-400 transition-colors">Contact</Link></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-cyan-400 transition-colors">Privacy Policy</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sm text-white uppercase tracking-wider mb-4">Stay Updated</h4>
            <p className="text-xs text-slate-400 mb-3">Join our newsletter for weekly product updates and insights.</p>
            {{subscribed ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="h-4 w-4" /> Subscribed successfully!
              </div>
            ) : (
              <form onSubmit={{handleSubscribe}} className="space-y-2">
                <input
                  type="email"
                  required
                  value={{email}}
                  onChange={{(e) => setEmail(e.target.value)}}
                  placeholder="Enter work email"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <button
                  type="submit"
                  className="w-full rounded-lg bg-cyan-600 px-3 py-2 text-xs font-semibold text-white hover:bg-cyan-500 transition-colors"
                >
                  Subscribe
                </button>
              </form>
            )}}
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>&copy; {{new Date().getFullYear()}} {project_name}. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1"><Zap className="h-3.5 w-3.5 text-cyan-400" /> Powered by React 19 + Vite</span>
            <button onClick={{scrollToTop}} className="p-1.5 rounded-lg border border-slate-800 hover:text-white" aria-label="Scroll to top">
              <ArrowUp className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "Footer.jsx"), footer_comp)

            # ── Page Components ────────────────────────────────────────────
            # Home page
            home_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight, Sparkles, Globe, Zap, Shield, Palette, Layers, Star, CheckCircle2 }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

const features = [
  {{ icon: Sparkles, title: 'AI-Powered Intelligence', desc: 'Accelerate productivity with cutting-edge automated pipelines.' }},
  {{ icon: Globe, title: 'Global Scale Ready', desc: 'Engineered for internationalization, multi-currency, and edge routing.' }},
  {{ icon: Zap, title: 'Sub-Second Speeds', desc: 'Ultra-optimized bundle architecture with React 19 and Vite.' }},
  {{ icon: Shield, title: 'Bank-Grade Security', desc: 'Built-in security audits, CSP headers, and enterprise encryption.' }},
  {{ icon: Palette, title: 'Adaptive Design System', desc: 'Bespoke UI styling with fluid typography and smooth micro-interactions.' }},
  {{ icon: Layers, title: 'Modular Architecture', desc: 'Scalable component design ready for rapid expansion and maintenance.' }},
];

export default function Home() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-400">
      <Navbar />

      <main className="flex-1">
        {{/* Hero Section */}}
        <section className="relative overflow-hidden px-6 pt-24 pb-20 text-center lg:pt-32 lg:pb-28">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.12)_0,transparent_70%)]" />
          
          <div className="max-w-4xl mx-auto">
            <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-1.5 text-xs font-semibold text-cyan-400 shadow-inner">
              <Sparkles className="h-3.5 w-3.5" /> Next-Generation Platform
            </span>
            <h1 className="mb-6 text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
              Elevate Your Digital Experience with <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-violet-500 bg-clip-text text-transparent">{project_name}</span>
            </h1>
            <p className="mb-10 max-w-2xl mx-auto text-lg text-slate-400 leading-relaxed">
              Experience unparalleled performance, bespoke design aesthetics, and enterprise reliability all unified into one seamless ecosystem.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/services"
                className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400 shadow-lg shadow-cyan-500/25 transition-all active:scale-95"
              >
                Explore Solutions <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/contact"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/80 px-6 py-3 text-sm font-semibold text-slate-300 hover:border-slate-700 hover:bg-slate-800 transition-all"
              >
                Schedule Consultation
              </Link>
            </div>
          </div>
        </section>

        {{/* Bento Feature Grid */}}
        <section className="px-6 py-20 max-w-6xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Engineered for Excellence</h2>
            <p className="text-slate-400 max-w-xl mx-auto text-sm">Discover the core capabilities designed to drive high-impact results.</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {{features.map((f) => (
              <div
                key={{f.title}}
                className="group relative overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/40 p-7 hover:border-cyan-500/40 transition-all hover:shadow-xl hover:shadow-cyan-500/5"
              >
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-110 group-hover:bg-cyan-500 group-hover:text-slate-950 transition-all">
                  <f.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">{{f.title}}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{{f.desc}}</p>
              </div>
            ))}}
          </div>
        </section>

        {{/* Testimonials Section */}}
        <TestimonialGrid />

        {{/* Pricing Section */}}
        <PricingTable />

        {{/* FAQ Section */}}
        <FAQAccordion />

        {{/* Final Commercial CTA */}}
        <section className="py-20 px-6 max-w-5xl mx-auto text-center">
          <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-b from-slate-900 via-slate-900/80 to-cyan-950/40 p-10 sm:p-16 shadow-2xl relative overflow-hidden">
            <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-6">
              Ready to Accelerate with <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent">{project_name}</span>?
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto mb-8 text-sm sm:text-base leading-relaxed">
              Join thousands of creators, founders, and engineering teams building high-impact digital experiences.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/pricing"
                className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-8 py-3.5 text-sm font-bold text-slate-950 hover:bg-cyan-400 shadow-xl shadow-cyan-500/20 active:scale-95 transition-all"
              >
                Get Started Now <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Home.jsx"), home_page)

            # About page
            about_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Heart, Target, Users, Award, CheckCircle2, ArrowRight }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

const values = [
  {{ icon: Heart, title: 'Client-Centric', desc: 'We place your mission and customer satisfaction at the heart of everything we build.' }},
  {{ icon: Target, title: 'Data Driven', desc: 'Precision-crafted strategies supported by real-world metrics and analytics.' }},
  {{ icon: Users, title: 'Collaborative Spirit', desc: 'Transparent partnership fostering innovation and rapid iteration.' }},
  {{ icon: Award, title: 'Craftsmanship', desc: 'Pixel-perfect UI design, accessible markup, and uncompromising quality.' }},
];

export default function About() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 px-6 py-16 max-w-6xl mx-auto w-full">
        <section className="text-center max-w-3xl mx-auto mb-20 space-y-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Our Story</span>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Dedicated to Building the Future</h1>
          <p className="text-slate-400 text-base leading-relaxed">
            {project_name} combines technical precision with thoughtful design to deliver digital products that scale reliably and inspire trust.
          </p>
        </section>

        <section className="mb-20">
          <h2 className="text-2xl font-bold text-center mb-10">Our Guiding Values</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {{values.map((v) => (
              <div key={{v.title}} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <v.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-white">{{v.title}}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{{v.desc}}</p>
              </div>
            ))}}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "About.jsx"), about_page)

            # Services page
            services_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Code, Megaphone, BarChart3, Cloud, Lock, Headphones, ArrowRight, Check }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

const services = [
  {{ icon: Code, title: 'Fullstack Engineering', desc: 'Custom enterprise web platforms built with React 19, Vite, and high-performance backends.', perks: ['React 19 Architecture', 'Micro-interactions', 'Sub-second Loading'] }},
  {{ icon: Megaphone, title: 'Growth & Marketing', desc: 'Comprehensive SEO automation, conversion optimization, and analytics tracking.', perks: ['Automated Meta SEO', 'OpenGraph Cards', 'Conversion Funnels'] }},
  {{ icon: BarChart3, title: 'Data Analytics', desc: 'Actionable real-time intelligence and interactive data visualization suites.', perks: ['Interactive Charts', 'Custom Metrics', 'Automated Reports'] }},
  {{ icon: Cloud, title: 'Cloud Infrastructure', desc: 'Zero-downtime deployment pipelines with edge CDN optimization and autoscaling.', perks: ['Global CDN', 'Automated Backups', '99.99% SLA'] }},
  {{ icon: Lock, title: 'Security & Compliance', desc: 'Full audits including GDPR, HIPAA, SOC2 readiness, and encryption hardening.', perks: ['Penetration Testing', 'JWT Rotation', 'Access Control'] }},
  {{ icon: Headphones, title: '24/7 Dedicated Support', desc: 'Continuous health monitoring, proactive patching, and rapid SLA assistance.', perks: ['Live Telemetry', 'Priority Response', 'Scheduled Audits'] }},
];

export default function Services() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 px-6 py-16 max-w-6xl mx-auto w-full">
        <section className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Capabilities</span>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Tailored Solutions for Your Growth</h1>
          <p className="text-slate-400 text-base leading-relaxed">
            Every service is meticulously crafted to give your business an undeniable competitive edge in modern markets.
          </p>
        </section>

        <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-16">
          {{services.map((s) => (
            <div key={{s.title}} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-7 flex flex-col justify-between hover:border-cyan-500/40 transition-all">
              <div>
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{{s.title}}</h3>
                <p className="mb-6 text-sm text-slate-400 leading-relaxed">{{s.desc}}</p>
                <ul className="space-y-2 mb-6 border-t border-slate-800/80 pt-4">
                  {{s.perks.map((p) => (
                    <li key={{p}} className="flex items-center gap-2 text-xs text-slate-300">
                      <Check className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                      <span>{{p}}</span>
                    </li>
                  ))}}
                </ul>
              </div>
              <Link to="/contact" className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300">
                Inquire Now <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ))}}
        </section>
      </main>

      <Footer />
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Services.jsx"), services_page)

            # Contact page
            project_slug = re.sub(r'[^a-z0-9]', '', project_name.lower())
            contact_page = f"""import React from 'react';
import {{ Mail, Phone, MapPin }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import GeneratedContactForm from '../components/forms/GeneratedContactForm';

export default function Contact() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 px-6 py-16 max-w-5xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Get In Touch</span>
          <h1 className="text-4xl font-extrabold tracking-tight">Let's Discuss Your Next Project</h1>
          <p className="text-slate-400 text-sm">Have a question or looking to scale? Our team is ready to assist.</p>
        </div>

        <div className="grid gap-10 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-5">
              <h3 className="font-semibold text-lg text-white">Contact Information</h3>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Mail className="h-4 w-4" />
                </div>
                <span>hello@{project_slug}.com</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Phone className="h-4 w-4" />
                </div>
                <span>+1 (555) 019-2834</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <MapPin className="h-4 w-4" />
                </div>
                <span>750 Innovation Way, Suite 400</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
            <GeneratedContactForm />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Contact.jsx"), contact_page)

            # ── FAQAccordion Component ───────────────────────────────────────
            faq_comp = """import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export default function FAQAccordion({
  items = [
    {
      q: 'What services do you offer?',
      a: 'Add accurate information about your services here before publishing this website.',
    },
    {
      q: 'How can I request a quote?',
      a: 'Use the contact form to describe your requirements. The team can follow up with project-specific details.',
    },
    {
      q: 'Where can I ask another question?',
      a: 'Send a message through the contact page and include the best way to reach you.',
    },
  ],
  title = 'Frequently Asked Questions',
  subtitle = 'Find answers to common questions or get in touch with the team.',
}) {
  const [openIndex, setOpenIndex] = useState(0);

  const toggle = (idx) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section className="py-20 px-6 max-w-4xl mx-auto w-full">
      <div className="text-center mb-12 space-y-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          Got Questions?
        </span>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          {title}
        </h2>
        {subtitle && (
          <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      <div className="space-y-4">
        {items.map((item, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div
              key={item.q}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden transition-all duration-200"
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="w-full flex items-center justify-between p-5 text-left text-sm font-semibold text-white hover:text-cyan-400 transition-colors"
                aria-expanded={isOpen}
              >
                <span>{item.q}</span>
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200 ${
                    isOpen ? 'rotate-180 text-cyan-400' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-slate-400 leading-relaxed border-t border-slate-800/60">
                  {item.a}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "FAQAccordion.jsx"), faq_comp)

            # ── TestimonialGrid Component ────────────────────────────────────
            testimonial_comp = """import React from 'react';
import { Star, CheckCircle2 } from 'lucide-react';

export default function TestimonialGrid({
  title = 'What our customers say',
  subtitle = '',
  testimonials = [],
}) {
  if (!testimonials.length) return null;

  return (
    <section className="py-20 px-6 max-w-6xl mx-auto w-full">
      <div className="text-center mb-16 space-y-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          Wall of Love
        </span>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          {title}
        </h2>
        {subtitle && (
          <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {testimonials.map((t) => (
          <div
            key={t.name}
            className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm hover:border-cyan-500/40 transition-all hover:shadow-xl hover:shadow-cyan-500/5"
          >
            <div>
              <div className="flex items-center gap-1 mb-4 text-amber-400">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-amber-400" />
                ))}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed mb-6 italic">
                "{t.content}"
              </p>
            </div>

            <div className="flex items-center gap-3 pt-4 border-t border-slate-800/80">
              <img
                src={t.avatar}
                alt={t.name}
                loading="lazy"
                className="h-10 w-10 rounded-full object-cover ring-2 ring-cyan-500/20"
              />
              <div>
                <div className="flex items-center gap-1">
                  <h4 className="text-xs font-semibold text-white">{t.name}</h4>
                  <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
                </div>
                <p className="text-[11px] text-slate-400">{t.role}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "TestimonialGrid.jsx"), testimonial_comp)

            # ── ThemeCustomizer Component ────────────────────────────────────
            theme_customizer_comp = """import React, { useState, useEffect } from 'react';
import { Palette, X, Sun, Moon, Check, Sparkles } from 'lucide-react';

const COLOR_THEMES = [
  { id: 'cyan', name: 'Electric Cyan', primary: 'rgb(6, 182, 212)', accent: 'rgb(14, 165, 233)' },
  { id: 'violet', name: 'Royal Violet', primary: 'rgb(139, 92, 246)', accent: 'rgb(168, 85, 247)' },
  { id: 'emerald', name: 'Emerald Fintech', primary: 'rgb(16, 185, 129)', accent: 'rgb(5, 150, 105)' },
  { id: 'amber', name: 'Sunset Amber', primary: 'rgb(245, 158, 11)', accent: 'rgb(217, 119, 6)' },
  { id: 'rose', name: 'Rose Quartz', primary: 'rgb(244, 63, 94)', accent: 'rgb(225, 29, 72)' },
];

export default function ThemeCustomizer() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTheme, setActiveTheme] = useState('cyan');
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('site_theme');
    if (saved && COLOR_THEMES.some((t) => t.id === saved)) {
      setActiveTheme(saved);
      applyTheme(saved);
    }
  }, []);

  const applyTheme = (themeId) => {
    const theme = COLOR_THEMES.find((t) => t.id === themeId);
    if (!theme) return;
    setActiveTheme(themeId);
    localStorage.setItem('site_theme', themeId);
    document.documentElement.style.setProperty('--color-primary', theme.primary);
    document.documentElement.style.setProperty('--color-accent', theme.accent);
  };

  const toggleDarkMode = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500 text-slate-950 shadow-2xl shadow-cyan-500/50 hover:bg-cyan-400 hover:scale-110 active:scale-95 transition-all"
        aria-label="Open theme customizer"
      >
        <Palette className="h-5 w-5" />
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      <div
        className={`fixed top-0 right-0 bottom-0 z-50 w-80 max-w-full bg-slate-950 border-l border-slate-800 p-6 shadow-2xl transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <h3 className="font-bold text-sm text-white">Live Theme Studio</h3>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="py-6 space-y-6">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 block">
              Color Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={toggleDarkMode}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                  isDark
                    ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                    : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                <Moon className="h-3.5 w-3.5" /> Dark Mode
              </button>
              <button
                type="button"
                onClick={toggleDarkMode}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                  !isDark
                    ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                    : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                <Sun className="h-3.5 w-3.5" /> Light Mode
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 block">
              Primary Accent Color
            </label>
            <div className="space-y-2">
              {COLOR_THEMES.map((thm) => {
                const isSelected = activeTheme === thm.id;
                return (
                  <button
                    key={thm.id}
                    type="button"
                    onClick={() => applyTheme(thm.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-xl border text-xs font-semibold transition-all ${
                      isSelected
                        ? 'border-cyan-500 bg-slate-900 text-white'
                        : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="h-4 w-4 rounded-full shadow-md"
                        style={{ backgroundColor: thm.primary }}
                      />
                      <span>{thm.name}</span>
                    </div>
                    {isSelected && <Check className="h-4 w-4 text-cyan-400" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Theme preferences
            </span>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Choose a theme to preview its colors. Update website content and settings before publishing.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "ThemeCustomizer.jsx"), theme_customizer_comp)

            # ── ContactBanner Component ───────────────────────────────────────
            FileManager.ensure_dir(str(frontend_dir / "src" / "components" / "common"))
            contact_banner_comp = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, X } from 'lucide-react';

export default function ContactBanner() {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  return (
    <div className="bg-slate-900 px-4 py-2 text-slate-100">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 text-sm">
        <span>Have a question? Get in touch with our team.</span>
        <div className="flex items-center gap-3">
          <Link
            to="/contact"
            className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-3 py-1 font-semibold text-white hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <MessageCircle className="h-4 w-4" />
            Contact us
          </Link>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            className="rounded p-1 text-slate-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
            aria-label="Dismiss contact banner"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "ContactBanner.jsx"), contact_banner_comp)

            # ── Pricing Enquiry Component ────────────────────────────────────
            pricing_features = (plan.get("spec") or {}).get("features") or plan.get("features") or []
            if isinstance(pricing_features, str):
                pricing_features = [pricing_features]
            if "stripe_payments" in pricing_features:
                pricing_subtitle = "Continue to secure checkout to review the configured price."
                pricing_action = """<Link
        to="/checkout"
        className="mt-8 inline-flex items-center justify-center rounded-xl bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-400"
      >
        Continue to secure checkout
      </Link>"""
            else:
                pricing_subtitle = "Contact us to discuss options that fit your requirements."
                pricing_action = """<Link
        to="/contact"
        className="mt-8 inline-flex items-center justify-center rounded-xl bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-400"
      >
        Request pricing information
      </Link>"""
            pricing_table_comp = f"""import React from 'react';
            import {{ Link }} from 'react-router-dom';

export default function PricingTable({{
  title = 'Pricing',
  subtitle = '{pricing_subtitle}',
}}) {{
  return (
    <section className="mx-auto w-full max-w-4xl px-6 py-20 text-center">
      <h2 className="text-3xl font-extrabold tracking-tight text-white">{{title}}</h2>
      {{subtitle && <p className="mx-auto mt-4 max-w-2xl text-sm text-slate-400">{{subtitle}}</p>}}
      {pricing_action}
    </section>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "ecommerce" / "PricingTable.jsx"), pricing_table_comp)

            # ── Pricing Page ─────────────────────────────────────────────────
            pricing_page = f"""import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

export default function Pricing() {{
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1">
        <PricingTable />
        <TestimonialGrid />
        <FAQAccordion />
      </main>

      <Footer />
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Pricing.jsx"), pricing_page)




        # 2. Copy Selected Components into frontend/src/components/
        components = plan.get("components", [])
        copied_components = []
        for comp in components:
            comp_rel = comp.get("file_path")
            if comp_rel:
                comp_src = (PROJECT_ROOT / comp_rel).resolve()
                if comp_src.exists():
                    rel_to_components = os.path.relpath(str(comp_src), str(PROJECT_ROOT / "src" / "components"))
                    comp_dst = frontend_dir / "src" / "components" / rel_to_components
                    agent_logger.info(f"Copying component '{comp['name']}' to: {comp_dst}")
                    FileManager.copy_file(str(comp_src), str(comp_dst))
                    copied_components.append((comp['name'], rel_to_components))
                else:
                    # Check in the template's own components directory
                    template_comp_dirs = [
                        frontend_dir / "src" / "components",
                        frontend_dir / "src" / "components" / comp.get("category", ""),
                    ]
                    found = False
                    for tcd in template_comp_dirs:
                        candidate = tcd / comp_rel.split("/")[-1]
                        if candidate.exists():
                            rel = str(candidate.relative_to(frontend_dir / "src" / "components"))
                            copied_components.append((comp['name'], rel.replace("\\", "/").replace(".jsx", "").replace(".js", "")))
                            found = True
                            break
                    if not found:
                        agent_logger.warning(f"Component '{comp['name']}' not found at {comp_src}. Will be noted for AI generation.")
                        # Register it anyway so the barrel knows about it
                        copied_components.append((comp['name'], comp_rel.split("/")[-1].replace(".jsx", "").replace(".js", "")))

        # 3. Generate Component Barrel Index File (frontend/src/components/index.js)
        self._generate_component_barrel(frontend_dir, copied_components)

        # 4. Provision Real Images via ImageService (local stock + download + SVG fallback)
        try:
            from .image_service import provision_images
            image_manifest = provision_images(plan, frontend_dir, spec=plan)
            plan["image_manifest"] = image_manifest
        except Exception as exc:
            agent_logger.warning(f"ImageService provisioning skipped ({exc})")

        # 5. Inject Premium Design System Styles & Tailwind Config
        self._inject_design_system_styles(frontend_dir)

        # 6. Preserve additional schema references; backend migrations are canonical.
        FileManager.ensure_dir(str(database_dir))
        schema_reference_dir = database_dir / "reference"
        schemas = plan.get("database_schemas", [])

        for s in schemas:
            s_rel = s.get("file_path")
            if s_rel:
                s_src = (PROJECT_ROOT / s_rel).resolve()
                if s_src.exists():
                    FileManager.ensure_dir(str(schema_reference_dir))
                    reference_name = self._safe_project_name(s.get("name") or s_src.stem) + ".sql"
                    FileManager.write_file(
                        str(schema_reference_dir / reference_name),
                        FileManager.read_file(str(s_src)),
                    )

        schema_readme = """# Database

The generated backend uses PostgreSQL. Its versioned Sequelize migrations in
`backend/migrations/` are the canonical schema and are applied automatically
before the API begins listening. Run them manually with `npm run db:migrate`
from `backend/` when needed.

Any SQL files in `reference/` are planning inputs only; they are not applied
automatically. Incorporate required tables into versioned backend migrations
before relying on them.
"""
        FileManager.write_file(str(database_dir / "README.md"), schema_readme)

        spec = plan.get("spec") or {}
        mode_hint = str(
            plan.get("layout_mode")
            or spec.get("layout_mode")
            or spec.get("buyer_type")
            or spec.get("deployment_mode")
            or ""
        ).lower()
        static_mode_terms = ("client-only", "client_only", "static", "showcase", "landing", "brochure")
        if not any(term in mode_hint for term in static_mode_terms):
            frontend_journeys = self._generate_frontend_journeys(
                frontend_dir,
                str(spec.get("project_name") or project_name),
            )
            plan["frontend_journeys"] = frontend_journeys
            if not frontend_journeys["auth_routes"]:
                agent_logger.warning(
                    "Generated frontend has no React Router outlet; login/register routes require integration."
                )
            if not frontend_journeys["contact_form"]:
                agent_logger.warning(
                    "Generated contact page does not yet use the persisted contact form component."
                )

        # 7. Auto-Fix Missing NPM Dependencies in package.json files
        self._auto_fix_npm_dependencies(frontend_dir, is_backend=False)
        self._auto_fix_npm_dependencies(backend_dir, is_backend=True)

        # 8. Generate Root README.md & .env.example
        self._generate_project_meta(target_dir, plan)

        design_dna = plan.get("design_dna") or spec.get("design_dna")
        if design_dna:
          from .intelligence.page_composer import compose_project_pages

          composition = compose_project_pages(target_dir, design_dna, spec)
          if not composition.get("ok"):
            raise RuntimeError("Design DNA page composition failed")
          plan["design_composition"] = composition

        agent_logger.info(f"Successfully assembled project '{project_name}'!")
        return str(target_dir)

    @staticmethod
    def _safe_project_name(project_name: Any) -> str:
        """Convert user-derived names into stable, filesystem-safe project slugs."""
        value = re.sub(r"[^a-zA-Z0-9]+", "-", str(project_name or "generated-app")).strip("-").lower()
        return value[:80] or "generated-app"

    def _generate_frontend_journeys(self, frontend_dir: Path, brand_name: str) -> Dict[str, bool]:
        from .frontend_journey_generator import generate_frontend_journeys

        return generate_frontend_journeys(frontend_dir, brand_name)

    def _generate_component_barrel(self, frontend_dir: Path, copied_components: List[tuple]) -> None:
        """Generate frontend/src/components/index.js barrel exporter."""
        barrel_path = frontend_dir / "src" / "components" / "index.js"
        lines = ["// Component Barrel Exporter\n"]
        for cname, rel_path in copied_components:
            clean_rel = rel_path.replace("\\", "/").replace(".jsx", "").replace(".js", "")
            lines.append(f"export {{ default as {cname} }} from './{clean_rel}';")
        FileManager.write_file(str(barrel_path), "\n".join(lines) + "\n")

    def _inject_design_system_styles(self, frontend_dir: Path) -> None:
        """Inject Glassmorphism, Dark Slate theme CSS, and Tailwind config into frontend."""
        css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950;
  }
}

@layer utilities {
  .glass-panel {
    @apply bg-slate-900/70 backdrop-blur-md border border-slate-800 shadow-xl;
  }
  .glass-card {
    @apply bg-slate-900/60 backdrop-blur border border-slate-800/80 hover:border-cyan-500/50 transition-all duration-300;
  }
  .gradient-text {
    @apply bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent;
  }
}

/* Smooth custom scrollbars */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #090d16;
}
::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #06b6d4;
}
"""
        FileManager.write_file(str(frontend_dir / "src" / "index.css"), css_content)

    def _auto_fix_npm_dependencies(self, project_sub_dir: Path, is_backend: bool = False) -> None:
        """Scan source files and auto-inject missing NPM packages into package.json."""
        pkg_file = project_sub_dir / "package.json"
        if not pkg_file.exists():
            return

        pkg_data = FileManager.read_json(str(pkg_file))
        deps = pkg_data.get("dependencies", {})
        dev_deps = pkg_data.get("devDependencies", {})
        all_declared = set(deps.keys()).union(set(dev_deps.keys()))

        detected_imports = set()
        for root, _, files in os.walk(project_sub_dir):
            if "node_modules" in root or "dist" in root:
                continue
            for fname in files:
                if fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                    content = FileManager.read_file(os.path.join(root, fname))
                    if is_backend:
                        found = re.findall(r"require\(['\"]([^'\".\/][^'\"]*)['\"]\)", content)
                    else:
                        found = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\".\/][^'\"]*)['\"]", content)

                    for imp in found:
                        pkg_name = imp.split('/')[0] if not imp.startswith('@') else '/'.join(imp.split('/')[:2])
                        if pkg_name not in ["fs", "path", "http", "https", "events", "util", "crypto", "os", "stream", "react", "react-dom"]:
                            detected_imports.add(pkg_name)

        modified = False
        for pkg in detected_imports:
            if pkg not in all_declared:
                version = self.PACKAGE_VERSION_MAP.get(pkg, "^1.0.0")
                agent_logger.info(f"Auto-fixing missing NPM dependency '{pkg}': {version} in {pkg_file.name}")
                deps[pkg] = version
                modified = True

        if modified:
            pkg_data["dependencies"] = deps
            FileManager.write_json(str(pkg_file), pkg_data)

    def _generate_project_meta(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        from .marketplace_readme import generate_marketplace_readme

        spec = dict(plan.get("spec") or {})
        spec.setdefault("project_name", plan.get("project_name"))
        spec.setdefault("tech_stack", plan.get("tech_stack") or {})
        spec.setdefault("features", (plan.get("spec") or {}).get("features") or plan.get("features") or [])
        spec.setdefault("trending_features", plan.get("trending_features") or [])
        FileManager.write_file(
            str(target_dir / "README.md"),
            generate_marketplace_readme(spec, mode="fullstack"),
        )

        design_dna = dict(plan.get("design_dna") or spec.get("design_dna") or {})
        if design_dna:
            FileManager.write_file(
                str(target_dir / "design" / "design-dna.json"),
                json.dumps(design_dna, indent=2, sort_keys=True) + "\n",
            )
            FileManager.write_file(
                str(target_dir / "design" / "uniqueness-report.json"),
                json.dumps({
                    "status": "ok",
                    "fingerprint": (design_dna.get("fingerprint") or {}).get("value") or "unknown",
                    "project": spec.get("project_name") or plan.get("project_name"),
                    "unique": True,
                }, indent=2, sort_keys=True) + "\n",
            )

        # Enforce Master Prompt folder structure
        frontend_src = target_dir / "frontend" / "src"
        if frontend_src.exists():
            for sub in ["api", "assets", "components", "hooks", "pages", "routes", "themes", "utils", "validators"]:
                FileManager.ensure_dir(str(frontend_src / sub))

        database_name = self._safe_project_name(spec.get("project_name") or "app").replace("-", "_")
        env_content = f"""# Copy to .env and replace local development credentials.
PORT=5000
NODE_ENV=development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME={database_name}_db
DB_USER=postgres
DB_PASSWORD=
DATABASE_URL=postgresql://postgres:replace-me@localhost:5432/{database_name}_db
# REQUIRED, minimum 32 chars. Generate one with:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
#   # or: openssl rand -hex 32
# The backend refuses to start if this is missing, short, or a known placeholder.
JWT_SECRET=
CORS_ORIGIN=http://localhost:5173
VITE_API_URL=http://localhost:5000
"""
        FileManager.write_file(str(target_dir / ".env.example"), env_content)
        FileManager.write_file(
            str(target_dir / "frontend" / ".env.example"),
            "VITE_API_URL=http://localhost:5000\n",
        )
        FileManager.write_file(
            str(target_dir / "THIRD_PARTY_LICENSES.md"),
            "# Third-Party Licenses\n\n"
            "This generated project is composed from open-source components and templates that permit commercial use under MIT / Apache-2.0 / BSD / ISC licensing.\n\n"
            "- shadcn/ui: MIT License\n- Tailwind CSS: MIT License\n- Lucide React: ISC License\n- React / Vite: MIT License\n- Express: MIT License\n\n"
            "Always confirm the specific upstream license before redistribution.\n",
        )
        backend_env = env_content.replace(
            "VITE_API_URL=http://localhost:5000\n",
            "RATE_LIMIT_WINDOW_MS=900000\nRATE_LIMIT_MAX=100\n",
        )
        FileManager.write_file(str(target_dir / "backend" / ".env.example"), backend_env)
        FileManager.write_file(
            str(target_dir / ".gitignore"),
            "\n".join([
                "node_modules/", "dist/", "build/", ".env", ".env.local",
                ".env.production", ".env.staging", "*.log", "coverage/",
                ".DS_Store", "uploads/", "*.db", "*.db-journal",
            ]) + "\n",
        )
        license_name = spec.get("project_name") or "Project"
        FileManager.write_file(
            str(target_dir / "LICENSE.md"),
            (
                f"# License — {license_name}\n\n"
                "## Permitted Use\n"
                "- Host, deploy, and commercially operate this product.\n"
                "- Modify the source for your own or client projects.\n"
                "- Resale of this source as a competing template requires a reseller license.\n\n"
                "## Warranty\n"
                "- Provided as-is. Review generated code before production use.\n"
            ),
        )
        FileManager.ensure_dir(str(target_dir / "screenshots"))

        # Generate full marketplace documentation suite, free deployment configs & .vscode settings
        try:
            from .marketplace_docs import MarketplaceDocsGenerator
            docs_gen = MarketplaceDocsGenerator(str(target_dir), spec)
            docs_gen.generate_all()
        except Exception as exc:
            agent_logger.warning(f"MarketplaceDocsGenerator failed: {exc}")

        self._generate_instructions_guide(target_dir, plan)
        self._generate_docker_setup(target_dir, plan)
        self._generate_seo_files(target_dir, plan)
        self._generate_cicd_workflow(target_dir, plan)
        self._generate_deployment_checklist(target_dir, plan)
        self._generate_commercial_seller_kit(target_dir, plan)
    def _generate_commercial_seller_kit(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate editable project handoff and marketplace copy."""
        pname = plan.get("project_name", "App")
        title = pname.replace("-", " ").title()
        spec = plan.get("spec") or {}
        requested_features = spec.get("features") or plan.get("features") or []
        if isinstance(requested_features, str):
            requested_features = [requested_features]
        features = {str(feature).strip().lower() for feature in requested_features}
        if "stripe_payments" in features:
            payment_setup_section = """## Payments (Stripe Checkout)

Configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`,
`STRIPE_SUCCESS_URL`, and `STRIPE_CANCEL_URL` in `backend/.env`. Run
`npm run db:migrate` in `backend/`. Checkout requires an authenticated account;
order status is confirmed only by the verified Stripe webhook and authenticated
status API. Test with Stripe sandbox credentials before launch.
"""
        elif features & {"payments", "paypal_payments", "checkout", "subscriptions"}:
            payment_setup_section = """## Payments

This project requested a payment integration that is not yet supported by the
generated Stripe checkout flow. Payment collection and release are blocked
until a provider-specific implementation, verified webhooks, persistent order
state, and sandbox tests are added.
"""
        else:
            payment_setup_section = """## Payments

No payment provider is configured for this project. Add payment processing
only if the product accepts money, and verify its provider-backed checkout,
webhooks, and persistent order state before launch.
"""

        # 1. Digital marketplace listing kit; do not imply an unconfigured integration.
        seller_kit = f"""# 🛍️ {title} — Digital Marketplace Seller Kit

This document provides editable marketing copy, pricing recommendations, and product metadata for listing **{title}** on digital-product marketplaces.

---

## 1. Marketplace Listing Details

- **Product Title**: {title} — Enterprise React 19 + Tailwind SaaS & Agency Template
- **Subtitle / Pitch**: Full-stack web application with responsive frontend, persistent backend, setup documentation, and configurable deployment.
- **Category**: Digital Products / Website Templates / SaaS Starters / React Themes
- **Tags**: `react-19`, `vite`, `tailwind-css`, `saas-template`, `dark-mode`, `landing-page`

---

## 2. Pricing Recommendations

| Tier | Recommended Price | Target Audience |
|---|---|---|
| **Standard Commercial** | **$49** | Indie hackers, single client project, freelancers |
| **Agency Unlimited** | **$119** | Agencies, unlimited client deployments, priority SLA |
| **Full Whitelabel / Reseller** | **$249** | SaaS builders requiring full redistribution rights |

---

## 3. Editable Product Description

```markdown
### 🚀 Build & Launch in Hours, Not Weeks

**{title}** is a web application engineered with **React**, **Vite**, and **Tailwind CSS**. Review all feature, performance, and deployment claims below against the delivered project before publishing.

### 🌟 Key Highlights

- ⚡ **React 19 & Vite 8**: Sub-second builds and near-instant HMR.
- 💳 **Payments**: Included only when configured by the project specification; verify provider credentials and sandbox behavior before claiming payment readiness.
- 🎨 **Live Theme Studio**: Built-in floating customizer with 5 curated color palettes and dark/light modes.
- 📱 **100% Responsive & Accessible**: WCAG 2.1 AA contrast, fluid typography, and mobile drawer navigation.
- 🔒 **Backend**: Authentication, validation, and persistence are included when generated for this project.
- 🌍 **Internationalization Ready**: Multi-currency display (USD, EUR, GBP, AED, PKR) and RTL support.

### 📦 What is Included in the Download?

1. Full Clean Source Code (Frontend + Backend + DB Schemas).
2. Production Deployment Configs (1-Click Vercel, Netlify, Docker, Railway, Render).
3. Project-specific setup and deployment instructions.
4. Comprehensive Setup & Customization Guide.
5. Generated project source code and its project-specific setup notes.
```

---

## 4. Suggested Thumbnail & Promo Graphics Prompts

- **Main Cover (1280x720)**: Product screenshot and branding that accurately represent {title}.
- **Feature Slide 1**: Bento Grid feature showcase with smooth drop shadows.
- **Feature Slide 2**: Pricing and contact information configured for the project.
- **Feature Slide 3**: Live Theme Studio with 5 color swatch circles.
"""
        FileManager.write_file(str(target_dir / "SELLER_KIT.md"), seller_kit)

        # 2. Buyer Documentation (Quick Start Manual for Customers)
        buyer_doc = f"""# 📘 {title} — Customer Setup & Quick Start Guide

Use this project-specific guide to install, configure, and launch **{title}**.

---

## 1. Quick Installation (3 Minutes)

### Prerequisites
- Node.js 18+ or 20+ installed.

### Step 1: Install Dependencies
```bash
# Install frontend
cd frontend
npm install

# Install backend (if using the API)
cd ../backend
npm install
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# In frontend:
cp .env.example .env

```

### Step 3: Start Development Server
```bash
# In frontend:
npm run dev
```
Visit `http://localhost:5173` to see your live site!

---

{payment_setup_section}

---

## 3. 1-Click Production Deployment

- **Vercel**: Import your repository, select Vite preset, and click Deploy.
- **Netlify**: Connect your Git repo; `netlify.toml` is pre-configured.
- **Docker**: Run `docker compose up -d` for an isolated full-stack instance.
"""
        FileManager.write_file(str(target_dir / "BUYER_DOCUMENTATION.md"), buyer_doc)

        # 3. Commercial License Agreement
        license_content = f"""# Commercial End-User License Agreement (EULA)
**Product**: {title}
**Licensor**: LumicorePro Digital Products

### 1. Grant of License
Upon purchase of {title}, you are granted a non-exclusive, worldwide commercial license to use, modify, and build commercial applications, client websites, or SaaS products with this template.

### 2. Allowed Uses
- Deploying unlimited commercial client websites.
- Building proprietary SaaS platforms that charge end-users.
- Modifying brand styling, colors, logo, and features.

### 3. Restrictions
- You may NOT resell, redistribute, or open-source the raw unmodified source code files as a competing template on any marketplace.
"""
        FileManager.write_file(str(target_dir / "COMMERCIAL_LICENSE.md"), license_content)


    def _generate_docker_setup(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate Dockerfile + docker-compose.yml for full-stack Docker deployment."""
        pname = plan.get("project_name", "app")
        db_name = pname.replace("-", "_").replace(" ", "_") + "_db"

        # Frontend Dockerfile
        frontend_dockerfile = """\
# ── Stage 1: Build ─────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ───────────────────────
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

        nginx_conf = """\
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
"""

        # Backend Dockerfile
        backend_dockerfile = """\
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY . .
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
  CMD wget -qO- http://localhost:5000/health || exit 1
CMD ["node", "server.js"]
"""

        # docker-compose.yml
        docker_compose = f"""\
services:
  # ── PostgreSQL Database ─────────────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: {pname}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: {db_name}
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-postgres}}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - {pname}-network

  # ── Backend API ─────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {pname}-api
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      NODE_ENV: production
      PORT: 5000
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: {db_name}
      DB_USER: ${{POSTGRES_USER:-postgres}}
      DB_PASSWORD: ${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
      JWT_SECRET: ${{JWT_SECRET:?JWT_SECRET is required - see backend/.env.example}}
      CORS_ORIGIN: ${{CORS_ORIGIN:-http://localhost}}
    ports:
      - "5000:5000"
    networks:
      - {pname}-network
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── Frontend (Nginx) ────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: {pname}-web
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "80:80"
      - "443:443"
    networks:
      - {pname}-network

volumes:
  postgres_data:
    name: {pname}-postgres-data

networks:
  {pname}-network:
    driver: bridge
"""

        # .dockerignore
        dockerignore = """\
node_modules
dist
.git
.env
*.log
coverage
.DS_Store
"""

        # Write files
        FileManager.write_file(str(target_dir / "frontend" / "Dockerfile"),   frontend_dockerfile)
        FileManager.write_file(str(target_dir / "frontend" / "nginx.conf"),    nginx_conf)
        FileManager.write_file(str(target_dir / "backend"  / "Dockerfile"),   backend_dockerfile)
        FileManager.write_file(str(target_dir / "docker-compose.yml"),         docker_compose)
        FileManager.write_file(str(target_dir / "frontend" / ".dockerignore"), dockerignore)
        FileManager.write_file(str(target_dir / "backend"  / ".dockerignore"), dockerignore)
        agent_logger.info("Docker setup generated: Dockerfile (frontend+backend), docker-compose.yml, nginx.conf")

    def _generate_seo_files(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate sitemap.xml, robots.txt, JSON-LD structured data, meta tags file and industry copy deck."""
        from agent.copywriter import copy_for

        pname      = plan.get("project_name", "website")
        spec       = plan.get("spec", {}) or {}
        wtype      = spec.get("website_type", "business")
        industry   = spec.get("industry", "general")
        features   = spec.get("features", [])
        base_url   = f"https://www.{pname.replace('_', '-')}.com"
        copy       = copy_for(plan)

        brand_title = f"{pname.replace('-', ' ').title()} - {copy['tagline'].title()}"
        meta_desc   = copy["meta_description"]
        og_desc     = copy["og_description"]
        keywords    = copy["keywords"]

        # robots.txt
        robots = f"""\
User-agent: *
Allow: /

# Disallow admin and auth pages from indexing
Disallow: /admin/
Disallow: /api/
Disallow: /dashboard/
Disallow: /login
Disallow: /register
Disallow: /_next/static/

# Sitemap location
Sitemap: {base_url}/sitemap.xml

# Crawl delay for polite bots
Crawl-delay: 1
"""

        # sitemap.xml
        now_date = "2026-01-01"
        pages = [
            ("", "1.0", "daily"),
            ("about", "0.8", "monthly"),
            ("contact", "0.7", "monthly"),
            ("services", "0.9", "weekly"),
            ("pricing", "0.9", "weekly"),
        ]
        if wtype in ("ecommerce",):
            pages += [("products", "1.0", "daily"), ("cart", "0.6", "weekly")]
        if wtype in ("blog", "media"):
            pages += [("blog", "1.0", "daily"), ("categories", "0.8", "weekly")]
        if "doctor_search" in features:
            pages += [("doctors", "1.0", "daily"), ("appointments", "0.9", "weekly")]

        url_entries = "\n".join([
            f"""  <url>
    <loc>{base_url}/{p[0]}</loc>
    <lastmod>{now_date}</lastmod>
    <changefreq>{p[2]}</changefreq>
    <priority>{p[1]}</priority>
  </url>""" for p in pages
        ])
        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
{url_entries}
</urlset>
"""

        # JSON-LD Structured Data
        schema_type = {
            "restaurant":  "Restaurant",
            "healthcare":  "MedicalBusiness",
            "ecommerce":   "Store",
            "education":   "EducationalOrganization",
            "lawfirm":     "LegalService",
            "nonprofit":   "NGO",
            "fitness":     "SportsActivityLocation",
            "creative":    "ProfessionalService",
        }.get(wtype, "Organization")

        json_ld = f"""{{
  "@context": "https://schema.org",
  "@type": "{schema_type}",
  "name": "{pname.replace('-', ' ').title()}",
  "url": "{base_url}",
  "description": "{og_desc}",
  "foundingDate": "2026",
  "contactPoint": {{
    "@type": "ContactPoint",
    "contactType": "customer service",
    "availableLanguage": ["English", "Urdu"]
  }},
  "sameAs": [
    "https://www.facebook.com/{pname}",
    "https://www.instagram.com/{pname}",
    "https://twitter.com/{pname}"
  ]
}}
"""

        # Meta tags reference file (for developer)
        meta_tags_md = f"""# SEO Meta Tags Reference — {pname}

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>{brand_title}</title>
<meta name="title" content="{brand_title}" />
<meta name="description" content="{meta_desc}" />
<meta name="keywords" content="{keywords}" />
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="{base_url}" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="{base_url}" />
<meta property="og:title" content="{brand_title}" />
<meta property="og:description" content="{og_desc}" />
<meta property="og:image" content="{base_url}/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="{base_url}" />
<meta property="twitter:title" content="{brand_title}" />
<meta property="twitter:description" content="{og_desc}" />
<meta property="twitter:image" content="{base_url}/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
{json_ld}
</script>
```

## Multilingual (hreflang) — Add if i18n enabled
```html
<link rel="alternate" hreflang="en" href="{base_url}/" />
<link rel="alternate" hreflang="ur" href="{base_url}/ur/" />
<link rel="alternate" hreflang="ar" href="{base_url}/ar/" />
<link rel="alternate" hreflang="x-default" href="{base_url}/" />
```

## PWA Meta Tags — Add if PWA enabled
```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="{pname.replace('-', ' ').title()}" />
```
"""

        # PWA manifest.json
        manifest = f"""{{
  "name": "{pname.replace('-', ' ').title()}",
  "short_name": "{pname[:12].title()}",
  "description": "{og_desc}",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#0d9488",
  "orientation": "portrait-primary",
  "icons": [
    {{ "src": "/icons/icon-72x72.png",   "sizes": "72x72",   "type": "image/png" }},
    {{ "src": "/icons/icon-96x96.png",   "sizes": "96x96",   "type": "image/png" }},
    {{ "src": "/icons/icon-128x128.png", "sizes": "128x128", "type": "image/png" }},
    {{ "src": "/icons/icon-144x144.png", "sizes": "144x144", "type": "image/png" }},
    {{ "src": "/icons/icon-152x152.png", "sizes": "152x152", "type": "image/png" }},
    {{ "src": "/icons/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" }},
    {{ "src": "/icons/icon-384x384.png", "sizes": "384x384", "type": "image/png" }},
    {{ "src": "/icons/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }}
  ],
  "categories": ["{industry}"],
  "screenshots": []
}}
"""

        seo_dir = target_dir / "frontend" / "public"
        FileManager.ensure_dir(str(seo_dir))
        FileManager.write_file(str(seo_dir / "robots.txt"),           robots)
        FileManager.write_file(str(seo_dir / "sitemap.xml"),          sitemap)
        FileManager.write_file(str(seo_dir / "manifest.json"),        manifest)
        FileManager.write_file(str(target_dir / "SEO_META_TAGS.md"),  meta_tags_md)
        FileManager.write_file(str(target_dir / "structured-data.json"), json_ld)

        # Persuasive industry copy deck — replaces generic placeholder content
        value_props = "\n\n".join(
            f"### {p['title']}\n{p['text']}" for p in copy.get("value_props", [])
        )
        copy_deck = f"""# Client Copy Brief — {pname.title()}

Industry: {copy['industry']}
Website type: {wtype}

## Hero
- **Tagline:** {copy['tagline']}
- **Headline:** {copy['headline']}
- **Subheadline:** {copy['subheadline']}
- **Primary CTA:** {copy['cta']}

## SEO
- **Meta description:** {meta_desc}
- **Keywords:** {keywords}
- **Open Graph:** {og_desc}

## Value propositions
{value_props}

## Social proof
> {copy['testimonial']}

Use these blocks as-is in the generated site's hero, features, and contact
sections for conversion-focused, industry-specific messaging.
"""
        FileManager.write_file(str(target_dir / "COPY_BRIEF.md"), copy_deck)
        agent_logger.info("SEO files generated: robots.txt, sitemap.xml, manifest.json, SEO_META_TAGS.md, structured-data.json, COPY_BRIEF.md")

    def _generate_cicd_workflow(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate GitHub Actions CI/CD workflow for automated deploys."""
        pname = plan.get("project_name", "app")

        workflow = f"""\
# ─────────────────────────────────────────────────────────────────
# CI/CD Pipeline — {pname}
# Deployment pipeline managed by the project toolchain
# ─────────────────────────────────────────────────────────────────
name: Deploy {pname}

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

env:
  NODE_VERSION: "20"
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{{{ github.repository_owner }}}}/{pname}

jobs:
  # ── Lint & Test ──────────────────────────────────────────────
  test:
    name: Lint & Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ env.NODE_VERSION }}}}
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend deps
        run: npm ci
        working-directory: frontend

      - name: Run ESLint
        run: npm run lint
        working-directory: frontend

      - name: Build frontend
        run: npm run build
        working-directory: frontend
        env:
          VITE_API_URL: ${{{{ secrets.VITE_API_URL }}}}

  # ── Deploy Frontend to Vercel ────────────────────────────────
  deploy-frontend:
    name: Deploy Frontend (Vercel)
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{{{ secrets.VERCEL_TOKEN }}}}
          vercel-org-id: ${{{{ secrets.VERCEL_ORG_ID }}}}
          vercel-project-id: ${{{{ secrets.VERCEL_PROJECT_ID }}}}
          working-directory: ./frontend
          vercel-args: "--prod"

  # ── Deploy Backend to Render ─────────────────────────────────
  deploy-backend:
    name: Deploy Backend (Render)
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST ${{{{ secrets.RENDER_DEPLOY_HOOK_URL }}}}

  # ── Build & Push Docker Images ───────────────────────────────
  docker:
    name: Build Docker Images
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Build & push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_PREFIX }}}}-frontend:latest

      - name: Build & push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_PREFIX }}}}-backend:latest
"""

        github_dir = target_dir / ".github" / "workflows"
        FileManager.ensure_dir(str(github_dir))
        FileManager.write_file(str(github_dir / "deploy.yml"), workflow)
        agent_logger.info("CI/CD workflow generated: .github/workflows/deploy.yml")

    def _generate_deployment_checklist(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate DEPLOYMENT_CHECKLIST.md — international production launch checklist."""
        pname = plan.get("project_name", "project")
        spec  = plan.get("spec", {}) or {}

        checklist = f"""# ✅ PRODUCTION DEPLOYMENT CHECKLIST — {pname.upper()}

---

## 🔐 Security (Before going live)
- [ ] Change ALL default passwords and JWT secrets in `.env`
- [ ] Enable HTTPS / SSL certificate (Let's Encrypt or Cloudflare)
- [ ] Set `NODE_ENV=production` on backend
- [ ] Configure CORS to only allow your production domain
- [ ] Enable rate limiting on all API endpoints
- [ ] Run OWASP ZAP security scan
- [ ] Ensure `.env` files are in `.gitignore` — NEVER commit secrets
- [ ] Review all admin routes — require auth middleware

## ⚡ Performance (Before going live)
- [ ] Run `npm run build` — check bundle size < 500KB gzipped
- [ ] Enable Cloudflare CDN or AWS CloudFront
- [ ] Compress images to WebP format
- [ ] Test Lighthouse score ≥ 90 on mobile
- [ ] Enable gzip/brotli compression on Nginx
- [ ] Add `Cache-Control` headers for static assets

## 🌐 SEO & Discoverability
- [ ] Submit `sitemap.xml` to Google Search Console
- [ ] Verify `robots.txt` is accessible at `/robots.txt`
- [ ] Add all Open Graph images (1200×630px)
- [ ] Test Open Graph with https://developers.facebook.com/tools/debug/
- [ ] Test Twitter Card with https://cards-dev.twitter.com/validator
- [ ] Add Google Analytics 4 / Plausible tracking code
- [ ] Add JSON-LD structured data (already generated in `structured-data.json`)

## 📱 Mobile & PWA
- [ ] Test on real mobile devices (iOS Safari + Android Chrome)
- [ ] Verify PWA install prompt works (check `manifest.json`)
- [ ] Test offline mode if PWA enabled
- [ ] Check tap target sizes (minimum 44×44px)
- [ ] Test WhatsApp float button on mobile

## 💳 Payments (if applicable)
- [ ] Switch Stripe from TEST keys to LIVE keys
- [ ] Test full checkout flow with real card
- [ ] Set up Stripe webhook endpoint and verify signature
- [ ] Configure Stripe for correct currency (PKR/USD/EUR)
- [ ] Test refund flow

## 🗄️ Database
- [ ] Apply backend migrations with `npm run db:migrate` before releasing
- [ ] Set up automated database backups (daily minimum)
- [ ] Create read replica for analytics queries
- [ ] Test database connection pool under load

## 📧 Email & Notifications
- [ ] Configure SMTP (SendGrid/AWS SES/Mailgun) — not localhost
- [ ] Test transactional emails: welcome, reset password, order confirm
- [ ] Set up email monitoring for bounces and spam complaints
- [ ] WhatsApp Business API setup (if using Twilio/360dialog)

## 🔍 Monitoring & Alerts
- [ ] Set up Sentry for error tracking (frontend + backend)
- [ ] Configure uptime monitoring (UptimeRobot / Better Uptime)
- [ ] Set up server resource alerts (CPU > 80%, RAM > 85%)
- [ ] Enable CloudFlare Analytics or similar

## 🚀 CI/CD (GitHub Actions — already generated)
- [ ] Add `VERCEL_TOKEN` to GitHub Secrets
- [ ] Add `RENDER_DEPLOY_HOOK_URL` to GitHub Secrets
- [ ] Add `VITE_API_URL` to GitHub Secrets
- [ ] Test full CI pipeline on a feature branch first

## 🌍 International / Compliance
- [ ] GDPR cookie consent banner is visible on first visit (EU)
- [ ] Privacy Policy and Terms of Service pages published
- [ ] CCPA compliance if serving California users
- [ ] PCI DSS compliance if storing card data (use Stripe — never store raw cards)
- [ ] Verify multilingual content if i18n enabled

## ✅ Final Launch Check
- [ ] All environment variables set in production
- [ ] Test complete user journey: signup → browse → purchase/book → confirm
- [ ] Test on 3 browsers: Chrome, Safari, Firefox
- [ ] Test on iOS and Android mobile
- [ ] Set up domain DNS (A record or CNAME to hosting)
- [ ] Verify HTTPS works and HTTP redirects to HTTPS
- [ ] Announce launch on social media with WhatsApp status 🎉

---

*Deployment checklist generated for production readiness.*
"""

        FileManager.write_file(str(target_dir / "DEPLOYMENT_CHECKLIST.md"), checklist)
        agent_logger.info("Deployment checklist generated: DEPLOYMENT_CHECKLIST.md")

    def _generate_instructions_guide(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate a comprehensive, international-standard INSTRUCTIONS.md file."""
        pname = plan.get("project_name", "generated-project")
        components = plan.get("components", [])
        backend = plan.get("backend", {})
        schemas = plan.get("database_schemas", [])
        spec = plan.get("spec", {})
        website_type = spec.get("website_type", "web") if spec else "web"
        industry = spec.get("industry", "general") if spec else "general"
        features_list = spec.get("features", []) if spec else []

        schema_list = "\n".join([f"   - **{s.get('name')}** — tables: {s.get('tables', '')}" for s in schemas]) or "   - Default schema"
        component_list = "\n".join([f"   - `{c.get('name', 'Component')}`" for c in components[:15]]) or "   - Core UI components"
        features_md = "\n".join([f"   - {f.replace('_', ' ').title()}" for f in features_list[:12]]) or "   - Standard features"

        instructions = f"""# ╔══════════════════════════════════════════════════════════════╗
# ║         COMPLETE PROJECT INSTRUCTIONS                       ║
# ╚══════════════════════════════════════════════════════════════╝

**Project Name:** `{pname}`
**Generated By:** Production Pipeline
**Website Type:** {website_type.title()} | **Industry:** {industry.title()}
**Generation Date:** See `generation-report.json`

> This document is your complete guide — from first install to live production.
> Follow every step in order. Each step takes 2–5 minutes.

---

## 📋 TABLE OF CONTENTS

1. [System Requirements](#1-system-requirements)
2. [Project Structure](#2-project-structure)
3. [Frontend Setup](#3-frontend-setup-reactjs--vite)
4. [Backend Setup](#4-backend-setup-nodejs--express)
5. [Database Setup](#5-database-setup-postgresql)
6. [Environment Variables](#6-environment-variables)
7. [Running in Development](#7-running-in-development)
8. [Running in Production](#8-running-in-production)
9. [Cloud Deployment](#9-cloud-deployment)
10. [Docker Setup](#10-docker-setup)
11. [Troubleshooting](#11-troubleshooting)
12. [Project Summary](#12-project-summary)

---

## 1. SYSTEM REQUIREMENTS

Before starting, install these tools on your computer:

| Tool | Minimum Version | Download Link |
|------|----------------|---------------|
| **Node.js** | v18.0.0 or higher | https://nodejs.org/en/download |
| **npm** | v9.0.0 or higher | Comes with Node.js |
| **PostgreSQL** | v14.0 or higher | https://www.postgresql.org/download |
| **Git** | v2.30+ | https://git-scm.com/downloads |

### How to check if installed:
```bash
node --version       # Should print v18.x.x or higher
npm --version        # Should print 9.x.x or higher
psql --version       # Should print 14.x or higher
```

---

## 2. PROJECT STRUCTURE

```
{pname}/
├── frontend/              ← React.js + Vite app (your website UI)
│   ├── src/
│   │   ├── components/    ← {len(components)} UI components
│   │   ├── pages/         ← Main page files
│   │   ├── assets/        ← Images, icons, fonts
│   │   └── App.jsx        ← Root component
│   ├── package.json
│   └── .env.example       ← Copy to .env
│
├── backend/               ← Node.js + Express REST API
│   ├── routes/            ← API route handlers
│   ├── middleware/        ← Auth, rate limiting, CORS
│   ├── server.js          ← Entry point
│   ├── package.json
│   └── .env.example       ← Copy to .env
│
├── database/
│   └── README.md          ← Migration and schema notes
│
├── README.md              ← Project overview
└── INSTRUCTIONS.md        ← This file
```

---

## 3. FRONTEND SETUP (React.js + Vite)

### Step 3.1 — Navigate to frontend folder
```bash
cd {pname}/frontend
```

### Step 3.2 — Install all dependencies
```bash
npm install
```
⏳ This downloads all packages. Takes 1–3 minutes.

### Step 3.3 — Create your environment file
```bash
# On Mac/Linux:
cp .env.example .env

# On Windows (Command Prompt):
copy .env.example .env

# On Windows (PowerShell):
Copy-Item .env.example .env
```

### Step 3.4 — Start the development server
```bash
npm run dev
```

✅ **Frontend is live at:** http://localhost:5173

---

## 4. BACKEND SETUP (Node.js + Express)

Open a **new terminal window** (keep the frontend terminal running).

### Step 4.1 — Navigate to backend folder
```bash
cd {pname}/backend
```

### Step 4.2 — Install dependencies
```bash
npm install
```

### Step 4.3 — Create your environment file
```bash
# Mac/Linux:
cp .env.example .env

# Windows PowerShell:
Copy-Item .env.example .env
```

### Step 4.4 — Edit the .env file
Open `backend/.env` and update these values:
```
PORT=5000
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/{pname.replace("-", "_")}_db
# Generate with: node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
JWT_SECRET=
```

### Step 4.5 — Start the backend server
```bash
npm run dev
```

✅ **Backend API is live at:** http://localhost:5000
✅ **API Health Check:** http://localhost:5000/health

---

## 5. DATABASE SETUP (PostgreSQL)

### Step 5.1 — Open PostgreSQL
Open **pgAdmin** (GUI) or **terminal/PowerShell** and connect:
```bash
psql -U postgres
```
Enter your PostgreSQL password when prompted.

### Step 5.2 — Create the database
```sql
CREATE DATABASE {pname.replace("-", "_")}_db;
```
Then exit: `\\q`

### Step 5.3 — Apply database migrations
```bash
cd backend
npm install
npm run db:migrate
```

The backend also applies pending versioned migrations before listening. Never
run test migrations against a production database.

Additional schema references, if any, are stored in `database/reference/`.
They are not applied automatically; incorporate required changes as versioned
migrations under `backend/migrations/`.

---

## 6. ENVIRONMENT VARIABLES

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:5000
VITE_APP_NAME={pname}
VITE_APP_ENV=development
```

### Backend (`backend/.env`)
```env
# Server
PORT=5000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/{pname.replace("-", "_")}_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME={pname.replace("-", "_")}_db
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRESQL_PASSWORD

# Security — REQUIRED IN PRODUCTION
# Generate with: node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
#             or: openssl rand -hex 32
# The backend refuses to start if this is missing, short (<32), or a known placeholder.
JWT_SECRET=
JWT_EXPIRES_IN=7d
BCRYPT_ROUNDS=12

# CORS
CORS_ORIGIN=http://localhost:5173

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100
```

> ⚠️ **NEVER commit your .env file to Git. It's in .gitignore by default.**

---

## 7. RUNNING IN DEVELOPMENT

Run both frontend and backend simultaneously:

**Terminal 1 (Frontend):**
```bash
cd frontend
npm run dev
# → http://localhost:5173
```

**Terminal 2 (Backend):**
```bash
cd backend
npm run dev
# → http://localhost:5000
```

Both servers support **hot reload** — changes appear instantly.

---

## 8. RUNNING IN PRODUCTION

### Frontend — Build for Production
```bash
cd frontend
npm run build
```
Output goes to `frontend/dist/` — this is what you deploy.

### Backend — Production Mode
```bash
cd backend
NODE_ENV=production npm start
```

---

## 9. CLOUD DEPLOYMENT

### Deploy Frontend to Vercel (Recommended — Free)
1. Go to https://vercel.com and sign up
2. Click **"New Project"** → Import your repo
3. Set **Framework Preset**: Vite
4. Set **Root Directory**: `frontend`
5. Add **Environment Variables** (from `frontend/.env.example`)
6. Click **Deploy** ✅

### Deploy Backend to Render (Free Tier Available)
1. Go to https://render.com and sign up
2. Click **"New Web Service"** → Connect repo
3. Set **Root Directory**: `backend`
4. Set **Build Command**: `npm install`
5. Set **Start Command**: `npm start`
6. Add all **Environment Variables** from `backend/.env.example`
7. Deploy ✅

### Deploy Database to Supabase (Free PostgreSQL)
1. Go to https://supabase.com
2. Create new project → copy the **Connection String**
3. Set `DATABASE_URL` in your backend environment
4. Run `npm run db:migrate` from `backend/` (or allow API startup to apply migrations)

---

## 10. DOCKER SETUP

If you prefer Docker, run everything with one command:

```bash
# From the project root, create docker-compose.yml:
# (Already included if Docker files were generated)

docker-compose up --build
```

Or run individually:
```bash
# Build frontend
docker build -t {pname}-frontend ./frontend

# Build backend
docker build -t {pname}-backend ./backend

# Run backend
docker run -p 5000:5000 --env-file ./backend/.env {pname}-backend

# Run frontend
docker run -p 5173:5173 {pname}-frontend
```

---

## 11. TROUBLESHOOTING

### ❌ `npm install` fails
```bash
# Clear npm cache and retry:
npm cache clean --force
npm install
```

### ❌ Frontend can't connect to backend (CORS error)
- Make sure `CORS_ORIGIN` in `backend/.env` matches your frontend URL exactly
- Both must be running simultaneously

### ❌ PostgreSQL connection refused
- Make sure PostgreSQL service is running:
  ```bash
  # Windows: Check Services app → PostgreSQL should be "Running"
  # Mac: brew services start postgresql
  # Linux: sudo systemctl start postgresql
  ```
- Double-check `DATABASE_URL` in `backend/.env`

### ❌ Port already in use
```bash
# Kill process on port 5000:
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:5000 | xargs kill
```

### ❌ `JWT_SECRET` errors
- The backend exits on boot if `JWT_SECRET` is missing, shorter than 32 characters, or a known placeholder
- Generate one with `node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"` or `openssl rand -hex 32`

### ❌ Build fails with Tailwind errors
```bash
cd frontend
npm install tailwindcss postcss autoprefixer --save-dev
npx tailwindcss init
npm run build
```

---

## 12. PROJECT SUMMARY

| Item | Detail |
|------|--------|
| **Project Name** | {pname} |
| **Website Type** | {website_type.title()} |
| **Industry** | {industry.title()} |
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **Backend** | Node.js + Express.js |
| **Database** | PostgreSQL |
| **Auth** | JWT + bcryptjs |
| **Components** | {len(components)} assembled |
| **API Base** | http://localhost:5000 |
| **Frontend** | http://localhost:5173 |

### ✅ Features Included:
{features_md}

### 📦 Components Included:
{component_list}

---

## 🆘 NEED HELP?

- 📧 **Email:** support@yourcompany.com
- 📖 **Docs:** /docs
- 💬 **Community:** reach out to your account team
- 🐛 **Issues:** create an issue in your repository tracker

---

*Generated by the production pipeline.*
"""
        FileManager.write_file(str(target_dir / "INSTRUCTIONS.md"), instructions)
