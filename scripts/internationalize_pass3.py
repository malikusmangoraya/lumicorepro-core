"""Pass-3: make the international layer genuinely LIVE in every generated project.

Targets the real, audit-confirmed gaps (no_rtl, no_currency, i18n never imported,
footer selector presence) WITHOUT breaking any build:

  A. Rewrite src/i18n/index.js as a DEP-FREE bootstrap:
       - language detection via localStorage/navigator (no languagedetector pkg)
       - RTL list, dir/lang switching on <html> at init + languageChanged
       - eager locale glob, Intl-aware currency formatting
     Only written when the file currently references the missing
     'i18next-browser-languagedetector' package (the thing that made it dead),
     or doesn't contain our marker. Idempotent.
  B. Ensure src/i18n/locales/{en,ar}.json exist (scaffold when the dir is missing,
     keep existing richer files untouched).
  C. Wire `import './i18n';` into src/main.jsx (idempotent).
  D. Scaffold src/context/CurrencyContext.jsx, src/components/ui/CurrencySelector.jsx,
     src/components/ui/LanguageSelector.jsx (dep-free, self-contained).
  E. Patch src/lib/AppProviders.jsx to wrap children in <CurrencyProvider> (guarded).
  F. Patch src/components/Footer.jsx: insert an i18n selector strip (language +
     currency selectors with t() labels) right before </footer>, add the imports.
  G. Rebuild ONLY projects whose sources this pass modified (npm.cmd on Windows).

Skips projects without src/main.jsx. Every change is guarded by existing-anchor
checks; never invents routes/pages.
"""
import json
import os
import re
import subprocess
from pathlib import Path

try:
    from scripts.intl_templates import (
        I18N_INDEX, CURRENCY_CONTEXT, CURRENCY_SELECTOR, LANGUAGE_SELECTOR,
        FOOTER_STRIP,
    )
except ImportError:
    from intl_templates import (
        I18N_INDEX, CURRENCY_CONTEXT, CURRENCY_SELECTOR, LANGUAGE_SELECTOR,
        FOOTER_STRIP,
    )

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"
MARKER = "/* lumicorepro-intl-js-live */"

RTL = ["ar", "he", "fa", "ur", "ps", "sd"]
LANG_BY_DIR = {
    "ar": "Arabic",
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "hi": "हिन्दी",
    "id": "Bahasa Indonesia",
    "ja": "日本語",
    "ko": "한국어",
    "pt": "Português",
    "ru": "Русский",
    "tr": "Türkçe",
    "zh": "中文",
}


