"""
A/B Testing Engine — LumicorePro AI Agent
==========================================
Phase 14 — Global Growth

Generates A/B test configurations, feature flags, and experiment scaffolding:
  - Experiment definitions per website type (hero, CTA, pricing, checkout)
  - PostHog feature flags config
  - GrowthBook experiment JSON
  - React useFeatureFlag hook + A/B test wrapper component
  - Analytics event tracking for experiment variants
  - EXPERIMENTS.md documentation

Industry-calibrated: which tests give highest ROI per website type.
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class ABTestingEngine:
    """A/B testing framework generator for global conversion optimization."""

    # ── High-ROI experiments per website type ─────────────────────────────
    EXPERIMENTS: Dict[str, List[Dict[str, Any]]] = {
        "ecommerce": [
            {
                "id": "hero_cta_text",
                "name": "Hero CTA Button Text",
                "hypothesis": "Changing CTA from 'Shop Now' to 'Explore Collection' increases CTR by 15%",
                "metric": "cta_click_rate",
                "variants": [
                    {"id": "control",   "name": "Shop Now",          "weight": 0.5},
                    {"id": "variant_a", "name": "Explore Collection", "weight": 0.5},
                ],
                "min_sample": 1000, "expected_lift": "12-18%", "priority": "high",
            },
            {
                "id": "product_card_layout",
                "name": "Product Card Layout",
                "hypothesis": "Grid view vs list view — grid increases add-to-cart by 22%",
                "metric": "add_to_cart_rate",
                "variants": [
                    {"id": "control",   "name": "Grid 4-col",  "weight": 0.5},
                    {"id": "variant_a", "name": "Grid 3-col",  "weight": 0.25},
                    {"id": "variant_b", "name": "List view",   "weight": 0.25},
                ],
                "min_sample": 2000, "expected_lift": "10-25%", "priority": "high",
            },
            {
                "id": "checkout_steps",
                "name": "Checkout Flow Steps",
                "hypothesis": "Single-page checkout reduces abandonment by 30% vs multi-step",
                "metric": "checkout_completion_rate",
                "variants": [
                    {"id": "control",   "name": "Multi-step (3 pages)", "weight": 0.5},
                    {"id": "variant_a", "name": "Single page",          "weight": 0.5},
                ],
                "min_sample": 500, "expected_lift": "20-35%", "priority": "critical",
            },
            {
                "id": "trust_badges",
                "name": "Trust Badge Placement",
                "hypothesis": "Moving trust badges near checkout button increases conversions",
                "metric": "purchase_rate",
                "variants": [
                    {"id": "control",   "name": "Footer only",          "weight": 0.5},
                    {"id": "variant_a", "name": "Near add-to-cart btn", "weight": 0.5},
                ],
                "min_sample": 800, "expected_lift": "5-12%", "priority": "medium",
            },
        ],
        "saas": [
            {
                "id": "pricing_page_layout",
                "name": "Pricing Page Highlight",
                "hypothesis": "Highlighting 'Pro' plan increases Pro signups by 25%",
                "metric": "plan_selection_rate",
                "variants": [
                    {"id": "control",   "name": "All plans equal",    "weight": 0.5},
                    {"id": "variant_a", "name": "Pro plan highlighted","weight": 0.5},
                ],
                "min_sample": 300, "expected_lift": "18-30%", "priority": "critical",
            },
            {
                "id": "cta_trial_copy",
                "name": "Free Trial CTA Copy",
                "hypothesis": "'Start free trial' vs 'Get started free' — testing urgency",
                "metric": "signup_rate",
                "variants": [
                    {"id": "control",   "name": "Start free trial",  "weight": 0.33},
                    {"id": "variant_a", "name": "Get started free",  "weight": 0.33},
                    {"id": "variant_b", "name": "Try free for 14 days","weight":0.34},
                ],
                "min_sample": 500, "expected_lift": "8-20%", "priority": "high",
            },
            {
                "id": "social_proof_position",
                "name": "Social Proof Placement",
                "hypothesis": "Testimonials above fold vs below — above increases signups",
                "metric": "signup_rate",
                "variants": [
                    {"id": "control",   "name": "Below hero",  "weight": 0.5},
                    {"id": "variant_a", "name": "In hero section","weight": 0.5},
                ],
                "min_sample": 400, "expected_lift": "10-15%", "priority": "medium",
            },
        ],
        "restaurant": [
            {
                "id": "menu_display",
                "name": "Menu Display Format",
                "hypothesis": "Photo-first menu vs text-first — photos increase avg order value",
                "metric": "average_order_value",
                "variants": [
                    {"id": "control",   "name": "Text with small photos", "weight": 0.5},
                    {"id": "variant_a", "name": "Large photo cards",       "weight": 0.5},
                ],
                "min_sample": 300, "expected_lift": "15-25%", "priority": "high",
            },
            {
                "id": "order_cta",
                "name": "Order Button Colour",
                "hypothesis": "Green vs orange CTA button — orange increases tap rate on mobile",
                "metric": "order_button_click",
                "variants": [
                    {"id": "control",   "name": "Green",  "weight": 0.5},
                    {"id": "variant_a", "name": "Orange", "weight": 0.5},
                ],
                "min_sample": 200, "expected_lift": "5-12%", "priority": "medium",
            },
        ],
        "healthcare": [
            {
                "id": "booking_form_length",
                "name": "Appointment Booking Form",
                "hypothesis": "Shorter form (3 fields) vs full form (8 fields) increases bookings",
                "metric": "appointment_booking_rate",
                "variants": [
                    {"id": "control",   "name": "Full form (8 fields)",   "weight": 0.5},
                    {"id": "variant_a", "name": "Short form (3 fields)",  "weight": 0.5},
                ],
                "min_sample": 200, "expected_lift": "25-40%", "priority": "critical",
            },
        ],
        "default": [
            {
                "id": "hero_headline",
                "name": "Hero Headline Copy",
                "hypothesis": "Benefit-focused headline outperforms feature-focused",
                "metric": "scroll_depth",
                "variants": [
                    {"id": "control",   "name": "Feature-focused", "weight": 0.5},
                    {"id": "variant_a", "name": "Benefit-focused",  "weight": 0.5},
                ],
                "min_sample": 500, "expected_lift": "10-20%", "priority": "high",
            },
            {
                "id": "contact_form_cta",
                "name": "Contact Form CTA",
                "hypothesis": "'Send Message' vs 'Get Free Consultation' increases submissions",
                "metric": "form_submission_rate",
                "variants": [
                    {"id": "control",   "name": "Send Message",         "weight": 0.5},
                    {"id": "variant_a", "name": "Get Free Consultation","weight": 0.5},
                ],
                "min_sample": 200, "expected_lift": "15-30%", "priority": "high",
            },
        ],
    }

    # ── Feature flags ─────────────────────────────────────────────────────
    FEATURE_FLAGS: Dict[str, List[Dict[str, Any]]] = {
        "ecommerce": [
            {"key": "show_ai_recommendations",  "description": "AI product recommendations widget",    "default": False, "rollout": 20},
            {"key": "one_click_checkout",        "description": "One-click checkout for returning users","default": False, "rollout": 10},
            {"key": "live_inventory_counter",    "description": "Show live stock countdown",            "default": True,  "rollout": 100},
            {"key": "social_proof_notifications","description": "Live purchase notifications popup",    "default": False, "rollout": 50},
        ],
        "saas": [
            {"key": "new_onboarding_flow",       "description": "Redesigned onboarding wizard",         "default": False, "rollout": 25},
            {"key": "ai_assistant",              "description": "In-app AI assistant",                  "default": False, "rollout": 5},
            {"key": "advanced_analytics",        "description": "Advanced analytics dashboard beta",    "default": False, "rollout": 15},
        ],
        "default": [
            {"key": "dark_mode",                 "description": "Dark mode toggle",                     "default": False, "rollout": 100},
            {"key": "newsletter_popup",          "description": "Newsletter signup popup",              "default": True,  "rollout": 80},
            {"key": "chat_widget",               "description": "Live chat widget",                     "default": False, "rollout": 50},
        ],
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate A/B test configs and feature flag scaffolding."""
        agent_logger.info("ABTestingEngine: Generating A/B tests and feature flags...")

        website_type = spec.get("website_type", "default")
        experiments  = self.EXPERIMENTS.get(website_type, self.EXPERIMENTS["default"])
        flags        = self.FEATURE_FLAGS.get(website_type, self.FEATURE_FLAGS["default"])
        artifacts    = []

        config_dir = os.path.join(project_dir, "frontend", "src", "config")
        os.makedirs(config_dir, exist_ok=True)

        # 1. experiments.json — GrowthBook / PostHog compatible
        exp_path = os.path.join(config_dir, "experiments.json")
        self._write(exp_path, json.dumps({"experiments": experiments}, indent=2))
        artifacts.append(exp_path)

        # 2. feature-flags.json
        ff_path = os.path.join(config_dir, "feature-flags.json")
        self._write(ff_path, json.dumps({"flags": flags}, indent=2))
        artifacts.append(ff_path)

        # 3. useExperiment.js — React hook
        hook_dir = os.path.join(project_dir, "frontend", "src", "hooks")
        os.makedirs(hook_dir, exist_ok=True)
        hook_path = os.path.join(hook_dir, "useExperiment.js")
        self._write(hook_path, self._build_react_hook(experiments, flags))
        artifacts.append(hook_path)

        # 4. ABTest.jsx — wrapper component
        comp_dir = os.path.join(project_dir, "frontend", "src", "components", "common")
        os.makedirs(comp_dir, exist_ok=True)
        comp_path = os.path.join(comp_dir, "ABTest.jsx")
        self._write(comp_path, self._build_ab_component())
        artifacts.append(comp_path)

        # 5. posthog-config.js
        ph_path = os.path.join(config_dir, "posthog-config.js")
        self._write(ph_path, self._build_posthog_config(experiments))
        artifacts.append(ph_path)

        # 6. EXPERIMENTS.md
        md_path = os.path.join(project_dir, "EXPERIMENTS.md")
        self._write(md_path, self._build_experiments_md(experiments, flags, website_type))
        artifacts.append(md_path)

        result = {
            "experiments_defined": len(experiments),
            "total_experiments": len(experiments),
            "feature_flags":       len(flags),
            "artifacts":           artifacts,
            "high_priority_tests": [e["id"] for e in experiments if e.get("priority") in ("critical", "high")],
            "total_expected_lift": f"{sum(int(e.get('expected_lift','0-0').split('-')[0].replace('%','').strip() or 0) for e in experiments)}%+ across all tests",
        }
        agent_logger.info(
            f"ABTestingEngine: {len(experiments)} experiments, "
            f"{len(flags)} feature flags."
        )
        return result

    def _build_react_hook(self, experiments, flags):
        exp_ids = json.dumps([e["id"] for e in experiments])
        flag_keys = json.dumps([f["key"] for f in flags])
        return f"""/**
 * useExperiment — A/B Testing & Feature Flags Hook
 * Auto-generated for A/B testing & feature flagging
 *
 * Usage:
 *   const variant = useExperiment('hero_cta_text');
 *   const isEnabled = useFeatureFlag('show_ai_recommendations');
 */

import {{ useState, useEffect, useCallback }} from 'react';

// Experiment IDs for this project
export const EXPERIMENT_IDS = {exp_ids};
export const FEATURE_FLAG_KEYS = {flag_keys};

// Storage key for consistent variant assignment
const STORAGE_KEY = 'lumicore_experiments';

function getStoredVariants() {{
  try {{
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
  }} catch {{ return {{}}; }}
}}

function assignVariant(experimentId, variants) {{
  const stored = getStoredVariants();
  if (stored[experimentId]) return stored[experimentId];

  // Weighted random assignment
  const rand = Math.random();
  let cumulative = 0;
  for (const v of variants) {{
    cumulative += v.weight;
    if (rand < cumulative) {{
      stored[experimentId] = v.id;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
      return v.id;
    }}
  }}
  return variants[0].id;
}}

/**
 * Returns assigned variant id for an experiment
 * @param {{string}} experimentId
 * @param {{Array}} variants  — [{{id, name, weight}}]
 */
export function useExperiment(experimentId, variants = []) {{
  const [variant, setVariant] = useState(() => {{
    if (!variants.length) return 'control';
    return assignVariant(experimentId, variants);
  }});

  useEffect(() => {{
    // Track experiment exposure
    if (window.__posthog) {{
      window.__posthog.capture('$experiment_started', {{
        experiment: experimentId,
        variant,
      }});
    }}
    if (window.gtag) {{
      window.gtag('event', 'experiment_impression', {{
        experiment_id: experimentId,
        variant_id: variant,
      }});
    }}
  }}, [experimentId, variant]);

  return variant;
}}

/**
 * Returns boolean for a feature flag
 * @param {{string}} flagKey
 * @param {{boolean}} defaultValue
 */
export function useFeatureFlag(flagKey, defaultValue = false) {{
  const [enabled, setEnabled] = useState(defaultValue);

  useEffect(() => {{
    // Check PostHog feature flag
    if (window.__posthog?.isFeatureEnabled) {{
      const isEnabled = window.__posthog.isFeatureEnabled(flagKey);
      if (isEnabled !== undefined) setEnabled(isEnabled);
    }}
  }}, [flagKey]);

  return enabled;
}}

export default useExperiment;
"""

    def _build_ab_component(self):
        return """/**
 * ABTest — Declarative A/B Test Wrapper Component
 * Auto-generated for A/B testing & feature flagging
 *
 * Usage:
 *   <ABTest
 *     experimentId="hero_cta_text"
 *     variants={[
 *       { id: 'control',   weight: 0.5, children: <Button>Shop Now</Button> },
 *       { id: 'variant_a', weight: 0.5, children: <Button>Explore</Button> },
 *     ]}
 *   />
 */

import { useExperiment } from '@/hooks/useExperiment';

export default function ABTest({ experimentId, variants = [], fallback = null }) {
  const assignedVariant = useExperiment(
    experimentId,
    variants.map(({ id, weight }) => ({ id, weight }))
  );

  const match = variants.find((v) => v.id === assignedVariant);
  return match?.children ?? fallback ?? null;
}

/**
 * FeatureFlag — Conditional render based on feature flag
 *
 * Usage:
 *   <FeatureFlag flag="show_ai_recommendations">
 *     <AIRecommendations />
 *   </FeatureFlag>
 */
export function FeatureFlag({ flag, defaultValue = false, children, fallback = null }) {
  const { useFeatureFlag } = require('@/hooks/useExperiment');
  const enabled = useFeatureFlag(flag, defaultValue);
  return enabled ? children : fallback;
}
"""

    def _build_posthog_config(self, experiments):
        exp_list = json.dumps([{"id": e["id"], "name": e["name"]} for e in experiments], indent=2)
        return f"""/**
 * PostHog Analytics + Feature Flags Config
 * Auto-generated for A/B testing & feature flagging
 *
 * Setup: npm install posthog-js
 * Add VITE_POSTHOG_KEY=phc_xxx to .env
 */

export const POSTHOG_CONFIG = {{
  apiKey:    import.meta.env.VITE_POSTHOG_KEY || '',
  apiHost:   import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
  options: {{
    autocapture:           true,
    capture_pageview:      true,
    capture_pageleave:     true,
    disable_session_recording: false,
    enable_recording_console_log: false,
    bootstrap: {{
      featureFlags: {{}},
    }},
  }},
}};

// Registered experiments for this project
export const REGISTERED_EXPERIMENTS = {exp_list};

// Initialize PostHog
export function initPostHog() {{
  if (!POSTHOG_CONFIG.apiKey) return;
  import('posthog-js').then(({{ default: posthog }}) => {{
    posthog.init(POSTHOG_CONFIG.apiKey, POSTHOG_CONFIG.options);
    window.__posthog = posthog;
    console.log('[PostHog] Initialized');
  }});
}}
"""

    def _build_experiments_md(self, experiments, flags, website_type):
        lines = [
            f"# A/B Testing & Feature Flags — {website_type.title()} Website",
            "\n## Experiments\n",
            "| ID | Name | Priority | Min Sample | Expected Lift |",
            "|----|------|----------|------------|---------------|",
        ]
        for e in experiments:
            lines.append(f"| `{e['id']}` | {e['name']} | {e.get('priority','medium')} | {e['min_sample']} | {e.get('expected_lift','N/A')} |")
        lines += ["\n### Experiment Details\n"]
        for e in experiments:
            lines += [
                f"#### {e['name']} (`{e['id']}`)",
                f"**Hypothesis:** {e['hypothesis']}",
                f"**Success Metric:** `{e['metric']}`",
                "**Variants:**",
            ]
            for v in e["variants"]:
                lines.append(f"  - `{v['id']}`: {v['name']} ({int(v['weight']*100)}% traffic)")
            lines.append("")
        lines += ["\n## Feature Flags\n",
                  "| Key | Description | Default | Rollout % |",
                  "|-----|-------------|---------|-----------|"]
        for f in flags:
            lines.append(f"| `{f['key']}` | {f['description']} | {f['default']} | {f['rollout']}% |")
        lines += ["\n## Implementation Guide\n",
                  "1. Install PostHog: `npm install posthog-js`",
                  "2. Add `VITE_POSTHOG_KEY=phc_xxx` to `.env`",
                  "3. Call `initPostHog()` in `main.jsx`",
                  "4. Use `useExperiment('hero_cta_text', variants)` hook in components",
                  "5. Monitor results in PostHog Experiments dashboard",
                  "\n> Run each experiment for minimum 2 weeks for statistical significance."]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"ABTestingEngine: Could not write {path}: {e}")
