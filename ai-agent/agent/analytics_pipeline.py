"""
Analytics Pipeline — LumicorePro AI Agent
==========================================
Phase 14 — Global Analytics

Generates complete analytics infrastructure:
  - GA4 (Google Analytics 4) — events, conversions, audiences
  - PostHog (open-source, self-hostable) — events, session recording
  - Mixpanel — funnel events, user profiles
  - Plausible (privacy-first, EU-compliant) — page views, goals
  - Fathom (cookie-free GDPR alternative)
  - Analytics abstraction layer (provider-agnostic tracking API)
  - Event taxonomy per website type (standardised event names)
  - React useAnalytics hook
  - ANALYTICS.md setup guide
"""

import os
import json
from typing import Dict, Any, List
from utils.logger import agent_logger


class AnalyticsPipeline:
    """Multi-provider analytics config generator for global data insights."""

    # ── Event taxonomy per website type ──────────────────────────────────
    # Following GA4 recommended event naming conventions
    EVENT_TAXONOMY: Dict[str, List[Dict[str, Any]]] = {
        "ecommerce": [
            # GA4 Enhanced Ecommerce standard events
            {"name": "view_item_list",    "trigger": "Products page load",          "params": ["item_list_id", "item_list_name", "items"]},
            {"name": "view_item",         "trigger": "Product detail page load",    "params": ["currency", "value", "items"]},
            {"name": "add_to_cart",       "trigger": "Add to cart button click",    "params": ["currency", "value", "items"]},
            {"name": "remove_from_cart",  "trigger": "Remove from cart",            "params": ["currency", "value", "items"]},
            {"name": "view_cart",         "trigger": "Cart page view",              "params": ["currency", "value", "items"]},
            {"name": "begin_checkout",    "trigger": "Checkout step 1",             "params": ["currency", "value", "coupon", "items"]},
            {"name": "add_payment_info",  "trigger": "Payment info entered",        "params": ["currency", "value", "payment_type", "items"]},
            {"name": "purchase",          "trigger": "Order confirmed",             "params": ["transaction_id", "affiliation", "revenue", "tax", "shipping", "coupon", "items"]},
            {"name": "refund",            "trigger": "Refund processed",            "params": ["transaction_id", "value", "items"]},
            {"name": "add_to_wishlist",   "trigger": "Wishlist button click",       "params": ["currency", "value", "items"]},
            {"name": "search",            "trigger": "Search submitted",            "params": ["search_term"]},
            {"name": "select_promotion",  "trigger": "Banner/promo click",          "params": ["creative_name", "creative_slot", "promotion_id"]},
            {"name": "sign_up",           "trigger": "Account created",             "params": ["method"]},
            {"name": "login",             "trigger": "User logged in",              "params": ["method"]},
        ],
        "saas": [
            {"name": "sign_up",           "trigger": "Account created",             "params": ["method", "plan"]},
            {"name": "login",             "trigger": "User logged in",              "params": ["method"]},
            {"name": "trial_started",     "trigger": "Free trial started",          "params": ["plan", "trial_days"]},
            {"name": "trial_converted",   "trigger": "Trial → paid conversion",     "params": ["plan", "value", "currency"]},
            {"name": "plan_selected",     "trigger": "Pricing page plan click",     "params": ["plan_id", "plan_name", "value"]},
            {"name": "subscription_created","trigger":"Subscription confirmed",     "params": ["plan_id", "value", "currency"]},
            {"name": "subscription_cancelled","trigger":"Cancellation confirmed",   "params": ["plan_id", "reason"]},
            {"name": "feature_used",      "trigger": "Key feature interaction",     "params": ["feature_name", "feature_category"]},
            {"name": "onboarding_step",   "trigger": "Onboarding step completed",  "params": ["step", "step_name"]},
            {"name": "onboarding_completed","trigger":"Full onboarding done",       "params": ["duration_seconds"]},
            {"name": "invite_sent",       "trigger": "Team member invited",         "params": ["invitee_role"]},
            {"name": "search",            "trigger": "In-app search",               "params": ["search_term", "results_count"]},
        ],
        "restaurant": [
            {"name": "menu_viewed",       "trigger": "Menu page/tab viewed",        "params": ["menu_category"]},
            {"name": "item_viewed",       "trigger": "Menu item clicked",           "params": ["item_id", "item_name", "price"]},
            {"name": "add_to_order",      "trigger": "Item added to order",         "params": ["item_id", "item_name", "quantity", "value"]},
            {"name": "order_placed",      "trigger": "Order submitted",             "params": ["order_type", "value", "currency", "items"]},
            {"name": "reservation_made",  "trigger": "Table booking confirmed",     "params": ["party_size", "date", "time"]},
            {"name": "search",            "trigger": "Menu search",                 "params": ["search_term"]},
        ],
        "healthcare": [
            {"name": "doctor_viewed",     "trigger": "Doctor profile viewed",       "params": ["doctor_id", "specialty"]},
            {"name": "appointment_started","trigger":"Booking flow started",        "params": ["service_type", "doctor_id"]},
            {"name": "appointment_booked","trigger":"Appointment confirmed",        "params": ["service_type", "date", "doctor_id"]},
            {"name": "search",            "trigger": "Doctor/service search",       "params": ["search_term", "specialty"]},
            {"name": "contact_submitted", "trigger": "Contact form submitted",      "params": ["form_type"]},
        ],
        "default": [
            {"name": "page_view",         "trigger": "Page load",                   "params": ["page_title", "page_location"]},
            {"name": "scroll",            "trigger": "25/50/75/90% scroll depth",   "params": ["percent_scrolled"]},
            {"name": "click",             "trigger": "Link/button click",           "params": ["link_text", "link_url"]},
            {"name": "search",            "trigger": "Site search",                 "params": ["search_term"]},
            {"name": "contact_submitted", "trigger": "Contact form submitted",      "params": ["form_id"]},
            {"name": "sign_up",           "trigger": "Newsletter/account signup",   "params": ["method"]},
            {"name": "share",             "trigger": "Social share button click",   "params": ["method", "content_type"]},
        ],
    }

    # ── Conversion goals per type ─────────────────────────────────────────
    CONVERSION_GOALS: Dict[str, List[str]] = {
        "ecommerce": ["purchase", "add_to_cart", "begin_checkout", "sign_up"],
        "saas":      ["subscription_created", "trial_started", "sign_up", "trial_converted"],
        "restaurant":["order_placed", "reservation_made"],
        "healthcare":["appointment_booked"],
        "default":   ["contact_submitted", "sign_up"],
    }

    # ── Analytics provider configs ────────────────────────────────────────
    PROVIDERS = {
        "ga4":      {"privacy": "medium", "cost": "free",     "gdpr": "consent_required", "self_hosted": False},
        "posthog":  {"privacy": "high",   "cost": "freemium", "gdpr": "compliant",        "self_hosted": True},
        "mixpanel": {"privacy": "medium", "cost": "freemium", "gdpr": "consent_required", "self_hosted": False},
        "plausible":{"privacy": "high",   "cost": "paid",     "gdpr": "cookie_free",      "self_hosted": True},
        "fathom":   {"privacy": "high",   "cost": "paid",     "gdpr": "cookie_free",      "self_hosted": False},
    }

    def generate(self, spec: Dict[str, Any], project_dir: str) -> Dict[str, Any]:
        """Generate analytics infrastructure for the project."""
        agent_logger.info("AnalyticsPipeline: Generating multi-provider analytics config...")

        website_type = spec.get("website_type", "default")
        region       = spec.get("region", "NA")
        events       = self.EVENT_TAXONOMY.get(website_type, self.EVENT_TAXONOMY["default"])
        conversions  = self.CONVERSION_GOALS.get(website_type, self.CONVERSION_GOALS["default"])

        # EU region → recommend privacy-first (Plausible/PostHog)
        recommended_provider = "plausible" if region == "EU" else "ga4"
        secondary_provider   = "posthog"

        artifacts = []
        config_dir = os.path.join(project_dir, "frontend", "src", "config")
        hooks_dir  = os.path.join(project_dir, "frontend", "src", "hooks")
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(hooks_dir, exist_ok=True)

        # 1. analytics-config.js — provider config
        cfg_path = os.path.join(config_dir, "analytics-config.js")
        self._write(cfg_path, self._build_config(recommended_provider, secondary_provider, events))
        artifacts.append(cfg_path)

        # 2. analytics.js — abstraction layer (provider-agnostic API)
        abs_path = os.path.join(config_dir, "analytics.js")
        self._write(abs_path, self._build_abstraction(events))
        artifacts.append(abs_path)

        # 3. useAnalytics.js — React hook
        hook_path = os.path.join(hooks_dir, "useAnalytics.js")
        self._write(hook_path, self._build_hook(events, conversions))
        artifacts.append(hook_path)

        # 4. event-taxonomy.json — reference doc
        tax_path = os.path.join(config_dir, "event-taxonomy.json")
        self._write(tax_path, json.dumps({
            "website_type": website_type,
            "provider":     recommended_provider,
            "events":       events,
            "conversions":  conversions,
        }, indent=2))
        artifacts.append(tax_path)

        # 5. ANALYTICS.md
        md_path = os.path.join(project_dir, "ANALYTICS.md")
        self._write(md_path, self._build_md(events, conversions, recommended_provider, region, website_type))
        artifacts.append(md_path)

        result = {
            "recommended_provider": recommended_provider,
            "secondary_provider":   secondary_provider,
            "events_defined":       len(events),
          "total_events":          len(events),
            "conversion_goals":     conversions,
            "gdpr_safe":            recommended_provider in ("plausible", "posthog", "fathom"),
            "artifacts":            artifacts,
        }
        agent_logger.info(
            f"AnalyticsPipeline: {len(events)} events, "
            f"provider={recommended_provider}, region={region}"
        )
        return result

    def _build_config(self, primary, secondary, events):
        event_map = {e["name"]: e["trigger"] for e in events}
        return f"""/**
 * Analytics Configuration
 * Primary: {primary} | Secondary: {secondary}
 */

export const ANALYTICS_CONFIG = {{
  primary: {{
    provider: '{primary}',
    // GA4
    ga4MeasurementId:  import.meta.env.VITE_GA4_ID || '',
    // PostHog
    posthogKey:        import.meta.env.VITE_POSTHOG_KEY || '',
    posthogHost:       import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
    // Plausible (privacy-first)
    plausibleDomain:   import.meta.env.VITE_PLAUSIBLE_DOMAIN || '',
    plausibleApiHost:  import.meta.env.VITE_PLAUSIBLE_HOST || 'https://plausible.io',
    // Mixpanel
    mixpanelToken:     import.meta.env.VITE_MIXPANEL_TOKEN || '',
    // Fathom (cookie-free)
    fathomSiteId:      import.meta.env.VITE_FATHOM_SITE_ID || '',
  }},
  options: {{
    debug:            import.meta.env.DEV,
    respectDoNotTrack: true,
    cookieless:       {json.dumps(primary in ("plausible", "fathom"))},
    sampleRate:       1.0,  // 100% of users
  }},
}};

// Event name registry
export const EVENTS = {json.dumps(event_map, indent=2)};
"""

    def _build_abstraction(self, events):
        track_fns = "\n".join(
            f"  /** {e['trigger']} */\n"
            f"  {e['name'].replace('.', '_')}: (params) => track('{e['name']}', params),"
            for e in events[:8]
        )
        return f"""/**
 * Analytics Abstraction Layer — Provider-agnostic tracking API
 *
 * Usage:
 *   import analytics from '@/config/analytics';
 *   analytics.track('purchase', {{ value: 99.99, currency: 'USD' }});
 *   analytics.page('/products');
 *   analytics.identify(userId, {{ email, plan }});
 */

import {{ ANALYTICS_CONFIG, EVENTS }} from './analytics-config';

// ── Core tracking functions ────────────────────────────────────────────────
export function track(eventName, properties = {{}}) {{
  if (ANALYTICS_CONFIG.options.respectDoNotTrack && navigator.doNotTrack === '1') return;

  const cfg = ANALYTICS_CONFIG.primary;
  const props = {{ ...properties, timestamp: new Date().toISOString() }};

  // GA4
  if (cfg.ga4MeasurementId && window.gtag) {{
    window.gtag('event', eventName, props);
  }}

  // PostHog
  if (cfg.posthogKey && window.__posthog) {{
    window.__posthog.capture(eventName, props);
  }}

  // Plausible
  if (cfg.plausibleDomain && window.plausible) {{
    window.plausible(eventName, {{ props }});
  }}

  // Mixpanel
  if (cfg.mixpanelToken && window.mixpanel) {{
    window.mixpanel.track(eventName, props);
  }}

  // Fathom
  if (cfg.fathomSiteId && window.fathom) {{
    window.fathom.trackEvent(eventName, {{ _value: properties.value || 0 }});
  }}

  if (ANALYTICS_CONFIG.options.debug) {{
    console.log(`[Analytics] ${{eventName}}`, props);
  }}
}}

export function page(url, title) {{
  const cfg = ANALYTICS_CONFIG.primary;
  if (cfg.ga4MeasurementId && window.gtag) {{
    window.gtag('event', 'page_view', {{ page_location: url, page_title: title }});
  }}
  if (cfg.plausibleDomain && window.plausible) {{
    window.plausible('pageview');
  }}
  if (cfg.posthogKey && window.__posthog) {{
    window.__posthog.capture('$pageview', {{ $current_url: url }});
  }}
}}

export function identify(userId, traits = {{}}) {{
  const cfg = ANALYTICS_CONFIG.primary;
  if (cfg.posthogKey && window.__posthog) {{
    window.__posthog.identify(userId, traits);
  }}
  if (cfg.mixpanelToken && window.mixpanel) {{
    window.mixpanel.identify(userId);
    window.mixpanel.people.set(traits);
  }}
  if (cfg.ga4MeasurementId && window.gtag) {{
    window.gtag('set', 'user_properties', traits);
  }}
}}

export function reset() {{
  if (window.__posthog) window.__posthog.reset();
  if (window.mixpanel) window.mixpanel.reset();
}}

// ── Typed event helpers ────────────────────────────────────────────────────
const analytics = {{
  track, page, identify, reset,
{track_fns}
}};

export default analytics;
"""

    def _build_hook(self, events, conversions):
        return f"""/**
 * useAnalytics — React hook for analytics tracking
 *
 * Usage:
 *   const {{ trackEvent, trackConversion }} = useAnalytics();
 *   trackEvent('add_to_cart', {{ value: 29.99 }});
 */

import {{ useCallback, useEffect }} from 'react';
import {{ useLocation }} from 'react-router-dom';
import analytics from '@/config/analytics';

export const CONVERSION_EVENTS = {json.dumps(conversions)};

export function useAnalytics() {{
  const location = useLocation();

  // Auto-track page views on route change
  useEffect(() => {{
    analytics.page(location.pathname + location.search, document.title);
  }}, [location]);

  const trackEvent = useCallback((eventName, properties = {{}}) => {{
    analytics.track(eventName, properties);
  }}, []);

  const trackConversion = useCallback((eventName, value, currency = 'USD', extra = {{}}) => {{
    analytics.track(eventName, {{ value, currency, ...extra }});
    // Mark as conversion in all providers
    if (window.gtag) {{
      window.gtag('event', 'conversion', {{ send_to: 'AW-xxx/yyy', value, currency }});
    }}
  }}, []);

  const identifyUser = useCallback((userId, traits) => {{
    analytics.identify(userId, traits);
  }}, []);

  return {{ trackEvent, trackConversion, identifyUser }};
}}

export default useAnalytics;
"""

    def _build_md(self, events, conversions, provider, region, website_type):
        gdpr_note = "\n> ⚠️ **EU Region:** GDPR requires cookie consent before loading GA4/Mixpanel.\n> Plausible/Fathom are recommended as they are cookie-free.\n" if region == "EU" else ""
        lines = [
            f"# Analytics Setup Guide — {website_type.title()}",
            gdpr_note,
            "\n## Recommended Provider Stack\n",
            f"- **Primary:** {provider} (region-optimised for {region})",
            "- **Secondary:** PostHog (session recording + feature flags)",
            "\n## Environment Variables\n```bash",
            "VITE_GA4_ID=G-XXXXXXXXXX",
            "VITE_POSTHOG_KEY=phc_xxxxx",
            "VITE_POSTHOG_HOST=https://app.posthog.com",
            "VITE_PLAUSIBLE_DOMAIN=yourdomain.com",
            "VITE_MIXPANEL_TOKEN=xxxxxxxxx",
            "VITE_FATHOM_SITE_ID=XXXXXXX",
            "```",
            "\n## Conversion Goals\n",
            "The following events are tracked as conversions:\n",
        ]
        for c in conversions:
            lines.append(f"- `{c}`")
        lines += [
            "\n## Event Taxonomy\n",
            "| Event | Trigger | Key Parameters |",
            "|-------|---------|----------------|",
        ]
        for e in events:
            params = ", ".join(e["params"][:3]) + ("..." if len(e["params"]) > 3 else "")
            lines.append(f"| `{e['name']}` | {e['trigger']} | {params} |")
        lines += [
            "\n## Quick Start\n```jsx",
            "import useAnalytics from '@/hooks/useAnalytics';",
            "",
            "function CheckoutButton({ item }) {",
            "  const { trackEvent } = useAnalytics();",
            "  return (",
            "    <button onClick={() => trackEvent('add_to_cart', {",
            "      currency: 'USD', value: item.price, items: [item]",
            "    })}>",
            "      Add to Cart",
            "    </button>",
            "  );",
            "}",
            "```",
        ]
        return "\n".join(lines)

    def _write(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"AnalyticsPipeline: Could not write {path}: {e}")
