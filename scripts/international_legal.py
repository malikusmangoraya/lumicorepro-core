"""International legal pages generator — v7.10.

Adds Privacy Policy + Terms of Service pages (professional, brand-parametrized,
international-standard compliance content) to every project and wires the
routes into App.jsx. Footer links (already live) point here.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"

sys.path.insert(0, str(ROOT / "scripts"))
from brand_map import BRANDS  # noqa: E402
from industry_content import content as industry_content  # noqa: E402

HEADER = """import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function {NAME}() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-10">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-4xl mx-auto px-6">
            <p className="section-eyebrow">{EYEBROW}</p>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-[1.05] mb-4"
              style={{ color: 'var(--t-heading)' }}>
              {TITLE}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Last updated: {DATE}. Applies to all services provided by {BRAND}.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-4xl mx-auto px-6 space-y-10">
            {BODY}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""

PRIVACY_BODY = """<div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Introduction
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {BRAND} (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;us&rdquo;) respects your privacy.
                  This policy explains what information we collect when you visit our website, create an
                  account, or use our services, how we use it, and the choices you have.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Information we collect
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li><strong>Account details</strong> — name, email address and, where provided, billing information.</li>
                  <li><strong>Usage data</strong> — pages viewed, features used and device/technical data (IP address, browser, OS).</li>
                  <li><strong>Communications</strong> — emails, support conversations and enquiry forms you send us.</li>
                  <li><strong>Cookies</strong> — small files that help the site remember your preferences and understand aggregate usage.</li>
                </ul>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  How we use information
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li>To provide and improve the products and services you request.</li>
                  <li>To send service notices, transactional updates and — only with consent — marketing.</li>
                  <li>To personalise your experience and keep the site secure.</li>
                  <li>To comply with legal obligations and enforce our Terms of Service.</li>
                </ul>
                <p className="mt-4 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We process data on the legal bases of performance of a contract, legitimate interest
                  (operation and improvement of our service), consent (where you opt in), and legal compliance.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Sharing & security
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We never sell your personal data. We share it only with service providers who help us
                  operate (hosting, payments, analytics), always under contract and only to the extent
                  needed. Your data is encrypted in transit and at rest, access-controlled and reviewed
                  regularly.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Retention & your rights
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We keep personal data only as long as needed for the purposes above or as required by law,
                  then delete or anonymise it. Depending on your jurisdiction you may have the right to
                  access, rectify, erase, restrict or port your data, and to withdraw consent at any time.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Cookies & local storage
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We use essential cookies to run the site and optional analytics cookies to understand
                  aggregate usage. You can disable non-essential cookies in your browser at any time.
                  This site works in all browsers even with cookies disabled.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Contact
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Questions about this policy or your data? Email us at{' '}
                  <a className="font-medium underline underline-offset-2" style={{ color: 'var(--t-primary)' }}
                     href="mailto:{EMAIL}@{DOMAIN}">privacy@{DOMAIN}</a>.
                </p>
              </div>"""

TERMS_BODY = """<div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Agreement to terms
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  These terms govern your use of the website and services operated by {BRAND}
                  (&ldquo;we&rdquo;, &ldquo;us&rdquo;). By accessing the site or creating an account you agree to be bound
                  by these terms. If you do not agree, please do not use the service.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Use of the service
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li>You must be at least 18 years old or have parent/guardian consent.</li>
                  <li>You are responsible for the accuracy of your account information and for keeping credentials secure.</li>
                  <li>You must not misuse the service: no unlawful activity, no spam or abuse, no interference with other users or our infrastructure.</li>
                  <li>We may suspend accounts that violate these terms, with notice where practicable.</li>
                </ul>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Intellectual property
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  All content on this site — text, design, graphics, branding and software — is owned by
                  {BRAND} or its licensors and protected by applicable law. You may not reproduce, resell
                  or redistribute our materials without written permission, except for your own lawful use
                  of the service.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Payments & cancellations
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  All charges are shown clearly before you confirm any purchase. Payments are processed by
                  our payment partners; we do not store your card details. Subscriptions renew as described
                  at checkout unless cancelled before the renewal date. Refunds are handled in line with the
                  policy on the relevant product page and applicable law.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Disclaimers & liability
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  The service is provided &ldquo;as is&rdquo; without warranties of any kind, to the fullest extent
                  permitted by law. To the extent permitted by law, {BRAND} shall not be liable for indirect,
                  incidental or consequential damages. Nothing in these terms limits liability that cannot
                  be limited by law.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Changes & governing law
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We may update these terms from time to time; material changes will be notified on this page.
                  Continued use after a change means acceptance of the updated terms. These terms are
                  governed by the laws of the jurisdiction in which {BRAND} is established.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Contact
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Questions about these terms? Email us at{' '}
                  <a className="font-medium underline underline-offset-2" style={{ color: 'var(--t-primary)' }}
                     href="mailto:legal@{DOMAIN}">legal@{DOMAIN}</a>.
                </p>
              </div>"""


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;")


def build_legal(root: str) -> bool:
    front = PROJECTS / root / "frontend"
    pages = front / "src" / "pages"
    if not pages.exists():
        return False
    b = BRANDS.get(root, BRANDS["build"])
    domain = str(b["name"]).lower().replace("&", "").replace(" ", "") + ".com"
    brand = esc(b["name"])
    ic = industry_content(b["industry"])
    email_h = ic["contact"]["email"].rstrip("@")
    date = "17 September 2026"

    def patch_comp(comp_name: str, title: str, eyebrow: str, body: str) -> None:
        comp = HEADER.replace("{NAME}", comp_name).replace("{TITLE}", title)
        comp = comp.replace("{EYEBROW}", eyebrow).replace("{DATE}", date)
        comp = comp.replace("{BRAND}", brand).replace("{DOMAIN}", domain).replace("{EMAIL}", email_h)
        comp = comp.replace("{BODY}", body)
        (pages / f"{comp_name}.jsx").write_text(comp, encoding="utf-8")

    patch_comp("Privacy", "Privacy Policy", "COMPLIANCE & TRUST", PRIVACY_BODY)
    patch_comp("Terms", "Terms of Service", "LEGAL AGREEMENT", TERMS_BODY)

    # ---- wire routes into App.jsx (idempotent) ----
    app = front / "src" / "App.jsx"
    if not app.exists():
        return True
    t = app.read_text(encoding="utf-8")
    changed = False
    if "const Privacy = lazy" not in t:
        t = t.replace(
            "const Contact = lazy(() => import('./pages/Contact'));",
            "const Contact = lazy(() => import('./pages/Contact'));\n"
            "const Privacy = lazy(() => import('./pages/Privacy'));\n"
            "const Terms = lazy(() => import('./pages/Terms'));",
        )
        t = t.replace(
            '<Route path="/register" element={<Register />} />',
            '<Route path="/register" element={<Register />} />\n'
            '            <Route path="/privacy" element={<Privacy />} />\n'
            '            <Route path="/terms" element={<Terms />} />',
        )
        app.write_text(t, encoding="utf-8")
        changed = True
    return True


def main():
    slugs = sys.argv[1:] or [
        d.name
        for d in sorted(PROJECTS.iterdir())
        if (d / "frontend" / "package.json").exists()
    ]
    ok = fail = 0
    for s in slugs:
        if build_legal(s):
            ok += 1
        else:
            fail += 1
            print(f"  WARN {s}")
    print(f"international-legal: {ok} ok, {fail} warn")


if __name__ == "__main__":
    main()