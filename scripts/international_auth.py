"""Branded, international Login / Register / Admin pages per project.

Login & Register: split hero + form layout, correct labels/autocomplete, password
visibility toggle, brand name in copy. Admin: token-based dashboard with the
brand's own stats, recent activity and quick actions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_map import BRANDS

GEN = Path(__file__).resolve().parent.parent / "generated-projects"


def js(s) -> str:
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


LOGIN = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, Eye, ShieldCheck, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Login() {
  const [show, setShow] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main className="flex-1 grid lg:grid-cols-2">
        <section
          className="relative hidden lg:flex flex-col justify-between p-12 text-white"
          style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-80">__EYEBROW__</p>
            <h2 className="mt-6 text-4xl font-black leading-tight max-w-sm">__TAGLINE__</h2>
            <p className="mt-4 max-w-sm text-white/85 leading-relaxed">__SUB__</p>
          </div>
          <ul className="space-y-3 text-sm">
            <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Secure, encrypted sign-in</li>
            <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Your data stays yours</li>
          </ul>
        </section>

        <section className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-md" data-reveal>
            <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--t-heading)' }}>
              Welcome back to __NAME__
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Sign in to continue to your account.
            </p>

            <form onSubmit={(e) => e.preventDefault()} className="mt-8 space-y-5">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Email address
                </label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="email" name="email" type="email" required autoComplete="email"
                    placeholder="you@example.com"
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                </div>
              </div>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label htmlFor="password" className="block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                    Password
                  </label>
                  <Link to="/contact" className="text-xs font-semibold text-primary">Forgot password?</Link>
                </div>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="current-password"
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? 'Hide password' : 'Show password'}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <input type="checkbox" className="rounded border-[var(--t-border)]" /> Keep me signed in
              </label>

              <button type="submit" className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                Sign in <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              New to __NAME__?{' '}
              <Link to="/register" className="font-semibold text-primary">Create an account</Link>
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""


REGISTER = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, Eye, ShieldCheck, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Register() {
  const [show, setShow] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main className="flex-1 grid lg:grid-cols-2">
        <section
          className="relative hidden lg:flex flex-col justify-between p-12 text-white"
          style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] opacity-80">JOIN __NAME__</p>
            <h2 className="mt-6 text-4xl font-black leading-tight max-w-sm">Start your __INDUSTRY__ journey today</h2>
            <ul className="mt-8 space-y-3 text-sm">
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Free to join, no card required</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Set up in under two minutes</li>
              <li className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Cancel or change any time</li>
            </ul>
          </div>
          <p className="text-white/70 text-sm">__TAGLINE__</p>
        </section>

        <section className="flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-md" data-reveal>
            <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--t-heading)' }}>
              Create your account
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Join __NAME__ in a couple of minutes.
            </p>

            <form onSubmit={(e) => e.preventDefault()} className="mt-8 space-y-5">
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Full name
                </label>
                <input
                  id="name" name="name" type="text" required autoComplete="name" placeholder="Jane Doe"
                  className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                />
              </div>
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Email address
                </label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="email" name="email" type="email" required autoComplete="email" placeholder="you@example.com"
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium" style={{ color: 'var(--t-heading)' }}>
                  Password
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    id="password" name="password" type={show ? 'text' : 'password'} required autoComplete="new-password"
                    placeholder="At least 8 characters"
                    className="w-full rounded-xl border border-[var(--t-border)] bg-surface py-3 pl-10 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShow(!show)}
                    aria-label={show ? 'Hide password' : 'Show password'}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <label className="flex items-start gap-2 text-sm text-slate-500 dark:text-slate-400">
                <input type="checkbox" required className="mt-1 rounded border-[var(--t-border)]" />
                <span>I agree to the Terms of Service and Privacy Policy.</span>
              </label>

              <button type="submit" className="btn-primary inline-flex w-full items-center justify-center gap-2 py-3 text-sm">
                Create account <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-primary">Sign in</Link>
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""


ADMIN = """import React from 'react';
import { useTranslation } from 'react-i18next';
import { BarChart3, Users, ShoppingBag, TrendingUp, Activity, Clock, ArrowRight, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const kpis = [
  { icon: BarChart3, label: '__S1L__', value: '__S1__', trend: '+12%' },
  { icon: Users, label: '__S2L__', value: '__S2__', trend: '+4%' },
  { icon: ShoppingBag, label: '__S3L__', value: '__S3__', trend: '+8%' },
  { icon: TrendingUp, label: '__S4L__', value: '__S4__', trend: '+3%' },
];

const activity = [
  { icon: Activity, text: 'New __INDUSTRY__ enquiry received', time: '2m ago' },
  { icon: ShieldCheck, text: 'Payment verified and settled', time: '18m ago' },
  { icon: Users, text: 'New team member invited', time: '1h ago' },
  { icon: Clock, text: 'Weekly performance report generated', time: '3h ago' },
];

export default function Admin() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <Navbar />
      <main className="flex-1 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap items-end justify-between gap-4 mb-10">
            <div>
              <p className="section-eyebrow">Dashboard</p>
              <h1 className="section-heading mt-1">__NAME__ control room</h1>
            </div>
            <span className="glass-md rounded-xl px-4 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400" data-reveal>
              Live · updated moments ago
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
            {kpis.map((k, i) => (
              <div key={i} className="card-panel p-6 card-lift" data-reveal>
                <div className="flex items-center justify-between mb-4">
                  <span
                    className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-white"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    <k.icon className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-bold text-primary">{k.trend}</span>
                </div>
                <p className="text-3xl font-black" style={{ color: 'var(--t-heading)' }}>{k.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{k.label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card-panel p-7" data-reveal>
              <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>Revenue overview</h2>
              <div className="flex items-end gap-3 h-48">
                {[42, 58, 49, 71, 63, 84, 76, 92, 88, 96, 90, 100].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t-lg" style={{ height: h + '%', background: 'linear-gradient(180deg, var(--t-primary), var(--t-accent))', opacity: 0.35 + (h / 150) }} />
                ))}
              </div>
              <div className="mt-3 flex justify-between text-[10px] uppercase tracking-widest text-slate-400">
                <span>Jan</span><span>Jun</span><span>Dec</span>
              </div>
            </div>

            <div className="card-panel p-7" data-reveal>
              <h2 className="font-bold text-lg mb-5" style={{ color: 'var(--t-heading)' }}>Recent activity</h2>
              <ul className="space-y-4">
                {activity.map((a, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface text-primary">
                      <a.icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>{a.text}</p>
                      <p className="text-xs text-slate-400">{a.time}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <button className="btn-outline mt-6 inline-flex w-full items-center justify-center gap-2 py-2.5 text-sm">
                View all <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
"""


def fill(tpl: str, brand: dict) -> str:
    name = brand["name"]
    return (
        tpl.replace("__NAME__", js(name))
        .replace("__EYEBROW__", js(brand["eyebrow"]))
        .replace("__TAGLINE__", js(brand["tagline"]))
        .replace("__SUB__", js(brand["sub"]))
        .replace("__INDUSTRY__", js(brand["industry"].replace("-", " ")))
        .replace("__S1__", js(brand["stat1"])).replace("__S2__", js(brand["stat2"]))
        .replace("__S3__", js(brand["stat3"])).replace("__S4__", js(brand["stat4"]))
        .replace("__S1L__", js(brand["stat1l"])).replace("__S2L__", js(brand["stat2l"]))
        .replace("__S3L__", js(brand["stat3l"])).replace("__S4L__", js(brand["stat4l"]))
    )


def main() -> int:
    wanted = set(sys.argv[1:])
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    n = 0
    for proj in projects:
        brand = BRANDS.get(proj.name, BRANDS["build"])
        pages = proj / "frontend" / "src" / "pages"
        if not pages.exists():
            continue
        for fname, tpl in (("Login.jsx", LOGIN), ("Register.jsx", REGISTER), ("Admin.jsx", ADMIN)):
            fp = pages / fname
            if fp.exists():
                fp.write_text(fill(tpl, brand), encoding="utf-8")
        n += 1
    print(f"International auth/admin pages regenerated x {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())