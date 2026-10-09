#!/usr/bin/env python3
"""Make every `delivery/` package buildable by a buyer who just runs npm.

Every delivered project currently ships `src/` + `dist/` + a README that says

    npm install
    npm run dev
    npm run build

...but the package contains no `package.json`, no `vite.config.js`, no root
`index.html`, no Tailwind/PostCSS config, no `.env.example` and no licence. The
build instructions in the shipped README cannot succeed. This script fixes that
for all of them from the real source:

  * `package.json`      - dependencies derived from the imports actually present
                          in `src/`, versions pinned to the set proven green in
                          `products/*/frontend`.
  * `vite.config.js`    - defines the `@` alias the source imports (14 of them
                          per site), env-driven `base` for sub-path hosting, and
                          vendor chunking so React is not re-downloaded on deploy.
  * `index.html`        - rebuilt from the shipped `dist/index.html` so the SEO
                          head (title, description, canonical, OG, Twitter,
                          hreflang, JSON-LD) survives, with the hashed build
                          artefacts replaced by the `/src/main.jsx` entry.
  * `tailwind.config.js` / `postcss.config.js` - generated from that project's own
                          `src/styles/design-tokens.json` so brand colours come
                          from tokens rather than hardcoded hex.
  * `public/`           - the static files a Vite build would otherwise delete
                          (`favicon.svg`, `manifest.json`, `robots.txt`,
                          `og-image.svg`, `_headers`, `_redirects`, `sitemap.xml`,
                          pre-rendered legal HTML) so `npm run build` reproduces a
                          complete `dist/` instead of a stripped one.
  * `.env.example`      - every `import.meta.env.*` reference found in the source.
  * `README.md`         - a real buyer README: what it is, install, env table,
                          structure, scripts, build output, deployment.
  * `LICENSE.md`, `.gitignore`.

It is idempotent: existing files are left alone unless `--force` is passed.

    python scripts/harden_delivery_package.py                 # all sites
    python scripts/harden_delivery_package.py apex-digital    # one site
    python scripts/harden_delivery_package.py --force         # rewrite
    python scripts/harden_delivery_package.py --report-only   # audit only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
DELIVERY = ROOT / "delivery"
REPORT = ROOT / "docs" / "audit" / "delivery_harden_report.json"

# Versions proven to build green in products/*/frontend (audited 11/11).
DEP_VERSIONS = {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "@tanstack/react-query": "^5.59.0",
    "zustand": "^5.0.0",
    "react-router-dom": "^6.22.0",
    "lucide-react": "^1.31.0",
    "framer-motion": "^11.18.2",
    "i18next": "^25.0.0",
    "react-i18next": "^16.0.0",
    "i18next-browser-languagedetector": "^8.0.0",
    "axios": "^1.6.0",
    # 3D projects. drei 10.7.9 peers are react ^19 / three >=0.159 /
    # @react-three/fiber ^9, which the pins above satisfy.
    "three": "^0.174.0",
    "@react-three/fiber": "^9.7.0",
    "@react-three/drei": "^10.7.9",
}
DEV_VERSIONS = {
    "@vitejs/plugin-react": "^6.0.4",
    "vite": "^8.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
}

IMPORT_RE = re.compile(r"""(?:from|import)\s+['"]([^'"]+)['"]""")
# A real bare specifier: `pkg`, `pkg/sub`, `@scope/pkg`, `@scope/pkg/sub`. This
# rejects template-literal noise such as `from 'Shop Now'`, which is prose
# inside a generated string rather than an import.
SPECIFIER_RE = re.compile(r"^(?:@[a-z0-9\-~][\w\-.]*/)?[a-z0-9\-~][\w\-.]*(?:/[\w\-.]+)*$")
ENV_RE = re.compile(r"import\.meta\.env\.([A-Z0-9_]+)")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
CANONICAL_RE = re.compile(r"""<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>""")
DESC_RE = re.compile(r"""<meta\s+name="description"\s+content="([^"]*)"\s*/?>""")

