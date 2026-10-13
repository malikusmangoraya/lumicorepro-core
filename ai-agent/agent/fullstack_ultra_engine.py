"""Full-Stack Ultra Engine — LumicorePro AI Agent
================================================
High-speed autonomous engine that generates clean, production-ready, international-standard
full-stack web applications (React 19 + Tailwind 3 Frontend, Express.js REST API Backend,
Sequelize Database Models, JWT Auth, Docker Infrastructure) in single-digit seconds.
"""

import os
import time
import json
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger
from agent.hyper_unique_site_engine import HyperUniqueSiteEngine
from agent.omni_repair_engine import OmniRepairEngine
from agent.generation_contract import resolve_generation_contract


class FullStackUltraEngine:
    """Generates complete, clean, professional full-stack web applications at maximum velocity."""

    def __init__(self):
        self.unique_engine = HyperUniqueSiteEngine()
        self.repair_engine = OmniRepairEngine()

    def generate_project(
        self,
        destination_dir: str,
        prompt: str = "Enterprise AI Cloud Platform",
        brand_name: Optional[str] = None,
        industry: str = "saas",
        primary_color: Optional[str] = None,
        *,
        generation_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generates a complete full-stack project in destination_dir concurrently."""
        start_time = time.perf_counter()
        contract = generation_contract or resolve_generation_contract({})
        if contract.get("layout_mode") != "enterprise":
            raise ValueError("FullStackUltraEngine currently supports enterprise full-stack delivery only")
        brand = brand_name or prompt.split()[0].capitalize()
        blueprint = self.unique_engine.synthesize_hyper_unique_blueprint(prompt, brand)
        color = primary_color or blueprint["palette"]["primary"]
        accent = blueprint["palette"]["accent"]
        palette = blueprint["palette"]

        dest = os.path.abspath(destination_dir)
        os.makedirs(dest, exist_ok=True)

        # Plan all files to write concurrently
        files_map: Dict[str, str] = {}

        # ── 1. Frontend Files ─────────────────────────────────────────────
        self._build_frontend_files(files_map, brand, color, accent, palette, industry)

        # ── 2. Backend Files ──────────────────────────────────────────────
        self._build_backend_files(files_map, brand)
        self._configure_postgresql_backend(files_map, brand)

        # ── 3. DevOps & Documentation Files ───────────────────────────────
        self._build_devops_files(files_map, brand, prompt)
        files_map["backend/migrations/001_create_core_tables.js"] = self._postgres_migration()
        files_map["backend/package.json"] = self._fullstack_backend_package(files_map["backend/package.json"])
        files_map["LICENSE.md"] = self._generated_license(brand)

        # ── Concurrent Parallel File Writing ──────────────────────────────
        write_errors = []
        def _write_single_file(rel_path: str, content: str):
            full_path = os.path.join(dest, rel_path)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fh:
                    fh.write(content)
            except Exception as exc:
                write_errors.append(f"{rel_path}: {exc}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(_write_single_file, rel_p, content) for rel_p, content in files_map.items()]
            concurrent.futures.wait(futures)

        # ── Self-Healing Omni-Repair Pass ─────────────────────────────────
        repair_report = self.repair_engine.scan_and_repair_project(dest)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        agent_logger.info(
            f"FullStackUltraEngine: Generated {len(files_map)} full-stack files in {elapsed_ms}ms"
        )

        return {
            "success": len(write_errors) == 0,
            "brand": brand,
            "industry": industry,
            "destination": dest,
            "total_files": len(files_map),
            "elapsed_ms": elapsed_ms,
            "errors": write_errors,
            "palette": palette,
            "omni_repairs": repair_report.get("repairs_applied", 0),
            "stack": {
                "frontend": "React 19 + Vite + Tailwind CSS + Lucide Icons + Framer Motion",
                "backend": "Express.js + Sequelize + JWT + bcrypt + Helmet + CORS",
                "database": "PostgreSQL",
                "devops": "Docker + docker-compose + Nginx reverse proxy",
            },
        }

    @staticmethod
    def _fullstack_backend_package(package_text: str) -> str:
        package = json.loads(package_text)
        package.setdefault("scripts", {}).update({"db:migrate": "node migrations/run.js", "test": "node --test"})
        dependencies = package.setdefault("dependencies", {})
        dependencies.pop("sqlite3", None)
        dependencies["pg"] = "^8.13.1"
        dependencies["pg-hstore"] = "^2.3.4"
        return json.dumps(package, indent=2)

    @staticmethod
    def _configure_postgresql_backend(files_map: Dict[str, str], brand: str) -> None:
        files_map["backend/models/index.js"] = """const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || 'lumicore_app',
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  logging: false,
});

