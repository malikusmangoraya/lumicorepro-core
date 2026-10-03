"""Pass 3 — wire t() into shared components and top-level pages

Converts static strings in Navbar, Footer, Home, About, Services, Pricing,
Contact to translation calls. Idempotent: skips files already using t().

Map strategy:
  Navbar links -> navigation/main/common: Home/About/Services/Contact via
  t('navigation.home', 'Home') or t('common.home')
  CTAs -> common.get_started, read_more etc
  Footer -> footer.*
  Legal -> common.privacy_policy, terms
  Hero -> page namespace or common keys as fallback
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"


def slugs():
    return [d.name for d in sorted(PROJECTS.iterdir()) if (d / "frontend" / "package.json").exists()]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def write(p: Path, t: str):
    p.write_text(t, encoding="utf-8")


def add_use_translation(t: str) -> str:
    if "useTranslation" in t:
        return t
    # insert after first React import
    m = re.search(r"^import React.*?$", t, re.M)
    if m:
        t = t[:m.end()] + "\nimport { useTranslation } from 'react-i18next';" + t[m.end():]
        return t
    t = "import { useTranslation } from 'react-i18next';\n" + t
    return t


def init_hook(t: str) -> str:
    if "const { t }" in t or "const t =" in t:
        return t
    # find function component start
    m = re.search(r"export default function (\w+)\(\)\s*\{", t)
    if m:
        t = t[:m.end()] + "\n  const { t } = useTranslation();" + t[m.end():]
        return t
    m = re.search(r"function (\w+)\(\)\s*\{", t)
    if m:
        t = t[:m.end()] + "\n  const { t } = useTranslation();" + t[m.end():]
        # ensure export default exists
        return t
    return t


def patch_navbar(t: str) -> str:
    # links
    t = t.replace('label: \'Home\'', 'label: t(\'common.home\', \'Home\')')
    t = t.replace('label: "Home"', 'label: t("common.home", "Home")')
    t = t.replace('label: \'About\'', 'label: t(\'common.about\', \'About\')')
    t = t.replace('label: "About"', 'label: t("common.about", "About")')
    t = t.replace('label: \'Services\'', 'label: t(\'common.services\', \'Services\')')
    t = t.replace('label: "Services"', 'label: t("common.services", "Services")')
    t = t.replace('label: \'Contact\'', 'label: t(\'common.contact\', \'Contact\')')
    t = t.replace('label: "Contact"', 'label: t("common.contact", "Contact")')
    t = t.replace('aria-label="Menu"', 'aria-label={t("accessibility.open_menu", "Menu")}')
    t = t.replace('aria-label="Close"', 'aria-label={t("accessibility.close_menu", "Close")}')
    # CTA generic -> get_started
    t = re.sub(r'Apex Digital Free Demo|Get Started', lambda m: '{t("common.get_started", "Get Started")}', t)
    return t


def patch_footer(t: str) -> str:
    # all-rights-reserved: match inside a <p>...</p> text node but keep the
    # closing tag. Use a callback that preserves everything after the sentence.
    def all_rights(m):
        return m.group(0).replace(
            re.escape(m.group(1)) if m.group(1) else m.group(0), "")  # noop guard
    # Safer: line-based replacement for the copyright paragraph.
    def fix_copy(m):
        seg = m.group(0)
        seg = re.sub(r"All rights reserved\.", "{t('footer.all_rights', 'All rights reserved.')}", seg, flags=re.I)
        # ensure the paragraph is closed if we are the last line in it
        return seg
    t = re.sub(r"&copy;[^<]*", fix_copy, t)
    t = re.sub(r">All rights reserved\.(?!\s*<)", "> {t('footer.all_rights', 'All rights reserved.')}", t)
    t = re.sub(r"Privacy\s+Policy", "{t('common.privacy_policy', 'Privacy Policy')}", t)
    t = re.sub(r"Terms(?: of Service)?", "{t('common.terms', 'Terms of Service')}", t)
    # only replace a standalone 'Subscribe' label (button text / heading), not 'Subscribed'
    t = re.sub(r">Subscribe<", ">{t('footer.subscribe', 'Subscribe')}<", t)
    t = t.replace('placeholder="Your email"', 'placeholder={t("footer.your_email", "Your email")}')
    t = t.replace('placeholder="Email address"', 'placeholder={t("footer.your_email", "Email address")}')
    return t


def main():
    targets = sys.argv[1:] or slugs()
    for slug in targets:
        fe = PROJECTS / slug / "frontend" / "src"
        for name in ("components/Navbar.jsx", "components/Footer.jsx",
                     "pages/Home.jsx", "pages/About.jsx", "pages/Services.jsx",
                     "pages/Pricing.jsx", "pages/Contact.jsx"):
            p = fe / name
            if not p.exists():
                continue
            t = read(p)
            if t == "" or "useTranslation" in t:
                pass
            t = add_use_translation(t)
            t = init_hook(t)
            if name.endswith("Navbar.jsx"):
                t = patch_navbar(t)
            if name.endswith("Footer.jsx"):
                t = patch_footer(t)
            write(p, t)
    print("Pass 3 complete")


if __name__ == "__main__":
    main()