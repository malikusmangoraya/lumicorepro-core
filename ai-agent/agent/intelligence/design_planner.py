"""Design Planner — the explicit pre-coding planning layer of LumicorePro Agent.

This is a *layer*, not a helper. It runs as its own pipeline stage **before any
file is written** and emits one authoritative contract that every later stage
obeys:

    Business -> Audience -> Brand -> Reference -> IA -> Journeys -> Content
             -> Visual system -> Page blueprints -> Interaction -> Technical

Nothing downstream is allowed to improvise: code generation consumes
``design_plan["page_plans"]`` for structure and ``design_plan["design_system"]``
for every colour/space/type decision. The contract is also persisted to the
project (``DESIGN_PLAN.md`` + ``design-plan.json``) so a later "change the hero"
request edits a plan instead of guessing at code.

Inputs (all optional, all deterministic):
  - industry / brand playbook YAML (``ai-agent/playbooks``)
  - a screenshot design spec  (:mod:`agent.intelligence.screenshot_to_code`)
  - a live-site reference spec (:mod:`agent.intelligence.browser_integration`)
  - benchmark / reference intelligence from ``benchmark_first``

Every output is a plain dict so it can be JSON-serialised into the generation
report and into ``design-manifest.json``.

Honesty rule: anything not actually measured (e.g. reference colours when the
reference could not be read) is reported as ``not_measured`` rather than being
invented, so no downstream stage can present a guess as a reading.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml

    _HAS_YAML = True
except Exception:  # pragma: no cover - yaml is optional
    _HAS_YAML = False


_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_PLAYBOOKS_DIR = _BASE_DIR / "playbooks"
_INDUSTRY_DIR = _PLAYBOOKS_DIR / "industries"
_BRAND_DIR = _PLAYBOOKS_DIR / "brands"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Knowledge tables — the deterministic spine of the plan
# ═══════════════════════════════════════════════════════════════════════════

INDUSTRY_PAGES: Dict[str, List[str]] = {
    "saas": ["Home", "Features", "Pricing", "About", "Contact", "Login", "Register", "Dashboard", "Admin"],
    "ecommerce": ["Home", "Products", "ProductDetail", "Cart", "Checkout", "About", "Contact", "Login", "Register"],
    "healthcare": ["Home", "Services", "Doctors", "Appointments", "About", "Contact", "Login", "Portal"],
    "fintech": ["Home", "Features", "Pricing", "Security", "About", "Contact", "Login", "Register", "Dashboard"],
    "education": ["Home", "Courses", "About", "Pricing", "Contact", "Login", "Register", "Dashboard"],
    "real-estate": ["Home", "Listings", "ListingDetail", "About", "Contact", "Login", "Register", "Dashboard"],
    "food": ["Home", "Menu", "Order", "About", "Contact", "Login", "Register"],
    "sports": ["Home", "Programs", "Schedule", "About", "Contact", "Login", "Register", "Dashboard"],
    "hospitality": ["Home", "Rooms", "Booking", "About", "Contact", "Login", "Register"],
    "entertainment": ["Home", "Events", "Tickets", "About", "Contact", "Login", "Register"],
    "portfolio": ["Home", "Work", "About", "Contact", "Resume"],
    "marketplace": ["Home", "Listings", "Sell", "About", "Contact", "Login", "Register", "Dashboard"],
    "automotive": ["Home", "Inventory", "InventoryDetail", "About", "Contact", "Login", "Register"],
    "fashion": ["Home", "Shop", "ProductDetail", "Lookbook", "About", "Contact", "Cart", "Login"],
    "travel": ["Home", "Destinations", "Booking", "About", "Contact", "Login", "Register"],
}

# Section templates per page type. Each entry is a *section key*, not free text.
PAGE_SECTIONS: Dict[str, List[str]] = {
    "Home": ["hero", "proof_strip", "features", "stats", "problem", "personas",
             "testimonial", "pricing_teaser", "faq", "cta", "newsletter"],
    "Features": ["hero", "feature_grid", "comparison", "cta"],
    "Pricing": ["hero", "pricing_tiers", "comparison", "faq", "cta"],
    "About": ["hero", "story", "team", "values", "cta"],
    "Contact": ["hero", "contact_form", "map", "faq"],
    "Login": ["hero", "login_form", "social_login"],
    "Register": ["hero", "register_form", "social_login"],
    "Dashboard": ["sidebar", "topbar", "kpi_cards", "charts", "activity_feed", "quick_actions"],
    "Admin": ["sidebar", "topbar", "user_table", "audit_logs", "settings"],
    "Products": ["hero", "filter_bar", "product_grid", "pagination"],
    "ProductDetail": ["hero", "product_gallery", "product_info", "reviews", "related_products"],
    "Cart": ["hero", "cart_lines", "order_summary", "coupon_field"],
    "Checkout": ["hero", "checkout_form", "order_summary", "payment_methods"],
    "Services": ["hero", "services_grid", "process", "faq", "cta"],
    "Doctors": ["hero", "doctor_grid", "filter_bar"],
    "Appointments": ["hero", "appointment_form", "booking_slots", "confirmation_state"],
    "Courses": ["hero", "course_grid", "curriculum", "testimonials"],
    "Listings": ["hero", "filter_bar", "listing_grid", "map_toggle", "pagination"],
    "ListingDetail": ["hero", "gallery", "listing_info", "contact_agent", "mortgage_estimator"],
    "Inventory": ["hero", "filter_bar", "inventory_grid", "compare_tray"],
    "InventoryDetail": ["hero", "vehicle_gallery", "vehicle_specs", "finance_calculator", "contact_dealer"],
    "Menu": ["hero", "menu_categories", "menu_items"],
    "Order": ["hero", "menu_items", "cart_drawer", "order_form"],
    "Programs": ["hero", "program_grid", "coach_panel"],
    "Schedule": ["hero", "schedule_table", "filter_bar"],
    "Rooms": ["hero", "room_grid", "rate_calendar"],
    "Booking": ["hero", "booking_form", "guest_form", "payment_methods", "confirmation_state"],
    "Events": ["hero", "event_grid", "event_detail_teaser"],
    "Tickets": ["hero", "ticket_selection", "seat_map", "order_summary"],
    "Work": ["hero", "project_grid", "case_study_teaser"],
    "Resume": ["hero", "experience_timeline", "skills", "education"],
    "Sell": ["hero", "listing_form", "photo_upload", "pricing_guide"],
    "Security": ["hero", "security_controls", "compliance_badges", "faq"],
    "Portal": ["hero", "appointment_form", "records_list", "prescriptions"],
    "Shop": ["hero", "category_nav", "product_grid"],
    "Lookbook": ["hero", "look_grid", "editorial_blocks"],
    "Destinations": ["hero", "destination_grid", "seasonal_picks"],
}

# Section key -> intent the generator must honour (grid, component, motion, a11y).
SECTION_SPECS: Dict[str, Dict[str, Any]] = {
    "hero": {
        "purpose": "Explain the offer and earn the first scroll within 3 seconds.",
        "layout": "split_or_centered",
        "grid": "12-col / 7-5 split or centered 8-col",
        "components": ["Eyebrow", "H1", "Subhead", "PrimaryCTA", "SecondaryCTA", "HeroMedia"],
        "motion": "entrance_fade_up",
        "a11y": "single_h1, contrast>=4.5:1, CTA reachable by keyboard",
        "max_words": 32,
    },
    "proof_strip": {
        "purpose": "Borrow credibility before the first argument.",
        "layout": "inline_row",
        "grid": "4-6 equal columns",
        "components": ["LogoRow", "TrustBadge"],
        "motion": "none",
        "a11y": "logos need alt/aria-label text",
        "max_words": 12,
    },
    "features": {
        "purpose": "Turn capabilities into visitor benefits.",
        "layout": "grid",
        "grid": "3-col cards, max 6 items",
        "components": ["FeatureCard", "Icon", "Title", "Body"],
        "motion": "scroll_reveal_stagger",
        "a11y": "heading order preserved, icons labelled",
        "max_words": 28,
    },
    "stats": {
        "purpose": "Prove scale with numbers, not adjectives.",
        "layout": "band",
        "grid": "3-4 columns",
        "components": ["StatCard"],
        "motion": "count_up",
        "a11y": "numbers announced as text, not canvas",
        "max_words": 6,
    },
    "problem": {
        "purpose": "Name the pain the visitor already feels.",
        "layout": "two_column",
        "grid": "5-7 split",
        "components": ["ProblemStatement", "PainList"],
        "motion": "scroll_reveal",
        "a11y": "list semantics",
        "max_words": 45,
    },
    "personas": {
        "purpose": "Let each visitor find themselves in the product.",
        "layout": "grid",
        "grid": "3-col cards",
        "components": ["PersonaCard"],
        "motion": "scroll_reveal_stagger",
        "a11y": "avatar alt text",
        "max_words": 34,
    },
    "testimonial": {
        "purpose": "Third-party proof with a name and a company.",
        "layout": "grid_or_quotes",
        "grid": "3-col quotes",
        "components": ["TestimonialCard", "RatingStars"],
        "motion": "none",
        "a11y": "blockquote + cite",
        "max_words": 38,
    },
    "pricing_teaser": {
        "purpose": "Show the entry price without hiding the full table.",
        "layout": "grid",
        "grid": "3-col tiers",
        "components": ["PricingCard", "PriceTag", "FeatureList"],
        "motion": "scroll_reveal",
        "a11y": "price is real text",
        "max_words": 22,
    },
    "pricing_tiers": {
        "purpose": "Full pricing comparison with an obvious recommended tier.",
        "layout": "grid",
        "grid": "3-col tiers, middle emphasized",
        "components": ["PricingCard", "PriceTag", "FeatureList", "Badge"],
        "motion": "scroll_reveal_stagger",
        "a11y": "table semantics or list with headings",
        "max_words": 26,
    },
    "faq": {
        "purpose": "Remove the last objections.",
        "layout": "accordion",
        "grid": "single 8-col",
        "components": ["Accordion", "FaqItem"],
        "motion": "height_fade",
        "a11y": "button + aria-expanded + aria-controls",
        "max_words": 40,
    },
    "cta": {
        "purpose": "One obvious next step, repeated with the hero promise.",
        "layout": "band_or_card",
        "grid": "centered 8-col",
        "components": ["CtaBand", "PrimaryCTA"],
        "motion": "fade_in",
        "a11y": "single primary CTA per view",
        "max_words": 18,
    },
    "newsletter": {
        "purpose": "Capture the visitor who is not ready to buy today.",
        "layout": "inline_form",
        "grid": "single row, label + input + button",
        "components": ["NewsletterForm", "Input", "Button", "StatusText"],
        "motion": "none",
        "a11y": "visible label, aria-live for result",
        "max_words": 14,
    },
    "story": {
        "purpose": "Explain why the company exists.",
        "layout": "editorial",
        "grid": "6-col text, offset media",
        "components": ["Prose", "Timeline"],
        "motion": "scroll_reveal",
        "a11y": "reading order preserved",
        "max_words": 90,
    },
    "team": {
        "purpose": "Put real people behind the promise.",
        "layout": "grid",
        "grid": "3-4 col portraits",
        "components": ["TeamCard", "Avatar"],
        "motion": "scroll_reveal_stagger",
        "a11y": "avatar alt text, role as text",
        "max_words": 18,
    },
    "values": {
        "purpose": "State the operating principles, not slogans.",
        "layout": "grid",
        "grid": "3-col",
        "components": ["ValueCard"],
        "motion": "scroll_reveal",
        "a11y": "heading hierarchy",
        "max_words": 24,
    },
    "contact_form": {
        "purpose": "Capture an enquiry with validation and a real success state.",
        "layout": "two_column",
        "grid": "5-7 split",
        "components": ["ContactForm", "Field", "Textarea", "SubmitButton", "StatusText"],
        "motion": "none",
        "a11y": "labels tied to inputs, aria-describedby errors",
        "max_words": 16,
    },
    "map": {
        "purpose": "Prove the location exists.",
        "layout": "full_bleed",
        "grid": "12-col band",
        "components": ["StaticMap", "Address"],
        "motion": "none",
        "a11y": "address as text, map is decorative",
        "max_words": 12,
    },
    "login_form": {
        "purpose": "Authenticate returning users in the fewest fields.",
        "layout": "centered_card",
        "grid": "centered 5-col",
        "components": ["AuthForm", "Field", "PasswordField", "SubmitButton", "ForgotLink"],
        "motion": "fade_in",
        "a11y": "autocomplete tokens, visible labels, error role=alert",
        "max_words": 10,
    },
    "register_form": {
        "purpose": "Create an account with the fewest required fields.",
        "layout": "centered_card",
        "grid": "centered 5-col",
        "components": ["AuthForm", "Field", "PasswordStrength", "Checkbox", "SubmitButton"],
        "motion": "fade_in",
        "a11y": "autocomplete tokens, inline field errors",
        "max_words": 12,
    },
    "sidebar": {"purpose": "Orient the operator.", "layout": "app_shell",
                "grid": "260px rail + content", "components": ["SideNav"],
                "motion": "none", "a11y": "nav landmark + aria-current", "max_words": 4},
    "topbar": {"purpose": "Global search, notifications, account.", "layout": "app_shell",
               "grid": "full width", "components": ["TopBar", "SearchInput", "NotificationBell"],
               "motion": "none", "a11y": "banner landmark", "max_words": 4},
    "kpi_cards": {"purpose": "Show the four numbers that matter.", "layout": "grid",
                  "grid": "4-col", "components": ["KpiCard"],
                  "motion": "count_up", "a11y": "values as text", "max_words": 5},
    "charts": {"purpose": "Show the trend behind the number.", "layout": "grid",
               "grid": "2-col", "components": ["ChartCard", "RechartsChart"],
               "motion": "none", "a11y": "chart has a text summary", "max_words": 6},
    "activity_feed": {"purpose": "Prove the system is live.", "layout": "list",
                      "grid": "single 8-col", "components": ["ActivityItem"],
                      "motion": "none", "a11y": "time elements", "max_words": 14},
    "quick_actions": {"purpose": "Shortcuts to the three most common jobs.", "layout": "inline",
                      "grid": "3-col", "components": ["ActionButton"],
                      "motion": "none", "a11y": "visible labels", "max_words": 5},
    "user_table": {"purpose": "Manage accounts with real CRUD.", "layout": "table",
                   "grid": "12-col table", "components": ["DataTable", "Pagination", "RowActions"],
                   "motion": "none", "a11y": "th scope, row actions labelled", "max_words": 8},
    "audit_logs": {"purpose": "Show an immutable trail.", "layout": "table",
                   "grid": "12-col table", "components": ["DataTable", "FilterBar"],
                   "motion": "none", "a11y": "th scope", "max_words": 10},
    "settings": {"purpose": "Change preferences with feedback.", "layout": "form",
                 "grid": "single 8-col", "components": ["SettingsForm", "Toggle"],
                 "motion": "none", "a11y": "labels + status region", "max_words": 10},
    "social_login": {"purpose": "Offer a one-tap alternative to typing.", "layout": "inline",
                     "grid": "stacked under form", "components": ["SocialButton"],
                     "motion": "none", "a11y": "provider name in label", "max_words": 4},
    "filter_bar": {"purpose": "Let visitors narrow a long list.", "layout": "inline_controls",
                   "grid": "wrapping row, sticky on desktop", "components": ["SearchInput", "Select", "Chip", "ResetButton"],
                   "motion": "none", "a11y": "labelled inputs, results count announced", "max_words": 8},
    "product_grid": {"purpose": "Show enough choice to decide, not enough to overwhelm.",
                     "layout": "grid", "grid": "2-col mobile, 3-4 col desktop",
                     "components": ["ProductCard", "PriceTag", "AddToCartButton", "LazyImage"],
                     "motion": "scroll_reveal_stagger", "a11y": "image alt, price as text", "max_words": 14},
    "pagination": {"purpose": "Keep a long list navigable.", "layout": "inline_controls",
                   "grid": "centred row", "components": ["Pagination", "PageLink"],
                   "motion": "none", "a11y": "nav landmark + aria-current", "max_words": 4},
    "product_gallery": {"purpose": "Show the product honestly.", "layout": "grid",
                        "grid": "1 large + thumbnails", "components": ["Gallery", "Thumbnail", "Zoom"],
                        "motion": "fade", "a11y": "alt text on every image", "max_words": 4},
    "product_info": {"purpose": "Answer price, variant and stock in one view.",
                     "layout": "two_column", "grid": "7-5 split",
                     "components": ["PriceTag", "VariantPicker", "QuantitySelector", "AddToCartButton", "StockStatus"],
                     "motion": "none", "a11y": "label tied to each control", "max_words": 30},
    "reviews": {"purpose": "Show unedited customer experience.", "layout": "grid",
                "grid": "summary + 3-col list", "components": ["RatingStars", "ReviewCard"],
                "motion": "none", "a11y": "blockquote + cite, rating in text", "max_words": 34},
    "related_products": {"purpose": "Offer the natural next purchase.", "layout": "grid",
                         "grid": "4-col", "components": ["ProductCard"],
                         "motion": "scroll_reveal", "a11y": "image alt", "max_words": 10},
    "cart_lines": {"purpose": "Show exactly what will be bought.", "layout": "list",
                   "grid": "single 8-col", "components": ["CartLine", "QuantitySelector", "RemoveButton", "LineTotal"],
                   "motion": "none", "a11y": "quantity labelled per line", "max_words": 12},
    "order_summary": {"purpose": "Make the total never a surprise.", "layout": "card",
                      "grid": "single 4-col, sticky", "components": ["SummaryRow", "TotalRow", "TaxRow"],
                      "motion": "none", "a11y": "totals as a description list", "max_words": 16},
    "coupon_field": {"purpose": "Allow a discount without hiding it.", "layout": "inline_form",
                     "grid": "input + apply", "components": ["Input", "ApplyButton", "StatusText"],
                     "motion": "none", "a11y": "aria-live for applied/rejected", "max_words": 8},
    "checkout_form": {"purpose": "Collect the minimum needed to complete the order.",
                      "layout": "two_column", "grid": "7-5 split",
                      "components": ["CheckoutForm", "Field", "AddressBlock", "SubmitButton", "StatusText"],
                      "motion": "none", "a11y": "visible labels, inline errors, no surprise fields", "max_words": 18},
    "payment_methods": {"purpose": "Show accepted payment with no hidden step.",
                        "layout": "list", "grid": "stacked options",
                        "components": ["PaymentOption", "RadioGroup"],
                        "motion": "none", "a11y": "fieldset + legend + radio semantics", "max_words": 10},
    "services_grid": {"purpose": "Show what is actually delivered.", "layout": "grid",
                      "grid": "3-col, up to 6 items", "components": ["ServiceCard", "Icon"],
                      "motion": "scroll_reveal_stagger", "a11y": "heading order", "max_words": 26},
    "process": {"purpose": "Remove the fear of the unknown.", "layout": "steps",
                "grid": "3-4 numbered steps", "components": ["StepCard", "StepNumber"],
                "motion": "scroll_reveal", "a11y": "ordered list semantics", "max_words": 22},
    "doctor_grid": {"purpose": "Make the clinician findable.", "layout": "grid",
                    "grid": "3-col", "components": ["DoctorCard", "Specialty", "AvailabilityBadge"],
                    "motion": "scroll_reveal", "a11y": "photo alt text", "max_words": 16},
    "appointment_form": {"purpose": "Book a slot with instant feedback.",
                         "layout": "two_column", "grid": "6-6 split",
                         "components": ["AppointmentForm", "DatePicker", "SlotPicker", "ConfirmButton"],
                         "motion": "none", "a11y": "label + aria-live confirmation", "max_words": 16},
    "booking_slots": {"purpose": "Show availability honestly.", "layout": "grid",
                      "grid": "time-slot chips", "components": ["SlotChip"],
                      "motion": "none", "a11y": "unavailable slots disabled, not hidden", "max_words": 4},
    "confirmation_state": {"purpose": "Prove the action succeeded.", "layout": "centered_card",
                           "grid": "centred 6-col", "components": ["ConfirmationCard", "ReferenceNumber"],
                           "motion": "fade_in", "a11y": "role=status on confirmation", "max_words": 26},
    "course_grid": {"purpose": "Show what can be learned.", "layout": "grid",
                    "grid": "3-col", "components": ["CourseCard", "LevelBadge", "Duration"],
                    "motion": "scroll_reveal", "a11y": "card heading links to detail", "max_words": 18},
    "curriculum": {"purpose": "Show the syllabus depth.", "layout": "accordion",
                   "grid": "single 8-col", "components": ["Accordion", "ModuleList"],
                   "motion": "height_fade", "a11y": "aria-expanded per module", "max_words": 20},
    "listing_grid": {"purpose": "Present every available home.", "layout": "grid",
                     "grid": "3-col cards", "components": ["ListingCard", "PriceTag", "MediaStrip", "Badge"],
                     "motion": "scroll_reveal_stagger", "a11y": "image alt, price as text", "max_words": 16},
    "map_toggle": {"purpose": "Switch between list and map without losing filters.",
                   "layout": "split", "grid": "60/40 split", "components": ["ToggleGroup", "StaticMap"],
                   "motion": "none", "a11y": "toggle has aria-pressed", "max_words": 4},
    "gallery": {"purpose": "Show the property honestly.", "layout": "grid",
                "grid": "hero image + strip", "components": ["Gallery", "Thumbnail"],
                "motion": "fade", "a11y": "alt text per image", "max_words": 4},
    "listing_info": {"purpose": "Answer every buyer question inline.", "layout": "two_column",
                     "grid": "7-5 split", "components": ["FactList", "Description", "PriceTag"],
                     "motion": "none", "a11y": "facts as a description list", "max_words": 60},
    "contact_agent": {"purpose": "Give the visitor a human.", "layout": "card",
                      "grid": "single 6-col", "components": ["AgentCard", "ContactForm"],
                      "motion": "none", "a11y": "form labels, status region", "max_words": 18},
    "mortgage_estimator": {"purpose": "Show affordability without a bank.",
                           "layout": "inline_form", "grid": "3 inputs + result",
                           "components": ["Input", "EstimateResult"],
                           "motion": "none", "a11y": "result announced via aria-live", "max_words": 10},
    "inventory_grid": {"purpose": "Present available stock.", "layout": "grid",
                       "grid": "3-col", "components": ["VehicleCard", "PriceTag", "MileageBadge"],
                       "motion": "scroll_reveal", "a11y": "image alt", "max_words": 16},
    "compare_tray": {"purpose": "Support side-by-side decisions.", "layout": "sticky_bar",
                     "grid": "fixed bottom bar", "components": ["CompareTray", "CompareButton"],
                     "motion": "slide_up", "a11y": "count announced, dismissible", "max_words": 8},
    "vehicle_gallery": {"purpose": "Show the vehicle from every angle.", "layout": "grid",
                        "grid": "1 large + thumbnails", "components": ["Gallery", "Thumbnail"],
                        "motion": "fade", "a11y": "alt text per image", "max_words": 4},
    "vehicle_specs": {"purpose": "Answer the spec question precisely.", "layout": "table",
                      "grid": "2-col spec table", "components": ["SpecTable"],
                      "motion": "none", "a11y": "th scope", "max_words": 10},
    "finance_calculator": {"purpose": "Show a realistic monthly figure.", "layout": "inline_form",
                           "grid": "3 inputs + result", "components": ["Input", "MonthlyEstimate"],
                           "motion": "none", "a11y": "result in aria-live", "max_words": 10},
    "contact_dealer": {"purpose": "Convert interest into a booked test drive.",
                       "layout": "two_column", "grid": "5-7 split",
                       "components": ["ContactForm", "Field", "SubmitButton"],
                       "motion": "none", "a11y": "labels + inline errors", "max_words": 16},
    "menu_categories": {"purpose": "Let a diner navigate by course.", "layout": "inline_controls",
                        "grid": "chip row", "components": ["Chip", "CategoryNav"],
                        "motion": "none", "a11y": "aria-pressed per chip", "max_words": 6},
    "menu_items": {"purpose": "Show price and dietary truth.", "layout": "two_column",
                   "grid": "name + description + price", "components": ["MenuItem", "DietaryBadge"],
                   "motion": "scroll_reveal", "a11y": "price as text", "max_words": 22},
    "cart_drawer": {"purpose": "Keep the basket reachable while browsing.",
                    "layout": "side_panel", "grid": "right drawer 400px",
                    "components": ["CartDrawer", "CartLine", "TotalRow"],
                    "motion": "slide_in", "a11y": "dialog semantics + focus trap + Escape to close", "max_words": 12},
    "order_form": {"purpose": "Collect delivery details once.", "layout": "card",
                   "grid": "single 6-col", "components": ["OrderForm", "Field", "SubmitButton"],
                   "motion": "none", "a11y": "labels + inline errors", "max_words": 16},
    "program_grid": {"purpose": "Show what the visitor can train for.", "layout": "grid",
                     "grid": "3-col", "components": ["ProgramCard", "Duration", "IntensityBadge"],
                     "motion": "scroll_reveal", "a11y": "card heading links to detail", "max_words": 18},
    "coach_panel": {"purpose": "Put a person behind the programme.", "layout": "grid",
                    "grid": "3-col portraits", "components": ["CoachCard", "Avatar"],
                    "motion": "scroll_reveal", "a11y": "photo alt text", "max_words": 16},
    "schedule_table": {"purpose": "Show when things happen.", "layout": "table",
                       "grid": "7-col timetable", "components": ["ScheduleTable", "SessionRow"],
                       "motion": "none", "a11y": "th scope + caption", "max_words": 10},
    "room_grid": {"purpose": "Show each room honestly.", "layout": "grid",
                  "grid": "3-col", "components": ["RoomCard", "PriceTag", "AmenityList"],
                  "motion": "scroll_reveal", "a11y": "image alt", "max_words": 18},
    "rate_calendar": {"purpose": "Show price by date.", "layout": "calendar",
                      "grid": "7-col month grid", "components": ["Calendar", "RateCell"],
                      "motion": "none", "a11y": "each day is a labelled button", "max_words": 6},
    "booking_form": {"purpose": "Book without losing context.", "layout": "two_column",
                     "grid": "7-5 split", "components": ["BookingForm", "DatePicker", "GuestPicker"],
                     "motion": "none", "a11y": "labels + aria-live confirmation", "max_words": 18},
    "guest_form": {"purpose": "Collect guest details exactly once.", "layout": "card",
                   "grid": "2-col fields", "components": ["GuestForm", "Field"],
                   "motion": "none", "a11y": "autocomplete tokens, inline errors", "max_words": 14},
    "event_grid": {"purpose": "Show what is on.", "layout": "grid",
                   "grid": "3-col", "components": ["EventCard", "DateBadge", "PriceTag"],
                   "motion": "scroll_reveal", "a11y": "date as text, image alt", "max_words": 16},
    "event_detail_teaser": {"purpose": "Make one event feel unmissable.", "layout": "card",
                            "grid": "hero image + copy", "components": ["EventTeaser", "CtaLink"],
                            "motion": "scroll_reveal", "a11y": "descriptive link text", "max_words": 26},
    "ticket_selection": {"purpose": "Pick a ticket tier and quantity.", "layout": "list",
                         "grid": "radio options", "components": ["TicketOption", "QuantitySelector"],
                         "motion": "none", "a11y": "fieldset + legend + radio", "max_words": 14},
    "seat_map": {"purpose": "Let the buyer choose a seat.", "layout": "grid",
                 "grid": "seat matrix", "components": ["SeatMap", "SeatButton"],
                 "motion": "none", "a11y": "each seat a labelled button, taken seats disabled", "max_words": 4},
    "project_grid": {"purpose": "Prove the work with images first.", "layout": "grid",
                     "grid": "editorial masonry", "components": ["ProjectCard", "LazyImage"],
                     "motion": "scroll_reveal", "a11y": "image alt, title as heading", "max_words": 16},
    "case_study_teaser": {"purpose": "Prove outcomes, not adjectives.", "layout": "two_column",
                          "grid": "6-6 split", "components": ["MetricRow", "CaseTeaser"],
                          "motion": "scroll_reveal", "a11y": "metrics as text", "max_words": 30},
    "experience_timeline": {"purpose": "Show a credible track record.", "layout": "timeline",
                            "grid": "single 8-col vertical", "components": ["Timeline", "TimelineItem"],
                            "motion": "scroll_reveal", "a11y": "ordered list semantics", "max_words": 40},
    "skills": {"purpose": "Make the capability scannable.", "layout": "grid",
               "grid": "3-col chips", "components": ["SkillChip"],
               "motion": "none", "a11y": "list semantics", "max_words": 6},
    "education": {"purpose": "Show credentials honestly.", "layout": "list",
                  "grid": "single 8-col", "components": ["CredentialItem"],
                  "motion": "scroll_reveal", "a11y": "time elements", "max_words": 30},
    "listing_form": {"purpose": "Collect a complete listing.", "layout": "two_column",
                     "grid": "7-5 split", "components": ["ListingForm", "Field", "Textarea"],
                     "motion": "none", "a11y": "labels + inline errors", "max_words": 18},
    "photo_upload": {"purpose": "Make the listing credible.", "layout": "dropzone",
                     "grid": "single 8-col", "components": ["Dropzone", "UploadPreview"],
                     "motion": "none", "a11y": "input[type=file] + labelled dropzone", "max_words": 8},
    "pricing_guide": {"purpose": "Explain the fee before it is charged.", "layout": "card",
                      "grid": "single 8-col", "components": ["FeeTable", "Note"],
                      "motion": "none", "a11y": "table headers", "max_words": 30},
    "security_controls": {"purpose": "State controls in plain language.", "layout": "grid",
                          "grid": "3-col", "components": ["ControlCard", "Icon"],
                          "motion": "scroll_reveal", "a11y": "heading order", "max_words": 22},
    "compliance_badges": {"purpose": "Evidence the claim, not decorate.", "layout": "inline",
                          "grid": "wrapping chips", "components": ["ComplianceBadge"],
                          "motion": "none", "a11y": "badge has a text label", "max_words": 6},
    "records_list": {"purpose": "Show the visitor their own data.", "layout": "table",
                     "grid": "12-col table", "components": ["DataTable", "FilterBar"],
                     "motion": "none", "a11y": "th scope", "max_words": 12},
    "prescriptions": {"purpose": "Show medication history clearly.", "layout": "list",
                      "grid": "single 8-col", "components": ["PrescriptionItem"],
                      "motion": "none", "a11y": "date + name as text", "max_words": 20},
    "category_nav": {"purpose": "Let a shopper narrow immediately.", "layout": "inline_controls",
                     "grid": "chip row", "components": ["CategoryChip"],
                     "motion": "none", "a11y": "aria-pressed per chip", "max_words": 6},
    "look_grid": {"purpose": "Sell the collection, not the discount.", "layout": "grid",
                  "grid": "editorial 2-col alternating", "components": ["LookCard", "LazyImage"],
                  "motion": "scroll_reveal", "a11y": "image alt describes the look", "max_words": 12},
    "editorial_blocks": {"purpose": "Give the page a magazine rhythm.", "layout": "full_bleed",
                         "grid": "alternating bands", "components": ["EditorialBlock", "PullQuote"],
                         "motion": "scroll_reveal", "a11y": "reading order preserved", "max_words": 50},
    "destination_grid": {"purpose": "Sell the place honestly.", "layout": "grid",
                         "grid": "3-col with full-bleed hero card", "components": ["DestinationCard", "PriceTag"],
                         "motion": "scroll_reveal", "a11y": "image alt", "max_words": 18},
    "seasonal_picks": {"purpose": "Create a reason to book now.", "layout": "grid",
                       "grid": "3-col", "components": ["PickCard", "PriceTag"],
                       "motion": "scroll_reveal", "a11y": "image alt", "max_words": 16},
    "comparison": {"purpose": "Differentiate against the obvious alternative.", "layout": "table",
                   "grid": "3-col feature comparison", "components": ["ComparisonTable", "CheckIcon", "MinusIcon"],
                   "motion": "none", "a11y": "table headers", "max_words": 16},
    "feature_grid": {"purpose": "Deep-dive the capability set.", "layout": "grid",
                     "grid": "3-col, up to 9 items", "components": ["FeatureCard"],
                     "motion": "scroll_reveal_stagger", "a11y": "heading order", "max_words": 30},
}

# UX anti-patterns the plan must explicitly forbid (MASTER_PROMPT Part 3).
ANTI_PATTERNS: Tuple[str, ...] = (
    "hidden_pricing",
    "excessive_modals",
    "weak_search",
    "unclear_checkout",
    "fake_reviews",
    "vague_cta",
    "unnecessary_carousels",
    "countdown_timer_pressure",
    "forced_newsletter_popup",
)

DESIGN_SYSTEM: Dict[str, Any] = {
    "colors": {
        "primary": "#3f3a35",
        "primary_light": "#6b635c",
        "primary_dark": "#2a2622",
        "accent": "#8a6f4d",
        "bg": "#0e1116",
        "surface": "#151920",
        "surface_2": "#1c212a",
        "border": "#26292f",
        "text": "#e8e6e3",
        "text_dim": "#9a9793",
        "on_primary": "#ffffff",
        "success": "#3f9c6d",
        "warning": "#c08a2e",
        "danger": "#c0483f",
    },
    "typography": {
        "heading_font": "Inter",
        "body_font": "Inter",
        "heading_weight": 700,
        "body_weight": 400,
        "scale": {"h1": "2.5rem", "h2": "2rem", "h3": "1.5rem", "h4": "1.25rem",
                  "body": "1rem", "small": "0.875rem"},
    },
    "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px",
                "xl": "32px", "2xl": "48px", "3xl": "64px"},
    "border_radius": {"sm": "6px", "md": "10px", "lg": "14px", "xl": "20px", "full": "9999px"},
    "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.1)",
        "md": "0 4px 12px rgba(0,0,0,0.15)",
        "lg": "0 8px 24px rgba(0,0,0,0.2)",
        "xl": "0 16px 48px rgba(0,0,0,0.25)",
    },
    "components": {
        "button": {"radius": "8px", "padding": "12px 20px", "font_weight": 500},
        "card": {"radius": "12px", "padding": "24px", "border": "1px solid var(--border)"},
        "input": {"radius": "8px", "padding": "10px 14px", "border": "1px solid var(--border)"},
        "badge": {"radius": "9999px", "padding": "4px 10px", "font_size": "12px"},
    },
}

# Breakpoints the plan commits to (320 -> 1920).
BREAKPOINTS: List[Dict[str, Any]] = [
    {"name": "mobile", "min_px": 320, "max_px": 767, "columns": 4, "nav": "hamburger",
     "rule": "single column, 16px gutters, 44px tap targets"},
    {"name": "tablet", "min_px": 768, "max_px": 1023, "columns": 8, "nav": "condensed",
     "rule": "two columns max, 24px gutters"},
    {"name": "laptop", "min_px": 1024, "max_px": 1439, "columns": 12, "nav": "full",
     "rule": "12-col grid, 32px gutters"},
    {"name": "desktop", "min_px": 1440, "max_px": 1920, "columns": 12, "nav": "full",
     "rule": "12-col grid, container capped at 1280px"},
]

# Copy slots every page must fill — this is what stops "lorem ipsum" shipping.
COPY_SLOTS: Dict[str, List[Tuple[str, str]]] = {
    "Home": [("hero", "eyebrow/headline/subhead/cta_primary/cta_secondary"),
             ("problem", "problem_statement/pain_points"),
             ("features", "feature_titles+descriptions"),
             ("stats", "stat_values+labels"),
             ("personas", "persona_name+role+need"),
             ("testimonial", "quote+name+role+company"),
             ("pricing_teaser", "tier_name+price+one_liner"),
             ("faq", "question+answer"),
             ("cta", "headline+button"),
             ("newsletter", "label+button+success_message")],
    "About": [("story", "origin/milestones"), ("team", "name/role/bio"),
              ("values", "value_title+description")],
    "Contact": [("contact_form", "heading/labels/submit/success/error"),
                ("map", "address/hours")],
    "Pricing": [("pricing_tiers", "tier_name/price/period/features/cta"),
                ("comparison", "row_labels"), ("faq", "question+answer")],
    "Login": [("login_form", "heading/labels/submit/error/forgot"),
              ("social_login", "provider_buttons")],
    "Register": [("register_form", "heading/labels/password_rules/consent/submit/error"),
                 ("social_login", "provider_buttons")],
}

# Pages that must always exist regardless of industry hint.
ALWAYS_PAGES = ("Home", "Contact")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Colour maths — the plan refuses to ship an unreadable system
# ═══════════════════════════════════════════════════════════════════════════

def _hex_to_rgb(value: str) -> Optional[Tuple[int, int, int]]:
    raw = str(value or "").strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return None
    try:
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError:
        return None


def _channel_luminance(value: int) -> float:
    srgb = value / 255.0
    return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str) -> Optional[float]:
    """WCAG relative luminance, or None when the colour is not a hex value."""
    rgb = _hex_to_rgb(value)
    if rgb is None:
        return None
    red, green, blue = (_channel_luminance(ch) for ch in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> Optional[float]:
    """WCAG contrast ratio (1.0 – 21.0), or None if either colour is unusable."""
    lum_fg = relative_luminance(foreground)
    lum_bg = relative_luminance(background)
    if lum_fg is None or lum_bg is None:
        return None
    lighter, darker = max(lum_fg, lum_bg), min(lum_fg, lum_bg)
    return round((lighter + 0.05) / (darker + 0.05), 2)


_TEXT_CANDIDATES = ("#ffffff", "#f5f3f0", "#e8e6e3", "#c9c6c2", "#9a9793", "#6b635c", "#0e1116", "#151920")


def _readable_text(foreground: str, backgrounds: List[str], target: float = 4.5) -> str:
    """Return the best foreground colour that clears `target` on *every* background.

    Used instead of *rejecting* a reference colour: a screenshot may genuinely
    contain a low-contrast pairing, and the fix belongs in the token, not in a
    build failure. One colour has to serve every surface the text lands on, so
    the winner is the candidate with the best *worst-case* ratio.
    """
    usable = [bg for bg in backgrounds if relative_luminance(bg) is not None]
    if not usable:
        return foreground

    def worst(candidate: str) -> float:
        ratios = [contrast_ratio(candidate, bg) for bg in usable]
        return min(r for r in ratios if r is not None) if ratios else 0.0

    current = worst(foreground)
    if current >= target:
        return foreground
    best, best_score = foreground, current
    for candidate in _TEXT_CANDIDATES:
        score = worst(candidate)
        if score > best_score:
            best, best_score = candidate, score
    return best


# ═══════════════════════════════════════════════════════════════════════════
# 3. Playbooks
# ═══════════════════════════════════════════════════════════════════════════

def load_playbook(industry: str, brand_style: str = "") -> Dict[str, Any]:
    """Load industry + brand playbooks when available on disk."""
    result: Dict[str, Any] = {"industry": {}, "brand": {}}
    if not _HAS_YAML:
        return result

    industry_file = _INDUSTRY_DIR / f"{str(industry or '').strip().lower()}.yaml"
    brand_file = _BRAND_DIR / f"{str(brand_style or '').strip().lower()}.yaml"
    for key, target in (("industry", industry_file), ("brand", brand_file)):
        if not target.is_file():
            continue
        try:
            data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                result[key] = data
        except Exception:
            continue
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 4. Design system assembly
# ═══════════════════════════════════════════════════════════════════════════

_COLOR_KEYS = ("primary", "primary_light", "primary_dark", "accent", "bg", "surface",
               "surface_2", "border", "text", "text_dim", "on_primary", "success",
               "warning", "danger")

#: Only these may be overridden by an explicit brand palette. ``bg`` is on the
#: list because the whole point of a palette pass is to re-skin the surface.
_PALETTE_OVERRIDABLE = ("primary", "primary_light", "primary_dark", "accent", "bg",
                        "surface", "surface_2", "border", "text", "text_dim")


def build_design_system(
    palette: Optional[Dict[str, str]] = None,
    design_tokens: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return an isolated, contrast-checked design system overlaid with tokens.

    The base palette is deliberately hue-neutral so a build never injects a
    blue-family default; brand colour always comes from the resolved blueprint.
    Text colours are pulled back to a readable value when a reference pairing
    fails WCAG AA, and the correction is recorded in ``contrast_fixes``.
    """
    system = copy.deepcopy(DESIGN_SYSTEM)
    tokens = design_tokens if isinstance(design_tokens, dict) else {}
    colors = system.setdefault("colors", {})

    for key in _COLOR_KEYS:
        value = tokens.get(key)
        if isinstance(value, str) and value.strip():
            colors[key] = value.strip()

    for key, value in (palette or {}).items():
        name = str(key)
        if name in _PALETTE_OVERRIDABLE and isinstance(value, str) and value.strip():
            colors[name] = value.strip()

    typography = system.setdefault("typography", {})
    for key in ("heading_font", "body_font"):
        value = tokens.get(key)
        if isinstance(value, str) and value.strip():
            typography[key] = value.strip()
    base_size = tokens.get("base_size_px") or tokens.get("base_font_size")
    if isinstance(base_size, (int, float)) and 12 <= float(base_size) <= 24:
        typography["base_size_px"] = int(base_size)

    # Correct legibility in place, then re-measure so `clean` reflects the
    # shipped colours rather than the intent.
    first_pass = audit_contrast(colors)
    for fix in first_pass.get("fixes") or []:
        colors[fix["token"]] = fix["corrected_to"]
    final = audit_contrast(colors)
    final["corrected_tokens"] = [f["token"] for f in first_pass.get("fixes") or []]
    final["clean"] = final.get("all_pass", False)
    system["contrast"] = final
    return system