const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
});

module.exports = { sequelize, User };
"""

    @staticmethod
    def _postgres_migration() -> str:
        return """const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('users', {
      id: { type: DataTypes.UUID, primaryKey: true },
      name: { type: DataTypes.STRING, allowNull: false },
      email: { type: DataTypes.STRING, allowNull: false, unique: true },
      password: { type: DataTypes.STRING, allowNull: false },
      role: { type: DataTypes.STRING, allowNull: false, defaultValue: 'user' },
      created_at: { type: DataTypes.DATE, allowNull: false },
      updated_at: { type: DataTypes.DATE, allowNull: false },
    });
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('users');
  },
};
"""

    @staticmethod
    def _generated_license(brand: str) -> str:
        return (
            f"# {brand} License\n\n"
            "Commercial use and modification are permitted for the purchaser and their clients. "
            "Redistribution as a competing template is not permitted.\n"
        )

    def _build_frontend_files(self, fmap: Dict[str, str], brand: str, color: str, accent: str, palette: Dict[str, str], industry: str):
        # package.json
        fmap["frontend/package.json"] = json.dumps({
            "name": f"{brand.lower()}-frontend",
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
                "react-router-dom": "^6.28.0",
                "lucide-react": "^1.31.0",
                "framer-motion": "^11.18.2",
                "clsx": "^2.1.1",
                "tailwind-merge": "^2.6.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.3.4",
                "vite": "^6.0.0",
                "tailwindcss": "^3.4.17",
                "postcss": "^8.4.49",
                "autoprefixer": "^10.4.20"
            }
        }, indent=2)

        # vite.config.js
        fmap["frontend/vite.config.js"] = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: true },
});
"""

        # tailwind.config.js
        fmap["frontend/tailwind.config.js"] = f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  content: ["./index.html", "./src/**/*.{{js,ts,jsx,tsx}}"],
  darkMode: "class",
  theme: {{
    extend: {{
      colors: {{
        brand: {{
          primary: "{color}",
          accent: "{accent}",
          surface: "{palette['surface']}",
          background: "{palette['background']}",
        }},
      }},
    }},
  }},
  plugins: [],
}};
"""

        # index.html
        fmap["frontend/index.html"] = f"""<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{brand} — Professional Global Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body class="bg-slate-950 text-slate-50 antialiased selection:bg-brand-primary selection:text-white">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

        # src/index.css
        fmap["frontend/src/index.css"] = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
"""

        # src/main.jsx
        fmap["frontend/src/main.jsx"] = """import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
"""

        # src/App.jsx
        fmap["frontend/src/App.jsx"] = f"""import React from 'react';
import {{ Routes, Route }} from 'react-router-dom';
import GlassNavbar from './components/common/GlassNavbar.jsx';
import ModernFooter from './components/common/ModernFooter.jsx';
import Home from './pages/Home.jsx';
import Features from './pages/Features.jsx';
import Pricing from './pages/Pricing.jsx';
import About from './pages/About.jsx';
import Contact from './pages/Contact.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';

