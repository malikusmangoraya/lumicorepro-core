"""
Performance Budget Engine — LumicorePro AI Agent
=================================================
Phase 13 — Global Performance

Generates:
  - Core Web Vitals budgets per website type (LCP, CLS, FID/INP, TTFB)
  - Lighthouse CI config (lighthouserc.json) with per-category thresholds
  - Budget.json for webpack/vite bundle size limits
  - Preload/preconnect hints for critical resources
  - Image optimization checklist
  - PERFORMANCE.md report
  - Vite build config optimizations (code splitting, chunk strategy)
  - Service Worker cache strategy per resource type

Industry-calibrated targets based on 2025/2026 real-world benchmarks.
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class PerformanceBudgetEngine:
    """Core Web Vitals & Lighthouse CI budget generator for global performance."""

    # ── Per-type performance targets ──────────────────────────────────────
    # Based on Google's "Good" CWV thresholds + industry competitive baselines
    TARGETS: Dict[str, Dict[str, Any]] = {
        "ecommerce": {
            "lcp_ms":   2000,   # Largest Contentful Paint
            "cls":      0.05,   # Cumulative Layout Shift
            "inp_ms":   150,    # Interaction to Next Paint (replaces FID)
            "ttfb_ms":  600,    # Time to First Byte
            "fcp_ms":   1200,   # First Contentful Paint
            "tbt_ms":   200,    # Total Blocking Time
            "lighthouse": {"performance": 92, "accessibility": 90, "best_practices": 90, "seo": 92},
            "bundle_kb": {"js": 250, "css": 60, "total": 400},
            "note": "E-commerce: every 100ms delay = ~1% conversion loss",
        },
        "saas": {
            "lcp_ms":   2500, "cls": 0.05, "inp_ms": 150, "ttfb_ms": 600,
            "fcp_ms":   1500, "tbt_ms": 200,
            "lighthouse": {"performance": 90, "accessibility": 92, "best_practices": 93, "seo": 90},
            "bundle_kb": {"js": 300, "css": 70, "total": 500},
            "note": "SaaS: dashboard routes can lazy-load; landing must be fast",
        },
        "restaurant": {
            "lcp_ms":   2000, "cls": 0.08, "inp_ms": 200, "ttfb_ms": 800,
            "fcp_ms":   1500, "tbt_ms": 300,
            "lighthouse": {"performance": 88, "accessibility": 90, "best_practices": 88, "seo": 90},
            "bundle_kb": {"js": 200, "css": 50, "total": 350},
            "note": "Restaurant: 88% mobile visitors — optimize images aggressively",
        },
        "healthcare": {
            "lcp_ms":   2500, "cls": 0.05, "inp_ms": 150, "ttfb_ms": 600,
            "fcp_ms":   1500, "tbt_ms": 200,
            "lighthouse": {"performance": 90, "accessibility": 95, "best_practices": 92, "seo": 90},
            "bundle_kb": {"js": 220, "css": 55, "total": 380},
            "note": "Healthcare: accessibility target 95 — WCAG AAA recommended",
        },
        "fintech": {
            "lcp_ms":   2000, "cls": 0.03, "inp_ms": 100, "ttfb_ms": 400,
            "fcp_ms":   1000, "tbt_ms": 150,
            "lighthouse": {"performance": 95, "accessibility": 92, "best_practices": 95, "seo": 90},
            "bundle_kb": {"js": 280, "css": 60, "total": 450},
            "note": "Fintech: near-zero CLS required — layout shifts destroy trust",
        },
        "portfolio": {
            "lcp_ms":   2000, "cls": 0.05, "inp_ms": 200, "ttfb_ms": 600,
            "fcp_ms":   1200, "tbt_ms": 150,
            "lighthouse": {"performance": 95, "accessibility": 90, "best_practices": 92, "seo": 90},
            "bundle_kb": {"js": 180, "css": 40, "total": 300},
            "note": "Portfolio: Lighthouse score IS your portfolio — aim for 100",
        },
        "education": {
            "lcp_ms":   2500, "cls": 0.08, "inp_ms": 200, "ttfb_ms": 800,
            "fcp_ms":   1500, "tbt_ms": 300,
            "lighthouse": {"performance": 88, "accessibility": 92, "best_practices": 90, "seo": 90},
            "bundle_kb": {"js": 300, "css": 70, "total": 500},
            "note": "Education: video assets — use lazy loading + HLS streaming",
        },
        "default": {
            "lcp_ms":   2500, "cls": 0.10, "inp_ms": 200, "ttfb_ms": 800,
            "fcp_ms":   1800, "tbt_ms": 300,
            "lighthouse": {"performance": 88, "accessibility": 88, "best_practices": 88, "seo": 88},
            "bundle_kb": {"js": 250, "css": 60, "total": 400},
            "note": "Good baseline — tune per industry after launch",
        },
    }

    # ── Cache strategy per resource type ──────────────────────────────────
    CACHE_STRATEGY: Dict[str, Dict[str, Any]] = {
        "html":       {"strategy": "network-first",  "maxAge": 0,        "desc": "Always fresh HTML"},
        "css":        {"strategy": "cache-first",    "maxAge": 31536000, "desc": "1 year — hash in filename"},
        "js":         {"strategy": "cache-first",    "maxAge": 31536000, "desc": "1 year — hash in filename"},
        "images":     {"strategy": "cache-first",    "maxAge": 2592000,  "desc": "30 days"},
        "fonts":      {"strategy": "cache-first",    "maxAge": 31536000, "desc": "1 year"},
        "api":        {"strategy": "network-first",  "maxAge": 300,      "desc": "5 min stale-while-revalidate"},
        "static":     {"strategy": "cache-first",    "maxAge": 86400,    "desc": "24 hours"},
    }

    # ── Critical preconnect origins per stack ─────────────────────────────
    PRECONNECT_ORIGINS: Dict[str, List[str]] = {
        "stripe":     ["https://js.stripe.com", "https://api.stripe.com"],
        "google":     ["https://fonts.googleapis.com", "https://fonts.gstatic.com",
                       "https://www.googletagmanager.com"],
        "cloudflare": ["https://cdnjs.cloudflare.com"],
        "firebase":   ["https://firebasestorage.googleapis.com"],
        "sentry":     ["https://sentry.io"],
        "intercom":   ["https://widget.intercom.io", "https://api.intercom.io"],
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate all performance budget artifacts."""
        agent_logger.info("PerformanceBudgetEngine: Generating Core Web Vitals budgets...")

        website_type = spec.get("website_type", "default")
        targets = self.TARGETS.get(website_type, self.TARGETS["default"])
        features = spec.get("features", [])

        # Determine preconnect origins needed
        preconnects = list(self.PRECONNECT_ORIGINS.get("google", []))
        if any(f in features for f in ["payment", "stripe", "checkout"]):
            preconnects += self.PRECONNECT_ORIGINS["stripe"]
        if "sentry" in str(spec).lower():
            preconnects += self.PRECONNECT_ORIGINS["sentry"]

        artifacts = []
        root = project_dir
        frontend = os.path.join(project_dir, "frontend")
        os.makedirs(frontend, exist_ok=True)

        # 1. lighthouserc.json
        lhrc_path = os.path.join(root, ".lighthouserc.json")
        self._write(lhrc_path, json.dumps(self._build_lhrc(targets, spec), indent=2))
        artifacts.append(lhrc_path)

        # 2. budget.json (webpack / vite-bundle-analyzer)
        budget_path = os.path.join(frontend, "budget.json")
        self._write(budget_path, json.dumps(self._build_budget_json(targets), indent=2))
        artifacts.append(budget_path)

        # 3. vite.config.performance.js — optimized vite config fragment
        vite_perf_path = os.path.join(frontend, "vite.config.performance.js")
        self._write(vite_perf_path, self._build_vite_config(targets, website_type))
        artifacts.append(vite_perf_path)

        # 4. sw-cache-strategy.js — Service Worker cache config
        sw_path = os.path.join(frontend, "src", "sw-cache-strategy.js")
        os.makedirs(os.path.dirname(sw_path), exist_ok=True)
        self._write(sw_path, self._build_sw_config())
        artifacts.append(sw_path)

        # 5. PERFORMANCE.md
        perf_md_path = os.path.join(root, "PERFORMANCE.md")
        self._write(perf_md_path, self._build_perf_md(targets, website_type, preconnects))
        artifacts.append(perf_md_path)

        result = {
            "website_type":    website_type,
            "targets":         targets,
            "preconnects":     preconnects,
            "cache_strategies": self.CACHE_STRATEGY,
            "artifacts":       artifacts,
            "lighthouse_targets": targets["lighthouse"],
            "bundle_budget_kb":  targets["bundle_kb"],
            "cwv_targets": {
                "lcp_ms":  targets["lcp_ms"],
                "cls":     targets["cls"],
                "inp_ms":  targets["inp_ms"],
                "ttfb_ms": targets["ttfb_ms"],
            },
        }
        agent_logger.info(
            f"PerformanceBudgetEngine: LCP<{targets['lcp_ms']}ms, "
            f"CLS<{targets['cls']}, Lighthouse perf≥{targets['lighthouse']['performance']}"
        )
        return result

    def _build_lhrc(self, targets, spec):
        lh = targets["lighthouse"]
        return {
            "ci": {
                "collect": {
                    "numberOfRuns": 3,
                    "startServerCommand": "npm run preview",
                    "url": ["http://localhost:4173"],
                },
                "assert": {
                    "assertions": {
                        "categories:performance":     ["error", {"minScore": lh["performance"] / 100}],
                        "categories:accessibility":   ["error", {"minScore": lh["accessibility"] / 100}],
                        "categories:best-practices":  ["error", {"minScore": lh["best_practices"] / 100}],
                        "categories:seo":             ["error", {"minScore": lh["seo"] / 100}],
                        "first-contentful-paint":     ["warn",  {"maxNumericValue": targets["fcp_ms"]}],
                        "largest-contentful-paint":   ["error", {"maxNumericValue": targets["lcp_ms"]}],
                        "total-blocking-time":        ["warn",  {"maxNumericValue": targets["tbt_ms"]}],
                        "cumulative-layout-shift":    ["error", {"maxNumericValue": targets["cls"]}],
                        "interactive":                ["warn",  {"maxNumericValue": targets["inp_ms"] * 10}],
                    }
                },
                "upload": {"target": "temporary-public-storage"},
            }
        }

    def _build_budget_json(self, targets):
        kb = targets["bundle_kb"]
        return [
            {
                "resourceSizes": [
                    {"resourceType": "script",     "budget": kb["js"]},
                    {"resourceType": "stylesheet",  "budget": kb["css"]},
                    {"resourceType": "total",       "budget": kb["total"]},
                    {"resourceType": "image",       "budget": 500},
                    {"resourceType": "font",        "budget": 100},
                ],
                "resourceCounts": [
                    {"resourceType": "third-party", "budget": 10},
                    {"resourceType": "script",      "budget": 20},
                ],
                "timings": [
                    {"metric": "interactive",              "budget": 3500},
                    {"metric": "first-contentful-paint",   "budget": 2000},
                    {"metric": "largest-contentful-paint", "budget": 2500},
                ]
            }
        ]

    def _build_vite_config(self, targets, website_type):
        return f"""/**
 * Vite Performance Config — {website_type}
 * Merge this into your vite.config.js build section
 * LCP target: <{targets['lcp_ms']}ms | Bundle JS: <{targets['bundle_kb']['js']}KB
 */
export const performanceBuildConfig = {{
  build: {{
    target: 'es2020',
    minify: 'terser',
    terserOptions: {{
      compress: {{ drop_console: true, drop_debugger: true, pure_funcs: ['console.log'] }},
    }},
    rollupOptions: {{
      output: {{
        // Route-based code splitting
        manualChunks(id) {{
          if (id.includes('node_modules')) {{
            // Vendor chunk: react ecosystem
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {{
              return 'vendor-react';
            }}
            // Charts separate chunk
            if (id.includes('recharts') || id.includes('d3')) {{
              return 'vendor-charts';
            }}
            // Animation separate chunk
            if (id.includes('framer-motion') || id.includes('gsap')) {{
              return 'vendor-animation';
            }}
            // Everything else in vendor
            return 'vendor';
          }}
          // Page-level splitting
          if (id.includes('/pages/')) {{
            const page = id.split('/pages/')[1].split('/')[0];
            return `page-${{page}}`;
          }}
        }},
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      }},
    }},
    // Warn if chunks exceed budget
    chunkSizeWarningLimit: {targets['bundle_kb']['js']},
    // Report compressed sizes
    reportCompressedSize: true,
    // Enable source maps for error monitoring
    sourcemap: process.env.NODE_ENV !== 'production',
  }},
  // Image optimization
  assetsInclude: ['**/*.avif', '**/*.webp'],
}};
"""

    def _build_sw_config(self):
        strategies = json.dumps(self.CACHE_STRATEGY, indent=2)
        return f"""/**
 * Service Worker Cache Strategy
 */

export const CACHE_STRATEGIES = {strategies};

export const CACHE_NAME = 'lumicore-v1';
export const OFFLINE_URL = '/offline.html';

/**
 * Get cache strategy for a given request URL
 */
export function getStrategy(url) {{
  if (url.includes('/api/'))   return CACHE_STRATEGIES.api;
  if (url.match(/\\.html$/))   return CACHE_STRATEGIES.html;
  if (url.match(/\\.css$/))    return CACHE_STRATEGIES.css;
  if (url.match(/\\.(js|mjs)$/)) return CACHE_STRATEGIES.js;
  if (url.match(/\\.(png|jpg|jpeg|webp|avif|gif|svg)$/)) return CACHE_STRATEGIES.images;
  if (url.match(/\\.(woff2?|ttf|eot)$/)) return CACHE_STRATEGIES.fonts;
  return CACHE_STRATEGIES.static;
}}
"""

    def _build_perf_md(self, targets, website_type, preconnects):
        lh = targets["lighthouse"]
        kb = targets["bundle_kb"]
        lines = [
            f"# Performance Budget — {website_type.title()} Website",
            "\n## Core Web Vitals Targets\n",
            "| Metric | Target | Google 'Good' Threshold |",
            "|--------|--------|------------------------|",
            f"| LCP (Largest Contentful Paint) | < {targets['lcp_ms']}ms | < 2500ms |",
            f"| CLS (Cumulative Layout Shift)  | < {targets['cls']}   | < 0.10   |",
            f"| INP (Interaction to Next Paint)| < {targets['inp_ms']}ms | < 200ms  |",
            f"| TTFB (Time to First Byte)       | < {targets['ttfb_ms']}ms | < 800ms  |",
            f"| FCP (First Contentful Paint)    | < {targets['fcp_ms']}ms | < 1800ms |",
            f"| TBT (Total Blocking Time)       | < {targets['tbt_ms']}ms | < 300ms  |",
            "\n## Lighthouse Score Targets\n",
            f"- Performance:    ≥ {lh['performance']}",
            f"- Accessibility:  ≥ {lh['accessibility']}",
            f"- Best Practices: ≥ {lh['best_practices']}",
            f"- SEO:            ≥ {lh['seo']}",
            "\n## Bundle Size Budgets\n",
            f"- JavaScript: < {kb['js']} KB (gzipped)",
            f"- CSS:        < {kb['css']} KB (gzipped)",
            f"- Total page: < {kb['total']} KB (gzipped)",
            "\n## Critical Resource Preconnects\n",
        ]
        for origin in preconnects:
            lines.append(f"```html\n<link rel=\"preconnect\" href=\"{origin}\">\n```")
        lines += [
            "\n## Optimization Checklist\n",
            "- [ ] Convert all images to WebP/AVIF format",
            "- [ ] Enable Brotli compression on server",
            "- [ ] Set long cache headers for hashed assets (1 year)",
            "- [ ] Defer non-critical JavaScript",
            "- [ ] Use font-display: swap for web fonts",
            "- [ ] Add width/height to all `<img>` elements",
            "- [ ] Eliminate render-blocking resources",
            "- [ ] Preload LCP image with `<link rel=preload>`",
            "- [ ] Run Lighthouse CI on every PR",
            f"\n> Note: {targets['note']}",
        ]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"PerformanceBudgetEngine: Could not write {path}: {e}")