ENV_DOCS = {
    "VITE_SITE_URL": "Absolute origin the site is deployed at (`https://your-domain.com`). Rewrites canonical, Open Graph, hreflang and JSON-LD at build time.",
    "VITE_BASE_PATH": "Sub-path the site is served from. `/` for a root domain, `/your-repo/` for GitHub Pages project sites.",
    "VITE_API_URL": "Base URL of the backend API. Leave as `/api` to use the dev proxy.",
    "VITE_API_TIMEOUT": "Request timeout in milliseconds. Defaults to 12000.",
    "VITE_GA4_ID": "Google Analytics 4 measurement ID (`G-XXXXXXX`). Empty disables GA4.",
    "VITE_POSTHOG_KEY": "PostHog project API key. Empty disables PostHog.",
    "VITE_POSTHOG_HOST": "PostHog ingestion host. Defaults to `https://app.posthog.com`.",
    "VITE_PLAUSIBLE_DOMAIN": "Plausible site domain. Empty disables Plausible.",
    "VITE_PLAUSIBLE_HOST": "Plausible API host. Defaults to `https://plausible.io`.",
    "VITE_MIXPANEL_TOKEN": "Mixpanel project token. Empty disables Mixpanel.",
    "VITE_FATHOM_SITE_ID": "Fathom site ID. Empty disables Fathom.",
    "VITE_FORMSPREE_ID": "Formspree form ID used by the lead form when no API is configured.",
    "VITE_LEADS_WEBHOOK": "Webhook URL that receives lead submissions.",
}

# Static files that must live in public/ so a Vite build reproduces them.
PUBLIC_FILES = [
    "favicon.svg",
    "manifest.json",
    "robots.txt",
    "og-image.svg",
    "sitemap.xml",
    "_headers",
    "_redirects",
    "privacy-policy.html",
    "terms-of-service.html",
]


def read(path: pathlib.Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def slug_name(slug: str) -> str:
    return slug.replace("-", " ").strip().title()


def scan_src(src: pathlib.Path) -> tuple[set[str], set[str], int]:
    """Return (bare npm imports, env var references, file count)."""
    imports: set[str] = set()
    envs: set[str] = set()
    files = 0
    for f in sorted(src.rglob("*.js*")):
        files += 1
        text = read(f)
        for m in IMPORT_RE.findall(text):
            if m.startswith(".") or m.startswith("@/"):
                continue
            parts = m.split("/")
            pkg = parts[0] if not m.startswith("@") else "/".join(parts[:2])
            if not SPECIFIER_RE.match(pkg):
                continue
            imports.add(pkg)
        envs.update(ENV_RE.findall(text))
    return imports, envs, files


TAILWIND_DEFAULT_COLORS = {
    "slate", "gray", "zinc", "neutral", "stone", "red", "orange", "amber",
    "yellow", "lime", "green", "emerald", "teal", "cyan", "sky", "blue",
    "indigo", "violet", "purple", "fuchsia", "pink", "rose", "white", "black",
    "transparent", "current", "inherit",
}
APPLY_RE = re.compile(r"@apply\s+([^;]+);")


def to_css_color(value: str) -> str | None:
    """Normalise a CSS custom property value to something Tailwind accepts."""
    value = value.strip().rstrip(";").strip()
    if not value:
        return None
    if re.fullmatch(r"(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})", value):
        return "rgb(" + ", ".join(re.findall(r"\d{1,3}", value)) + ")"
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}\b", value):
        return value
    if re.fullmatch(r"[a-zA-Z]+", value):
        return value
    return None