export default function App() {{
  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">
      <GlassNavbar brand="{brand}" />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={{<Home />}} />
          <Route path="/features" element={{<Features />}} />
          <Route path="/pricing" element={{<Pricing />}} />
          <Route path="/about" element={{<About />}} />
          <Route path="/contact" element={{<Contact />}} />
          <Route path="/login" element={{<Login />}} />
          <Route path="/register" element={{<Register />}} />
          <Route path="/dashboard" element={{<Dashboard />}} />
        </Routes>
      </main>
      <ModernFooter brand="{brand}" />
    </div>
  );
}}
"""

        # src/components/common/UniqueLogo.jsx
        fmap["frontend/src/components/common/UniqueLogo.jsx"] = f"""import React from 'react';

export default function UniqueLogo({{ size = "w-8 h-8", className = "" }}) {{
  return (
    <div className={{`inline-flex items-center justify-center ${{size}} ${{className}}`}}>
      <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="{color}" />
            <stop offset="100%" stopColor="{accent}" />
          </linearGradient>
        </defs>
        <polygon points="24,4 40,14 40,34 24,44 8,34 8,14" fill="none" stroke="url(#logoGrad)" strokeWidth="3" />
        <circle cx="24" cy="24" r="5" fill="{accent}" />
        <line x1="24" y1="4" x2="24" y2="19" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="40" y1="34" x2="27" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
        <line x1="8" y1="34" x2="21" y2="26" stroke="url(#logoGrad)" strokeWidth="2" />
      </svg>
    </div>
  );
}}
"""

        # src/components/common/GlassNavbar.jsx
        fmap["frontend/src/components/common/GlassNavbar.jsx"] = f"""import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Menu, X, Globe, DollarSign, ArrowRight }} from 'lucide-react';
import UniqueLogo from './UniqueLogo.jsx';

export default function GlassNavbar({{ brand = "{brand}" }}) {{
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currency, setCurrency] = useState('USD');

  const navLinks = [
    {{ name: 'Features', path: '/features' }},
    {{ name: 'Pricing', path: '/pricing' }},
    {{ name: 'About', path: '/about' }},
    {{ name: 'Contact', path: '/contact' }},
  ];

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/70 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <UniqueLogo size="w-9 h-9" />
          <span className="text-xl font-extrabold tracking-tight text-white group-hover:text-cyan-400 transition-colors">
            {brand}
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {{navLinks.map((item) => (
            <Link
              key={{item.name}}
              to={{item.path}}
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              {{item.name}}
            </Link>
          ))}}
        </nav>

        <div className="hidden md:flex items-center gap-4">
          <div className="flex items-center gap-1 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded-full">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={{currency}}
              onChange={{(e) => setCurrency(e.target.value)}}
              className="bg-transparent text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="USD" className="bg-slate-900">USD ($)</option>
              <option value="EUR" className="bg-slate-900">EUR (€)</option>
              <option value="GBP" className="bg-slate-900">GBP (£)</option>
              <option value="PKR" className="bg-slate-900">PKR (₨)</option>
            </select>
          </div>

          <Link
            to="/login"
            className="text-sm font-medium text-slate-300 hover:text-white px-3 py-2"
          >
            Sign in
          </Link>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-{color} to-cyan-500 hover:opacity-95 shadow-lg shadow-{color}/20 transition-all"
          >
            Get Started <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <button
          onClick={{() => setMobileOpen(!mobileOpen)}}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          {{mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}}
        </button>
      </div>

      {{mobileOpen && (
        <div className="md:hidden px-4 pt-2 pb-6 bg-slate-950 border-b border-slate-800 space-y-3">
          {{navLinks.map((item) => (
            <Link
              key={{item.name}}
              to={{item.path}}
              onClick={{() => setMobileOpen(false)}}
              className="block text-base font-medium text-slate-300 hover:text-white py-2"
            >
              {{item.name}}
            </Link>
          ))}}
          <div className="pt-4 border-t border-slate-800 flex flex-col gap-3">
            <Link to="/login" className="text-center py-2 text-slate-300">Sign in</Link>
            <Link to="/register" className="text-center py-2.5 rounded-full bg-{color} text-white font-semibold">Get Started</Link>
          </div>
        </div>
      )}}
    </header>
  );
}}
"""

        # src/components/common/ModernFooter.jsx
        fmap["frontend/src/components/common/ModernFooter.jsx"] = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ShieldCheck, Heart }} from 'lucide-react';
import UniqueLogo from './UniqueLogo.jsx';

export default function ModernFooter({{ brand = "{brand}" }}) {{
  return (
    <footer className="bg-slate-950 border-t border-slate-900 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <UniqueLogo size="w-8 h-8" />
              <span className="text-xl font-extrabold text-white">{brand}</span>
            </div>
            <p className="text-slate-400 text-sm max-w-sm mb-6 leading-relaxed">
              Precision-engineered digital infrastructure delivering sub-millisecond experiences for global scale.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Systems Operational
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Product</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><Link to="/features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/features" className="hover:text-white transition-colors">Enterprise</Link></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Console</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Company</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><Link to="/about" className="hover:text-white transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Careers</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">Press</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">Legal</h4>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Security Posture</a></li>
              <li><a href="#" className="hover:text-white transition-colors">GDPR Compliance</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 {brand} Inc. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-slate-400" /> ISO 27001 Certified</span>
            <span>Built with precision engineering</span>
          </div>
        </div>
      </div>
    </footer>
  );
}}
"""

        # src/pages/Home.jsx
        fmap["frontend/src/pages/Home.jsx"] = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight, CheckCircle2, Zap, Shield, Globe, Cpu, BarChart3 }} from 'lucide-react';