def audit_contrast(colors: Dict[str, str]) -> Dict[str, Any]:
    """Measure the pairs that decide whether the site is readable.

    Pairs are chosen to match how tokens are actually used: body text lands on
    ``bg``/``surface``/``surface_2`` and on top of ``primary`` buttons, while
    ``primary``/``accent`` appear as link or icon colour on ``bg``. A brand colour
    is never silently rewritten — only the *text* tokens are corrected, because
    changing the brand hue would discard the reference while changing text hue
    only restores legibility.
    """
    pairs = (
        # (label, fg, bg, target, role) — `role` decides how a failure is
        # reported. Body text must pass; a brand colour used as link/icon text
        # is advisory, because the same token is usually a *fill* on buttons.
        ("text on bg", "text", "bg", 4.5, "body"),
        ("text on surface", "text", "surface", 4.5, "body"),
        ("text on surface_2", "text", "surface_2", 4.5, "body"),
        ("text_dim on surface", "text_dim", "surface", 4.5, "body"),
        ("on_primary on primary", "on_primary", "primary", 4.5, "body"),
        ("primary as link on bg", "primary", "bg", 3.0, "accent"),
        ("accent as link on bg", "accent", "bg", 3.0, "accent"),
    )
    # Backgrounds each corrected token has to stay readable on.
    text_backgrounds = ["bg", "surface", "surface_2"]
    checks: List[Dict[str, Any]] = []
    failures: Dict[str, List[str]] = {}
    for label, fg_key, bg_key, target, role in pairs:
        fg, bg = colors.get(fg_key), colors.get(bg_key)
        ratio = contrast_ratio(fg, bg) if fg and bg else None
        if ratio is None:
            status = "not_measured"
        elif ratio >= target:
            status = "pass"
        else:
            status = "fail" if role == "body" else "advisory"
        entry: Dict[str, Any] = {
            "pair": label,
            "foreground": fg,
            "background": bg,
            "target": target,
            "role": role,
            "ratio": ratio,
            "status": status,
        }
        if status == "fail":
            entry["correctable"] = True
            failures.setdefault(fg_key, []).append(bg_key)
        checks.append(entry)

    fixes: List[Dict[str, Any]] = []
    for token, bg_keys in failures.items():
        if token not in ("text", "text_dim", "on_primary"):
            continue  # brand colour: report, do not rewrite
        if token == "on_primary":
            surfaces = [colors.get("primary") or ""]
        else:
            surfaces = [colors.get(key) or "" for key in text_backgrounds]
        corrected = _readable_text(colors.get(token, ""), [s for s in surfaces if s], 4.5)
        if corrected == colors.get(token):
            continue
        fixes.append({
            "token": token,
            "against": bg_keys,
            "ratio": next(
                (c["ratio"] for c in checks
                 if c["foreground"] == colors.get(token) and c["status"] == "fail"), None),
            "corrected_to": corrected,
            "corrected_ratio": min(
                (contrast_ratio(corrected, s) for s in surfaces
                 if s and contrast_ratio(corrected, s) is not None), default=None),
        })

    return {
        "checks": checks,
        "fixes": fixes,
        "warnings": [c["pair"] for c in checks if c["status"] == "advisory"],
        "worst_ratio": min(
            (c["ratio"] for c in checks if c.get("ratio") is not None), default=None
        ),
        "all_pass": all(c["status"] == "pass" for c in checks if c["role"] == "body"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. The plan
# ═══════════════════════════════════════════════════════════════════════════

def _resolve_pages(
    industry: str,
    explicit: Optional[List[str]],
    reference_sections: Optional[List[str]],
) -> List[str]:
    """Pick the page list: explicit > industry table > a safe default."""
    if explicit:
        return [str(p).strip() for p in explicit if str(p).strip()]
    pages = list(INDUSTRY_PAGES.get(industry) or INDUSTRY_PAGES["saas"])
    if reference_sections:
        # A single-page reference (a landing screenshot) means: build Home from
        # that structure, and still ship the pages a real product needs.
        pages = ["Home"] + [p for p in pages if p != "Home"]
    for required in ALWAYS_PAGES:
        if required not in pages:
            pages.append(required)
    return pages


def _home_sections_from_reference(reference_sections: List[str]) -> Optional[List[str]]:
    """Translate measured region names into planner section keys.

    Returns None when the mapping is too weak to trust, so the caller keeps the
    industry default instead of silently inheriting a bad structure.
    """
    if not reference_sections:
        return None
    alias = {
        "navbar": "proof_strip", "nav": "proof_strip", "header": "proof_strip",
        "hero": "hero", "banner": "hero", "features": "features",
        "feature_grid": "features", "products": "features", "services": "features",
        "stats": "stats", "problem": "problem", "personas": "personas",
        "testimonial": "testimonial", "testimonials": "testimonial",
        "pricing": "pricing_teaser", "faq": "faq", "cta": "cta",
        "newsletter": "newsletter", "footer": "cta",
    }
    mapped: List[str] = []
    for raw in reference_sections:
        key = alias.get(str(raw).strip().lower())
        if key and key not in mapped:
            mapped.append(key)
    if len(mapped) < 3:
        return None
    ordered = [s for s in PAGE_SECTIONS["Home"] if s in mapped]
    return ordered or None


def _build_page_plan(page: str, sections: List[str]) -> Dict[str, Any]:
    """Per-page blueprint: sections with layout, components, motion and a11y."""
    is_auth = page in ("Login", "Register")
    is_app = page in ("Dashboard", "Admin")
    section_plans: List[Dict[str, Any]] = []
    for key in sections:
        spec = SECTION_SPECS.get(key, {})
        section_plans.append({
            "section": key,
            "purpose": spec.get("purpose", "Support the page goal."),
            "layout": spec.get("layout", "single_column"),
            "grid": spec.get("grid", "single 8-col"),
            "components": list(spec.get("components") or []),
            "motion": spec.get("motion", "none"),
            "a11y": spec.get("a11y", "semantic markup, labelled controls"),
            "max_words": spec.get("max_words", 40),
            "data_reveal": True,
        })
    return {
        "sections": sections,
        "section_plans": section_plans,
        "layout": "centered_card" if is_auth else ("app_shell" if is_app else "multi_section"),
        "hero_variant": "centered" if is_auth else ("none" if is_app else "split"),
        "max_sections": len(sections),
        "heading_count": {"h1": 1, "h2": min(4, len(sections)), "h3": "per-section"},
    }


def _user_journeys(pages: List[str], website_type: str) -> List[Dict[str, Any]]:
    """Explicit START -> ACTION -> RESPONSE -> NEXT -> SUCCESS -> ERROR flows."""
    journeys: List[Dict[str, Any]] = [{
        "name": "first_visit_to_conversion",
        "pages": ["Home"] + [p for p in pages if p in ("Pricing", "Contact", "Register")],
        "steps": [
            {"stage": "START", "action": "Land on Home hero", "response": "Understand offer in 3s"},
            {"stage": "ACTION", "action": "Click primary CTA", "response": "Route to the conversion target"},
            {"stage": "NEXT", "action": "Scan proof (stats/testimonials)", "response": "Reduced doubt"},
            {"stage": "SUCCESS", "action": "Complete the target action", "response": "Visible confirmation"},
            {"stage": "ERROR", "action": "Invalid input / failed request", "response": "Inline specific error"},
            {"stage": "RECOVERY", "action": "Retry after fixing input", "response": "State preserved, no data loss"},
        ],
    }]
    if website_type in ("ecommerce", "marketplace", "fashion"):
        journeys.append({
            "name": "browse_to_checkout",
            "pages": ["Home", "Products", "ProductDetail", "Cart", "Checkout"],
            "steps": [
                {"stage": "START", "action": "Enter a category", "response": "Filterable product grid"},
                {"stage": "ACTION", "action": "Open a product", "response": "Images, price, variants, stock"},
                {"stage": "NEXT", "action": "Add to cart", "response": "Cart count + total update"},
                {"stage": "SUCCESS", "action": "Checkout", "response": "Order confirmation"},
                {"stage": "ERROR", "action": "Payment declined", "response": "Explicit retry, no lost cart"},
                {"stage": "RECOVERY", "action": "Change payment method", "response": "Same order resumes"},
            ],
        })
    if "Register" in pages or "Login" in pages:
        journeys.append({
            "name": "authenticate",
            "pages": ["Register", "Login", "Dashboard"],
            "steps": [
                {"stage": "START", "action": "Choose register or login", "response": "Minimal form"},
                {"stage": "ACTION", "action": "Submit credentials", "response": "Field-level validation first"},
                {"stage": "NEXT", "action": "Authenticate", "response": "Token issued, redirect to Dashboard"},
                {"stage": "SUCCESS", "action": "Reach the dashboard", "response": "Personalised data"},
                {"stage": "ERROR", "action": "Wrong password", "response": "role=alert message, field retained"},
                {"stage": "RECOVERY", "action": "Use password reset", "response": "Return to login pre-filled"},
            ],
        })
    return journeys


def create_design_plan(
    business_type: str,
    industry: str = "saas",
    brand_style: str = "corporate",
    pages: Optional[List[str]] = None,
    custom_sections: Optional[Dict[str, List[str]]] = None,
    palette: Optional[Dict[str, str]] = None,
    design_tokens: Optional[Dict[str, Any]] = None,
    website_type: str = "",
    audience: Optional[List[str]] = None,
    reference_sections: Optional[List[str]] = None,
    reference_intelligence: Optional[Dict[str, Any]] = None,
    brand_name: str = "",
    prompt: str = "",
) -> Dict[str, Any]:
    """Produce the complete pre-coding design contract.

    This is the Design Planner layer — it decides the website structure, visual
    system, content obligations, UX flow and technical shape BEFORE coding
    begins. Returns a dict whose ``pages`` / ``page_plans`` / ``design_system``
    keys are the single source of truth for the generation stage.
    """
    industry = str(industry or "saas").strip().lower()
    brand_style = str(brand_style or "corporate").strip().lower()
    website_type = str(website_type or business_type or "").strip().lower()

    selected_pages = _resolve_pages(industry, pages, reference_sections)
    playbooks = load_playbook(industry, brand_style)
    reference_home = _home_sections_from_reference(reference_sections or [])

    page_plans: Dict[str, Any] = {}
    for page in selected_pages:
        sections = (custom_sections or {}).get(page)
        if not sections and page == "Home" and reference_home:
            sections = reference_home
        sections = sections or PAGE_SECTIONS.get(page, ["hero", "content", "cta"])
        page_plans[page] = _build_page_plan(page, sections)

    design_system = build_design_system(palette, design_tokens)
    references = reference_intelligence if isinstance(reference_intelligence, dict) else {}

    plan: Dict[str, Any] = {
        "status": "planned",
        "planner_version": "2.0",
        "business_type": business_type,
        "industry": industry,
        "brand_style": brand_style,
        "brand_name": brand_name,
        "pages": selected_pages,
        "page_plans": page_plans,
        "design_system": design_system,
        "playbooks": playbooks,
        "playbooks_loaded": bool(playbooks.get("industry") or playbooks.get("brand")),
        "audience": {
            "primary": (audience or ["the decision-maker evaluating this category"])[0],
            "all": list(audience or ["the decision-maker evaluating this category"]),
        },
        "information_architecture": {
            "nav_model": "top_nav_with_footer_sitemap",
            "max_nav_items": 5,
            "depth": 1,
            "routes": [
                "/" if page == "Home" else f"/{page.lower()}" for page in selected_pages
            ],
        },
        "ux_flow": {
            "entry": "Home",
            "primary_conversion": "cta",
            "secondary_conversion": "newsletter",
            "navigation": "top_nav",
            "mobile_nav": "hamburger",
            "state_model": "loading | success | error | empty | retry on every fetch",
        },
        "user_journeys": _user_journeys(selected_pages, website_type),
        "content_strategy": {
            "tone": "professional",
            "language": "en",
            "i18n_ready": True,
            "rtl_ready": True,
            "no_placeholders": True,
            "slots": COPY_SLOTS,
            "forbidden": ("lorem ipsum", "TODO", "coming soon", "dummy", "placeholder text"),
        },
        "responsive": {
            "breakpoints": BREAKPOINTS,
            "mobile_first": True,
            "min_width_px": 320,
            "max_width_px": 1920,
            "rule": "no fixed widths, no horizontal scroll at any breakpoint",
        },
        "accessibility": {
            "target": "WCAG 2.1 AA",
            "landmarks": ["header", "main", "nav", "footer"],
            "skip_link": True,
            "focus_visible": True,
            "reduced_motion": "respect prefers-reduced-motion",
            "keyboard": "tab/enter/escape on every interactive element",
        },
        "motion_plan": {
            "intensity": "medium",
            "entrance": "fade + 12px rise, 200ms, cubic-bezier(0.16, 1, 0.3, 1)",
            "hover": "transform 200ms only",
            "forbidden": ["parallax on mobile", "auto-playing carousels", "flash >3/s"],
        },
        "asset_plan": {
            "images": "real curated photography, WebP, lazy below the fold",
            "icons": "lucide-react with text labels",
            "logo": "generated vector mark, never plain text",
            "fonts": "max 2 families, font-display swap",
        },
        "quality_targets": {
            "design_score": 80,
            "bundle_gzip_kb": 200,
            "lcp_s": 1.5,
            "cls": 0.05,
            "a11y_violations": 0,
        },
        "anti_patterns_to_avoid": list(ANTI_PATTERNS),
        "reference_intelligence": {
            "applied": bool(references),
            "hints": list(references.get("reference_hints") or references.get("peers") or []),
            "structure_from_reference": bool(reference_home),
        },
        "technical": {
            "framework": "react",
            "styling": "tailwind",
            "state": "zustand + react-query",
            "routing": "react-router",
            "i18n": "i18next",
            "deployment": "github_pages",
        },
        "prompt_digest": hashlib.sha256((prompt or "").encode("utf-8", "replace")).hexdigest()[:16],
    }

    plan["fingerprint"] = plan_fingerprint(plan)
    plan["validation"] = validate_design_plan(plan)
    return plan


def plan_fingerprint(plan: Dict[str, Any]) -> str:
    """Stable hash of the structural decisions, for cache/change detection."""
    payload = {
        "pages": plan.get("pages"),
        "sections": {k: v.get("sections") for k, v in (plan.get("page_plans") or {}).items()},
        "colors": (plan.get("design_system") or {}).get("colors"),
        "typography": (plan.get("design_system") or {}).get("typography"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════
# 6. Validation — hard issues block, soft issues warn
# ═══════════════════════════════════════════════════════════════════════════

class PlanIssues(list):
    """A list of issue strings that also carries severity metadata.

    Subclassing ``list`` is deliberate: every existing caller treats the result
    as a plain list (``len(...)``, ``[:3]``, truthiness, ``== []``) and keeps
    working, while new callers can read ``hard`` / ``soft`` / ``valid`` / ``score``.
    """

    def __init__(self, issues: List[str], hard: List[str], soft: List[str]) -> None:
        super().__init__(issues)
        self.hard: List[str] = list(hard)
        self.soft: List[str] = list(soft)

    @property
    def valid(self) -> bool:
        return not self.hard

    @property
    def score(self) -> int:
        return max(0, 100 - 10 * len(self.hard) - 3 * len(self.soft))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "issues": list(self),
            "hard": list(self.hard),
            "soft": list(self.soft),
            "valid": self.valid,
            "score": self.score,
        }


def validate_design_plan(plan: Dict[str, Any]) -> PlanIssues:
    """Validate a plan, returning a list-like :class:`PlanIssues`.

    ``hard`` issues mean the plan cannot be built as written (no pages, a page
    with no sections, unreadable text colours). ``soft`` issues are advisory
    (an unknown section key, no journeys recorded) and never block codegen.
    """
    issues: List[str] = []
    hard: List[str] = []
    soft: List[str] = []

    def add(message: str, severity: str = "hard") -> None:
        issues.append(message)
        (hard if severity == "hard" else soft).append(message)

    if not plan:
        return PlanIssues(["Design plan is empty"], ["Design plan is empty"], [])

    pages = plan.get("pages") or []
    if not pages:
        add("No pages defined")
    elif "Home" not in pages:
        add("No Home page defined")

    system = plan.get("design_system") or {}
    colors = system.get("colors") or {}
    if not colors.get("primary"):
        add("No primary color defined")

    contrast = system.get("contrast") or {}
    if contrast and not contrast.get("all_pass", True):
        add("Design system body-text contrast below WCAG AA", "hard")

    page_plans = plan.get("page_plans") or {}
    for page in pages:
        pplan = page_plans.get(page) or {}
        sections = pplan.get("sections") or []
        if not sections:
            add(f"Page {page} has no sections")
            continue
        if not pplan.get("section_plans"):
            add(f"Page {page} has section blueprints missing", "soft")
        for section in sections:
            if section not in SECTION_SPECS:
                add(f"Page {page}: unknown section '{section}'", "soft")

    if not plan.get("user_journeys"):
        add("No user journeys defined", "soft")
    if not (plan.get("information_architecture") or {}).get("routes"):
        add("No routes defined", "soft")

    return PlanIssues(issues, hard, soft)


def plan_blockers(plan: Dict[str, Any]) -> List[str]:
    """Hard issues only — the list a codegen gate should refuse on."""
    result = validate_design_plan(plan)
    return list(result.get("hard") or [])


# ═══════════════════════════════════════════════════════════════════════════
# 7. Persistence — a plan you cannot read back is not a plan
# ═══════════════════════════════════════════════════════════════════════════

def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "page").strip().lower()).strip("-") or "page"


def render_plan_markdown(plan: Dict[str, Any]) -> str:
    """Human-readable DESIGN_PLAN.md — the artefact a reviewer reads first."""
    if not plan:
        return "# Design Plan\n\nNo plan was produced.\n"

    system = plan.get("design_system") or {}
    colors = system.get("colors") or {}
    typography = system.get("typography") or {}
    validation = plan.get("validation") or {}

    lines: List[str] = [
        "# Design Plan",
        "",
        f"- **Industry**: {plan.get('industry')}",
        f"- **Brand style**: {plan.get('brand_style')}",
        f"- **Website type**: {plan.get('business_type')}",
        f"- **Fingerprint**: `{plan.get('fingerprint')}`",
        f"- **Validation**: {'valid' if validation.get('valid', True) else 'INVALID'}"
        f" ({validation.get('score', 0)}/100)",
        "",
        "## Pages",
        "",
    ]
    for page in plan.get("pages") or []:
        lines.append(f"- `{_slug(page)}` — {', '.join((plan['page_plans'][page]['sections']))}")

    lines += ["", "## Design system", "", "| Token | Value |", "| --- | --- |"]
    for key in sorted(colors):
        lines.append(f"| {key} | `{colors[key]}` |")
    lines += [
        "",
        f"Heading font: `{typography.get('heading_font')}` · Body font: `{typography.get('body_font')}`",
        "",
    ]

    contrast = system.get("contrast") or {}
    if contrast.get("checks"):
        lines += ["## Contrast (WCAG AA)", "", "| Pair | Ratio | Target | Status |", "| --- | --- | --- | --- |"]
        for check in contrast["checks"]:
            lines.append(
                f"| {check['pair']} | {check.get('ratio') or 'n/a'} | {check['target']} | {check['status']} |"
            )
        lines.append("")

    journeys = plan.get("user_journeys") or []
    if journeys:
        lines += ["## User journeys", ""]
        for journey in journeys:
            lines.append(f"### {journey.get('name')}")
            lines.append("")
            for step in journey.get("steps") or []:
                lines.append(f"- **{step.get('stage')}** — {step.get('action')} → {step.get('response')}")
            lines.append("")

    lines += ["## Anti-patterns to avoid", ""]
    lines += [f"- {item}" for item in plan.get("anti_patterns_to_avoid") or []]
    lines += ["", "## Section blueprints", ""]
    for page, pplan in (plan.get("page_plans") or {}).items():
        lines.append(f"### {page}")
        lines.append("")
        for section in pplan.get("section_plans") or []:
            lines.append(
                f"- **{section['section']}** — {section['layout']} / {section['grid']} · "
                f"motion: {section['motion']} · a11y: {section['a11y']}"
            )
            if section.get("components"):
                lines.append(f"  - components: {', '.join(section['components'])}")
        lines.append("")

    return "\n".join(lines)


def write_design_plan_artifacts(project_dir: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    """Persist DESIGN_PLAN.md + design-plan.json into the project."""
    written: Dict[str, Any] = {"ok": False, "paths": {}}
    if not project_dir or not plan:
        written["reason"] = "no project_dir or plan"
        return written
    try:
        root = Path(project_dir)
        root.mkdir(parents=True, exist_ok=True)
        md_path = root / "DESIGN_PLAN.md"
        json_path = root / "design-plan.json"
        md_path.write_text(render_plan_markdown(plan), encoding="utf-8")
        json_path.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
        written["ok"] = True
        written["paths"] = {"markdown": str(md_path), "json": str(json_path)}
    except Exception as exc:  # pragma: no cover - disk failure
        written["reason"] = str(exc)[:200]
    return written


def load_design_plan(path: str) -> Dict[str, Any]:
    """Read a persisted plan back (used by the iterate loop)."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, TypeError):
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}