def palette_from_css(src: pathlib.Path) -> tuple[dict, list[str]]:
    """Recover a palette from `--t-*` custom properties in the CSS.

    Two projects ship no `design-tokens.json`, but their stylesheets still carry
    the brand palette as CSS variables, in RGB-triplet form inside light/dark
    blocks. The later block wins, matching which theme the build actually uses.
    Without this the generated Tailwind config has no colours and `@apply
    from-accent` fails the build.
    """
    colors: dict[str, str] = {}
    fonts: list[str] = []
    for css in sorted(src.rglob("*.css")):
        text = read(css)
        for name, value in re.findall(r"--t-([a-z0-9-]+)\s*:\s*([^;]+);", text):
            if name.endswith("-rgb"):
                continue
            converted = to_css_color(value)
            if converted:
                colors[name] = converted
        for family in re.findall(r"font-family:\s*['\"]?([A-Za-z][\w\- ]*[A-Za-z])", text):
            family = family.strip()
            if family and family not in fonts and not family.startswith("sans"):
                fonts.append(family)
    return colors, fonts


def audit_apply_colors(src: pathlib.Path, palette: dict[str, str]) -> list[str]:
    """Report `@apply` colour utilities the palette cannot resolve."""
    known = set(palette)
    unknown: set[str] = set()
    for css in src.rglob("*.css"):
        for block in APPLY_RE.findall(read(css)):
            for util in block.split():
                parts = util.split(":")[-1].split("-")
                if len(parts) < 2:
                    continue
                prefix, name = parts[0], parts[1]
                if prefix not in {"bg", "text", "border", "from", "via", "to", "ring", "fill", "stroke", "shadow", "outline", "decoration", "divide", "caret", "accent", "placeholder"}:
                    continue
                if name in TAILWIND_DEFAULT_COLORS or name.isdigit():
                    continue
                if name not in known:
                    unknown.add(f"{util} (index.css)")
    return sorted(unknown)


def load_tokens(src: pathlib.Path) -> dict:
    raw = read(src / "styles" / "design-tokens.json")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    palette, fonts = palette_from_css(src)
    if not palette:
        return {}
    typography = {
        "display": fonts[0] if fonts else "",
        "sans": fonts[1] if len(fonts) > 1 else (fonts[0] if fonts else ""),
        "mono": fonts[-1] if len(fonts) > 2 else "",
    }
    return {
        "style": "recovered-from-css",
        "palette": palette,
        "typography": typography,
        "source": "css-custom-properties",
    }


def site_facts(slug: str, site: pathlib.Path) -> dict:
    dist_index = read(site / "dist" / "index.html")
    title = TITLE_RE.search(dist_index)
    canonical = CANONICAL_RE.search(dist_index)
    desc = DESC_RE.search(dist_index)
    live = ""
    live_txt = read(site / "LIVE-LINK.txt")
    m = re.search(r"https?://\S+", live_txt)
    if m:
        live = m.group(0).strip()
    origin = ""
    if canonical:
        origin = canonical.group(1).rstrip("/")
    elif live:
        origin = live.rstrip("/")
    industry = ""
    readme = read(site / "README.md")
    mi = re.search(r"\*\*Industry:\*\*\s*([a-z0-9\- ]+)", readme)
    if mi:
        industry = mi.group(1).strip()
    return {
        "slug": slug,
        "brand": title.group(1).split("—")[0].strip() if title else slug_name(slug),
        "tagline": title.group(1).split("—", 1)[1].strip() if title and "—" in title.group(1) else "",
        "title": title.group(1).strip() if title else slug_name(slug),
        "description": desc.group(1).strip() if desc else "",
        "canonical": origin,
        "live": live,
        "industry": industry or "general",
    }


SITE_ORIGIN_TOKEN = "__SITE_ORIGIN__"
HOST_RE = re.compile(r"https?://([^/\"'\s)]+)")


