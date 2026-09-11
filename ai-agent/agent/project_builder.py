import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from config.settings import PROJECT_ROOT, GENERATED_PROJECTS_DIR
from utils.logger import agent_logger
from utils.file_manager import FileManager

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

    def _resolve_template_path(self, template_info: Dict[str, Any]) -> Path:
        """Resolve template directory path using mapping, with fallback logic."""
        rel_path = template_info.get("file_path", "") if template_info else ""
        # Use the mapping if available, otherwise use rel_path directly
        mapped = self.TEMPLATE_PATH_MAP.get(rel_path, rel_path)
        resolved = (PROJECT_ROOT / mapped).resolve()
        if resolved.exists():
            return resolved
        # Try mapping without the "src/templates/" prefix
        alt_path = "src/templates/" + rel_path.replace("src/templates/", "")
        alt_resolved = (PROJECT_ROOT / alt_path).resolve()
        if alt_resolved.exists():
            return alt_resolved
        # Try every known template path as fallback
        for known in self.TEMPLATE_PATH_MAP.values():
            candidate = (PROJECT_ROOT / known).resolve()
            if candidate.exists():
                agent_logger.warning(f"Template {rel_path} not found, falling back to {known}")
                return candidate
        return resolved  # Return original even if not found

    def build_project(self, plan: Dict[str, Any]) -> str:
        """Execute assembly plan and return path of generated project."""
        project_name = self._safe_project_name(plan.get("project_name", "generated-app"))

        # Idempotent regeneration: never overwrite an existing project dir.
        # Re-running the same spec gets a unique `-002`, `-003`, ... suffix so
        # previous generations keep their preview/dev history intact.
        target_dir = (GENERATED_PROJECTS_DIR / project_name).resolve()
        if target_dir.exists():
            base_name = project_name
            counter = 2
            while (GENERATED_PROJECTS_DIR / f"{base_name}-{counter:03d}").exists():
                counter += 1
            project_name = f"{base_name}-{counter:03d}"
            target_dir = (GENERATED_PROJECTS_DIR / project_name).resolve()

        plan["project_name"] = project_name
        target_dir.relative_to(GENERATED_PROJECTS_DIR)
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
                    "react": "^19.2.8",
                    "react-dom": "^19.2.8",
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
      '@': path.resolve(__dirname, './src'),
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

            # App.jsx — proper routing + page components + cookie consent banner
            default_app = """import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CookieConsent from './components/common/CookieConsent';

const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Services = lazy(() => import('./pages/Services'));
const Contact = lazy(() => import('./pages/Contact'));

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Loader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/services" element={<Services />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
      </Suspense>
      <CookieConsent />
    </BrowserRouter>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "App.jsx"), default_app)

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
      style={{
        position: 'fixed',
        bottom: 16,
        left: 16,
        right: 16,
        zIndex: 9999,
        maxWidth: 420,
        margin: '0 auto',
        padding: 16,
        borderRadius: 12,
        background: '#0f172a',
        color: '#e2e8f0',
        border: '1px solid #1e293b',
        boxShadow: '0 12px 32px rgba(0,0,0,0.45)',
        fontFamily: 'ui-sans-serif, system-ui, sans-serif',
      }}
    >
      <p style={{ margin: '0 0 12px', fontSize: 13, lineHeight: 1.5 }}>
        We use cookies to make our site work and, where you agree, to analyse traffic
        and personalise content. Essential cookies are always active.
      </p>
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={() => decide({ essential: true, analytics: true, marketing: false })}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 8,
            border: 'none',
            background: '#06b6d4',
            color: '#ffffff',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Accept All
        </button>
        <button
          onClick={() => decide({ essential: true, analytics: false, marketing: false })}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid #334155',
            background: 'transparent',
            color: '#cbd5e1',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Essential Only
        </button>
      </div>
    </div>
  );
}
"""
            FileManager.write_file(str(frontend_dir / "src" / "components" / "common" / "CookieConsent.jsx"), default_cookie_consent)

            # ── Page Components ────────────────────────────────────────────
            nav_style = "flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-slate-800"
            link_style = "text-sm text-slate-300 hover:text-cyan-400 transition-colors"
            section_style = "px-6 py-16 max-w-6xl mx-auto"
            btn_style = "inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 transition-colors"

            # Home page
            home_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight, Sparkles, Globe, Zap, Shield, Palette }} from 'lucide-react';

