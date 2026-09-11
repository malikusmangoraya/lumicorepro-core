"""
CDN Optimizer — LumicorePro AI Agent
=====================================
Phase 13 — Global Infrastructure

Generates production-ready CDN & edge deployment configurations:
  - Cloudflare (Workers, Cache Rules, Security Headers, Page Rules)
  - Vercel (vercel.json with headers, rewrites, regions, edge functions)
  - AWS CloudFront (distribution config + cache behaviors + OAC)
  - Netlify (_headers, _redirects, netlify.toml)
  - Nginx (optimized nginx.conf with gzip, caching, security)
  - Security headers (CSP, HSTS, X-Frame-Options, etc.)
  - CDN_DEPLOYMENT.md guide
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class CDNOptimizer:
    """Multi-CDN config generator for global edge deployment."""

    # ── Security header values ────────────────────────────────────────────
    SECURITY_HEADERS = {
        "Strict-Transport-Security":     "max-age=31536000; includeSubDomains; preload",
        "X-Content-Type-Options":        "nosniff",
        "X-Frame-Options":               "SAMEORIGIN",
        "X-XSS-Protection":              "1; mode=block",
        "Referrer-Policy":               "strict-origin-when-cross-origin",
        "Permissions-Policy":            "camera=(), microphone=(), geolocation=(self), payment=(self)",
        "Cross-Origin-Embedder-Policy":  "credentialless",
        "Cross-Origin-Opener-Policy":    "same-origin-allow-popups",
        "Cross-Origin-Resource-Policy":  "same-site",
    }

    # Cache-Control per resource type
    CACHE_RULES = {
        "hashed_assets":  "public, max-age=31536000, immutable",      # JS/CSS with hash
        "images":         "public, max-age=2592000, stale-while-revalidate=86400",  # 30 days
        "fonts":          "public, max-age=31536000, immutable",
        "html":           "public, max-age=0, must-revalidate",
        "api":            "private, no-store, no-cache",
        "manifest":       "public, max-age=86400",
        "sw":             "public, max-age=0, must-revalidate",
    }

    # ── Vercel edge regions (global) ──────────────────────────────────────
    VERCEL_REGIONS_GLOBAL = ["iad1", "sfo1", "lhr1", "fra1", "sin1", "hnd1", "bom1", "cdg1"]
    VERCEL_REGIONS_BY_REGION = {
        "NA":    ["iad1", "sfo1"],
        "EU":    ["lhr1", "fra1", "cdg1"],
        "SA":    ["bom1"],
        "MENA":  ["fra1", "bom1"],
        "APAC":  ["sin1", "hnd1"],
        "AF":    ["lhr1", "fra1"],
        "LATAM": ["iad1", "sfo1"],
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate all CDN configuration files."""
        agent_logger.info("CDNOptimizer: Generating multi-CDN deployment configs...")

        # Accept the historical (project_dir, spec) order used by integrations.
        if isinstance(spec, str) and isinstance(project_dir, dict):
            spec, project_dir = project_dir, spec

        region       = spec.get("region", "NA")
        project_name = spec.get("project_name", "project")
        features     = spec.get("features", [])
        website_type = spec.get("website_type", "ecommerce")
        has_api      = bool(spec.get("has_api", True))  # False for client-static showcase mode

        artifacts = []
        root = project_dir
        frontend = os.path.join(project_dir, "frontend", "public")
        os.makedirs(frontend, exist_ok=True)

        # 1. vercel.json
        vercel_path = os.path.join(root, "vercel.json")
        self._write(vercel_path, json.dumps(
            self._build_vercel(spec, region, has_api), indent=2
        ))
        artifacts.append(vercel_path)

        # 2. netlify.toml
        netlify_path = os.path.join(root, "netlify.toml")
        self._write(netlify_path, self._build_netlify(spec, has_api))
        artifacts.append(netlify_path)

        # 3. _headers (Netlify/Cloudflare Pages)
        headers_path = os.path.join(os.path.join(root, "frontend", "public"), "_headers")
        self._write(headers_path, self._build_headers_file(has_api))
        artifacts.append(headers_path)

        # 4. _redirects (Netlify SPA routing)
        redirects_path = os.path.join(os.path.join(root, "frontend", "public"), "_redirects")
        self._write(redirects_path, self._build_redirects(has_api))
        artifacts.append(redirects_path)

        # 5. nginx.conf (self-hosted / VPS / Docker) — API-gateway only for
        #    enterprise full-stack mode; client-static showcase has no backend.
        if has_api:
            nginx_dir = os.path.join(root, "nginx")
            os.makedirs(nginx_dir, exist_ok=True)
            nginx_path = os.path.join(nginx_dir, "nginx.conf")
            self._write(nginx_path, self._build_nginx(spec))
            artifacts.append(nginx_path)

        # 6. cloudflare-rules.json (Cloudflare cache rules export)
        cf_path = os.path.join(root, "cloudflare-rules.json")
        self._write(cf_path, json.dumps(self._build_cloudflare_rules(spec), indent=2))
        artifacts.append(cf_path)

        # 7. CDN_DEPLOYMENT.md
        cdn_md_path = os.path.join(root, "CDN_DEPLOYMENT.md")
        self._write(cdn_md_path, self._build_cdn_md(spec, region))
        artifacts.append(cdn_md_path)

        result = {
            "platforms_configured": ["vercel", "netlify", "nginx", "cloudflare"],
            "edge_regions":         self.VERCEL_REGIONS_BY_REGION.get(region, self.VERCEL_REGIONS_GLOBAL),
            "security_headers":     list(self.SECURITY_HEADERS.keys()),
            "cache_rules":          self.CACHE_RULES,
            "artifacts":            artifacts,
        }
        agent_logger.info(
            f"CDNOptimizer: {len(artifacts)} configs, "
            f"regions={self.VERCEL_REGIONS_BY_REGION.get(region, ['global'])}"
        )
        return result

    # ── Platform builders ─────────────────────────────────────────────────
    def _build_vercel(self, spec, region, has_api):
        regions = self.VERCEL_REGIONS_BY_REGION.get(region, self.VERCEL_REGIONS_GLOBAL)
        headers = [
            {
                "source": "/assets/(.*)",
                "headers": [
                    {"key": "Cache-Control", "value": self.CACHE_RULES["hashed_assets"]},
                ]
            },
            {
                "source": "/(.*)",
                "headers": [
                    {"key": k, "value": v} for k, v in self.SECURITY_HEADERS.items()
                ] + [{"key": "Cache-Control", "value": self.CACHE_RULES["html"]}]
            },
        ]
        rewrites = [{"source": "/((?!api/).*)", "destination": "/index.html"}]
        redirects = [
            {"source": "/index.html", "destination": "/", "permanent": True},
            {"source": "/:path*/", "destination": "/:path*", "permanent": True},
        ]
        config: Dict[str, Any] = {
            "version": 2,
            "framework": "vite",
            "buildCommand": "npm run build",
            "outputDirectory": "dist",
            "headers": headers,
            "rewrites": rewrites,
            "redirects": redirects,
            "regions": regions,
            "env": {
                "NODE_ENV": "production",
            },
            "functions": {
                "api/**": {
                    "memory": 512,
                    "maxDuration": 30,
                    "regions": regions,
                }
            } if has_api else {},
            "github": {
                "autoAlias": True,
                "silent": False,
            },
        }
        return config

    def _build_netlify(self, spec, has_api):
        lines = [
            "# Netlify Configuration",
            "",
            "[build]",
            '  command   = "npm run build"',
            '  publish   = "dist"',
            "",
            "[build.environment]",
            '  NODE_VERSION = "20"',
            '  NPM_VERSION  = "10"',
            "",
            "[[plugins]]",
            '  package = "@netlify/plugin-lighthouse"',
            "  [plugins.inputs]",
            '    output_path = "reports/lighthouse.html"',
            "",
            "[[headers]]",
            '  for = "/*"',
            "  [headers.values]",
        ]
        for k, v in self.SECURITY_HEADERS.items():
            lines.append(f'    {k} = "{v}"')
        lines += [
            "",
            "[[headers]]",
            '  for = "/assets/*"',
            "  [headers.values]",
            f'    Cache-Control = "{self.CACHE_RULES["hashed_assets"]}"',
            "",
            "[[redirects]]",
            '  from   = "/*"',
            '  to     = "/index.html"',
            "  status = 200",
            "",
            "[[redirects]]",
            '  from   = "/api/*"',
            '  to     = ":splat"',
            "  status = 200",
            '  force  = true',
        ]
        return "\n".join(lines)

    def _build_headers_file(self, has_api: bool = True):
        """Cloudflare Pages / Netlify _headers format."""
        lines = ["# Security & Cache Headers", "# Auto-generated — do not edit manually", ""]
        lines.append("/*")
        for k, v in self.SECURITY_HEADERS.items():
            lines.append(f"  {k}: {v}")
        lines += ["", "/assets/*", f"  Cache-Control: {self.CACHE_RULES['hashed_assets']}", ""]
        lines += ["/*.html", f"  Cache-Control: {self.CACHE_RULES['html']}", ""]
        if has_api:
            lines += ["/api/*", f"  Cache-Control: {self.CACHE_RULES['api']}", ""]
        return "\n".join(lines)

    def _build_redirects(self, has_api: bool = True):
        lines = [
            "# SPA routing — Netlify/Cloudflare Pages",
        ]
        if has_api:
            lines.append("/api/*  https://api.yourdomain.com/:splat  200")
        lines.append("/*      /index.html                         200")
        return "\n".join(lines)

    def _build_nginx(self, spec):
        project = spec.get("project_name", "project")
        return f"""# Nginx Configuration — {project}

user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {{
  worker_connections 4096;
  multi_accept on;
  use epoll;
}}

http {{
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  # Performance
  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;
  keepalive_timeout 65;
  types_hash_max_size 2048;
  server_tokens off;

  # Gzip
  gzip on;
  gzip_vary on;
  gzip_proxied any;
  gzip_comp_level 6;
  gzip_types text/plain text/css text/xml text/javascript
             application/json application/javascript application/xml+rss
             application/atom+xml image/svg+xml;

  # Brotli (requires ngx_brotli module)
  # brotli on;
  # brotli_comp_level 6;
  # brotli_types text/plain text/css application/json application/javascript;

  # Rate limiting zones
  limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
  limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

  # Logging
  log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                  '$status $body_bytes_sent "$http_referer" '
                  '"$http_user_agent" "$http_x_forwarded_for"';
  access_log /var/log/nginx/access.log main;

  server {{
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://$host$request_uri;
  }}

  server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    root /var/www/html/dist;
    index index.html;

    # TLS
    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "{self.SECURITY_HEADERS['Strict-Transport-Security']}" always;
    add_header X-Content-Type-Options    "{self.SECURITY_HEADERS['X-Content-Type-Options']}" always;
    add_header X-Frame-Options           "{self.SECURITY_HEADERS['X-Frame-Options']}" always;
    add_header Referrer-Policy           "{self.SECURITY_HEADERS['Referrer-Policy']}" always;
    add_header Permissions-Policy        "{self.SECURITY_HEADERS['Permissions-Policy']}" always;

    # SPA routing
    location / {{
      try_files $uri $uri/ /index.html;
      add_header Cache-Control "{self.CACHE_RULES['html']}";
    }}

    # Hashed assets — long cache
    location ~* \\.([0-9a-f]{{8}})\\.(js|css)$ {{
      add_header Cache-Control "{self.CACHE_RULES['hashed_assets']}";
      access_log off;
    }}

    # Images
    location ~* \\.(jpg|jpeg|png|webp|avif|gif|svg|ico)$ {{
      add_header Cache-Control "{self.CACHE_RULES['images']}";
      access_log off;
    }}

    # Fonts
    location ~* \\.(woff2?|ttf|eot)$ {{
      add_header Cache-Control "{self.CACHE_RULES['fonts']}";
      add_header Access-Control-Allow-Origin "*";
      access_log off;
    }}

    # API proxy
    location /api/ {{
      limit_req zone=api burst=20 nodelay;
      proxy_pass         http://backend:5000;
      proxy_http_version 1.1;
      proxy_set_header   Upgrade $http_upgrade;
      proxy_set_header   Connection 'upgrade';
      proxy_set_header   Host $host;
      proxy_set_header   X-Real-IP $remote_addr;
      proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header   X-Forwarded-Proto $scheme;
      proxy_cache_bypass $http_upgrade;
      add_header         Cache-Control "{self.CACHE_RULES['api']}";
    }}

    # Rate limit login
    location /api/auth/login {{
      limit_req zone=login burst=3 nodelay;
      proxy_pass http://backend:5000;
    }}

    # Block hidden files
    location ~ /\\. {{
      deny all;
      access_log off;
    }}
  }}
}}
"""

    def _build_cloudflare_rules(self, spec):
        return {
            "comment": "Cloudflare Cache Rules — edge caching tuned for the site",
            "rules": [
                {
                    "description": "Cache static assets 1 year",
                    "expression": '(http.request.uri.path matches "^/assets/.*\\.(js|css|woff2|ttf)$")',
                    "action": "cache",
                    "action_parameters": {
                        "cache": True,
                        "edge_ttl": {"mode": "override_origin", "default": 31536000},
                        "browser_ttl": {"mode": "override_origin", "default": 31536000},
                    }
                },
                {
                    "description": "Cache images 30 days",
                    "expression": '(http.request.uri.path matches ".*\\.(jpg|jpeg|png|webp|avif|gif|svg|ico)$")',
                    "action": "cache",
                    "action_parameters": {
                        "cache": True,
                        "edge_ttl": {"mode": "override_origin", "default": 2592000},
                    }
                },
                {
                    "description": "Bypass cache for API",
                    "expression": '(http.request.uri.path starts_with "/api/")',
                    "action": "bypass_cache",
                },
                {
                    "description": "Security headers on all responses",
                    "expression": '(http.request.uri.path matches ".*")',
                    "action": "rewrite",
                    "action_parameters": {
                        "headers": {h: {"operation": "set", "value": v} for h, v in list(self.SECURITY_HEADERS.items())[:4]}
                    }
                },
            ],
            "security": {
                "bot_fight_mode": True,
                "browser_integrity_check": True,
                "ddos_protection": "high",
                "waf_managed_rules": ["OWASP Core Rule Set", "Cloudflare OWASP Core"],
                "rate_limiting": [
                    {"name": "API Rate Limit", "path": "/api/*", "requests": 100, "period": 60, "action": "block"},
                    {"name": "Auth Rate Limit", "path": "/api/auth/*", "requests": 10, "period": 60, "action": "challenge"},
                ],
            }
        }

    def _build_cdn_md(self, spec, region):
        regions = self.VERCEL_REGIONS_BY_REGION.get(region, self.VERCEL_REGIONS_GLOBAL)
        lines = [
            f"# CDN & Deployment Configuration — {spec.get('project_name', 'Project')}",
            "\n## Quick Deploy\n",
            "### Vercel (Recommended)\n```bash",
            "npm i -g vercel",
            "vercel --prod",
            "```",
            "\n### Netlify\n```bash",
            "npm i -g netlify-cli",
            "netlify deploy --prod --dir=dist",
            "```",
            "\n### Docker + Nginx\n```bash",
            "docker-compose -f docker-compose.prod.yml up -d --build",
            "```",
            "\n## Edge Regions\n",
            f"Configured for: **{', '.join(regions)}**",
            "\n## Security Headers Configured\n",
        ]
        for h, v in self.SECURITY_HEADERS.items():
            lines.append(f"- `{h}`: `{v[:60]}{'...' if len(v)>60 else ''}`")
        lines += [
            "\n## Cache Strategy\n",
            "| Resource Type | Cache Control |",
            "|--------------|---------------|",
        ]
        for rtype, cc in self.CACHE_RULES.items():
            lines.append(f"| {rtype} | `{cc[:60]}` |")
        lines += [
            "\n## Post-Deploy Checklist\n",
            "- [ ] Verify SSL certificate is valid",
            "- [ ] Test security headers at securityheaders.com",
            "- [ ] Run Lighthouse from external network",
            "- [ ] Verify CDN caching with `curl -I https://yourdomain.com/assets/*.js`",
            "- [ ] Set up uptime monitoring (Better Uptime / UptimeRobot)",
            "- [ ] Enable Cloudflare WAF if using Cloudflare",
        ]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"CDNOptimizer: Could not write {path}: {e}")