def strip_build_artefacts(html: str) -> str:
    """Remove the hashed build output from the head.

    The shipped `dist/index.html` references its compiled entry as
    `/assets/index-<hash>.js` or `./assets/index-<hash>.js` depending on the
    project's `base`, with attributes in either order. Anything left behind is a
    reference to a file a fresh build will not produce, and the build fails on
    it. Matching whole tags and testing their contents is order independent;
    the JSON-LD block and the Google Fonts stylesheet have no `assets/` href and
    are preserved.
    """
    def is_entry_script(tag: str) -> bool:
        return "assets/" in tag and ".js" in tag and "src=" in tag

    def is_built_css(tag: str) -> bool:
        low = tag.lower()
        return "stylesheet" in low and "assets/" in low and ".css" in low

    def is_built_preload(tag: str) -> bool:
        # Vite injects modulepreload links for the emitted chunks. Reusing a
        # rebuilt dist/index.html as the source for the next generation
        # otherwise carries those hashed filenames forward forever.
        low = tag.lower()
        return "modulepreload" in low and "assets/" in low

    html = re.sub(r"<script[^>]*src=[^>]*>\s*</script>", lambda m: "" if is_entry_script(m.group(0)) else m.group(0), html)
    html = re.sub(
        r"<link[^>]*>",
        lambda m: "" if (is_built_css(m.group(0)) or is_built_preload(m.group(0))) else m.group(0),
        html,
    )
    # Tidy the whitespace the removals leave behind.
    return re.sub(r"\n{3,}", "\n\n", html)


def build_index_html(facts: dict, dist_index: str) -> str:
    """Rebuild the source entry HTML from the shipped built HTML.

    The built pages state two different homes for themselves: canonical and
    og:url point at the demo host while twitter:image and the JSON-LD graph
    point at a guessed apex domain. A crawler reading both is being told the
    site lives in two places. Every absolute URL is therefore rewritten to a
    single `__SITE_ORIGIN__` token, which the generated vite config replaces
    with `VITE_SITE_URL` at build time - so a buyer repoints the whole SEO head
    at their own domain with one environment variable.
    """
    html = dist_index
    canonical = CANONICAL_RE.search(html)
    canon = canonical.group(1).rstrip("/") if canonical else ""
    canon_host = HOST_RE.match(canon).group(1) if canon and HOST_RE.match(canon) else ""

    if canon:
        # Longest first, so the full canonical URL is tokenised before the bare host.
        html = html.replace(canon + "/", SITE_ORIGIN_TOKEN + "/").replace(canon, SITE_ORIGIN_TOKEN)
    for host in {h for h in HOST_RE.findall(html)}:
        if host == canon_host:
            html = html.replace(f"https://{host}", SITE_ORIGIN_TOKEN)
            html = html.replace(f"http://{host}", SITE_ORIGIN_TOKEN)
        else:
            html = html.replace(f"https://{host}", SITE_ORIGIN_TOKEN)
            html = html.replace(f"http://{host}", SITE_ORIGIN_TOKEN)

    # Drop build artefacts, point at the source entry instead.
    html = strip_build_artefacts(html)
    entry = '\n    <script type="module" src="/src/main.jsx"></script>\n  </head>'
    if 'rel="manifest"' not in html:
        html = html.replace("</head>", '    <link rel="manifest" href="/manifest.json" />\n  </head>', 1)
    if "</head>" in html:
        html = html.replace("</head>", entry, 1)
    if 'id="root"' not in html:
        html = html.replace("<body>", '<body>\n    <div id="root"></div>', 1)
    return html.rstrip() + "\n"


