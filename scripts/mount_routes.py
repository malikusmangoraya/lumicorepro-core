#!/usr/bin/env python3
"""Give every product a server entry point that actually serves its API.

The shipped `backend/server.js` mounts no routes at all — it carries the comment
"Routes will be mounted here" and then serves /health, /ready and the Swagger UI.
Every one of the ~33 route modules in `backend/routes`, including the complete
login/signup implementation, is dead code that no request can reach.

This script writes a real bootstrap in its place. Two details matter:

*   The route modules are ES modules while `server.js` itself is CommonJS, so
    each router is pulled in with a dynamic `import()`. A static `require()`
    cannot load ESM, and the two cannot be mixed in a single static statement.
*   Each router is mounted inside its own try/catch. A single module with a bad
    optional dependency (a payment gateway, a mail transport) then degrades to a
    logged error instead of preventing the whole API from starting.

    python scripts/mount_routes.py --dry-run
    python scripts/mount_routes.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

BOOTSTRAP = '''/**
 * {title} — API server
 *
 * Serves the REST API, the health probes and the Swagger reference.
 * The route modules in ./routes are ES modules; this entry point stays
 * CommonJS and pulls each one in with a dynamic import(), because a static
 * require() cannot load ESM.
 */
const fs = require('fs');
const path = require('path');
const {{ pathToFileURL }} = require('url');

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const compression = require('compression');
require('dotenv').config();

const {{ errorHandler, notFound }} = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 5000;
const ROUTES_PREFIX = process.env.API_PREFIX || '/api';

// ── Security ────────────────────────────────────────────────────────────────
app.use(helmet({{ crossOriginResourcePolicy: {{ policy: 'cross-origin' }} }}));

app.use(
  cors({{
    origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : true,
    credentials: true,
  }})
);

app.use(
  rateLimit({{
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 15 * 60 * 1000,
    max: parseInt(process.env.RATE_LIMIT_MAX, 10) || 300,
    standardHeaders: true,
    legacyHeaders: false,
    message: {{ error: 'Too many requests. Please slow down and try again shortly.' }},
  }})
);

app.use(express.json({{ limit: process.env.JSON_BODY_LIMIT || '2mb' }}));
app.use(express.urlencoded({{ extended: true, limit: process.env.JSON_BODY_LIMIT || '2mb' }}));
app.use(compression());

if (process.env.NODE_ENV !== 'test') {{
  app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));
}}

// ── Routing ─────────────────────────────────────────────────────────────────
/**
 * Load every `*.routes.js` module and mount it at /api/<name>.
 *
 * Each import is isolated: if one module cannot be evaluated (for example an
 * optional payment SDK is not configured), the rest of the API still serves and
 * the failure is reported clearly instead of taking the process down.
 */
async function mountRoutes() {{
  const routesDir = path.join(__dirname, 'routes');
  if (!fs.existsSync(routesDir)) {{
    console.warn(`[server] no routes directory at ${{routesDir}}`);
    return [];
  }}

  const files = fs
    .readdirSync(routesDir)
    .filter((f) => f.endsWith('.routes.js'))
    .sort();

  const mounted = [];
  for (const file of files) {{
    const name = file.replace('.routes.js', '');
    try {{
      const mod = await import(pathToFileURL(path.join(routesDir, file)).href);
      const router = mod.default || mod.router;
      if (typeof router !== 'function') {{
        console.warn(`[server] ${{file}} exported no router; skipped`);
        continue;
      }}
      app.use(`${{ROUTES_PREFIX}}/${{name}}`, router);
      mounted.push(name);
    }} catch (err) {{
      console.error(`[server] failed to mount ${{file}}: ${{err.message}}`);
    }}
  }}
  return mounted;
}}

// ── Operational endpoints ───────────────────────────────────────────────────
app.get('/health', (_req, res) => {{
  res.json({{
    status: 'OK',
    service: '{slug}',
    version: require('./package.json').version,
    environment: process.env.NODE_ENV || 'development',
    uptime: Math.round(process.uptime()),
    timestamp: new Date().toISOString(),
  }});
}});

app.get('/ready', (_req, res) => res.json({{ status: 'ready' }}));

// ── API documentation ───────────────────────────────────────────────────────
try {{
  const swaggerUi = require('swagger-ui-express');
  const swaggerSpec = require('./config/swagger');
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
}} catch (err) {{
  console.warn(`[server] API docs disabled: ${{err.message}}`);
}}

// ── Start ───────────────────────────────────────────────────────────────────
/**
 * Bind the port first, then load the routers.
 *
 * Loading a router can take a moment (each is a dynamic import, and a broken
 * optional dependency costs a failed resolution). Binding first means
 * /health and /ready answer immediately, so an orchestrator never marks the
 * container unhealthy just because a feature module is still loading.
 */
async function start() {{
  const server = app.listen(PORT, () => {{
    console.log(`[server] listening on port ${{PORT}} (${{process.env.NODE_ENV || 'development'}})`);
  }});

  const shutdown = (signal) => () => {{
    console.log(`[server] ${{signal}} received, closing`);
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(1), 10000).unref();
  }};
  process.on('SIGTERM', shutdown('SIGTERM'));
  process.on('SIGINT', shutdown('SIGINT'));

  const mounted = await mountRoutes();

  // The catch-all handlers go on LAST, after every router. Express matches in
  // registration order, so registering `notFound` before the feature routers
  // would swallow every API request and answer 404 for all of them.
  app.use(notFound);
  app.use(errorHandler);

  console.log(`[server] {title} — mounted ${{mounted.length}} route module(s): ${{mounted.join(', ') || 'none'}}`);
}}

if (require.main === module) {{
  start().catch((err) => {{
    console.error(`[server] failed to start: ${{err.stack || err.message}}`);
    process.exit(1);
  }});
}}

module.exports = {{ app, start }};
'''


@dataclass
class Report:
    name: str
    mounted: list[str] = field(default_factory=list)
    detail: str = ""


def titles() -> dict[str, str]:
    """Best-effort display title per product, from its frontend <title>."""
    out: dict[str, str] = {}
    for d in sorted(PRODUCTS.iterdir()) if PRODUCTS.is_dir() else []:
        if not d.is_dir():
            continue
        title = None
        idx = d / "frontend" / "index.html"
        if idx.is_file():
            m = re.search(r"<title>([^<]+)</title>", idx.read_text(encoding="utf-8", errors="replace"))
            if m:
                title = m.group(1).split("—")[0].strip()
        out[d.name] = title or d.name
    return out


def route_modules(be: Path) -> list[str]:
    rd = be / "routes"
    if not rd.is_dir():
        return []
    return sorted(f.name for f in rd.glob("*.routes.js"))


def process(proj: Path, name_map: dict[str, str], dry: bool) -> Report:
    rep = Report(name=proj.name)
    be = proj / "backend"
    server = be / "server.js"
    if not be.is_dir():
        rep.detail = "no backend/"
        return rep

    mods = route_modules(be)
    rep.mounted = [m.replace(".routes.js", "") for m in mods]

    title = name_map.get(proj.name, proj.name)
    content = BOOTSTRAP.format(title=title, slug=proj.name)

    if server.is_file():
        try:
            server.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            rep.detail = f"cannot read existing server.js: {exc}"
            return rep

    if not dry:
        server.write_text(content, encoding="utf-8")
    rep.detail = f"mounted {len(mods)} route module(s): {', '.join(rep.mounted) or 'none'}"
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    if not PRODUCTS.is_dir():
        print(f"No {PRODUCTS} directory", file=sys.stderr)
        return 2
    dirs = sorted(q for q in PRODUCTS.iterdir() if q.is_dir() and not q.name.startswith("."))
    if a.only:
        dirs = [q for q in dirs if a.only in q.name]
    if not dirs:
        print("No matching products", file=sys.stderr)
        return 2

    names = titles()
    print(f"=== mount_routes: {'DRY RUN' if a.dry_run else 'APPLY'} ({len(dirs)} product(s)) ===")
    total = 0
    for d in dirs:
        rep = process(d, names, a.dry_run)
        total += len(rep.mounted)
        print(f"-- {rep.name:20} {rep.detail}")
    print(f"\n=== {total} route module(s) will now be reachable ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())