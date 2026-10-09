"""Regenerate .env.example for every product, from the real code.

The old files listed 61 of the ~141 variables the backend reads, which meant a
buyer could not switch on OAuth, Redis, SMTP or Stripe at all. The frontend
examples were worse: they listed seven server secrets that Vite would never
expose, so any buyer who filled them in published credentials to the browser.

This regenerates both files from env_docs.VARS plus whatever the code actually
reads, so a key that is used but undocumented is added rather than silently
skipped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import env_docs  # noqa: E402

ROOT = Path(r"D:\lumicorepro-core\products")
BAR = "# " + "-" * 73

# Vite supplies these as build modes, so they are not configuration and have no
# business in .env.example.
VITE_BUILTINS = {"PROD", "DEV", "BASE_URL", "MODE", "SSR"}


def backend_vars(prod: Path) -> set[str]:
    keys: set[str] = set()
    for f in (prod / "backend").rglob("*.js"):
        if "node_modules" in f.parts:
            continue
        keys |= set(re.findall(
            r"process\.env\.([A-Z_][A-Z0-9_]*)",
            f.read_text(encoding="utf-8", errors="ignore")))
    return keys


def frontend_vars(prod: Path) -> set[str]:
    keys: set[str] = set()
    for f in (prod / "frontend" / "src").rglob("*"):
        if f.is_file() and f.suffix in {".js", ".jsx"}:
            keys |= set(re.findall(
                r"import\.meta\.env\.([A-Z_][A-Z0-9_]*)",
                f.read_text(encoding="utf-8", errors="ignore")))
    # Vite injects these itself; they are modes, not configuration
    return keys - VITE_BUILTINS


def brand(prod: Path) -> tuple[str, str]:
    slug = prod.name
    db = slug.replace("-", "_")
    return db, slug.replace("-", " ").title()


def render_backend(prod: Path, used: set[str]) -> str:
    db_slug, _ = brand(prod)
    out = [env_docs.HEADER]
    out.append(f"\n{BAR}\n# Backend — server only, never exposed to the browser\n{BAR}\n")

    groups = [(g, h, b) for g, h, b in env_docs.GROUPS if g != "core"]
    # core group is written first, from the static table
    for group, heading, blurb in env_docs.GROUPS:
        if group != "core":
            continue
        out.append(f"\n{BAR}\n# {heading}\n# {blurb}\n{BAR}\n")
        for key, (g, default, hint) in env_docs.VARS.items():
            if g != group:
                continue
            value = default
            if key == "DATABASE_URL":
                value = ("postgresql://postgres:REPLACE_WITH_A_STRONG_PASSWORD"
                         f"@localhost:5432/{db_slug}_db")
            elif key == "APP_BRAND":
                value = ""
            if hint:
                out.append(f"# {hint}")
            out.append(f"{key}={value}\n")
        k, _g, hint = env_docs.PAYMENT_GATEWAYS_ENABLED
        out.append(f"# {hint}")
        out.append(f"{k}=stripe,paypal,lemonsqueezy\n")

    for group, heading, blurb in groups:
        out.append(f"\n{BAR}\n# {heading}\n# {blurb}\n{BAR}\n")
        for key, (g, default, hint) in env_docs.VARS.items():
            if g != group:
                continue
            if hint:
                out.append(f"# {hint}")
            out.append(f"{key}={default}\n")

    out.append(f"\n{BAR}\n# Payment gateways\n#\n"
               f"# Every gateway is optional. A gateway that is not listed in\n"
               f"# PAYMENT_GATEWAYS_ENABLED is never mounted, so its keys stay unused.\n{BAR}\n")
    for provider, (blurb, keys) in env_docs.PAYMENTS.items():
        out.append(f"\n# {blurb}")
        for key, hint in keys:
            if hint:
                out.append(f"# {hint}")
            out.append(f"{key}=\n")
        out.append("")

    # anything the code reads that is not yet documented
    known = set(env_docs.VARS) | env_docs.EXTRA_CORE_KEYS
    for _provider, (_blurb, keys) in env_docs.PAYMENTS.items():
        known |= {k for k, _ in keys}
    leftovers = sorted(used - known)
    if leftovers:
        out.append(f"\n{BAR}\n"
                   f"# Additional variables read by this build\n"
                   f"#\n"
                   f"# These are read directly in code and have no safe default,\n"
                   f"# so they ship blank. Fill them only if the feature you want\n"
                   f"# needs them; each is optional and gated at its call site.\n{BAR}\n")
        for key in leftovers:
            out.append(f"{key}=\n")

    out.append(env_docs.FOOTER)
    return "\n".join(out)


def render_frontend(prod: Path, used: set[str]) -> str:
    analytics = ["VITE_GA4_ID", "VITE_PLAUSIBLE_DOMAIN", "VITE_PLAUSIBLE_HOST",
                 "VITE_POSTHOG_KEY", "VITE_POSTHOG_HOST", "VITE_MIXPANEL_TOKEN",
                 "VITE_FATHOM_SITE_ID"]
    used = used - set(analytics)
    out = [env_docs.HEADER]
    out.append(f"\n{BAR}\n"
               f"# Frontend — public by design\n"
               f"#\n"
               f"# Vite inlines every VITE_ key into the JavaScript bundle, so treat\n"
               f"# anything here as published. Server secrets are never listed on this\n"
               f"# side: they belong in backend/.env and must not be copied here.\n{BAR}\n")
    out.append("\n# VITE_API_URL — backend base URL the SPA calls\n"
               "# VITE_API_TIMEOUT — request timeout in milliseconds\n")
    for key in sorted(used):
        hint, default = env_docs.FRONTEND_VARS.get(key, ("", ""))
        if hint:
            out.append(f"# {hint}")
        out.append(f"{key}={default}\n")
    known = set(env_docs.FRONTEND_VARS)
    for key in sorted(used - known):
        out.append(f"{key}=\n")

    out.append("\n" + BAR + "\n"
               "# Analytics and third-party embeds — all optional.\n"
               "# Leave blank and the corresponding script is not injected.\n" + BAR + "\n")
    for key in analytics:
        hint, _ = env_docs.FRONTEND_VARS[key]
        out.append(f"# {hint}")
        out.append(f"{key}=\n")

    out.append("\n" + BAR + "\n# Server-side secrets — configured in backend/.env, NOT here\n"
               + BAR + "\n#\n"
               "#   JWT_SECRET            signing key for sessions\n"
               "#   JWT_REFRESH_SECRET    signing key for refresh tokens\n"
               "#   DATABASE_URL          PostgreSQL connection string\n"
               "#   STRIPE_SECRET_KEY     server-only Stripe key\n"
               "#   LEMONSQUEEZY_API_KEY  server-only Lemon Squeezy key\n"
               "#   SMTP_PASS             mailbox password\n"
               "#   GOOGLE_CLIENT_SECRET  OAuth client secret\n"
               "#   TURNSTILE_SECRET_KEY  server-side CAPTCHA verification\n\n"
               "# Copying any of these into this file publishes them to every\n"
               "# visitor. They belong in backend/.env only.\n")
    out.append(f"\n{BAR}\n# Cookie consent\n"
               f"#\n"
               f"# The consent banner is enabled by default in production builds.\n"
               f"# Set this to false only if you have your own consent mechanism.\n{BAR}\n")
    out.append("VITE_COOKIE_CONSENT_ENABLED=true\n")
    return "\n".join(out)


def main() -> int:
    total_be = total_fe = 0
    for prod in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        be = prod / "backend"
        if not be.is_dir():
            continue
        used = backend_vars(prod)
        text = render_backend(prod, used)
        (be / ".env.example").write_text(text, encoding="utf-8")
        total_be += len(used)

        fe = prod / "frontend"
        if (fe / "src").is_dir():
            ftext = render_frontend(prod, frontend_vars(prod))
            (fe / ".env.example").write_text(ftext, encoding="utf-8")
            total_fe += 1
        print(f"{prod.name:<18} backend keys documented: {len(used):>4}  "
              f"frontend example rewritten")
    print(f"\nrewrote {total_fe} frontend examples; "
          f"{total_be} backend key references covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())