export default function Home() {{
  return (
    <div className="space-y-24 py-12">
      <!-- Hero Section -->
      <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center pt-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-{color}/10 text-{color} border border-{color}/30 mb-8">
          <Zap className="w-3.5 h-3.5" /> Next-Generation Global Architecture
        </div>
        <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
          Supercharge your business with <span className="bg-clip-text text-transparent bg-gradient-to-r from-{color} via-cyan-400 to-indigo-400">{brand}</span>
        </h1>
        <p className="mt-6 text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
          The all-in-one international platform engineered for lightning speed, unmatched resilience, and global scale.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="w-full sm:w-auto px-8 py-4 rounded-full text-base font-bold text-white bg-gradient-to-r from-{color} to-cyan-500 shadow-xl shadow-{color}/25 hover:opacity-95 transition-all flex items-center justify-center gap-2"
          >
            Start Free Trial <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            to="/features"
            className="w-full sm:w-auto px-8 py-4 rounded-full text-base font-semibold text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors"
          >
            Explore Platform
          </Link>
        </div>
      </section>

      <!-- Bento Grid Section -->
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">Built for High-Growth Scale</h2>
          <p className="mt-4 text-slate-400">Everything needed to power modern enterprise operations.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-{color}/40 transition-colors">
            <Cpu className="w-10 h-10 text-{color} mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Automated Execution</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Sub-second execution pipelines that scale autonomously based on load.</p>
          </div>
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-{color}/40 transition-colors">
            <Shield className="w-10 h-10 text-{color} mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Enterprise Security</h3>
            <p className="text-slate-400 text-sm leading-relaxed">End-to-end encryption, automated compliance audit logs, and zero-trust perimeter.</p>
          </div>
          <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-{color}/40 transition-colors">
            <Globe className="w-10 h-10 text-{color} mb-6" />
            <h3 className="text-xl font-bold text-white mb-2">Global CDN Mesh</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Global multi-region replication with automatic failover and sub-15ms edge routing.</p>
          </div>
        </div>
      </section>
    </div>
  );
}}
"""

        # Remaining Pages: Features, Pricing, About, Contact, Login, Register, Dashboard
        pages = {
            "Features.jsx": f"""import React from 'react';