def _write(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _ready_index(i18n_dir: Path, extras: dict) -> str:
    i18n_dir.mkdir(parents=True, exist_ok=True)
    cur = i18n_dir / "CurrencyContext.jsx"
    txt = I18N_INDEX.replace(
        "/*__AVAL__*/", "', '".join(sorted(extras.keys()))
    ).replace("/*__RTL__*/", "', '".join(RTL))
    resources = {}
    src_en = extras.get("en")
    if src_en:
        resources["en"] = src_en
    src_ar = extras.get("ar")
    if src_ar:
        resources["ar"] = src_ar
    locales_dir = i18n_dir / "locales"
    if not locales_dir.exists():
        locales_dir.mkdir(parents=True, exist_ok=True)
        for lang, content in (("en", src_en), ("ar", src_ar)):
            if content:
                (locales_dir / f"{lang}.json").write_text(
                    json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
                )
    return txt


def apply(fe: Path, slug: str) -> list[str]:
    msgs = []
    src = fe / "src"
    if not (src / "main.jsx").exists():
        return [f"{slug}: skipped (no main.jsx)"]

    # ---------- A: i18n index (dep-free) ----------
    i18n_dir = src / "i18n"
    extras = {}
    if i18n_dir.exists():
        lc = i18n_dir / "locales"
        if lc.exists():
            for lf in ("en", "ar"):
                p = lc / f"{lf}.json"
                if p.exists():
                    try:
                        extras[lf] = json.loads(p.read_text(encoding="utf-8"))
                    except Exception:
                        pass
    has_bootstrap = False
    idx = i18n_dir / "index.js"
    if idx.exists():
        itxt = idx.read_text(encoding="utf-8", errors="ignore")
        has_bootstrap = MARKER in itxt
        if "i18next-browser-languagedetector" in itxt and not has_bootstrap:
            msgs.append(f"{slug}: rewriting i18n bootstrap (removed missing-dep detector)")
        elif not has_bootstrap:
            msgs.append(f"{slug}: rewriting i18n bootstrap (no live marker)")

    if not has_bootstrap:
        if not extras:
            extras = {
                "en": {"common": {"language": "Language", "currency": "Currency"}},
                "ar": {"common": {"language": "اللغة", "currency": "العملة"}},
            }
        if _write(idx, _ready_index(i18n_dir, extras)):
            msgs.append(f"{slug}: i18n bootstrap written (dep-free)")

    # ---------- B: locales scaffold (only when missing) ----------
    locales_dir = i18n_dir / "locales"
    if locales_dir.exists():
        for lang, label in (("en", "en"), ("ar", "ar")):
            p = locales_dir / f"{lang}.json"
            if not p.exists():
                fallback = {"common": {"language": label, "currency": "Currency"}}
                _write(p, json.dumps(fallback, ensure_ascii=False, indent=2))
                msgs.append(f"{slug}: scaffolded locales/{lang}.json")

    # ---------- C: main.jsx import ----------
    main_path = src / "main.jsx"
    mtxt = main_path.read_text(encoding="utf-8", errors="ignore")
    if "i18n" not in mtxt or ("import './i18n'" not in mtxt and "import \"./i18n\"" not in mtxt):
        anchor = mtxt.rfind("import '")
        if anchor == -1:
            anchor = mtxt.rfind("import \"")
        if anchor == -1:
            return msgs + [f"{slug}: no import anchor in main.jsx"]
        nl = mtxt.find("\n", anchor)
        if nl == -1:
            nl = len(mtxt)
        mtxt = mtxt[:nl] + "\nimport './i18n';" + mtxt[nl:]
        main_path.write_text(mtxt, encoding="utf-8")
        msgs.append(f"{slug}: wired i18n import in main.jsx")

    # ---------- D: scaffold CurrencyContext + selectors ----------
    ctx_path = src / "context" / "CurrencyContext.jsx"
    _write(ctx_path, CURRENCY_CONTEXT.replace("'app-token'", "'" + slug + "-token'"))
    for rel, content in (
        ("src/components/ui/CurrencySelector.jsx", CURRENCY_SELECTOR),
        ("src/components/ui/LanguageSelector.jsx", LANGUAGE_SELECTOR),
    ):
        _write(fe / rel, content)

    # ---------- E: CurrencyProvider wrap in AppProviders ----------
    appprov = src / "lib" / "AppProviders.jsx"
    if appprov.exists():
        atxt = appprov.read_text(encoding="utf-8", errors="ignore")
        if "CurrencyProvider" not in atxt and "QueryClientProvider" in atxt:
            # wrap {children} inside QueryClientProvider return
            m = re.search(r"return\s*(<QueryClientProvider[^>]*>)(.*?)(</QueryClientProvider\s*>;)", atxt, re.DOTALL)
            if m:
                inner = m.group(2)
                if "{children}" in inner:
                    new_atxt = atxt[: m.start()] + m.group(1) + inner.replace("{children}", "<CurrencyProvider>{children}</CurrencyProvider>", 1) + m.group(3) + atxt[m.end():]
                    new_atxt = new_atxt.replace(
                        "import { queryClient } from './queryClient';",
                        "import { queryClient } from './queryClient';\nimport { CurrencyProvider } from '../context/CurrencyContext';",
                        1,
                    )
                    appprov.write_text(new_atxt, encoding="utf-8")
                    msgs.append(f"{slug}: wrapped AppProviders with CurrencyProvider")
            else:
                msgs.append(f"{slug}: AppProviders shape not matched (skipping wrap)")

    # ---------- F: Footer i18n strip ----------
    footer = src / "components" / "Footer.jsx"
    if footer.exists():
        ftxt = footer.read_text(encoding="utf-8", errors="ignore")
        if "LanguageSelector" not in ftxt:
            strip = FOOTER_STRIP
            if "useTranslation" not in ftxt:
                ftxt = ftxt.replace(
                    "import React from 'react';",
                    "import React from 'react';\nimport { useTranslation } from 'react-i18next';",
                    1,
                )
            if "CurrencySelector" not in ftxt:
                anchor = ftxt.find("export default function Footer")
                if anchor != -1:
                    insert_point = ftxt.rfind("\n", 0, anchor)
                    if insert_point == -1:
                        insert_point = 0
                    ftxt = (
                        ftxt[:insert_point]
                        + "\nimport CurrencySelector from './ui/CurrencySelector';\nimport LanguageSelector from './ui/LanguageSelector';"
                        + ftxt[insert_point:]
                    )
            # function body: add t() hook
            if "const { t } = useTranslation();" not in ftxt:
                fn = re.search(r"export default function Footer\w*\s*\([^)]*\)\s*\{", ftxt)
                if fn:
                    end = ftxt.find("{", fn.start())
                    if end != -1:
                        bt = ftxt.find("{", end + 1) if False else end
                        ftxt = ftxt[:end + 1] + "\n  const { t } = useTranslation();" + ftxt[end + 1:]
            # insert strip before </footer>
            if "</footer>" in ftxt:
                ftxt = ftxt.replace("</footer>", strip + "</footer>", 1)
                footer.write_text(ftxt, encoding="utf-8")
                msgs.append(f"{slug}: footer i18n strip installed")
    return msgs


def build_changed(changed: list[str]) -> None:
    print(f"\ntouched {len(changed)} projects; rebuilding…")
    for slug in sorted(changed):
        fe = GEN / slug / "frontend"
        if not (fe / "package.json").exists():
            continue
        r = subprocess.run(
            "npm.cmd run build" if os.name == "nt" else "npm run build",
            cwd=str(fe),
            shell=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
        print(f"  {slug}: {'OK' if r.returncode == 0 else 'FAILED'}")
        if r.returncode != 0:
            print("    " + r.stderr[-1400:].replace("\n", "\n    "))


def main():
    import os

    changed = set()
    for proj in sorted(GEN.iterdir()):
        fe = proj / "frontend"
        if not (fe / "src" / "main.jsx").exists():
            continue
        msgs = apply(fe, proj.name)
        if any("wired" in m or "bootstrap written" in m or "strip installed" in m or "scaffold" in m or "wrap" in m or "rewriting" in m for m in msgs):
            changed.add(proj.name)
        for m in msgs:
            print(m)
    build_changed(sorted(changed))


if __name__ == "__main__":
    main()
