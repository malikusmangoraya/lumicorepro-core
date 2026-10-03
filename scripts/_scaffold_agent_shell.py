"""Scaffold the full provider/route/shell layer for the 10 AI-agent products.

For each agent frontend:
  1. copy ui/CurrencySelector + ui/LanguageSelector + context/CurrencyContext
     from the proven aurelia-estates reference (idempotent; skips existing),
  2. rewrite src/i18n/index.js (dep-free, AVAILABLE_LANGUAGES from locales),
  3. add `import './i18n';` to main.jsx,
  4. rewrite lib/AppProviders.jsx (QueryClient + CurrencyProvider),
  5. create Login/Register/Admin (from international_auth templates) and a
     self-contained Checkout page,
  6. rewrite App.jsx with the full 11-route lazy shell,
  7. append a `lumi-shell-agent` CSS block (brand tokens + agent-JS-compatible
     reveal + .card-lift) so var(--t-brand) and new sections render correctly.

Token colors come from the already-patched theme.js (unique agent palette).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
import international_auth as IA  # noqa: E402 (LOGIN/REGISTER/ADMIN templates)
from gen_unique_logos import theme_hexes  # noqa: E402

AGENTS = [
    "appointly-ai", "claimflow-ai", "clausecheck-ai", "insightpipe-ai",
    "leadscout-ai", "ledgerai", "onboarder-ai", "recruitiq-ai",
    "supportdesk-ai", "tablehost-ai",
]
REF = GEN / "aurelia-estates" / "frontend" / "src"

I18N_FREE = """/* LumicorePro agent i18n bootstrap - dep-free. */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export const RTL_LANGUAGES = ['ar', 'fa', 'he', 'ps', 'sd', 'ur'];
export const AVAILABLE_LANGUAGES = __LANGS__;

function detectLang(available) {
  try {
    const saved = localStorage.getItem('i18nextLng');
    if (saved && available.includes(saved)) return saved;
  } catch (e) { /* ignore */ }
  if (typeof navigator !== 'undefined') {
    const nav = (navigator.language || 'en').split('-')[0];
    if (available.includes(nav)) return nav;
  }
  return 'en';
}

function loadLocales() {
  const ctx = import.meta.glob('./locales/*.json', { eager: true });
  const resources = {};
  for (const path in ctx) {
    const lang = path.replace('./locales/', '').replace('.json', '');
    resources[lang] = { translation: ctx[path].default || ctx[path] };
  }
  return resources;
}

function applyDir(lng) {
  if (typeof document === 'undefined') return;
  const isRtl = RTL_LANGUAGES.includes(lng);
  document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lng);
}

i18n
  .use(initReactI18next)
  .init({
    resources: loadLocales(),
    fallbackLng: 'en',
    supportedLngs: AVAILABLE_LANGUAGES,
    lng: detectLang(AVAILABLE_LANGUAGES),
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    returnNull: false,
  });

i18n.on('languageChanged', applyDir);
applyDir(i18n.language || 'en');

export default i18n;
"""

APPS_PROVIDERS = """import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CurrencyProvider } from '../context/CurrencyContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, gcTime: 30 * 60 * 1000, retry: 2 },
  },
});

export default function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <CurrencyProvider>{children}</CurrencyProvider>
    </QueryClientProvider>
  );
}
"""

APP_ROUTES = """import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppProviders from './lib/AppProviders';
import MotionCanvas from './components/common/MotionCanvas';
import './lib/theme';

const Home = lazy(() => import('./pages/Home'));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Admin = lazy(() => import("./pages/Admin"));
const Checkout = lazy(() => import("./pages/Checkout"));
const About = lazy(() => import('./pages/About'));
const Services = lazy(() => import('./pages/Services'));
const Pricing = lazy(() => import('./pages/Pricing'));
const Contact = lazy(() => import('./pages/Contact'));
const Privacy = lazy(() => import('./pages/Privacy'));
const Terms = lazy(() => import('./pages/Terms'));

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="skeleton-shimmer h-8 w-8 rounded-full" />
    </div>
  );
}