def build_vite_config(slug: str, default_origin: str = "") -> str:
    return f"""import {{ defineConfig }} from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// index.html carries `__SITE_ORIGIN__` wherever an absolute URL is needed
// (canonical, og:url, hreflang, JSON-LD). Set VITE_SITE_URL to your deployed
// origin and the whole SEO head is repointed at build time; leave it unset and
// the shipped default is used.
const SITE_ORIGIN = process.env.VITE_SITE_URL || '{default_origin}';

// `base` is env driven so the same build serves a root domain and a project
// sub-path (GitHub Pages, `https://user.github.io/{slug}/`).
export default defineConfig({{
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [
    react(),
    {{
      name: 'lumi-site-origin',
      transformIndexHtml(html) {{
        return html.replaceAll('{SITE_ORIGIN_TOKEN}', SITE_ORIGIN);
      }},
    }},
  ],
  resolve: {{
    alias: {{
      '@': path.resolve(import.meta.dirname, './src'),
    }},
  }},
  server: {{
    port: 3000,
    proxy: {{
      '/api': {{
        target: process.env.VITE_API_PROXY || 'http://localhost:5000',
        changeOrigin: true,
      }},
    }},
  }},
  build: {{
    assetsInlineLimit: 8192,
    cssCodeSplit: true,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 700,
    rollupOptions: {{
      output: {{
        // Vendor code changes far less often than product code, so a content
        // deploy does not force visitors to re-download React, the router and
        // the query client.
        manualChunks(id) {{
          if (!id.includes('node_modules')) return undefined;
          if (/[\\\\/]node_modules[\\\\/](react|react-dom|scheduler)[\\\\/]/.test(id)) return 'vendor-react';
          if (/[\\\\/]node_modules[\\\\/](react-router|react-router-dom)[\\\\/]/.test(id)) return 'vendor-router';
          if (/[\\\\/]node_modules[\\\\/](i18next|react-i18next|i18next-browser-languagedetector)[\\\\/]/.test(id)) return 'vendor-i18n';
          if (/[\\\\/]node_modules[\\\\/](@tanstack|zustand|axios)[\\\\/]/.test(id)) return 'vendor-app';
          if (/[\\\\/]node_modules[\\\\/](framer-motion|motion-dom|motion-utils)[\\\\/]/.test(id)) return 'vendor-motion';
          if (/[\\\\/]node_modules[\\\\/]lucide-react[\\\\/]/.test(id)) return 'vendor-icons';
          return 'vendor';
        }},
      }},
    }},
  }},
}});
"""


FALLBACK_SANS = ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"]
FALLBACK_MONO = ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"]


def _js_key(key: str) -> str:
    """Quote object keys that are not valid JavaScript identifiers.

    `canvas-text: '...'` is a syntax error in JS - the parser reads `canvas`
    and then trips over the hyphen - so the whole Tailwind config fails to load
    and PostCSS then reports unrelated, meaningless errors against the CSS.
    """
    return key if re.fullmatch(r"[A-Za-z_$][\w$]*", key) else f"'{key}'"


def build_tailwind_config(tokens: dict) -> str:
    palette = tokens.get("palette", {}) or {}
    typo = tokens.get("typography", {}) or {}

    def fam(value: str, fallbacks: list[str]) -> str:
        """A real JS array literal: ['Poppins', 'ui-sans-serif', ...]."""
        items = ([value] if value else []) + fallbacks
        return "[" + ", ".join(f"'{i}'" for i in items) + "]"

    colors = "\n".join(
        f"        {_js_key(key)}: '{value}',"
        for key, value in palette.items()
        if isinstance(value, str)
    )
    display = fam(typo.get("display", ""), FALLBACK_SANS)
    sans = fam(typo.get("sans", ""), FALLBACK_SANS)
    mono = fam(typo.get("mono", ""), FALLBACK_MONO)
    style = tokens.get("style", "custom")
    return f"""// Generated from src/styles/design-tokens.json ({style}).
// Brand colour lives in the token file, not in JSX, so re-theming is a token
// edit rather than a find-and-replace across components.
/** @type {{import('tailwindcss').Config}} */
export default {{
  content: ['./index.html', './src/**/*.{{js,jsx,ts,tsx}}'],
  darkMode: 'class',
  theme: {{
    extend: {{
      colors: {{
{colors}
      }},
      fontFamily: {{
        display: {display},
        sans: {sans},
        mono: {mono},
      }},
    }},
  }},
  plugins: [],
}};
"""


POSTCSS_CONFIG = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

SPA_HEADERS = """# Netlify / Cloudflare Pages response headers.
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: geolocation=(), microphone=(), camera=()
"""

SPA_REDIRECTS = """# Single-page-app fallback: deep links such as /about are served by the
# client router, so every unknown path must resolve to the app shell.
/*  /index.html  200
"""

