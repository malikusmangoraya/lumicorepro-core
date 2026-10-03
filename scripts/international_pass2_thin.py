"""Pass 2 — bring the 26 thin projects up to the same international bar.

Adds to any project missing them:
  * src/context/CurrencyContext.jsx
  * src/components/ui/CurrencySelector.jsx + LanguageSelector.jsx
  * src/pages/Privacy.jsx + Terms.jsx   (real compliance copy, brand-aware)
  * /privacy + /terms routes in App.jsx
  * CurrencyProvider wrap inside AppProviders (or App) so useCurrency works

Idempotent: only writes what is missing.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"
sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402

CURRENCY_CONTEXT = '''import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export const CURRENCIES = ['USD', 'EUR', 'GBP', 'PKR', 'INR', 'AED', 'SAR'];

const CurrencyContext = createContext(null);

export function CurrencyProvider({ children }) {
  const [currency, setCurrency] = useState(() => {
    try {
      return localStorage.getItem('lumi-currency') || 'USD';
    } catch (e) {
      return 'USD';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('lumi-currency', currency);
    } catch (e) { /* storage unavailable */ }
  }, [currency]);

  const formatPrice = (amount) => {
    const n = Number(amount || 0);
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(n);
    } catch (e) {
      return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${currency}`;
    }
  };

  const value = useMemo(
    () => ({ currency, setCurrency, formatPrice, CURRENCIES }),
    [currency]
  );

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
}

export function useCurrency() {
  return useContext(CurrencyContext);
}
'''

CURRENCY_SELECTOR = '''import React from 'react';
import { useCurrency, CURRENCIES } from '../../context/CurrencyContext';

export default function CurrencySelector({ className = '' }) {
  const { currency, setCurrency } = useCurrency();
  return (
    <select
      value={currency}
      onChange={(e) => setCurrency(e.target.value)}
      aria-label="Select currency"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs transition-colors focus:outline-none ' + className}
    >
      {CURRENCIES.map((c) => (
        <option key={c} value={c}>{c}</option>
      ))}
    </select>
  );
}
'''

LANG_SELECTOR = '''import React from 'react';
import { useTranslation } from 'react-i18next';
import { AVAILABLE_LANGUAGES } from '../../i18n';

export default function LanguageSelector({ className = '' }) {
  const { i18n } = useTranslation();
  return (
    <select
      value={i18n.resolvedLanguage || i18n.language || 'en'}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
      aria-label="Select language"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs transition-colors focus:outline-none ' + className}
    >
      {AVAILABLE_LANGUAGES.map((l) => (
        <option key={l} value={l}>{l.toUpperCase()}</option>
      ))}
    </select>
  );
}
'''


def privacy_page(brand: str) -> str:
    return f'''import React from 'react';
import {{ useTranslation }} from 'react-i18next';
import LanguageSelector from '../components/ui/LanguageSelector';
import CurrencySelector from '../components/ui/CurrencySelector';

export default function Privacy() {{
  const {{ t }} = useTranslation();
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-20">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold tracking-tight">
          {{t('legal.privacy.title', 'Privacy Policy')}}
        </h1>
        <div className="flex items-center gap-2">
          <LanguageSelector />
          <CurrencySelector />
        </div>
      </div>

      <p className="mb-8 text-sm opacity-80">
        {{t('legal.privacy.updated', 'Last updated: 1 January 2026')}}
      </p>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.privacy.controller', 'Who we are')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.privacy.controllerBody',
            '{brand} ("we", "us") operates this website. We are the data controller for the personal information you provide through this site.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.privacy.data', 'What we collect')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.privacy.dataBody',
            'We collect only what you choose to give us: contact details you submit in a form, account details if you register, and anonymous usage statistics. We do not sell personal data.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.privacy.cookies', 'Cookies')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.privacy.cookiesBody',
            'We use essential cookies to remember your language and currency preference, and optional analytics cookies only with your consent. You can withdraw consent at any time.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.privacy.rights', 'Your rights')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.privacy.rightsBody',
            'Under the GDPR you may request access to, correction of, or deletion of your personal data, and you may object to processing. Contact us and we will respond within 30 days.'
          )}}
        </p>
      </section>

      <section>
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.privacy.contact', 'Contact')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t('legal.privacy.contactBody', 'Write to us from the contact page and we will action your request.')}}
        </p>
      </section>
    </main>
  );
}}
'''


def terms_page(brand: str) -> str:
    return f'''import React from 'react';
import {{ useTranslation }} from 'react-i18next';
import LanguageSelector from '../components/ui/LanguageSelector';
import CurrencySelector from '../components/ui/CurrencySelector';

export default function Terms() {{
  const {{ t }} = useTranslation();
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-20">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-3">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight">
          {{t('legal.terms.title', 'Terms of Service')}}
        </h1>
        <div className="flex items-center gap-2">
          <LanguageSelector />
          <CurrencySelector />
        </div>
      </div>

      <p className="mb-8 text-sm opacity-80">
        {{t('legal.terms.updated', 'Last updated: 1 January 2026')}}
      </p>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.terms.acceptance', 'Acceptance of terms')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.terms.acceptanceBody',
            'By accessing {brand} you agree to these terms. If you do not agree, please stop using the site.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.terms.use', 'Permitted use')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.terms.useBody',
            'You may browse and use this site for lawful purposes. You may not scrape, overload, reverse engineer, or attempt to gain unauthorised access to any part of it.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.terms.availability', 'Availability')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.terms.availabilityBody',
            'We aim for continuous availability but do not guarantee uninterrupted access. Maintenance and third-party dependencies may cause downtime.'
          )}}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.terms.liability', 'Limitation of liability')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.terms.liabilityBody',
            'To the maximum extent permitted by law, {brand} is not liable for indirect or consequential loss arising from use of this site.'
          )}}
        </p>
      </section>

      <section>
        <h2 className="mb-2 text-xl font-semibold">
          {{t('legal.terms.governing', 'Governing law')}}
        </h2>
        <p className="leading-relaxed opacity-90">
          {{t(
            'legal.terms.governingBody',
            'These terms are governed by the laws applicable in our place of establishment, without regard to conflict-of-law rules.'
          )}}
        </p>
      </section>
    </main>
  );
}}
'''


def brand_of(slug: str) -> str:
    b = BRANDS.get(slug)
    return b["name"] if b else slug.replace("-", " ").title()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def write(p: Path, t: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding="utf-8")


def _wrap_return_paren(t: str, wrap_tag: str) -> str | None:
    """Find the outermost `return (` ... matching `)` and wrap its contents.

    Re-indents the inner block by 2 spaces so the new wrapper stays readable.
    Handles both the single-line AppProviders form and the multi-line App form.
    """
    m = re.search(r"return\s*\(", t)
    if not m:
        return None
    open_paren = t.index("(", m.start())
    # match the closing paren for this return
    depth = 0
    close = -1
    for i in range(open_paren, len(t)):
        if t[i] == "(":
            depth += 1
        elif t[i] == ")":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close == -1:
        return None
    inner = t[open_paren + 1:close]  # may be "" for `return ()`
    # strip a leading newline and common indentation, remember the base indent
    stripped = inner.lstrip("\n")
    base_indent = ""
    m_ind = re.match(r"[ \t]*", stripped)
    base_indent = m_ind.group(0)
    body = stripped.rstrip()
    # re-indent every non-empty line by 2 spaces
    lines = body.split("\n")
    reindented = "\n".join(
        ("  " + ln) if ln.strip() else ln for ln in lines
    )
    new = (
        "return (\n"
        f"{base_indent}  <{wrap_tag}>\n"
        f"{reindented}\n"
        f"{base_indent}  </{wrap_tag}>"
        f"\n{base_indent[:-2] if len(base_indent) >= 2 else ''})"
    )
    return t[:m.start()] + new + t[close + 1:]


def _wrap_return_jsx(t: str, wrap_tag: str) -> str | None:
    """Handle `return <Tag ...>...</Tag>;` (single-line JSX, no parens)."""
    m = re.search(r"return\s+(<)", t)
    if not m:
        return None
    start = t.index("<", m.start())
    # find matching '>' of the opening tag, then its closing tag before ';'
    semi = t.rfind(";")
    if semi == -1 or semi < start:
        return None
    inner = t[start:semi]
    new = f"return (\n    <{wrap_tag}>\n      {inner}\n    </{wrap_tag}>\n  )"
    return t[:m.start()] + new + t[semi + 1:]


def ensure_provider(src: Path, rel: str) -> bool:
    """Wrap the root render tree in <CurrencyProvider> if not already wrapped."""
    if not src.exists():
        return False
    t = read(src)
    if "CurrencyProvider" in t:
        return False
    imp = "import { CurrencyProvider } from './context/CurrencyContext';"
    if imp not in t:
        if rel.startswith("lib/"):
            imp = "import { CurrencyProvider } from '../context/CurrencyContext';"
        m = re.search(r"^import .*?;$", t, re.M)
        if not m:
            return False
        t = t[:m.end()] + "\n" + imp + t[m.end():]
    new_t = _wrap_return_paren(t, "CurrencyProvider")
    if new_t is None:
        new_t = _wrap_return_jsx(t, "CurrencyProvider")
    if new_t is None:
        return False
    write(src, new_t)
    return True


def ensure_routes(app: Path) -> bool:
    if not app.exists():
        return False
    t = read(app)
    changed = False
    if "./pages/Privacy" not in t:
        if "const Contact = lazy" in t:
            t = t.replace(
                "const Contact = lazy",
                "const Privacy = lazy(() => import('./pages/Privacy'));\nconst Terms = lazy(() => import('./pages/Terms'));\nconst Contact = lazy",
                1)
        changed = True
    if 'path="/privacy"' not in t:
        anchor = '              <Route path="/" element={<Home />} />'
        add = ('              <Route path="/privacy" element={<Privacy />} />\n'
               '              <Route path="/terms" element={<Terms />} />\n')
        if anchor in t:
            t = t.replace(anchor, add + anchor, 1)
        else:
            m = re.search(r"^(\s*)<Route path=\"/\"\s+element=\{<Home\s*/>\}\s*/>$", t, re.M)
            if m:
                ind = m.group(1)
                t = t[:m.start()] + (f'{ind}<Route path="/privacy" element={{<Privacy />}} />\n'
                                     f'{ind}<Route path="/terms" element={{<Terms />}} />\n') + t[m.start():]
        changed = True
    if changed:
        write(app, t)
    return changed


def main():
    targets = sys.argv[1:] or [
        d.name for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    added = {"context": 0, "selectors": 0, "legal": 0, "routes": 0, "provider": 0}
    for slug in targets:
        fe = PROJECTS / slug / "frontend"
        src = fe / "src"
        brand = brand_of(slug)

        cc = src / "context" / "CurrencyContext.jsx"
        if not cc.exists():
            write(cc, CURRENCY_CONTEXT)
            added["context"] += 1

        ui = src / "components" / "ui"
        need = 0
        if not (ui / "CurrencySelector.jsx").exists():
            write(ui / "CurrencySelector.jsx", CURRENCY_SELECTOR)
            need += 1
        if not (ui / "LanguageSelector.jsx").exists():
            write(ui / "LanguageSelector.jsx", LANG_SELECTOR)
            need += 1
        added["selectors"] += 1 if need else 0

        leg = 0
        if not (src / "pages" / "Privacy.jsx").exists():
            write(src / "pages" / "Privacy.jsx", privacy_page(brand))
            leg += 1
        if not (src / "pages" / "Terms.jsx").exists():
            write(src / "pages" / "Terms.jsx", terms_page(brand))
            leg += 1
        added["legal"] += 1 if leg else 0

        if ensure_routes(src / "App.jsx"):
            added["routes"] += 1

        # provider wrap
        app = src / "App.jsx"
        prov = src / "lib" / "AppProviders.jsx"
        target = prov if prov.exists() else app
        if target.exists() and "CurrencyProvider" not in read(target):
            if ensure_provider(target, "App.jsx" if target == app else "lib/AppProviders.jsx"):
                added["provider"] += 1

    print("PASS 2 — thin-project international completion")
    for k, v in added.items():
        print(f"  {k:<12}: {v}")


if __name__ == "__main__":
    main()