export default function Features() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">Features & Capabilities</h1>
      <p className="text-slate-300 text-lg">Comprehensive tools built for performance, reliability, and precision.</p>
    </div>
  );
}}""",
            "Pricing.jsx": f"""import React from 'react';
export default function Pricing() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-20 text-center">
      <h1 className="text-4xl font-extrabold text-white mb-4">Transparent Pricing</h1>
      <p className="text-slate-300 mb-12">Choose the plan that fits your growth.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-left">
          <h3 className="text-xl font-bold text-white">Starter</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$29<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900 border-2 border-{color} text-left">
          <h3 className="text-xl font-bold text-white">Pro</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$79<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 text-left">
          <h3 className="text-xl font-bold text-white">Enterprise</h3>
          <p className="text-3xl font-extrabold text-white mt-4">$199<span className="text-sm text-slate-400 font-normal">/mo</span></p>
        </div>
      </div>
    </div>
  );
}}""",
            "About.jsx": f"""import React from 'react';
export default function About() {{
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">About {brand}</h1>
      <p className="text-slate-300 leading-relaxed">Engineered by a global team dedicated to building top-tier software architecture.</p>
    </div>
  );
}}""",
            "Contact.jsx": f"""import React from 'react';
export default function Contact() {{
  return (
    <div className="max-w-xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-extrabold text-white mb-6">Get in Touch</h1>
      <form className="space-y-4">
        <input type="text" placeholder="Name" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white" />
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white" />
        <textarea rows={{4}} placeholder="Message" className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white"></textarea>
        <button type="submit" className="w-full py-3.5 rounded-xl bg-{color} text-white font-bold">Send Message</button>
      </form>
    </div>
  );
}}""",
            "Login.jsx": f"""import React from 'react';
export default function Login() {{
  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Sign in to {brand}</h2>
      <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="password" placeholder="Password" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <button className="w-full py-3.5 rounded-xl bg-{color} text-white font-bold">Sign In</button>
      </div>
    </div>
  );
}}""",
            "Register.jsx": f"""import React from 'react';
export default function Register() {{
  return (
    <div className="max-w-md mx-auto px-6 py-24">
      <h2 className="text-3xl font-bold text-white text-center mb-8">Create Your Account</h2>
      <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
        <input type="text" placeholder="Full Name" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="email" placeholder="Email" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <input type="password" placeholder="Password" className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white" />
        <button className="w-full py-3.5 rounded-xl bg-{color} text-white font-bold">Get Started</button>
      </div>
    </div>
  );
}}""",
            "Dashboard.jsx": f"""import React from 'react';