const features = [
  {{ icon: Sparkles, title: 'AI-Powered', desc: 'Built with cutting-edge AI for intelligent automation.' }},
  {{ icon: Globe, title: 'Global Ready', desc: 'Multi-language, multi-currency, worldwide deployment.' }},
  {{ icon: Zap, title: 'Lightning Fast', desc: 'Optimized performance with sub-second load times.' }},
  {{ icon: Shield, title: 'Enterprise Security', desc: 'Bank-grade encryption and compliance built in.' }},
  {{ icon: Palette, title: 'Custom Design', desc: 'Unique, branded design tailored to your business.' }},
];

export default function Home() {{
  return (
    <div className="min-h-screen">
      <nav className="{nav_style}">
        <span className="text-lg font-bold text-cyan-400">{project_name}</span>
        <div className="flex gap-6">
          <Link to="/" className="{link_style}">Home</Link>
          <Link to="/about" className="{link_style}">About</Link>
          <Link to="/services" className="{link_style}">Services</Link>
          <Link to="/contact" className="{link_style}">Contact</Link>
        </div>
      </nav>

      <section className="flex flex-col items-center justify-center px-6 py-32 text-center">
        <span className="mb-4 inline-flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-400">
          <Sparkles className="h-3 w-3" /> AI-Generated Website
        </span>
        <h1 className="mb-6 max-w-3xl text-5xl font-extrabold leading-tight tracking-tight">
          Welcome to <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent">{project_name}</span>
        </h1>
        <p className="mb-10 max-w-xl text-lg text-slate-400">
          A production-quality website generated end-to-end by AI. Real content, real images, real deployment.
        </p>
        <div className="flex gap-4">
          <Link to="/services" className="{btn_style}">
            Our Services <ArrowRight className="h-4 w-4" />
          </Link>
          <Link to="/contact" className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">
            Get in Touch
          </Link>
        </div>
      </section>

      <section className="{section_style}">
        <h2 className="mb-10 text-center text-3xl font-bold">Why Choose Us</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {{features.map((f) => (
            <div key={{f.title}} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 hover:border-cyan-500/50 transition-colors">
              <f.icon className="mb-3 h-8 w-8 text-cyan-400" />
              <h3 className="mb-2 text-lg font-semibold">{{f.title}}</h3>
              <p className="text-sm text-slate-400">{{f.desc}}</p>
            </div>
          ))}}
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {{new Date().getFullYear()}} {project_name}. All rights reserved.
      </footer>
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Home.jsx"), home_page)

            # About page
            about_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Heart, Target, Users, Award }} from 'lucide-react';

const values = [
  {{ icon: Heart, title: 'Passion', desc: 'We love what we do and it shows in every project.' }},
  {{ icon: Target, title: 'Results', desc: 'Data-driven decisions that deliver measurable outcomes.' }},
  {{ icon: Users, title: 'Partnership', desc: 'Your success is our success. We work as one team.' }},
  {{ icon: Award, title: 'Excellence', desc: 'Industry-leading quality in everything we deliver.' }},
];

export default function About() {{
  return (
    <div className="min-h-screen">
      <nav className="{nav_style}">
        <Link to="/" className="text-lg font-bold text-cyan-400">{project_name}</Link>
        <div className="flex gap-6">
          <Link to="/" className="{link_style}">Home</Link>
          <Link to="/about" className="{link_style}">About</Link>
          <Link to="/services" className="{link_style}">Services</Link>
          <Link to="/contact" className="{link_style}">Contact</Link>
        </div>
      </nav>

      <section className="{section_style} text-center">
        <h1 className="mb-4 text-4xl font-extrabold">About Us</h1>
        <p className="mx-auto mb-12 max-w-2xl text-slate-400">
          We are a team of passionate professionals dedicated to delivering exceptional results for our clients.
        </p>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {{values.map((v) => (
            <div key={{v.title}} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
              <v.icon className="mx-auto mb-3 h-8 w-8 text-cyan-400" />
              <h3 className="mb-2 text-lg font-semibold">{{v.title}}</h3>
              <p className="text-sm text-slate-400">{{v.desc}}</p>
            </div>
          ))}}
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {{new Date().getFullYear()}} {project_name}. All rights reserved.
      </footer>
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "About.jsx"), about_page)

            # Services page
            services_page = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Code, Megaphone, BarChart3, Cloud, Lock, Headphones }} from 'lucide-react';