const basename =
  typeof window !== 'undefined' && window.location.pathname.split('/')[1]
    ? '/' + window.location.pathname.split('/')[1]
    : '/';

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter basename={basename}>
        <MotionCanvas className="fixed inset-0 -z-10" />
        <div className="cls-reserve">
          <Suspense fallback={<Loader />}>
            <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/services" element={<Services />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="*" element={<Home />} />
          </Routes>
          </Suspense>
        </div>
      </BrowserRouter>
    </AppProviders>
  );
}
"""

CHECKOUT = """import React, { useState } from 'react';
import { CreditCard, Lock, ShieldCheck, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const plan = {
  name: '__NAME__ Pro',
  price: '__PRICE__',
  per: '__PER__',
  features: ['Everything in Starter', 'Unlimited usage', 'Priority support'],
};

export default function Checkout() {
  const [done, setDone] = useState(false);
  const [form, setForm] = useState({ email: '', card: '', exp: '', cvc: '' });
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  if (done) {
    return (
      <div className="min-h-screen flex flex-col bg-canvas">
        <Navbar />
        <main className="flex-1 flex items-center justify-center px-6 py-24" data-reveal>
          <div className="w-full max-w-md text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full"
              style={{ background: 'var(--t-primary)' }}>
              <Check className="h-8 w-8 text-white" />
            </div>
            <h1 className="mt-6 text-2xl font-extrabold" style={{ color: 'var(--t-heading)' }}>
              Payment confirmed
            </h1>
            <p className="mt-2 text-sm text-slate-400">Your {plan.name} subscription is active. A receipt is on its way to {form.email || 'your inbox'}.</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main className="flex-1 grid lg:grid-cols-2 gap-10 px-6 py-16 max-w-5xl mx-auto w-full" data-reveal>
        <section>
          <p className="section-eyebrow">Secure checkout</p>
          <h1 className="section-heading">Almost there</h1>
          <p className="mt-2 text-sm text-slate-400">Locked-in pricing, no surprises, cancel anytime.</p>
          <form className="mt-8 space-y-4" onSubmit={(e) => { e.preventDefault(); setDone(true); }}>
            <label className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
              Email
              <input type="email" required value={form.email} onChange={set('email')}
                className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-white/30"
                placeholder="you@company.com" autoComplete="email" aria-label="Email address" />
            </label>
            <label className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
              Card number
              <div className="relative mt-1">
                <CreditCard className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input type="text" required inputMode="numeric" value={form.card} onChange={set('card')}
                  className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-3 text-sm text-slate-200 outline-none focus:border-white/30"
                  placeholder="1234 5678 9012 3456" aria-label="Card number" />
              </div>
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                Expiry
                <input type="text" required value={form.exp} onChange={set('exp')}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-white/30"
                  placeholder="MM/YY" aria-label="Expiry date" />
              </label>
              <label className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                CVC
                <input type="text" required inputMode="numeric" value={form.cvc} onChange={set('cvc')}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-white/30"
                  placeholder="123" aria-label="CVC" />
              </label>
            </div>
            <button className="btn-primary w-full py-3 text-sm font-semibold" type="submit">
              Pay {plan.price}{plan.per} &middot; {plan.name}
            </button>
            <p className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
              <Lock className="h-3.5 w-3.5" /> Encrypted &middot; <ShieldCheck className="h-3.5 w-3.5" /> PCI-aligned
            </p>
          </form>
        </section>
        <aside className="card-panel p-6 h-fit lg:sticky lg:top-24">
          <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--t-heading)' }}>Order summary</h2>
          <div className="mt-5 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-300">{plan.name}</span>
              <span className="font-semibold" style={{ color: 'var(--t-heading)' }}>{plan.price}{plan.per}</span>
            </div>
            <div className="flex items-center justify-between border-t border-white/10 pt-3">
              <span className="text-slate-300">Due today</span>
              <span className="font-bold" style={{ color: 'var(--t-primary)' }}>{plan.price}{plan.per}</span>
            </div>
          </div>
          <ul className="mt-6 space-y-2" aria-label="Plan features">
            {plan.features.map((f) => (
              <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                <Check className="mt-0.5 h-4 w-4 shrink-0" style={{ color: 'var(--t-primary)' }} /> {f}
              </li>
            ))}
          </ul>
        </aside>
      </main>
      <Footer />
    </div>
  );
}
"""

SHELL_CSS_TPL = """
/* ===== lumi-shell-agent (7.13) ===== */
:root {
  --t-brand: __BRAND__;
  --t-brand-soft: __BRAND_SOFT__;
  --t-accent-gold: __ACCENT__;
  --t-accent-cyan: __ACCENT_ALT__;
}
[data-reveal].lumi-reveal {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
[data-reveal].lumi-in { opacity: 1; transform: none; }
.card-lift {
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.card-lift:hover {
  transform: translateY(-6px);
  box-shadow: var(--t-shadow-lift, 0 12px 32px rgba(0, 0, 0, 0.18));
}
"""


def locale_list(fe_src) -> list:
    ld = fe_src / "i18n" / "locales"
    langs = ["ar", "de", "en", "es", "fr", "hi", "id", "ja", "ko", "pt", "ru",
             "tr", "ur", "zh"]
    if ld.exists():
        have = {p.stem for p in ld.glob("*.json")}
        return [l for l in langs if l in have]
    return langs[:12]


def copy_if_missing(fe_src: Path, rel: str) -> bool:
    dst = fe_src / rel
    src = REF / rel
    if not dst.exists() and src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return True
    return False


def patch_main(fe_src: Path) -> bool:
    fp = fe_src / "main.jsx"
    t = fp.read_text(encoding="utf-8")
    if "import './i18n'" in t:
        return False
    t = t.replace("import './index.css';", "import './i18n';\nimport './index.css';", 1)
    fp.write_text(t, encoding="utf-8")
    return True


def theme_palette(fe: Path) -> dict:
    th = theme_hexes(fe)
    brand = th.get("brand", "#e0a33a")
    accent = th.get("accent", "#e8842c")
    return {
        "__BRAND__": brand,
        "__BRAND_SOFT__": brand,
        "__ACCENT__": accent,
        "__ACCENT_ALT__": accent,
    }


def main() -> int:
    for slug in AGENTS:
        fe = GEN / slug / "frontend"
        fe_src = fe / "src"
        if not fe.exists():
            print("SKIP", slug, "(no frontend)"); continue
        # 1) selectors + currency context
        c1 = copy_if_missing(fe_src, "components/ui/CurrencySelector.jsx")
        c2 = copy_if_missing(fe_src, "components/ui/LanguageSelector.jsx")
        c3 = copy_if_missing(fe_src, "context/CurrencyContext.jsx")
        # 2) dep-free i18n
        langs = locale_list(fe_src)
        (fe_src / "i18n" / "index.js").write_text(
            I18N_FREE.replace("__LANGS__", repr(langs)), encoding="utf-8")
        # 3) main.jsx
        patch_main(fe_src)
        # 4) AppProviders
        (fe_src / "lib" / "AppProviders.jsx").write_text(APPS_PROVIDERS, encoding="utf-8")
        # 5) pages
        from brand_map import BRANDS
        brand = BRANDS.get(slug, BRANDS["build"])
        pages = fe_src / "pages"
        pages.mkdir(parents=True, exist_ok=True)
        for fname, tpl in (("Login.jsx", IA.LOGIN), ("Register.jsx", IA.REGISTER),
                           ("Admin.jsx", IA.ADMIN)):
            fp = pages / fname
            if not fp.exists():
                fp.write_text(IA.fill(tpl, brand), encoding="utf-8")
        if not (pages / "Checkout.jsx").exists():
            price = brand.get("stat1", "49")
            per = "/mo"
            (pages / "Checkout.jsx").write_text(
                CHECKOUT.replace("__NAME__", brand["name"])
                         .replace("__PRICE__", str(price).replace("<", "").replace(">", ""))
                         .replace("__PER__", per),
                encoding="utf-8")
        # 6) App.jsx full shell
        (fe_src / "App.jsx").write_text(APP_ROUTES, encoding="utf-8")
        # 7) shell CSS (tokens + reveal + card-lift, agent-JS compatible)
        css = fe_src / "index.css"
        css_t = css.read_text(encoding="utf-8")
        if "lumi-shell-agent" not in css_t:
            pal = theme_palette(fe)
            block = SHELL_CSS_TPL
            for k, v in pal.items():
                block = block.replace(k, v)
            css.write_text(css_t.rstrip() + "\n" + block, encoding="utf-8")
        print("%-18s ui=%d,%d,%d i18n=1 main=1 appprov=1 pages=1 app=1 css=1"
              % (slug, c1, c2, c3))
    print("scaffold done:", len(AGENTS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())