GITIGNORE = """node_modules/
dist/
dist-verify/
.verify/
*.local
.env
.env.*
!.env.example
.DS_Store
*.log
.vite/
coverage/
"""


def build_env_example(envs: set[str], facts: dict) -> str:
    ordered = [e for e in ENV_DOCS if e in envs]
    ordered += sorted(e for e in envs if e not in ENV_DOCS)
    # Consumed by vite.config.js rather than import.meta.env, so it will not
    # show up in the source scan but is still required to deploy correctly.
    for required in ("VITE_SITE_URL", "VITE_BASE_PATH"):
        if required not in ordered:
            ordered.insert(0, required)
    ordered = sorted(dict.fromkeys(ordered), key=lambda e: (e != "VITE_SITE_URL", e != "VITE_BASE_PATH", e))
    width = max(len(e) for e in ordered)
    rows = "\n".join(
        f"# {ENV_DOCS.get(e, 'Referenced by the source; set it to the value your deployment needs.')}\n{e.ljust(width)}="
        for e in ordered
    )
    return f"""# Environment for {facts['brand']}
#
# Copy to `.env` and fill in. Only variables prefixed with VITE_ reach the
# browser bundle - never put a secret key in this file. Every value here is
# optional: the site runs with all of them blank.

{rows}

# Local development: where `npm run dev` proxies /api requests.
# VITE_API_PROXY=http://localhost:5000
"""


LICENSE = """MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def build_readme(facts: dict, envs: set[str], src_files: int, deps: list[str], locales: int = 0) -> str:
    brand = facts["brand"]
    tagline = facts["tagline"] or facts["description"] or f"{brand} website and application."
    live = facts["live"] or "the deployment you publish this to"
    base_hint = f"/{facts['slug']}/" if facts["slug"] else "/"
    locale_claim = (
        f"{locales} translated locale files" if locales else "i18n wiring ready for more locales"
    )
    env_rows = "\n".join(
        f"| `{e}` | {ENV_DOCS.get(e, 'Deployment specific')} |"
        for e in (["VITE_BASE_PATH"] + sorted(envs))
        if e in ENV_DOCS or e in envs
    )
    dep_rows = "\n".join(f"| `{d}` | {DEP_VERSIONS.get(d, '')} |" for d in sorted(deps))
    return f"""# {brand}

{tagline}

A production-ready React {facts['industry']} front end: {src_files} source files,
Tailwind design tokens, {locale_claim}, lazy-loaded routes, SEO metadata and
JSON-LD, PWA manifest and offline shell.

**Live demo:** {live}

---

## Requirements

| Tool | Version |
|------|---------|
| Node.js | 20 or newer |
| npm | 10 or newer |

## Install

```bash
npm install
```

## Run locally

```bash
npm run dev      # http://localhost:3000
```

## Build

```bash
npm run build    # emits dist/
npm run preview  # serve the built dist/ locally
```

`dist/` is a static bundle - any static host can serve it.

## Scripts

| Command | What it does |
|---------|--------------|
| `npm run dev` | Vite dev server on port 3000 with HMR |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint over `src/` |

## Environment

Copy `.env.example` to `.env` and fill in what you need. Everything is
optional: the site runs with an empty `.env`.

| Variable | Purpose |
|----------|---------|
{env_rows}

Only `VITE_`-prefixed variables reach the browser. Never put a private key in
this project - the bundle is public.

## Structure

```
index.html            Entry HTML: SEO head, hreflang, OG, JSON-LD
public/               Copied verbatim into dist/ (favicon, manifest, robots,
                      sitemap, netlify-style _headers/_redirects)
src/
  main.jsx            React root
  App.jsx             Router with lazy-loaded routes
  pages/              Route components
  components/         UI, business, motion, navigation components
  layouts/            App and landing shells
  context/ store/     Currency context, Zustand stores
  hooks/ services/    Data fetching and API access
  i18n/locales/       translated locale files
  styles/             design-tokens.json, rtl.css
  config/             analytics, cookie consent, feature flags
tailwind.config.js    Brand colour and type scale, generated from
                      src/styles/design-tokens.json
vite.config.js        Build config, `@` alias, vendor chunking
```