export default function Dashboard() {{
  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white mb-8">Control Console</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Total Requests</p>
          <p className="text-2xl font-bold text-white mt-1">1,420,890</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Average Latency</p>
          <p className="text-2xl font-bold text-white mt-1">12.4ms</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Uptime</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">99.99%</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <p className="text-sm text-slate-400">Active Nodes</p>
          <p className="text-2xl font-bold text-white mt-1">48 / 48</p>
        </div>
      </div>
    </div>
  );
}}""",
        }
        for pname, pcontent in pages.items():
            fmap[f"frontend/src/pages/{pname}"] = pcontent

    def _build_backend_files(self, fmap: Dict[str, str], brand: str):
        # backend/package.json
        fmap["backend/package.json"] = json.dumps({
            "name": f"{brand.lower()}-backend",
            "version": "1.0.0",
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js",
                "db:migrate": "node migrations/run.js",
                "test": "node --test"
            },
            "dependencies": {
                "express": "^4.21.2",
                "cors": "^2.8.5",
                "helmet": "^8.0.0",
                "dotenv": "^16.4.7",
                "jsonwebtoken": "^9.0.2",
                "bcryptjs": "^2.4.3",
                "sequelize": "^6.37.5",
                "pg": "^8.13.1",
                "pg-hstore": "^2.3.4",
                "express-rate-limit": "^7.5.0",
                "compression": "^1.7.5"
            }
        }, indent=2)

        # backend/server.js
        fmap["backend/server.js"] = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const authRoutes = require('./routes/auth.routes');
const healthRoutes = require('./routes/health.routes');
const {{ sequelize }} = require('./models');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(helmet());
app.use(cors({{ origin: '*' }}));
app.use(compression());
app.use(express.json());

const limiter = rateLimit({{
  windowMs: 15 * 60 * 1000,
  max: 200,
}});
app.use(limiter);

app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/health', healthRoutes);

sequelize.sync().then(() => {{
  app.listen(PORT, () => {{
    console.log(`{brand} Backend API running on port ${{PORT}}`);
  }});
}}).catch(err => {{
  console.error('Database connection failed:', err);
}});

module.exports = app;
"""

        # backend/models/index.js
        fmap["backend/models/index.js"] = """const { Sequelize, DataTypes } = require('sequelize');

const sequelize = new Sequelize({
  dialect: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || 'lumicore_app',
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  logging: false,
});

const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
});

module.exports = { sequelize, User };
"""

        # backend/utils/jwtSecret.js -- fail-closed JWT secret resolution.
        # Plain (non-f) Python string literal: JS braces/$, backticks and
        # newlines below are emitted verbatim, so no brace doubling is needed.
        fmap["backend/utils/jwtSecret.js"] = """/**
 * Fail-closed JWT secret resolution.
 *
 * Refuses to boot when JWT_SECRET is missing, shorter than MIN_LENGTH, or a
 * well-known placeholder, so a publicly known value can never be used to forge
 * tokens (including admin tokens).
 *
 * Generate a secret with:
 *   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
 *   # or: openssl rand -hex 32
 */
const DENIED_SECRETS = [
  'secret',
  'changeme',
  'change_me',
  'change-me-in-production',
  'change_this_secret_in_production',
  'change_this_to_a_random_64_char_string',
  'lumi_jwt_secret',
  'replace-me',
  'replace_with_a_random_64_character_secret',
  'replace_with_secure_random_key',
  'secret_jwt_key',
  'secret_jwt_key_2026',
  'super_secret_production_key_2026',
  'your_jwt_secret_key_here',
  'your_super_secret_key_here_change_this',
  'your-super-secret-jwt-key-change-this',
  'your_super_secret_jwt_key_change_this_minimum_32_characters',
];

const MIN_LENGTH = 32;

function fail(reason) {
  console.error(`[fatal] JWT_SECRET ${reason}. Refusing to start.
Generate a strong secret with one of:
  node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
  # or: openssl rand -hex 32
Then set JWT_SECRET in your .env file.`);
  process.exit(1);
}

function resolveJwtSecret(env) {
  const source = env || process.env;
  const raw = source.JWT_SECRET;
  if (typeof raw !== 'string' || raw.trim() === '') fail('is not set');
  const secret = raw.trim();
  if (secret.length < MIN_LENGTH) {
    fail(`must be at least ${MIN_LENGTH} characters (got ${secret.length})`);
  }
  if (DENIED_SECRETS.indexOf(secret.toLowerCase()) !== -1) {
    fail('is a well-known placeholder value');
  }
  return secret;
}

const jwtSecret = Object.freeze(resolveJwtSecret(process.env));

module.exports = { jwtSecret, MIN_LENGTH };
"""

        # backend/routes/auth.routes.js
        fmap["backend/routes/auth.routes.js"] = """const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { User } = require('../models');
const { jwtSecret } = require('../utils/jwtSecret');

const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { name, email, password } = req.body;
    if (!name || !email || !password) return res.status(400).json({ error: 'Missing fields' });

    const hashedPassword = await bcrypt.hash(password, 12);
    const user = await User.create({ name, email, password: hashedPassword });
    const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });

    return res.status(201).json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ where: { email } });
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ id: user.id, email: user.email }, jwtSecret, { expiresIn: '7d' });
    return res.json({ success: true, token, user: { id: user.id, name: user.name, email: user.email } });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

module.exports = router;
"""

        # backend/routes/health.routes.js
        fmap["backend/routes/health.routes.js"] = """const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

module.exports = router;
"""

    def _build_devops_files(self, fmap: Dict[str, str], brand: str, prompt: str):
        fmap["docker-compose.yml"] = f"""version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: lumicore_app
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-postgres}}"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=lumicore_app
      - DB_USER=${{POSTGRES_USER:-postgres}}
      - DB_PASSWORD=${{POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}}
      - JWT_SECRET=${{JWT_SECRET:?JWT_SECRET is required - see backend/.env.example}}

volumes:
  postgres_data:
"""

        fmap["backend/migrations/run.js"] = """const { Umzug, SequelizeStorage } = require('umzug');
const { sequelize } = require('../models');

const umzug = new Umzug({
  migrations: { glob: 'migrations/00*.js' },
  context: sequelize.getQueryInterface(),
  storage: new SequelizeStorage({ sequelize }),
  logger: console,
});

module.exports = umzug;
if (require.main === module) {
  umzug.up().then(() => sequelize.close()).catch((error) => {
    console.error('Migration failed:', error.message);
    process.exitCode = 1;
  });
}
"""
        fmap["backend/package.json"] = json.dumps({
            **json.loads(fmap["backend/package.json"]),
            "dependencies": {**json.loads(fmap["backend/package.json"])["dependencies"], "umzug": "^3.8.2"},
        }, indent=2)
        fmap["backend/migrations/001_create_core_tables.js"] = """const { DataTypes } = require('sequelize');

module.exports = {
  async up({ context: queryInterface }) {
    await queryInterface.createTable('users', {
      id: { type: DataTypes.UUID, primaryKey: true },
      name: { type: DataTypes.STRING, allowNull: false },
      email: { type: DataTypes.STRING, allowNull: false, unique: true },
      password: { type: DataTypes.STRING, allowNull: false },
      role: { type: DataTypes.STRING, allowNull: false, defaultValue: 'user' },
      createdAt: { type: DataTypes.DATE, allowNull: false },
      updatedAt: { type: DataTypes.DATE, allowNull: false },
    });
  },
  async down({ context: queryInterface }) {
    await queryInterface.dropTable('users');
  },
};
"""

        fmap[".env.example"] = f"""PORT=5000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lumicore_app
DB_USER=postgres
POSTGRES_PASSWORD=
DB_PASSWORD=
# REQUIRED, minimum 32 chars. Generate one with:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
#   # or: openssl rand -hex 32
# The backend refuses to start if this is missing, short, or a known placeholder.
JWT_SECRET=
NODE_ENV=production
"""
        fmap["frontend/.env.example"] = "VITE_API_URL=http://localhost:5000/api/v1\n"

        fmap["README.md"] = f"""# {brand} — Full-Stack Application

Generated autonomously by **LumicorePro AI Agent**.

## Features
- **Database**: PostgreSQL with versioned Sequelize migrations.
- **Frontend**: React 19, Tailwind CSS, Lucide Icons, GlassNavbar, BentoGrid, ModernFooter.
- **Backend**: Express.js REST API, Sequelize ORM, JWT Authentication, Helmet security headers.
- **Infrastructure**: Docker containerization & production reverse-proxy support.

## Getting Started

### 1. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 2. Backend
```bash
cd backend
npm install
npm run dev
```

### 3. Docker Deploy
```bash
cp .env.example .env  # set POSTGRES_PASSWORD and JWT_SECRET first
docker compose up --build
```
"""
