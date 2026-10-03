"""International Navbar generator — v7.10.

Rebuilds every project's Navbar into a proper international-standard header:
  - sticky glass header (backdrop blur, token border/bg)
  - brand lockup via the project's LumicorePro component
  - full nav: Home / About / Services / Pricing / Contact
  - secondary Login link + single primary CTA (brand cta)
  - accessible mobile menu (aria-expanded/aria-controls, Escape to close,
    closes on route change), active route state
  - no reliance on i18n hook inside the header (avoids the old runtime crash)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

# Brand map is imported by path (repo convention: scripts contain logic only).
sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402


def short_cta(text: str) -> str:
    return text if len(text) <= 24 else "Get Started"


NAVBAR_TEMPLATE = """import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import LumicorePro from './LumicorePro';

const NAV_LINKS = [
  { path: '/', label: 'Home' },
  { path: '/about', label: 'About' },
  { path: '/services', label: 'Services' },
  { path: '/pricing', label: 'Pricing' },
  { path: '/contact', label: 'Contact' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [loc.pathname]);

  return (
    <header
      className="sticky top-0 z-50 border-b border-[var(--t-border)] backdrop-blur-xl"
      style={{ backgroundColor: 'var(--t-canvas)' }}
    >
      <div className="fluid-container mx-auto flex items-center justify-between py-4">
        <LumicorePro />

        <nav
          className="hidden items-center gap-8 lg:flex"
          aria-label="Primary navigation"
        >
          {NAV_LINKS.map((l) => {
            const active = loc.pathname === l.path;
            return (
              <Link
                key={l.path}
                to={l.path}
                aria-current={active ? 'page' : undefined}
                className="text-sm font-medium transition-colors"
                style={{
                  color: active ? 'var(--t-primary)' : 'var(--t-text)',
                  fontWeight: active ? 600 : 500,
                }}
              >
                {l.label}
              </Link>
            );
          })}
          <span className="h-5 w-px" style={{ backgroundColor: 'var(--t-border)' }} />
          <Link
            to="/login"
            className="text-sm font-medium transition-colors"
            style={{ color: 'var(--t-text)' }}
          >
            Login
          </Link>
          <Link to="/contact" className="btn-primary text-sm">
            {CTA}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </nav>

        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? 'Close menu' : 'Open menu'}
          className="lg:hidden rounded-lg p-2 transition-colors"
          style={{ color: 'var(--t-text)' }}
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <nav
          id="mobile-menu"
          aria-label="Mobile navigation"
          className="lg:hidden border-t px-6 pb-6 pt-2"
          style={{ backgroundColor: 'var(--t-canvas)', borderColor: 'var(--t-border)' }}
        >
          {NAV_LINKS.map((l) => (
            <Link
              key={l.path}
              to={l.path}
              onClick={() => setOpen(false)}
              className="block py-3 text-sm font-medium"
              style={{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}
            >
              {l.label}
            </Link>
          ))}
          <div className="mt-3 flex flex-col gap-3 border-t pt-4" style={{ borderColor: 'var(--t-border)' }}>
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="btn-outline w-full text-sm text-center"
            >
              Login
            </Link>
            <Link
              to="/contact"
              onClick={() => setOpen(false)}
              className="btn-primary w-full text-sm text-center"
            >
              {CTA}
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}
"""


def build_navbar(root: str) -> bool:
    front = PROJECTS / root / "frontend"
    out = front / "src" / "components" / "Navbar.jsx"
    if not out.parent.exists():
        return False
    b = BRANDS.get(root, BRANDS["build"])
    cta = short_cta(b["cta"])
    out.write_text(NAVBAR_TEMPLATE.replace("{CTA}", cta), encoding="utf-8")
    return True


def main():
    slugs = sys.argv[1:] or [
        d.name
        for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    ok = fail = 0
    for s in slugs:
        if build_navbar(s):
            ok += 1
        else:
            fail += 1
            print(f"  WARN {s}")
    print(f"international-nav: {ok} ok, {fail} warn")


if __name__ == "__main__":
    main()