## Dependencies

| Package | Version |
|---------|---------|
{dep_rows}

## Deployment

Set `VITE_BASE_PATH` to match where the site is served, then build:

```bash
VITE_BASE_PATH={base_hint} npm run build
```

- **Netlify / Cloudflare Pages** - publish directory `dist/`. `public/_headers`
  and `public/_redirects` are included for the SPA fallback and caching.
- **GitHub Pages** - push `dist/` to `gh-pages` and set
  `VITE_BASE_PATH=/<repo>/`.
- **Vercel** - framework preset Vite, output directory `dist`.
- **Any static host** - upload `dist/`.

`robots.txt` and `sitemap.xml` in `public/` are already generated; update the
origin inside them to your domain after deploying.

## Accessibility and motion

Keyboard-navigable, landmark-based, labelled form controls, visible focus
rings, `prefers-reduced-motion` respected, and RTL stylesheets for the
right-to-left locales.

## Licence

MIT - see `LICENSE.md`.
"""


def build_manifest(facts: dict, tokens: dict) -> str:
    palette = tokens.get("palette", {}) or {}
    theme_color = (
        palette.get("navBg")
        or palette.get("canvas")
        or palette.get("bg")
        or palette.get("surface")
        or "#0e1116"
    )
    background = palette.get("canvas") or theme_color
    name = facts["brand"]
    # Origin-relative: the manifest must work on whatever host the buyer
    # deploys to, not on the demo domain the package happened to be built from.
    start = "/"
    manifest = {
        "name": name,
        "short_name": name[:12],
        "description": facts["description"] or facts["tagline"],
        "start_url": start,
        "scope": start,
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": background,
        "theme_color": theme_color,
        "icons": [
            {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
        ],
    }
    return json.dumps(manifest, indent=2) + "\n"


def write(path: pathlib.Path, content: str, force: bool, actions: list[str]) -> bool:
    if path.exists() and not force:
        actions.append(f"kept {path.name}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    actions.append(f"wrote {path.name}")
    return True


def write_readme(path: pathlib.Path, content: str, force: bool, actions: list[str]) -> bool:
    """Rewrite the README when it is still the generated stub.

    The stub promised `npm install && npm run build` for a package with no
    package.json. Once the build config exists the README must describe the
    real project, so a stub is always replaced. A hand-written README is kept.
    """
    if path.exists() and not force:
        existing = read(path)
        if len(existing.strip()) >= 800:
            actions.append("kept README.md (hand-written)")
            return False
    return write(path, content, True, actions)


def harden(slug: str, site: pathlib.Path, force: bool, report_only: bool) -> dict:
    actions: list[str] = []
    src = site / "src"
    facts = site_facts(slug, site)
    imports, envs, src_files = scan_src(src)
    tokens = load_tokens(src)

    deps = sorted(d for d in imports if d in DEP_VERSIONS)
    unknown = sorted(d for d in imports if d not in DEP_VERSIONS and not d.startswith("node:"))

    package = {
        "name": slug,
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
        },
        "dependencies": {d: DEP_VERSIONS[d] for d in deps},
        "devDependencies": dict(sorted(DEV_VERSIONS.items())),
    }

    missing_before = sorted(
        f for f in ("package.json", "vite.config.js", "index.html", "tailwind.config.js",
                    "postcss.config.js", ".env.example", "LICENSE.md")
        if not (site / f).exists()
    )

    if not report_only:
        write(site / "package.json", json.dumps(package, indent=2) + "\n", force, actions)
        write(site / "vite.config.js", build_vite_config(slug, facts["canonical"]), force, actions)
        write(site / "postcss.config.js", POSTCSS_CONFIG, force, actions)
        write(site / "tailwind.config.js", build_tailwind_config(tokens), force, actions)
        write(site / ".gitignore", GITIGNORE, force, actions)
        write(site / "LICENSE.md", LICENSE, force, actions)
        write(site / ".env.example", build_env_example(envs, facts), force, actions)
        write_readme(
            site / "README.md",
            build_readme(
                facts,
                envs,
                src_files,
                deps,
                len(list((src / "i18n" / "locales").glob("*.json"))) if (src / "i18n" / "locales").exists() else 0,
            ),
            force,
            actions,
        )

        dist_index = read(site / "dist" / "index.html")
        if dist_index:
            write(site / "index.html", build_index_html(facts, dist_index), force, actions)

        # Static files a bare Vite build would drop from dist/.
        for name in PUBLIC_FILES:
            source = site / "dist" / name
            target = site / "public" / name
            if source.exists() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                actions.append(f"public/{name}")

        # PWA manifest: some projects were never given one. Without it the site is
    # not installable and the hosting platforms flag it.
    if not (site / "public" / "manifest.json").exists():
        (site / "public").mkdir(parents=True, exist_ok=True)
        (site / "public" / "manifest.json").write_text(
            build_manifest(facts, tokens), encoding="utf-8", newline="\n"
        )
        actions.append("public/manifest.json (generated)")

    # Some projects were built by a pipeline that never emitted the host
        # config. Without the SPA fallback a deep link such as /about 404s.
        if not (site / "public" / "_redirects").exists():
            (site / "public" / "_redirects").write_text(SPA_REDIRECTS, encoding="utf-8", newline="\n")
            actions.append("public/_redirects (SPA fallback)")
        if not (site / "public" / "_headers").exists():
            (site / "public" / "_headers").write_text(SPA_HEADERS, encoding="utf-8", newline="\n")
            actions.append("public/_headers (security + cache)")

    return {
        "slug": slug,
        "brand": facts["brand"],
        "industry": facts["industry"],
        "src_files": src_files,
        "locales": len(list((src / "i18n" / "locales").glob("*.json"))) if (src / "i18n" / "locales").exists() else 0,
        "deps": deps,
        "undeclared_imports": unknown,
        "unresolved_apply_colors": audit_apply_colors(src, tokens.get("palette", {}) or {}),
        "token_source": tokens.get("source", "design-tokens.json"),
        "env_refs": sorted(envs),
        "missing_before": missing_before,
        "actions": actions,
        "changed": bool(actions) and report_only is False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sites", nargs="*", help="limit to these site slugs")
    ap.add_argument("--force", action="store_true", help="overwrite existing generated files")
    ap.add_argument("--report-only", action="store_true", help="report gaps without writing")
    args = ap.parse_args()

    if not DELIVERY.exists():
        print(f"no delivery directory at {DELIVERY}", file=sys.stderr)
        return 1

    sites = sorted(p for p in DELIVERY.iterdir() if p.is_dir() and (p / "src").exists())
    if args.sites:
        wanted = set(args.sites)
        sites = [p for p in sites if p.name in wanted]

    results = []
    for site in sites:
        results.append(harden(site.name, site, args.force, args.report_only))

    already_ok = [r for r in results if not r["missing_before"]]
    gaps = {r["slug"]: r["missing_before"] for r in results if r["missing_before"]}
    undeclared = {r["slug"]: r["undeclared_imports"] for r in results if r["undeclared_imports"]}

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "mode": "report-only" if args.report_only else "harden",
                "sites": len(results),
                "sitesAlreadyComplete": len(already_ok),
                "gapsBefore": gaps,
                "undeclaredImports": undeclared,
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"sites scanned : {len(results)}")
    print(f"missing files : {sum(len(v) for v in gaps.values())} across {len(gaps)} sites")
    if undeclared:
        print(f"undeclared    : {len(undeclared)} sites -> {sorted({i for v in undeclared.values() for i in v})}")
    print(f"report        : {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