const services = [
  {{ icon: Code, title: 'Web Development', desc: 'Custom websites and web applications built with modern technologies.', price: 'From $999' }},
  {{ icon: Megaphone, title: 'Digital Marketing', desc: 'SEO, social media, and paid advertising to grow your business.', price: 'From $499/mo' }},
  {{ icon: BarChart3, title: 'Analytics & Insights', desc: 'Data-driven insights to optimize your business performance.', price: 'From $299/mo' }},
  {{ icon: Cloud, title: 'Cloud Hosting', desc: 'Reliable, scalable hosting with 99.9% uptime guarantee.', price: 'From $29/mo' }},
  {{ icon: Lock, title: 'Security Audit', desc: 'Comprehensive security assessment and hardening.', price: 'From $599' }},
  {{ icon: Headphones, title: '24/7 Support', desc: 'Round-the-clock technical support and maintenance.', price: 'From $199/mo' }},
];

export default function Services() {{
  return (
    <div className="min-h-screen">
      <nav className="{nav_style}">
        <Link to="/" className="text-lg font-bold text-cyan-400">{project_name}</Link>
        <div className="flex gap-6">
          <Link to="/" className="{link_style}">Home</Link>
          <Link to="/about" className="{link_style}">About</Link>
          <Link to="/services" className="{link_style}">Services</Link>
          <Link to="/contact" className="{link_style}">Contact</Link>
        </div>
      </nav>

      <section className="{section_style} text-center">
        <h1 className="mb-4 text-4xl font-extrabold">Our Services</h1>
        <p className="mx-auto mb-12 max-w-2xl text-slate-400">
          Professional solutions tailored to your business needs.
        </p>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {{services.map((s) => (
            <div key={{s.title}} className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 text-left hover:border-cyan-500/50 transition-colors">
              <s.icon className="mb-3 h-8 w-8 text-cyan-400" />
              <h3 className="mb-2 text-lg font-semibold">{{s.title}}</h3>
              <p className="mb-4 text-sm text-slate-400">{{s.desc}}</p>
              <span className="text-sm font-semibold text-cyan-400">{{s.price}}</span>
            </div>
          ))}}
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {{new Date().getFullYear()}} {project_name}. All rights reserved.
      </footer>
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Services.jsx"), services_page)

            # Contact page
            project_slug = re.sub(r'[^a-z0-9]', '', project_name.lower())
            contact_page = f"""import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Mail, Phone, MapPin, Send }} from 'lucide-react';

export default function Contact() {{
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {{
    e.preventDefault();
    setSubmitted(true);
  }};

  return (
    <div className="min-h-screen">
      <nav className="{nav_style}">
        <Link to="/" className="text-lg font-bold text-cyan-400">{project_name}</Link>
        <div className="flex gap-6">
          <Link to="/" className="{link_style}">Home</Link>
          <Link to="/about" className="{link_style}">About</Link>
          <Link to="/services" className="{link_style}">Services</Link>
          <Link to="/contact" className="{link_style}">Contact</Link>
        </div>
      </nav>

      <section className="{section_style}">
        <div className="mx-auto max-w-4xl">
          <h1 className="mb-4 text-center text-4xl font-extrabold">Get in Touch</h1>
          <p className="mb-12 text-center text-slate-400">
            Have a question or ready to start? We would love to hear from you.
          </p>

          <div className="grid gap-8 lg:grid-cols-2">
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-cyan-400" />
                <span className="text-slate-300">hello@{project_slug}.com</span>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-cyan-400" />
                <span className="text-slate-300">+1 (555) 123-4567</span>
              </div>
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-cyan-400" />
                <span className="text-slate-300">123 Business Ave, Suite 100</span>
              </div>
            </div>

            {{submitted ? (
              <div className="flex flex-col items-center justify-center rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-8 text-center">
                <Send className="mb-3 h-8 w-8 text-cyan-400" />
                <h3 className="text-lg font-semibold">Message Sent!</h3>
                <p className="text-sm text-slate-400">We will get back to you within 24 hours.</p>
              </div>
            ) : (
              <form onSubmit={{handleSubmit}} className="space-y-4">
                <input
                  type="text"
                  placeholder="Your Name"
                  required
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <input
                  type="email"
                  placeholder="Email Address"
                  required
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <textarea
                  placeholder="Your Message"
                  rows="4"
                  required
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                />
                <button type="submit" className="{btn_style}">
                  Send Message <Send className="h-4 w-4" />
                </button>
              </form>
            )}}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        &copy; {{new Date().getFullYear()}} {project_name}. All rights reserved.
      </footer>
    </div>
  );
}}
"""
            FileManager.write_file(str(frontend_dir / "src" / "pages" / "Contact.jsx"), contact_page)


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

        # 6. Consolidate Database Schemas into database/schema.sql
        FileManager.ensure_dir(str(database_dir))
        merged_sql = "-- Generated Database Schema\n\n"
        schemas = plan.get("database_schemas", [])

        for s in schemas:
            s_rel = s.get("file_path")
            if s_rel:
                s_src = (PROJECT_ROOT / s_rel).resolve()
                if s_src.exists():
                    merged_sql += f"-- Schema: {s.get('name')}\n"
                    merged_sql += FileManager.read_file(str(s_src)) + "\n\n"

        schema_dst = database_dir / "schema.sql"
        FileManager.write_file(str(schema_dst), merged_sql)

        # 7. Auto-Fix Missing NPM Dependencies in package.json files
        self._auto_fix_npm_dependencies(frontend_dir, is_backend=False)
        self._auto_fix_npm_dependencies(backend_dir, is_backend=True)

        # 8. Generate Root README.md & .env.example
        self._generate_project_meta(target_dir, plan)

        agent_logger.info(f"Successfully assembled project '{project_name}'!")
        return str(target_dir)

    @staticmethod
    def _safe_project_name(project_name: Any) -> str:
        """Convert user-derived names into stable, filesystem-safe project slugs."""
        value = re.sub(r"[^a-zA-Z0-9]+", "-", str(project_name or "generated-app")).strip("-").lower()
        return value[:80] or "generated-app"

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
        pname = plan.get("project_name")
        readme_content = f"""# {pname.upper()}

Built with the production pipeline — reproducible, tested, deployment-ready.

## Stack
- **Frontend**: React.js + Vite + Tailwind CSS
- **Backend**: Node.js + Express.js
- **Database**: PostgreSQL

See `INSTRUCTIONS.md` for complete installation, database migration, and deployment instructions.
"""
        FileManager.write_file(str(target_dir / "README.md"), readme_content)
        
        env_content = """# Environment Config
PORT=5000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lumicore_db
# Generate a unique secret before production deployment.
JWT_SECRET=replace_with_a_random_64_character_secret
"""
        FileManager.write_file(str(target_dir / "frontend" / ".env.example"), env_content)
        FileManager.write_file(str(target_dir / "backend" / ".env.example"), env_content)
        self._generate_instructions_guide(target_dir, plan)
        self._generate_docker_setup(target_dir, plan)
        self._generate_seo_files(target_dir, plan)
        self._generate_cicd_workflow(target_dir, plan)
        self._generate_deployment_checklist(target_dir, plan)

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
RUN npm ci --only=production=false
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
RUN npm ci --only=production
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
version: "3.9"

services:
  # ── PostgreSQL Database ─────────────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: {pname}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: {db_name}
      POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-changeme}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
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
      DATABASE_URL: postgresql://${{POSTGRES_USER:-postgres}}:${{POSTGRES_PASSWORD:-changeme}}@db:5432/{db_name}
      JWT_SECRET: ${{JWT_SECRET:-change_this_secret_in_production}}
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
      - backend
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
- [ ] Run `schema.sql` on production PostgreSQL
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
│   └── schema.sql         ← PostgreSQL schema (run this first)
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
JWT_SECRET=your_super_secret_key_here_change_this
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

### Step 5.3 — Run the schema
```bash
# Mac/Linux:
psql -U postgres -d {pname.replace("-", "_")}_db -f database/schema.sql

# Windows PowerShell:
psql -U postgres -d {pname.replace("-", "_")}_db -f database/schema.sql
```

✅ This creates all tables automatically.

### Included SQL Schemas:
{schema_list}

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

# Security — CHANGE THESE IN PRODUCTION
JWT_SECRET=change_this_to_a_random_64_char_string
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
3. Run `database/schema.sql` in the Supabase SQL Editor
4. Update `DATABASE_URL` in your backend env vars

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
- Make sure you set a proper secret in `backend/.env`
- Minimum 32 characters recommended

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

