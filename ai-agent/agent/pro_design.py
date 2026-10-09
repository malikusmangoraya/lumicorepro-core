"""
ProDesign — Professional Light-Theme Design System
===================================================
Replaces generic dark-glass SaaS look with a light, layered, consulting-style
professional design. Each project gets a unique color palette, SVG logo, and
industry-appropriate section content.

Used by: restyle_all.py (batch), finalize_layout (future projects).
"""
from pathlib import Path
import os
from typing import Dict, Any, Optional
from utils.logger import agent_logger
import json as _json_mod

# ── Lucide SVG map (for inline static HTML) ───────────────────────────────────
def _load_lucide_svg() -> Dict[str, str]:
    p = Path(__file__).parent / 'lucide_icons.json'
    if p.exists():
        try:
            return _json_mod.loads(p.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

_LUCIDE_SVG: Dict[str, str] = _load_lucide_svg()

def _icon_svg(name: str, color: str = 'currentColor', size: int = 24) -> str:
    """Return inline SVG for a Lucide icon by name."""
    inner = _LUCIDE_SVG.get(name, '')
    if not inner:
        return ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'


def _pascal(icon_name: str) -> str:
    """lucide-react kebab-case file name → PascalCase component export."""
    return ''.join(w[0].upper() + w[1:] for w in icon_name.split('-'))


def _rgb(hex_color: str) -> str:
    """#abc or #aabbcc → 'r g b' triplet (for Tailwind rgb(var(--t-*-rgb)))."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return '15 23 42'
    return f"{int(h[0:2], 16)} {int(h[2:4], 16)} {int(h[4:6], 16)}"


# ── UI Style System (9 design languages from the style wheel) ─────────────
# Each style brings a distinct formula: CSS primitives + palette shift.
# Default for every project: glassmorphism (enterprise).
UI_STYLE_DEFAULT = 'glassmorphism'

# ── International region palettes (culturally-aware color combos) ────────
# Applied on top of the base palette when the analyzer detects a target market.
# Each combo is chosen for the market's color psychology (luxury gold for the
# Gulf, saffron for South Asia, red/gold for East Asia, etc).
REGION_PALETTES: Dict[str, Dict[str, str]] = {
    'gcc': {'primary': '#b8860b', 'accent': '#0f766e', 'heading': '#5b3200',
            'navBg': '#fffaf0', 'footerBg': '#1c1917'},
    'south-asia': {'primary': '#ea580c', 'accent': '#16a34a', 'heading': '#451a03',
                   'navBg': '#fff7ed', 'footerBg': '#1c1917'},
    'east-asia': {'primary': '#dc2626', 'accent': '#d97706', 'heading': '#1f2937',
                  'navBg': '#fff7f7', 'footerBg': '#111827'},
    'europe': {'primary': '#1d4ed8', 'accent': '#0f766e', 'heading': '#0f172a',
               'navBg': '#f8fafc', 'footerBg': '#0f172a'},
    'north-america': {'primary': '#2563eb', 'accent': '#dc2626', 'heading': '#111827',
                      'navBg': '#f8fafc', 'footerBg': '#111827'},
    'latam': {'primary': '#f97316', 'accent': '#0d9488', 'heading': '#7c2d12',
              'navBg': '#fff7ed', 'footerBg': '#1c1917'},
    'africa': {'primary': '#b45309', 'accent': '#047857', 'heading': '#292524',
               'navBg': '#fafaf9', 'footerBg': '#1c1917'},
    'default': {},
}

# per-style dark/light palette overrides applied on top of the base palette
UI_STYLE_PALETTE = {
    'glassmorphism': {'navBg': '#f8fafc', 'footerBg': '#0f172a', 'dark': False},
    'minimalist':    {'navBg': '#ffffff', 'footerBg': '#0f172a', 'dark': False},
    'flat':          {'navBg': '#ffffff', 'footerBg': '#0f172a', 'dark': False},
    'bento':         {'navBg': '#f1f5f9', 'footerBg': '#0f172a', 'dark': False},
    'neobrutalism':  {'navBg': '#fffbeb', 'footerBg': '#111827', 'dark': False},
    'neumorphism':   {'navBg': '#e5e9f0', 'footerBg': '#0f172a', 'dark': False},
    'claymorphism':  {'navBg': '#fef9ec', 'footerBg': '#111827', 'dark': False},
    'skeuomorphism': {'navBg': '#f7f3ea', 'footerBg': '#3f2e1e', 'dark': False},
    'dark':          {'navBg': '#0b1120', 'footerBg': '#020617', 'dark': True,
                      'primary': '#22d3ee', 'accent': '#a78bfa', 'heading': '#e2e8f0',
                      'text': '#94a3b8'},
}

# Extra CSS injected into index.css per style (design-language primitives).
UI_STYLE_CSS = {
    'glassmorphism': '''  .card-panel {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.08);
  }
  .hero-aurora {
    background: radial-gradient(60% 60% at 20% 20%, rgba(99, 102, 241, 0.18), transparent 60%),
                radial-gradient(55% 55% at 80% 15%, rgba(34, 211, 238, 0.18), transparent 60%),
                radial-gradient(50% 60% at 55% 85%, rgba(124, 58, 237, 0.12), transparent 60%);
  }
''',
    'minimalist': '''  .card-panel {
    background: var(--t-surface);
    border: 1px solid var(--t-border);
    border-radius: 0.375rem;
  }
  .hero-aurora {
    background:
      linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  }
''',
    'flat': '''  .card-panel {
    background: var(--t-surface);
    border: 1px solid var(--t-border);
    border-radius: 0.5rem;
  }
  .hero-aurora {
    background: var(--t-canvas);
  }
''',
    'bento': '''  .bento-card {
    border-radius: 1.25rem;
    background: var(--t-surface);
    border: 1px solid var(--t-border);
    box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
    min-height: 8rem;
  }
  .hero-aurora {
    background:
      radial-gradient(70% 55% at 15% 20%, rgba(37, 99, 235, 0.14), transparent 60%),
      radial-gradient(60% 50% at 85% 30%, rgba(124, 58, 237, 0.12), transparent 60%);
  }
''',
    'neobrutalism': '''  .card-panel {
    background: var(--t-surface);
    border: 3px solid #111827;
    border-radius: 0.75rem;
    box-shadow: 5px 5px 0 #111827;
  }
  .hero-aurora {
    background:
      linear-gradient(120deg, #fff7ed 0%, #fef3c7 45%, #fce7f3 100%);
  }
''',
    'neumorphism': '''  .card-panel {
    background: #e9edf4;
    border-radius: 1.5rem;
    box-shadow: 9px 9px 22px rgba(145, 158, 175, 0.28),
                -9px -9px 22px rgba(255, 255, 255, 0.82);
  }
  .hero-aurora {
    background: #eceef4;
  }
''',
    'claymorphism': '''  .card-panel {
    background: linear-gradient(145deg, #fffdf5, #f5e9d4);
    border-radius: 1.75rem;
    border: 1px solid rgba(255, 255, 255, 0.9);
    box-shadow: inset -6px -8px 18px rgba(180, 120, 60, 0.18),
                inset 6px 8px 18px rgba(255, 255, 255, 0.85),
                0 10px 24px rgba(120, 80, 40, 0.12);
  }
  .hero-aurora {
    background: linear-gradient(160deg, #fffbf0, #fdeed6);
  }
''',
    'skeuomorphism': '''  .card-panel {
    background: linear-gradient(180deg, #fdfbf6, #efe7d8);
    border: 1px solid #d9cbb4;
    border-radius: 0.875rem;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9), 0 6px 18px rgba(80, 60, 30, 0.18);
  }
  .hero-aurora {
    background: linear-gradient(180deg, #f7f3ea 0%, #efe7d8 100%);
  }
''',
    'dark': '''  body {
    background-color: #0b1120;
    color: #e2e8f0;
  }
  .text-slate-500 { color: #94a3b8 !important; }
  .text-slate-700 { color: #cbd5e1 !important; }
  .section-heading { color: #e2e8f0; }
  .card-panel {
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
  }
  .hero-aurora {
    background:
      radial-gradient(60% 60% at 20% 20%, rgba(34, 211, 238, 0.16), transparent 60%),
      radial-gradient(55% 55% at 80% 15%, rgba(167, 139, 250, 0.16), transparent 60%),
      linear-gradient(160deg, #0b1120 0%, #020617 100%);
  }
''',
}

# ── 14 Project Palettes (unique per industry) ──────────────────────────────
PALETTES: Dict[str, Dict[str, Any]] = {
    'nexa-marketplace':    {'primary': '#6366f1', 'accent': '#f59e0b', 'heading': '#1e1b4b', 'navBg': '#ffffff', 'footerBg': '#1e1b4b'},
    'verapay-fintech':     {'primary': '#059669', 'accent': '#14b8a6', 'heading': '#064e3b', 'navBg': '#ffffff', 'footerBg': '#064e3b'},
    'edulify-lms':         {'primary': '#2563eb', 'accent': '#7c3aed', 'heading': '#1e3a5f', 'navBg': '#ffffff', 'footerBg': '#1e293b'},
    'telecare-health':     {'primary': '#e11d48', 'accent': '#059669', 'heading': '#1f2937', 'navBg': '#ffffff', 'footerBg': '#1f2937'},
    'realspace-estate':    {'primary': '#0284c7', 'accent': '#ea580c', 'heading': '#0c4a6e', 'navBg': '#ffffff', 'footerBg': '#0c4a6e'},
    'marketsphere':        {'primary': '#7c3aed', 'accent': '#ec4899', 'heading': '#2e1065', 'navBg': '#ffffff', 'footerBg': '#2e1065'},
    'storefront-pro':      {'primary': '#ea580c', 'accent': '#6366f1', 'heading': '#431407', 'navBg': '#ffffff', 'footerBg': '#431407'},
    'ai-content-studio':   {'primary': '#7c3aed', 'accent': '#06b6d4', 'heading': '#2e1065', 'navBg': '#ffffff', 'footerBg': '#2e1065'},
    'fooddelivery-express':{'primary': '#dc2626', 'accent': '#f59e0b', 'heading': '#1f2937', 'navBg': '#ffffff', 'footerBg': '#1f2937'},
    'travelbook-pro':      {'primary': '#0891b2', 'accent': '#0ea5e9', 'heading': '#164e63', 'navBg': '#ffffff', 'footerBg': '#164e63'},
    'fitnesscoach-go':     {'primary': '#16a34a', 'accent': '#eab308', 'heading': '#14532d', 'navBg': '#ffffff', 'footerBg': '#14532d'},
    'jobboard-hirehub':    {'primary': '#2563eb', 'accent': '#059669', 'heading': '#1e3a5f', 'navBg': '#ffffff', 'footerBg': '#1e293b'},
    'eventticket-live':    {'primary': '#9333ea', 'accent': '#e11d48', 'heading': '#3b0764', 'navBg': '#ffffff', 'footerBg': '#3b0764'},
    'cryptovault-pro':     {'primary': '#4f46e5', 'accent': '#f59e0b', 'heading': '#1e1b4b', 'navBg': '#ffffff', 'footerBg': '#1e1b4b'},
    'resupro':             {'primary': '#2563eb', 'accent': '#7c3aed', 'heading': '#1e3a5f', 'navBg': '#ffffff', 'footerBg': '#1e293b'},
}

# ── 14 Project Profiles (copy + features) ───────────────────────────────────
PROFILES: Dict[str, Dict[str, Any]] = {
    'nexa-marketplace': {
        'title': 'NexaMarket', 'tagline': 'Multi-Vendor Marketplace Platform',
        'eyebrow': 'MARKETPLACE READY',
        'hero_desc': 'Launch your multi-vendor marketplace with built-in payments, analytics, and seller dashboards.',
        'features': [
            ('Seller Onboarding', 'Automated vendor registration with KYC verification'),
            ('Product Catalog', 'Dynamic filtering, search, and real-time inventory management'),
            ('Payment Splitting', 'Automatic revenue sharing across vendors at checkout'),
            ('Analytics Dashboard', 'Revenue, traffic, and conversion insights per vendor'),
        ],
        'stats': [('12K+', 'Active Sellers'), ('2M+', 'Products Listed'), ('$48M', 'GMV Processed'), ('99.99%', 'Uptime')],
    },
    'verapay-fintech': {
        'title': 'VeraPay', 'tagline': 'Digital Payments & Wallet Platform',
        'eyebrow': 'FINTECH SOLUTION',
        'hero_desc': 'End-to-end digital payment infrastructure with multi-currency wallets and instant settlements.',
        'features': [
            ('Multi-Currency Wallet', 'Support 140+ currencies with real-time FX rates'),
            ('Instant Settlements', 'Same-day vendor payouts across global rails'),
            ('Fraud Detection', 'ML-powered risk scoring on every transaction'),
            ('Compliance Suite', 'Built-in KYC/AML with document verification'),
        ],
        'stats': [('500K+', 'Wallets Active'), ('$120M', 'Transacted'), ('0.01%', 'Fraud Rate'), ('<2s', 'Settlement')],
    },
    'edulify-lms': {
        'title': 'Edulify', 'tagline': 'Learning Management System',
        'eyebrow': 'EDTECH PLATFORM',
        'hero_desc': 'Enterprise LMS with live classes, progress tracking, certifications, and admin analytics.',
        'features': [
            ('Course Builder', 'Drag-and-drop lesson builder with quizzes and assignments'),
            ('Live Classes', 'Integrated video conferencing with attendance tracking'),
            ('Progress Analytics', 'Real-time learner dashboards with completion metrics'),
            ('Certificate Engine', 'Auto-generated verifiable certificates on completion'),
        ],
        'stats': [('25K+', 'Students'), ('500+', 'Courses'), ('94%', 'Completion Rate'), ('4.9/5', 'Avg Rating')],
    },
    'telecare-health': {
        'title': 'TeleCare', 'tagline': 'Telehealth & Patient Portal',
        'eyebrow': 'HEALTHCARE PLATFORM',
        'hero_desc': 'HIPAA-compliant telehealth platform with appointments, records, and video consultations.',
        'features': [
            ('Patient Portal', 'Secure access to medical records and prescriptions'),
            ('Video Consultation', 'HD video calls with screen sharing and notes'),
            ('Appointment Scheduling', 'Smart booking with provider availability'),
            ('E-Prescriptions', 'Digital prescriptions sent directly to pharmacies'),
        ],
        'stats': [('100K+', 'Patients'), ('5K+', 'Providers'), ('1M+', 'Consultations'), ('99.9%', 'Uptime')],
    },
    'realspace-estate': {
        'title': 'RealSpace', 'tagline': 'Property Listing & Management',
        'eyebrow': 'REAL ESTATE PLATFORM',
        'hero_desc': 'Full-stack real estate platform with virtual tours, mortgage calculators, and agent matching.',
        'features': [
            ('Virtual Tours', '360 property walkthroughs with interactive floor plans'),
            ('Smart Matching', 'AI-powered buyer-property matching by preferences'),
            ('Mortgage Calculator', 'Pre-qualification and payment estimator built-in'),
            ('Agent Dashboard', 'Lead management, showing scheduler, and CRM tools'),
        ],
        'stats': [('50K+', 'Properties'), ('12K+', 'Agents'), ('$8B', 'Listings Value'), ('30 days', 'Avg Sell Time')],
    },
    'marketsphere': {
        'title': 'MarketSphere', 'tagline': 'Digital Marketing Agency Suite',
        'eyebrow': 'AGENCY PLATFORM',
        'hero_desc': 'All-in-one agency toolkit: campaign management, client reporting, and creative pipelines.',
        'features': [
            ('Campaign Builder', 'Multi-channel campaign orchestrator with A/B testing'),
            ('Client Reporting', 'Automated white-label reports with live dashboards'),
            ('Asset Pipeline', 'Creative briefs, approvals, and version control'),
            ('SEO Toolkit', 'Keyword tracking, site audit, and backlink monitoring'),
        ],
        'stats': [('3K+', 'Agencies'), ('20K+', 'Campaigns'), ('45M+', 'Impressions'), ('4.8/5', 'Rating')],
    },
    'storefront-pro': {
        'title': 'Storefront Pro', 'tagline': 'Headless E-Commerce Engine',
        'eyebrow': 'ECOMMERCE ENGINE',
        'hero_desc': 'API-first headless commerce with inventory sync, checkout optimization, and analytics.',
        'features': [
            ('Headless API', 'RESTful and GraphQL APIs for any frontend'),
            ('Inventory Sync', 'Real-time stock sync across channels and warehouses'),
            ('Smart Checkout', 'One-click checkout with payment routing'),
            ('Conversion Analytics', 'Funnel tracking and cart abandonment alerts'),
        ],
        'stats': [('8K+', 'Stores'), ('2M+', 'Orders'), ('$320M', 'Revenue'), ('<800ms', 'Checkout')],
    },
    'ai-content-studio': {
        'title': 'AI Studio', 'tagline': 'AI-Powered Content Generation',
        'eyebrow': 'AI PLATFORM',
        'hero_desc': 'Generate blogs, social posts, ad copy, and emails with AI. Built-in brand voice and approval flows.',
        'features': [
            ('Content Generator', 'Blog posts, social captions, and email sequences on demand'),
            ('Brand Voice AI', 'Fine-tuned models that match your brand tone'),
            ('Approval Workflow', 'Multi-step review with stakeholder commenting'),
            ('Performance Tracker', 'Engagement analytics per content piece'),
        ],
        'stats': [('15K+', 'Creators'), ('500K+', 'Pieces Generated'), ('3x', 'Faster Output'), ('4.7/5', 'Rating')],
    },
    'fooddelivery-express': {
        'title': 'FoodExpress', 'tagline': 'Food Delivery & Restaurant Platform',
        'eyebrow': 'FOOD DELIVERY',
        'hero_desc': 'Complete food delivery solution: online ordering, restaurant management, and real-time dispatch.',
        'features': [
            ('Online Ordering', 'Branded menus with photos, modifiers, and upsells'),
            ('Live Tracking', 'Real-time GPS tracking from kitchen to doorstep'),
            ('Restaurant Dashboard', 'Order management, analytics, and menu control'),
            ('Dispatch Engine', 'Optimized rider assignment and route planning'),
        ],
        'stats': [('10K+', 'Restaurants'), ('2M+', 'Orders Delivered'), ('30 min', 'Avg Delivery'), ('$95M', 'GMV')],
    },
    'travelbook-pro': {
        'title': 'TravelBook', 'tagline': 'Travel Booking & Itinerary Platform',
        'eyebrow': 'TRAVEL PLATFORM',
        'hero_desc': 'End-to-end travel booking: flights, hotels, tours, and AI-generated itineraries.',
        'features': [
            ('Smart Search', 'Multi-provider flight and hotel comparison'),
            ('AI Itineraries', 'Personalized day-by-day travel plans'),
            ('Booking Engine', 'Secure checkout with flexible cancellation policies'),
            ('Offline Access', 'Download itineraries, tickets, and maps for offline use'),
        ],
        'stats': [('500K+', 'Travelers'), ('100K+', 'Hotels'), ('4.8/5', 'Rating'), ('45 countries', 'Coverage')],
    },
    'fitnesscoach-go': {
        'title': 'FitCoach', 'tagline': 'Fitness & Wellness Platform',
        'eyebrow': 'FITNESS PLATFORM',
        'hero_desc': 'Personal training platform with workout plans, nutrition tracking, and live class booking.',
        'features': [
            ('Workout Builder', 'Custom training programs with video demonstrations'),
            ('Nutrition Tracker', 'Meal logging with macro and calorie breakdown'),
            ('Live Classes', 'Stream classes with real-time leaderboard and chat'),
            ('Progress Dashboard', 'Body metrics, streaks, and achievement badges'),
        ],
        'stats': [('75K+', 'Active Users'), ('10K+', 'Workouts'), ('92%', 'Retention'), ('4.9/5', 'Rating')],
    },
    'jobboard-hirehub': {
        'title': 'HireHub', 'tagline': 'Job Board & Recruitment Platform',
        'eyebrow': 'HIRING PLATFORM',
        'hero_desc': 'Full-featured job board: applicant tracking, resume builder, AI matching, and dashboards.',
        'features': [
            ('Smart Matching', 'AI-powered candidate-job alignment scoring'),
            ('ATS Pipeline', 'Kanban board with automated stage transitions'),
            ('Resume Builder', 'Drag-and-drop builder with ATS-optimized templates'),
            ('Employer Dashboard', 'Posting analytics, candidate pipeline, and billing'),
        ],
        'stats': [('50K+', 'Jobs Posted'), ('200K+', 'Candidates'), ('12K+', 'Hires Made'), ('4.8/5', 'Rating')],
    },
    'eventticket-live': {
        'title': 'EventLive', 'tagline': 'Event Ticketing & Management',
        'eyebrow': 'EVENT PLATFORM',
        'hero_desc': 'Complete event management: ticketing, check-in, analytics, and live streaming integration.',
        'features': [
            ('Ticket Shop', 'Multi-tier ticketing with early-bird and VIP pricing'),
            ('Check-In App', 'QR code scanning with real-time attendance tracking'),
            ('Event Analytics', 'Sales, attendance, and revenue dashboards'),
            ('Live Streaming', 'Built-in streaming with recording and replay'),
        ],
        'stats': [('25K+', 'Events'), ('2M+', 'Tickets Sold'), ('8K+', 'Organizers'), ('4.7/5', 'Rating')],
    },
    'cryptovault-pro': {
        'title': 'CryptoVault', 'tagline': 'Crypto Portfolio & Trading Dashboard',
        'eyebrow': 'CRYPTO PLATFORM',
        'hero_desc': 'Multi-exchange crypto portfolio tracker with real-time PnL, alerts, and tax reporting.',
        'features': [
            ('Portfolio Sync', 'Connect exchanges and wallets for a unified view'),
            ('Real-Time PnL', 'Live profit/loss with historical performance charts'),
            ('Alert Engine', 'Price, volume, and custom condition alerts via email and SMS'),
            ('Tax Reports', 'Generate IRS-compliant tax reports with cost-basis tracking'),
        ],
        'stats': [('$2B+', 'Assets Tracked'), ('50K+', 'Users'), ('300+', 'Coins'), ('99.99%', 'Uptime')],
    },
    'resupro': {
        'title': 'ResuPro', 'tagline': 'AI Resume & CV Builder for Career Success',
        'eyebrow': 'CAREER PLATFORM',
        'hero_desc': 'Create interview-winning resumes in minutes with AI-powered writing, professional templates, and one-click export to PDF.',
        'features': [
            ('AI Writing Assistant', 'Smart sentence suggestions tuned for every job description'),
            ('ATS-Friendly Templates', 'Applicant tracking system optimised layouts recruiters love'),
            ('One-Click Export', 'Pixel-perfect PDF and DOCX exports in any language'),
            ('Career Analytics', 'Track views, downloads, and interview success rates'),
        ],
        'stats': [('500K+', 'Resumes Built'), ('4.9/5', 'User Rating'), ('200+', 'Templates'), ('2.3x', 'More Interviews')],
    },
}

# ── Project images (curated Unsplash, verified) ──────────────────────────────
# Each project gets a hero image, showcase image, and optional feature imagery.
UNSPLASH = {
    'hero-dash': 'photo-1460925895917-afdab827c52f/?auto=format&fit=crop&w=1200&q=80',
    'team-meet': 'photo-1521737711867-e3b97375f902/?auto=format&fit=crop&w=1200&q=80',
    'office-space': 'photo-1497366216548-37526070297c/?auto=format&fit=crop&w=1200&q=80',
    'office-anchor': 'photo-1497366754035-f200968a6e72/?auto=format&fit=crop&w=1200&q=80',
    'code-mac': 'photo-1498050108023-c5249f4df085/?auto=format&fit=crop&w=1200&q=80',
    'analytics': 'photo-1551288049-bebda4e38f71/?auto=format&fit=crop&w=1200&q=80',
    'planning': 'photo-1454165804606-c3d57bc86b40/?auto=format&fit=crop&w=1200&q=80',
    'laptop-desk': 'photo-1522199755839-a2bacb67c546/?auto=format&fit=crop&w=1200&q=80',
    'ccard-multi': 'photo-1556742049-0cfed4f6a45d/?auto=format&fit=crop&w=1200&q=80',
    'ccard-pay': 'photo-1563013544-824ae1b704d3/?auto=format&fit=crop&w=1200&q=80',
    'coins-pay': 'photo-1526304640581-d334cdbbf45e/?auto=format&fit=crop&w=1200&q=80',
    'terminal-pay': 'photo-1559526324-4b87b5e36e44/?auto=format&fit=crop&w=1200&q=80',
    'classroom': 'photo-1509062522246-3755977927d7/?auto=format&fit=crop&w=1200&q=80',
    'lecture': 'photo-1524178232363-1fb2b075b655/?auto=format&fit=crop&w=1200&q=80',
    'grad-cap': 'photo-1546410531-bb4caa6b424d/?auto=format&fit=crop&w=1200&q=80',
    'students-code': 'photo-1522202176988-66273c2fd55f/?auto=format&fit=crop&w=1200&q=80',
    'books': 'photo-1488190211105-8b0e65b80b4e/?auto=format&fit=crop&w=1200&q=80',
    'medical': 'photo-1576091160399-112ba8d25d1d/?auto=format&fit=crop&w=1200&q=80',
    'doctor-tab': 'photo-1579684385127-1ef15d508118/?auto=format&fit=crop&w=1200&q=80',
    'doc-cons': 'photo-1584982751601-97dcc096659c/?auto=format&fit=crop&w=1200&q=80',
    'hospital': 'photo-1538108149393-fbbd81895907/?auto=format&fit=crop&w=1200&q=80',
    'house-keys': 'photo-1560518883-ce09059eeffa/?auto=format&fit=crop&w=1200&q=80',
    'lux-home': 'photo-1512917774080-9991f1c4c750/?auto=format&fit=crop&w=1200&q=80',
    'house-yard': 'photo-1600585154340-be6161a56a0c/?auto=format&fit=crop&w=1200&q=80',
    'home-mod': 'photo-1568605114967-8130f3a36994/?auto=format&fit=crop&w=1200&q=80',
    'interior': 'photo-1600585154526-990dced4db0d/?auto=format&fit=crop&w=1200&q=80',
    'marketing': 'photo-1553729459-efe14ef6055d/?auto=format&fit=crop&w=1200&q=80',
    'brand-tools': 'photo-1466692476868-aef1dfb1e735/?auto=format&fit=crop&w=1200&q=80',
    'strategy': 'photo-1533750349088-cd871a92f312/?auto=format&fit=crop&w=1200&q=80',
    'seo-graph': 'photo-1547658719-da2b51169166/?auto=format&fit=crop&w=1200&q=80',
    'ecom-shop': 'photo-1472851294608-062f824d29cc/?auto=format&fit=crop&w=1200&q=80',
    'store-front': 'photo-1441986300917-64674bd600d8/?auto=format&fit=crop&w=1200&q=80',
    'shopping-bags': 'photo-1567401893414-76b7b1e5a7a5/?auto=format&fit=crop&w=1200&q=80',
    'checkout': 'photo-1441986300917-64674bd600d8/?auto=format&fit=crop&w=1200&q=80',
    'ai-robot': 'photo-1677442136019-21780ecad995/?auto=format&fit=crop&w=1200&q=80',
    'ai-chip': 'photo-1620712943543-bcc4688e7485/?auto=format&fit=crop&w=1200&q=80',
    'ai-gen': 'photo-1531482615713-2afd69097998/?auto=format&fit=crop&w=1200&q=80',
    'robot-desk': 'photo-1485827404703-89b55fcc595e/?auto=format&fit=crop&w=1200&q=80',
    'pizza': 'photo-1565299624946-b28f40a0ae38/?auto=format&fit=crop&w=1200&q=80',
    'food-bowl': 'photo-1504674900247-0877df9cc836/?auto=format&fit=crop&w=1200&q=80',
    'burger': 'photo-1568901346375-23c9450c58cd/?auto=format&fit=crop&w=1200&q=80',
    'restaurant': 'photo-1514933651103-005eec06c04b/?auto=format&fit=crop&w=1200&q=80',
    'nature-mtn': 'photo-1469474968028-56623f02e42e/?auto=format&fit=crop&w=1200&q=80',
    'beach-travel': 'photo-1476514525535-07fb3b4ae5f1/?auto=format&fit=crop&w=1200&q=80',
    'santorini': 'photo-1502920917128-1aa500764cbd/?auto=format&fit=crop&w=1200&q=80',
    'travel-path': 'photo-1503220317375-aaad61436b1b/?auto=format&fit=crop&w=1200&q=80',
    'fitness-gym': 'photo-1534438327276-14e5300c3a48/?auto=format&fit=crop&w=1200&q=80',
    'workout': 'photo-1571019613454-1cb2f99b2d8b/?auto=format&fit=crop&w=1200&q=80',
    'fitness-run': 'photo-1476480862126-209bfaa8edc8/?auto=format&fit=crop&w=1200&q=80',
    'gym-db': 'photo-1517836357463-d25dfeac3438/?auto=format&fit=crop&w=1200&q=80',
    'interview': 'photo-1573497019940-1c28c88b4f3e/?auto=format&fit=crop&w=1200&q=80',
    'job-search': 'photo-1586281380349-632531db7ed4/?auto=format&fit=crop&w=1200&q=80',
    'office-tower': 'photo-1486406146926-c627a92ad1ab/?auto=format&fit=crop&w=1200&q=80',
    'handshake': 'photo-1521791136064-7986c2920216/?auto=format&fit=crop&w=1200&q=80',
    'women-work': 'photo-1573496359142-b8d87734a5a2/?auto=format&fit=crop&w=1200&q=80',
    'concert': 'photo-1470229722913-7c0e2dbbafd3/?auto=format&fit=crop&w=1200&q=80',
    'event-crowd': 'photo-1501281668745-f7f57925c3b4/?auto=format&fit=crop&w=1200&q=80',
    'conference': 'photo-1540575467063-178a50c2df87/?auto=format&fit=crop&w=1200&q=80',
    'event-stage': 'photo-1459749411175-04bf5292ceea/?auto=format&fit=crop&w=1200&q=80',
    'crypto-coins': 'photo-1518546305927-5a555bb7020d/?auto=format&fit=crop&w=1200&q=80',
    'crypto-chart': 'photo-1642790106117-e829e14a795f/?auto=format&fit=crop&w=1200&q=80',
    'crypto-key': 'photo-1621761191319-c6fb62004040/?auto=format&fit=crop&w=1200&q=80',
    'btc-cash': 'photo-1639322537228-f710d846310a/?auto=format&fit=crop&w=1200&q=80',
    'virtual-care': 'photo-1584515933487-779824d29309/?auto=format&fit=crop&w=1200&q=80',
    'health-vid': 'photo-1571771894821-ce9b6c11b08e/?auto=format&fit=crop&w=1200&q=80',
}
IMG_BASE = 'https://images.unsplash.com/'

# repo → (hero, showcase, features[4])
IMAGES: Dict[str, Dict[str, Any]] = {
    'nexa-marketplace':    {'hero': 'ecom-shop', 'showcase': 'store-front', 'features': ['shopping-bags', 'team-meet', 'analytics', 'office-space']},
    'verapay-fintech':     {'hero': 'ccard-multi', 'showcase': 'terminal-pay', 'features': ['ccard-pay', 'coins-pay', 'code-mac', 'analytics']},
    'edulify-lms':         {'hero': 'students-code', 'showcase': 'classroom', 'features': ['grad-cap', 'lecture', 'books', 'students-code']},
    'telecare-health':     {'hero': 'doctor-tab', 'showcase': 'medical', 'features': ['doc-cons', 'hospital', 'virtual-care', 'health-vid']},
    'realspace-estate':    {'hero': 'lux-home', 'showcase': 'interior', 'features': ['house-keys', 'house-yard', 'home-mod', 'lux-home']},
    'marketsphere':        {'hero': 'marketing', 'showcase': 'brand-tools', 'features': ['strategy', 'seo-graph', 'team-meet', 'office-anchor']},
    'storefront-pro':      {'hero': 'ecom-shop', 'showcase': 'checkout', 'features': ['store-front', 'shopping-bags', 'ccard-pay', 'laptop-desk']},
    'ai-content-studio':   {'hero': 'ai-chip', 'showcase': 'ai-robot', 'features': ['ai-gen', 'robot-desk', 'code-mac', 'women-work']},
    'fooddelivery-express':{'hero': 'pizza', 'showcase': 'restaurant', 'features': ['food-bowl', 'burger', 'team-meet', 'laptop-desk']},
    'travelbook-pro':      {'hero': 'santorini', 'showcase': 'nature-mtn', 'features': ['beach-travel', 'travel-path', 'office-space', 'handshake']},
    'fitnesscoach-go':     {'hero': 'fitness-gym', 'showcase': 'workout', 'features': ['fitness-run', 'gym-db', 'team-meet', 'code-mac']},
    'jobboard-hirehub':    {'hero': 'interview', 'showcase': 'office-tower', 'features': ['job-search', 'handshake', 'team-meet', 'office-space']},
    'eventticket-live':    {'hero': 'concert', 'showcase': 'event-crowd', 'features': ['event-stage', 'conference', 'pizza', 'team-meet']},
    'cryptovault-pro':     {'hero': 'crypto-coins', 'showcase': 'crypto-chart', 'features': ['crypto-key', 'btc-cash', 'code-mac', 'analytics']},
    'resupro':             {'hero': 'laptop-desk', 'showcase': 'office-anchor', 'features': ['women-work', 'office-space', 'team-meet', 'analytics']},
}

# repo → lucide icon names per feature card + showcase bullet icons
ICONS: Dict[str, Dict[str, Any]] = {
    'nexa-marketplace':    {'features': ['store', 'package', 'credit-card', 'bar-chart-3'], 'showcase': ['credit-card', 'users', 'bar-chart-3']},
    'verapay-fintech':     {'features': ['wallet', 'zap', 'shield-check', 'file-check'], 'showcase': ['wallet', 'shield-check', 'globe']},
    'edulify-lms':         {'features': ['graduation-cap', 'video', 'trending-up', 'award'], 'showcase': ['video', 'graduation-cap', 'trending-up']},
    'telecare-health':     {'features': ['heart-pulse', 'video', 'calendar-check', 'file-check'], 'showcase': ['heart-pulse', 'video', 'calendar-check']},
    'realspace-estate':    {'features': ['home', 'map-pin', 'compass', 'building-2'], 'showcase': ['home', 'map-pin', 'compass']},
    'marketsphere':        {'features': ['target', 'bar-chart-3', 'pen-tool', 'search'], 'showcase': ['target', 'pen-tool', 'bar-chart-3']},
    'storefront-pro':      {'features': ['shopping-cart', 'layers', 'refresh-cw', 'credit-card'], 'showcase': ['shopping-cart', 'layers', 'refresh-cw']},
    'ai-content-studio':   {'features': ['sparkles', 'bot', 'list-checks', 'bar-chart-3'], 'showcase': ['sparkles', 'bot', 'list-checks']},
    'fooddelivery-express':{'features': ['truck', 'smartphone', 'clock', 'star'], 'showcase': ['truck', 'smartphone', 'clock']},
    'travelbook-pro':      {'features': ['plane', 'map', 'calendar-range', 'compass'], 'showcase': ['plane', 'map', 'compass']},
    'fitnesscoach-go':     {'features': ['dumbbell', 'activity', 'video', 'trending-up'], 'showcase': ['dumbbell', 'activity', 'trending-up']},
    'jobboard-hirehub':    {'features': ['briefcase', 'users', 'file-check', 'trending-up'], 'showcase': ['briefcase', 'users', 'trending-up']},
    'eventticket-live':    {'features': ['ticket', 'calendar-days', 'music', 'bar-chart-3'], 'showcase': ['ticket', 'calendar-days', 'music']},
    'cryptovault-pro':     {'features': ['lock', 'shield-check', 'wallet', 'file-check'], 'showcase': ['lock', 'trending-up', 'shield-check']},
    'resupro':            {'features': ['file-text', 'sparkles', 'wand-2', 'award'], 'showcase': ['file-text', 'sparkles', 'wand-2']},
}
FALLBACK_ICONS = {'features': ['layout-dashboard', 'shield-check', 'zap', 'trending-up'], 'showcase': ['layout-dashboard', 'zap', 'trending-up']}

# ── LumicorePro universal brand logo (transparent background) ────────────────
LUMICORE_MARK = '''<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LumicorePro" fill="none">
  <defs>
    <linearGradient id="lc-g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffd9a0"/>
      <stop offset="42%" stop-color="#e2b26b"/>
      <stop offset="100%" stop-color="#7a4fd0"/>
    </linearGradient>
    <radialGradient id="lc-r" cx="50%" cy="42%" r="60%">
      <stop offset="0%" stop-color="#fff8ec"/>
      <stop offset="55%" stop-color="#ffd9a0"/>
      <stop offset="100%" stop-color="#7a4fd0"/>
    </radialGradient>
  </defs>
  <g stroke="url(#lc-r)" stroke-width="1.6" stroke-linecap="round" opacity="0.9">
    <line x1="32" y1="6" x2="32" y2="16"/>
    <line x1="32" y1="58" x2="32" y2="48"/>
    <line x1="6" y1="32" x2="16" y2="32"/>
    <line x1="58" y1="32" x2="48" y2="32"/>
  </g>
  <path d="M32 5 L54 18 V46 L32 59 L10 46 V18 Z" stroke="url(#lc-r)" stroke-width="2"/>
  <path d="M32 8 L50 19 L50 45 L32 56 L14 45 L14 19 Z" fill="url(#lc-g)" opacity="0.22"/>
  <path d="M32 8 L50 19 L50 45 L32 56 L14 45 L14 19 Z" stroke="#ffd9a0" stroke-width="2" stroke-linejoin="round"/>
  <path d="M32 17 L44 24.5 V39.5 L32 47 L20 39.5 V24.5 Z" stroke="#ffffff" stroke-opacity="0.9" stroke-width="1.4" stroke-linejoin="round"/>
  <circle cx="32" cy="32" r="8" fill="url(#lc-r)"/>
  <path d="M28 32 h8 M32 28 v8" stroke="#241a3d" stroke-width="1.4" stroke-linecap="round" opacity="0.8"/>
</svg>'''


# ── Directory → repo mapping for the 14 live projects ──────────────────────
DIR_TO_REPO = {
    'generated-website': 'nexa-marketplace',
    'generated-website-002': 'verapay-fintech',
    'generated-website-003': 'edulify-lms',
    'generated-website-004': 'telecare-health',
    'generated-website-005': 'realspace-estate',
    'generated-website-006': 'marketsphere',
    'generated-website-007': 'storefront-pro',
    'generated-website-008': 'ai-content-studio',
    'food-restaurant-001': 'fooddelivery-express',
    'tourism-travel-001': 'travelbook-pro',
    'edtech-fitness-001': 'fitnesscoach-go',
    'realestate-realestate-001': 'jobboard-hirehub',
    'tourism-travel-001-002': 'eventticket-live',
    'personal-portfolio-001': 'cryptovault-pro',
}


def _svg_logo(name: str, palette: Dict[str, str]) -> str:
    """Generate a unique geometric SVG logo for the project (token-driven)."""
    h = sum(ord(c) for c in name)
    shapes = [
        f'<polygon points="24,4 42,14 42,34 24,44 6,34 6,14" fill="var(--t-primary)" opacity="0.95"/>'
        f'<polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9"/>'
        f'<polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="var(--t-accent)"/>',
        f'<rect x="8" y="8" width="32" height="32" rx="4" fill="var(--t-primary)" transform="rotate(45 24 24)" opacity="0.95"/>'
        f'<circle cx="24" cy="24" r="10" fill="white" opacity="0.9"/>'
        f'<circle cx="24" cy="24" r="6" fill="var(--t-accent)"/>',
        f'<polygon points="24,4 44,20 38,44 10,44 4,20" fill="var(--t-primary)" opacity="0.95"/>'
        f'<polygon points="24,14 34,22 31,36 17,36 14,22" fill="white" opacity="0.9"/>'
        f'<polygon points="24,20 28,23 27,29 21,29 20,23" fill="var(--t-accent)"/>',
        f'<rect x="4" y="4" width="40" height="40" rx="12" fill="var(--t-primary)" opacity="0.95"/>'
        f'<rect x="12" y="12" width="24" height="24" rx="6" fill="white" opacity="0.9"/>'
        f'<rect x="18" y="18" width="12" height="12" rx="3" fill="var(--t-accent)"/>',
    ]
    shape = shapes[h % len(shapes)]
    return f'<svg viewBox="0 0 48 48" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg">{shape}</svg>'


def _unique_logo_jsx(name: str, palette: Dict[str, str]) -> str:
    svg = _svg_logo(name, palette)
    words = name.replace('-', ' ').split()
    primary = words[0] if words else name
    accent = ' '.join(words[1:]) if len(words) > 1 else ''
    accent_span = f'''<span style={{{{ color: 'var(--t-primary)' }}}} className="ml-0.5">{accent}</span>''' if accent else ''
    return f'''import React from 'react';
import {{ Link }} from 'react-router-dom';

export default function UniqueLogo({{ size = 'md' }}) {{
  const sz = {{ sm: 24, md: 32, lg: 40 }}[size] || 32;
  return (
    <Link to="/" className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90">
      <div style={{{{ width: sz, height: sz }}}} className="shrink-0">
        {svg}
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{{{ color: 'var(--t-heading)' }}}}>
        {primary} {accent_span}
      </span>
    </Link>
  );
}}
'''


def _index_html(title: str, tagline: str) -> str:
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} - {tagline}</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet" />
    <meta name="description" content="{tagline} — {title}. Built with LumicorePro AI Agent." />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{tagline}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="{title}" />
    <meta property="og:locale" content="en_US" />
    <meta property="og:image" content="https://malikusmangoraya.github.io/{title.lower().replace(' ', '-')}/og.jpg" />
    <meta property="og:url" content="https://malikusmangoraya.github.io/{title.lower().replace(' ', '-')}/" />
    <meta name="twitter:card" content="summary_large_image" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''


def _index_css(palette: Dict[str, str], ui_style: str = UI_STYLE_DEFAULT, extra_css: str = '') -> str:
    p = palette['primary']
    a = palette['accent']
    h = palette['heading']
    r, g, b = int(p[1:3], 16), int(p[3:5], 16), int(p[5:7], 16)
    style_css = UI_STYLE_CSS.get(ui_style, UI_STYLE_CSS[UI_STYLE_DEFAULT])
    if extra_css:
        style_css = style_css + '\n' + extra_css
    return f'''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  body {{
    background-color: var(--t-canvas);
    @apply antialiased;
    font-family: 'Poppins', sans-serif;
    color: var(--t-text);
  }}
  h1, h2, h3, h4, h5, h6 {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    color: var(--t-heading);
  }}
}}

@layer components {{
  .btn-primary {{
    background-color: {p};
    color: white;
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }}
  .btn-primary:hover {{
    opacity: 0.92;
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba({r},{g},{b},0.25);
  }}
  .btn-outline {{
    border: 2px solid {h};
    color: {h};
    padding: 0.75rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }}
  .btn-outline:hover {{
    background-color: {h};
    color: white;
  }}
  .skeleton-shimmer {{
    background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }}
  .cls-reserve {{
    content-visibility: auto;
    contain-intrinsic-size: 0 500px;
  }}
  .glass-md {{
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
}}

@layer utilities {{
  .section-eyebrow {{
    font-family: 'Roboto', sans-serif;
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: {p};
    margin-bottom: 0.5rem;
    display: inline-block;
    position: relative;
    padding-left: 3rem;
  }}
  .section-eyebrow::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    width: 2.5rem;
    height: 2px;
    background-color: {p};
  }}
  .section-heading {{
    font-size: 2rem;
    font-weight: 800;
    color: {h};
    line-height: 1.2;
  }}
  .fluid-container {{
    width: 100%;
    max-width: 1280px;
    margin-inline: auto;
    padding-inline: clamp(1rem, 5vw, 4rem);
  }}
}}

@keyframes shimmer {{
  0% {{ background-position: 200% 0; }}
  100% {{ background-position: -200% 0; }}
}}

:root {{
  --fluid-space-0: clamp(0rem, 0vw, 0rem);
  --fluid-space-1: clamp(0.25rem, 0.5vw + 0.125rem, 0.5rem);
  --fluid-space-2: clamp(0.5rem, 1vw + 0.25rem, 1rem);
  --fluid-space-3: clamp(1rem, 2vw + 0.5rem, 1.5rem);
  --fluid-space-4: clamp(1.5rem, 3vw + 0.75rem, 2rem);
  --fluid-space-5: clamp(2rem, 4vw + 1rem, 3rem);
  --fluid-space-6: clamp(3rem, 5vw + 1.5rem, 4rem);
  --fluid-space-7: clamp(4rem, 6vw + 2rem, 5rem);
  --fluid-space-8: clamp(5rem, 8vw + 2.5rem, 7rem);
  --t-canvas: {palette.get('navBg', '#f8fafc')};
  --t-surface: {palette.get('cardBg', '#ffffff')};
  --t-primary: {p};
  --t-accent: {a};
  --t-heading: {h};
  --t-footer: {palette.get('footerBg', h)};
  --t-text: {palette.get('text', '#1e293b')};
  --t-muted: {palette.get('muted', '#64748b')};
  --t-border: {palette.get('border', '#e2e8f0')};
  --t-bg: {palette.get('cardBg', '#ffffff')};
  --t-canvas-rgb: {_rgb(palette.get('navBg', '#f8fafc'))};
  --t-surface-rgb: {_rgb(palette.get('cardBg', '#ffffff'))};
  --t-primary-rgb: {_rgb(p)};
  --t-accent-rgb: {_rgb(a)};
  --t-heading-rgb: {_rgb(h)};
  --t-text-rgb: {_rgb(palette.get('text', '#1e293b'))};
}}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #f1f5f9; }}
::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}

@media (max-width: 768px) {{
  .section-heading {{ font-size: 1.5rem; }}
}}
{style_css}
'''


def _design_tokens_json(repo_name: str, palette: Dict[str, str], ui_style: str = 'glassmorphism',
                        region: str = 'default') -> str:
    import json
    tokens = {
        'style': 'consulting_pro',
        'name': 'Consulting Professional',
        'ui_style': ui_style,
        'target_region': region,
        'project_name': repo_name,
        'palette': {
            'primary': palette['primary'],
            'accent': palette['accent'],
            'heading': palette['heading'],
            'navBg': palette['navBg'],
            'footerBg': palette['footerBg'],
            'text': '#1e293b',
            'muted': '#64748b',
            'card': '#ffffff',
            'surface': '#f8fafc',
            'border': '#e2e8f0',
            'bg': '#ffffff',
        },
        'typography': {'display': 'Poppins', 'sans': 'Roboto', 'mono': 'JetBrains Mono'},
        'theme': 'light',
    }
    return json.dumps(tokens, indent=2)


def _tailwind_config(palette: Dict[str, str]) -> str:
    p = palette['primary']
    a = palette['accent']
    h = palette['heading']
    pr, pg, pb = int(p[1:3], 16), int(p[3:5], 16), int(p[5:7], 16)
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    hr, hg, hb = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return f'''/** @type {{import('tailwindcss').Config}} */
export default {{
  content: ['./index.html', './src/**/*.{{js,jsx}}'],
  darkMode: 'class',
  theme: {{
    extend: {{
      colors: {{
        primary: 'rgb(var(--t-primary-rgb, {pr} {pg} {pb}) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, {ar} {ag} {ab}) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, {hr} {hg} {hb}) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 248 250 252) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 255 255 255) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 30 41 59) / <alpha-value>)',
      }},
      fontFamily: {{
        sans: ['Roboto', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
      }},
    }},
  }},
  plugins: [],
}};
'''


def _lumicore_logo_jsx() -> str:
    """LumicorePro universal logo component (transparent SVG mark + wordmark)."""
    return '''import React from 'react';
import { Link } from 'react-router-dom';

export default function LumicorePro({ to = '/', size = 34, dark = false }) {
  const gid = React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const gradId = `lcg-${gid}`;
  const mark = `url(#${gradId})`;
  return (
    <Link to={to} className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90" aria-label="LumicorePro">
      <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: 'var(--t-primary)' }} />
            <stop offset="100%" style={{ stopColor: 'var(--t-accent)' }} />
          </linearGradient>
        </defs>
        <rect x="6" y="6" width="52" height="52" rx="14" fill={mark} />
        <path d="M32 14 L44 22 V38 L32 46 L20 38 V22 Z" fill="none" stroke="white" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M32 21 L38 25.5 V32 L32 36.5 L26 32 V25.5 Z" fill="white" opacity="0.92" />
        <circle cx="32" cy="27.5" r="2.4" fill="var(--t-primary)" />
      </svg>
      <span className="font-display font-bold tracking-tight leading-none">
        <span className={dark ? 'text-white' : 'text-slate-900'}>Lumi</span>
        <span className="bg-gradient-to-r from-violet-500 to-cyan-400 bg-clip-text text-transparent">core</span>
        <span className={dark ? 'text-white/90' : 'text-slate-500'}>&#xb7;Pro</span>
      </span>
    </Link>
  );
}
'''


def _navbar_jsx(title: str, palette: Dict[str, str]) -> str:
    p = palette['primary']
    return f'''import React, {{ useState }} from 'react';
import {{ Link, useLocation }} from 'react-router-dom';
import {{ Menu, X }} from 'lucide-react';
import LumicorePro from './LumicorePro';

export default function Navbar() {{
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const links = [
    {{ path: '/', label: 'Home' }},
    {{ path: '/about', label: 'About' }},
    {{ path: '/services', label: 'Services' }},
    {{ path: '/contact', label: 'Contact' }},
  ];
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--t-border)] bg-canvas/95 backdrop-blur supports-[backdrop-filter]:bg-canvas/80">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <LumicorePro />
        <div className="hidden md:flex items-center gap-8">
          {{links.map(l => (
            <Link key={{l.path}} to={{l.path}} className="text-sm font-medium hover:text-primary transition-colors" style={{{{ color: loc.pathname === l.path ? 'var(--t-primary)' : 'var(--t-text)' }}}}>
              {{l.label}}
            </Link>
          ))}}
          <span className="hidden lg:inline-block text-sm font-bold" style={{{{ color: 'var(--t-primary)' }}}}>{title}</span>
          <Link to="/contact" className="btn-primary text-sm">{title} Free Demo</Link>
        </div>
        <button onClick={{() => setOpen(!open)}} className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100" aria-label="Menu">
          {{open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}}
        </button>
      </div>
      {{open && (
        <div className="md:hidden border-t border-[var(--t-border)] bg-canvas px-6 pb-4 pt-2">
          {{links.map(l => (
            <Link key={{l.path}} to={{l.path}} onClick={{() => setOpen(false)}} className="block py-2 text-sm font-medium hover:text-primary transition-colors" style={{{{ color: 'var(--t-text)' }}}}>
              {{l.label}}
            </Link>
          ))}}
          <Link to="/contact" onClick={{() => setOpen(false)}} className="btn-primary mt-2 text-sm text-center w-full">
            Get Started
          </Link>
        </div>
      )}}
    </nav>
  );
}}
'''


def _footer_jsx(title: str, palette: Dict[str, str]) -> str:
    return f'''import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ CheckCircle2 }} from 'lucide-react';
import LumicorePro from './LumicorePro';

export default function Footer() {{
  const [email, setEmail] = useState('');
  const [sub, setSub] = useState(false);
  return (
    <footer className="text-white" style={{{{ backgroundColor: 'var(--t-footer)' }}}}>
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-4">
          <div className="space-y-4">
            <LumicorePro dark />
            <p className="text-sm text-slate-300 leading-relaxed max-w-xs">
              Building exceptional digital products with performance, security, and design excellence.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              99.99% Operational
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/services" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">Case Studies</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Enterprise</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><Link to="/about" className="hover:text-white transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-sm uppercase tracking-wider mb-4">Stay Updated</h4>
            <p className="text-xs text-slate-300 mb-3">Weekly product updates and insights.</p>
            {{sub ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle2 className="h-4 w-4" /> Subscribed!
              </div>
            ) : (
              <form onSubmit={{e => {{ e.preventDefault(); if (email) setSub(true); }} }} className="space-y-2">
                <input type="email" required value={{email}} onChange={{e => setEmail(e.target.value)}} placeholder="Email address" className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-xs text-white placeholder-slate-400 focus:border-white/40 focus:outline-none" />
                <button type="submit" className="w-full rounded-lg px-3 py-2 text-xs font-semibold text-white transition-colors" style={{{{ backgroundColor: '{palette["primary"]}' }}}}>
                  Subscribe
                </button>
              </form>
            )}}
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>&copy; {{new Date().getFullYear()}} {title}. All rights reserved. Powered by <span className="font-semibold text-white">LumicorePro</span>.</p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-white">Twitter</a>
            <a href="#" className="hover:text-white">LinkedIn</a>
            <a href="#" className="hover:text-white">GitHub</a>
          </div>
        </div>
      </div>
    </footer>
  );
}}
'''


def _home_jsx(title: str, tagline: str, eyebrow: str, hero_desc: str,
              features: list, stats: list, palette: Dict[str, str],
              repo_name: str = '', ui_style: str = UI_STYLE_DEFAULT) -> str:
    p = palette['primary']
    h = palette['heading']
    icon_names = (ICONS.get(repo_name) or _derive_icons(repo_name))['features']
    show_icons = (ICONS.get(repo_name) or _derive_icons(repo_name))['showcase']
    images = IMAGES.get(repo_name) or _derive_images(repo_name)

    hero_img = ''
    show_img = ''
    feat_img = ''
    if images:
        hil = images['hero']
        sil = images['showcase']
        fil = images['features'][0] if images['features'] else 'office-space'
        hero_img = (
            f'<div className="hidden lg:block relative">\n'
            f'            <img src="{IMG_BASE}{UNSPLASH[hil]}" alt="{title} product overview" className="w-full h-96 lg:h-105 rounded-2xl object-cover shadow-2xl" loading="eager" />\n'
            f'            <div className="absolute -bottom-6 -left-6 rounded-xl bg-white p-4 shadow-xl border border-slate-100 flex items-center gap-3">\n'
            f'              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />\n'
            f'              <span className="text-xs font-semibold text-slate-700">Trusted by 50,000+ businesses worldwide</span>\n'
            f'            </div>\n'
            f'          </div>'
        )
        show_img = (
            f'<img src="{IMG_BASE}{UNSPLASH[sil]}" alt="{title} platform showcase" className="w-full rounded-2xl object-cover shadow-xl" style={{{{ maxHeight: 420 }}}} loading="lazy" />'
        )
        feat_img = (
            f'<img src="{IMG_BASE}{UNSPLASH[fil]}" alt="{title} features" className="w-full h-52 object-cover rounded-xl" loading="lazy" />'
        )

    # Feature cards with real Lucide icons + hover image reveal
    all_icons = list(dict.fromkeys([*icon_names, *show_icons]))
    import_names = []
    for x in all_icons:
        if not x:
            continue
        pc = _pascal(x)
        import_names.append('Home as HomeIcon' if pc == 'Home' else pc)
    icon_imports = ', '.join(import_names)
    feat_rows = []
    for tidx, (ftitle, fdesc) in enumerate(features):
        ic = _pascal(icon_names[tidx] if tidx < len(icon_names) else 'check-circle')
        if ic == 'Home':
            ic = 'HomeIcon'
        feat_img_extra = ''
        if images and tidx < len(images['features']):
            flag = images['features'][tidx]
            feat_img_extra = (
                f'<div className="relative mt-5 overflow-hidden rounded-lg" style={{{{ height: 120 }}}}>\n'
                f'                <img src="{IMG_BASE}{UNSPLASH[flag]}" alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy" />\n'
                f'                <div className="absolute inset-0 flex items-end p-3" style={{{{ background: "linear-gradient(to top, rgba(2,6,23,.4), transparent)" }}}} />\n'
                f'              </div>'
            )
        feat_rows.append(f'''              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
              <div className="p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg" style={{{{ background: 'linear-gradient(135deg, {p}, {palette.get('accent', p)})' }}}}>
                  <{ic} className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{{{ color: '{h}' }}}}>{ftitle}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{fdesc}</p>
              </div>
              {feat_img_extra}
            </div>''')
    feat_jsx = '\n'.join(feat_rows)

    stat_rows = []
    for sval, slabel in stats:
        stat_rows.append(f'''            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{{{ color: '{p}' }}}}>{'{'}'{sval}'{'}'}</div>
              <div className="text-sm text-slate-500">{slabel}</div>
            </div>''')
    stat_jsx = '\n'.join(stat_rows)

    # Showcase bullets with icons
    bullets = []
    bs = [
        ('Enterprise-grade security and compliance', 'shield-check'),
        ('Global support across time zones, 24/7', 'globe'),
        ('Seamless integrations with your stack', 'layers'),
    ]
    for i, (btxt, bic) in enumerate(bs):
        icc = _pascal(show_icons[i] if i < len(show_icons) else bic)
        if icc == 'Home':
            icc = 'HomeIcon'
        bullets.append(f'''                <li className="flex items-center gap-3">
                <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white" style={{{{ background: 'linear-gradient(135deg, {p}, {palette.get('accent', p)})' }}}}><{icc} className="h-4 w-4" /></span>
                <span className="text-sm font-medium text-slate-700">{btxt}</span>
              </li>''')
    bullets_jsx = '\n'.join(bullets)

    return f'''import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight, {icon_imports} }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {{
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden py-16 lg:py-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="max-w-2xl">
              <span className="section-eyebrow">{eyebrow}</span>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight mb-6" style={{{{ color: '{h}' }}}}>
                {tagline}
              </h1>
              <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-lg">
                {hero_desc}
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/contact" className="btn-primary">Get Started <ArrowRight className="h-4 w-4" /></Link>
                <Link to="/services" className="btn-outline">View Services</Link>
              </div>
              <ul className="mt-8 space-y-3 max-w-sm">
{bullets_jsx}
              </ul>
            </div>
            {hero_img}
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">What We Offer</span>
              <h2 className="section-heading">Why Choose {title}?</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
{feat_jsx}
            </div>
            {feat_img}
          </div>
        </section>

        <section className="py-16 px-6">
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
{stat_jsx}
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>{show_img}</div>
            <div>
              <span className="section-eyebrow">Platform Preview</span>
              <h2 className="section-heading mb-4">Built for the modern {tagline.split(' ')[-1] or 'enterprise'}</h2>
              <p className="text-slate-500 leading-relaxed mb-6">
                Every detail is engineered for performance, scalability, and a flawless user experience — from first click to everyday operations.
              </p>
              <Link to="/about" className="btn-primary">Learn More <ArrowRight className="h-4 w-4" /></Link>
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-3xl mx-auto text-center rounded-2xl p-12" style={{{{ background: 'linear-gradient(135deg, {h}, {p})' }}}}>
            <h2 className="text-3xl font-extrabold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-white/70 mb-8">
              Join thousands of professionals choosing {title} as their growth platform.
            </p>
            <Link to="/contact" className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3 font-semibold transition-all hover:shadow-xl" style={{{{ color: '{p}' }}}}>
              Start Free Trial <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}}
'''


def _standalone_html(repo_name: str) -> str:
    """Render a self-contained consulting-style landing page (for non-Vite projects)."""
    pal = PALETTES.get(repo_name, PALETTES['nexa-marketplace'])
    prof = PROFILES.get(repo_name, PROFILES['nexa-marketplace'])
    p = pal['primary']
    a = pal['accent']
    h = pal['heading']
    fb = pal['footerBg']
    title = prof['title']
    tagline = prof['tagline']
    eyebrow = prof['eyebrow']
    hero_desc = prof['hero_desc']
    features = prof['features']
    stats = prof['stats']
    initials = title[:2].upper()
    images = IMAGES.get(repo_name)
    icons = ICONS.get(repo_name, FALLBACK_ICONS)

    hero_img = ''
    show_img = ''
    if images:
        hero_img = (
            f'<img class="hero-img" src="{IMG_BASE}{UNSPLASH[images["hero"]]}" alt="{title} product overview" loading="eager" />'
        )
        show_img = (
            f'<img class="show-img" src="{IMG_BASE}{UNSPLASH[images["showcase"]]}" alt="{title} platform showcase" loading="lazy" />'
        )

    feat_rows = ''
    for i, (ft, fd) in enumerate(features):
        ic_name = icons['features'][i] if i < len(icons['features']) else 'check-circle'
        ic = _icon_svg(ic_name, '#ffffff')
        fimg = ''
        if images and i < len(images['features']):
            fimg = f'<img class="card-img" src="{IMG_BASE}{UNSPLASH[images["features"][i]]}" alt="" loading="lazy" />'
        feat_rows += f'''
        <div class="card">
          <div class="card-top">
            <div class="card-icon">{ic}</div>
            {fimg}
          </div>
          <h3>{ft}</h3>
          <p>{fd}</p>
        </div>'''

    stat_rows = ''
    for sv, sl in stats:
        sv_esc = sv.replace('<', '&lt;').replace('>', '&gt;')
        stat_rows += f'''
        <div class="stat"><div class="stat-num">{sv_esc}</div><div class="stat-label">{sl}</div></div>'''

    bullets = ''
    for i, (btxt, bic) in enumerate([
        ('Enterprise-grade security and compliance', 'shield-check'),
        ('Global support across time zones, 24/7', 'globe'),
        ('Seamless integrations with your stack', 'layers'),
    ]):
        ic_name = icons['showcase'][i] if i < len(icons['showcase']) else bic
        ic = _icon_svg(ic_name, p)
        bullets += f'<li class="bl"><span class="bl-ic">{ic}</span><span>{btxt}</span></li>'

    lumi_mark = LUMICORE_MARK

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} &mdash; {tagline}</title>
  <meta name="description" content="{hero_desc}" />
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,&quot;%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='{p}'/%3E%3Ctext x='16' y='22' font-size='14' text-anchor='middle' fill='white' font-family='Arial' font-weight='bold'%3E{initials}%3C/text%3E%3C/svg%3E" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Roboto', sans-serif; color: #475569; background: #ffffff; line-height: 1.6; }}
    h1, h2, h3, h4, .eyebrow, .logo-text {{ font-family: 'Poppins', sans-serif; }}
    a {{ text-decoration: none; }}
    img {{ display: block; }}
    .container {{ max-width: 1140px; margin: 0 auto; padding: 0 24px; }}

    .nav {{ position: sticky; top: 0; z-index: 50; background: rgba(255,255,255,0.95); backdrop-filter: blur(8px); border-bottom: 1px solid #eef2f7; }}
    .nav-inner {{ display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; max-width: 1140px; margin: 0 auto; }}
    .logo {{ display: flex; align-items: center; gap: 12px; }}
    .logo-text {{ font-weight: 700; font-size: 17px; color: {h}; }}
    .nav-links {{ display: flex; align-items: center; gap: 28px; }}
    .nav-links a {{ font-size: 14px; font-weight: 500; color: #64748b; transition: color .2s; }}
    .nav-links a:hover {{ color: {p}; }}
    .btn {{ display: inline-flex; align-items: center; gap: 8px; border-radius: 8px; font-weight: 600; font-size: 14px; padding: 12px 22px; transition: all .2s; cursor: pointer; border: none; font-family: 'Poppins', sans-serif; }}
    .btn-primary {{ background: {p}; color: #fff; }}
    .btn-primary:hover {{ box-shadow: 0 8px 20px {p}44; transform: translateY(-1px); }}
    .btn-outline {{ border: 1.5px solid {p}; color: {p}; background: transparent; }}
    .btn-outline:hover {{ background: {p}; color: #fff; }}

    .hero {{ padding: 80px 0; background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); }}
    .hero-grid {{ display: grid; grid-template-columns: 1.1fr 1fr; gap: 48px; align-items: center; }}
    .eyebrow {{ display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 2.5px; color: {p}; text-transform: uppercase; margin-bottom: 16px; background: {p}14; padding: 6px 14px; border-radius: 999px; }}
    .hero h1 {{ font-size: clamp(32px, 4.5vw, 50px); font-weight: 800; letter-spacing: -1px; color: {h}; line-height: 1.12; margin-bottom: 18px; }}
    .hero p {{ font-size: 17px; color: #64748b; max-width: 520px; margin-bottom: 26px; }}
    .hero-cta {{ display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 28px; }}
    .bullets {{ list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-width: 520px; margin: 0; padding: 0; }}
    .bl {{ display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; color: #334155; }}
    .bl-ic {{ display: inline-flex; width: 26px; height: 26px; align-items: center; justify-content: center; }}
    .hero-media {{ position: relative; }}
    .hero-img {{ width: 100%; aspect-ratio: 5/4; object-fit: cover; border-radius: 16px; box-shadow: 0 24px 60px -18px rgba(2,6,23,.35); }}
    .trust-pill {{ position: absolute; left: -18px; bottom: -18px; display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid #eef2f7; border-radius: 12px; padding: 12px 16px; box-shadow: 0 12px 30px rgba(2,6,23,.12); }}
    .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #4ade80; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}

    .features {{ padding: 84px 0; }}
    .sec-head {{ text-align: center; margin-bottom: 46px; }}
    .sec-head h2 {{ font-size: 30px; font-weight: 700; color: {h}; margin-bottom: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; }}
    .card {{ background: #fff; border: 1px solid #eef2f7; border-radius: 14px; overflow: hidden; transition: box-shadow .25s, transform .25s; }}
    .card:hover {{ box-shadow: 0 16px 36px #0f172a14; transform: translateY(-5px); }}
    .card-top {{ position: relative; }}
    .card-icon {{ position: absolute; top: 18px; left: 18px; width: 46px; height: 46px; border-radius: 11px; background: linear-gradient(135deg, {p}, {a}); color: #fff; display: grid; place-items: center; box-shadow: 0 8px 18px {p}44; z-index: 2; }}
    .card-img {{ width: 100%; height: 128px; object-fit: cover; }}
    .card h3 {{ font-size: 16px; color: {h}; margin: 18px 20px 6px; }}
    .card p {{ font-size: 14px; color: #64748b; margin: 0 20px 20px; }}

    .showcase {{ padding: 56px 0; background: #f8fafc; }}
    .show-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }}
    .show-img {{ width: 100%; aspect-ratio: 16/10; object-fit: cover; border-radius: 16px; box-shadow: 0 20px 50px -18px rgba(2,6,23,.3); }}
    .show-grid h2 {{ font-size: 30px; color: {h}; margin-bottom: 14px; }}

    .stats {{ padding: 56px 0; }}
    .stats-inner {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 28px; text-align: center; }}
    .stat-num {{ font-family: 'Poppins', sans-serif; font-size: 36px; font-weight: 800; color: {p}; }}
    .stat-label {{ font-size: 14px; color: #64748b; margin-top: 4px; }}

    .cta {{ padding: 84px 0; }}
    .cta-box {{ background: linear-gradient(135deg, {h}, {p}); color: #fff; border-radius: 18px; padding: 60px 40px; text-align: center; }}
    .cta-box h2 {{ font-size: 30px; font-weight: 700; margin-bottom: 12px; }}
    .cta-box p {{ color: #ffffffcc; margin-bottom: 28px; max-width: 520px; margin-left: auto; margin-right: auto; }}
    .btn-light {{ background: #fff; color: {p}; }}
    .btn-light:hover {{ box-shadow: 0 10px 24px rgba(0,0,0,0.18); transform: translateY(-1px); }}

    .footer {{ background: {fb}; color: #cbd5e1; padding: 56px 0 28px; }}
    .footer-top {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1.5fr; gap: 36px; margin-bottom: 36px; }}
    .footer .logo-text {{ color: #fff; }}
    .footer h4 {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: #fff; margin-bottom: 14px; }}
    .footer ul {{ list-style: none; }}
    .footer ul li {{ margin-bottom: 8px; }}
    .footer ul a {{ font-size: 14px; color: #94a3b8; transition: color .2s; }}
    .footer ul a:hover {{ color: #fff; }}
    .footer p {{ font-size: 14px; color: #94a3b8; margin-bottom: 10px; }}
    .status {{ display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; border: 1px solid #22c55e33; background: #22c55e1a; color: #4ade80; font-size: 12px; font-weight: 600; padding: 6px 12px; }}
    .footer-bottom {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; border-top: 1px solid #ffffff1a; padding-top: 22px; font-size: 13px; color: #94a3b8; }}
    .footer-bottom a {{ color: #cbd5e1; margin-left: 16px; }}
    .footer-bottom a:hover {{ color: #fff; }}
    .lumi-badge {{ display: inline-flex; align-items: center; gap: 10px; }}
    @media (max-width: 900px) {{ .hero-grid, .show-grid {{ grid-template-columns: 1fr; }} .nav-links {{ display: none; }} .footer-top {{ grid-template-columns: 1fr 1fr; }} .bullets {{ grid-template-columns: 1fr; }} .trust-pill {{ left: 12px; }} }}
    @media (max-width: 560px) {{ .footer-top {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header class="nav">
    <div class="nav-inner">
      <a class="logo" href=".">
        {lumi_mark}
        <span class="logo-text">{title}</span>
      </a>
      <nav class="nav-links">
        <a href=".">Home</a>
        <a href="#features">Features</a>
        <a href="#stats">Results</a>
        <a href="#cta">Contact</a>
        <a class="btn btn-primary" href="#cta">Get Started</a>
      </nav>
    </div>
  </header>

  <section class="hero">
    <div class="container">
      <div class="hero-grid">
        <div>
          <span class="eyebrow">{eyebrow}</span>
          <h1>{tagline}</h1>
          <p>{hero_desc}</p>
          <div class="hero-cta">
            <a class="btn btn-primary" href="#cta">Get Started &rarr;</a>
            <a class="btn btn-outline" href="#features">Explore Solutions</a>
          </div>
          <ul class="bullets">{bullets}</ul>
        </div>
        <div class="hero-media">
          {hero_img}
          <div class="trust-pill"><span class="dot"></span><span style="font-size:12px;font-weight:600;color:#334155">Trusted by 50,000+ businesses</span></div>
        </div>
      </div>
    </div>
  </section>

  <section class="features" id="features">
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">What We Offer</span>
        <h2>Why Choose {title}?</h2>
      </div>
      <div class="grid">{feat_rows}
      </div>
    </div>
  </section>

  <section class="showcase" id="showcase">
    <div class="container">
      <div class="show-grid">
        {show_img}
        <div>
          <span class="eyebrow">Platform Preview</span>
          <h2>Built for the modern {tagline.split(' ')[-1]}</h2>
          <p style="color:#64748b;line-height:1.7;margin-bottom:20px">Every detail is engineered for performance, scalability, and a flawless user experience &mdash; from first click to everyday operations.</p>
          <a class="btn btn-outline" href="#cta">Learn More &rarr;</a>
        </div>
      </div>
    </div>
  </section>

  <section class="stats" id="stats">
    <div class="container">
      <div class="stats-inner">{stat_rows}
      </div>
    </div>
  </section>

  <section class="cta" id="cta">
    <div class="container">
      <div class="cta-box">
        <h2>Ready to Transform Your Business?</h2>
        <p>Join thousands of professionals choosing {title} as their growth platform.</p>
        <a class="btn btn-light" href="#">Start Free Trial</a>
      </div>
    </div>
  </section>

  <footer class="footer">
    <div class="container">
      <div class="footer-top">
        <div>
          <a class="logo" href=".">
            {lumi_mark}
            <span class="logo-text">{title}</span>
          </a>
          <p>Building exceptional digital products with performance, security, and design excellence.</p>
          <span class="status"><span class="dot" />99.99% Operational</span>
        </div>
        <div>
          <h4>Product</h4>
          <ul>
            <li><a href="#features">Features</a></li>
            <li><a href="#stats">Results</a></li>
            <li><a href="#cta">Enterprise</a></li>
          </ul>
        </div>
        <div>
          <h4>Company</h4>
          <ul>
            <li><a href="#">About Us</a></li>
            <li><a href="#">Contact</a></li>
            <li><a href="#">Careers</a></li>
          </ul>
        </div>
        <div>
          <h4>Stay Updated</h4>
          <p>Weekly product updates and insights.</p>
          <span class="status"><span class="dot" />Product Newsletter</span>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2026 {title}. All rights reserved. Powered by <strong style="color:#fff">LumicorePro</strong>.</p>
        <div><a href="#">Twitter</a><a href="#">LinkedIn</a><a href="#">GitHub</a></div>
      </div>
    </div>
  </footer>
</body>
</html>'''


_FALLBACK_PALETTES = [
    {'primary': '#6366f1', 'accent': '#f59e0b', 'heading': '#1e1b4b', 'navBg': '#ffffff', 'footerBg': '#1e1b4b'},
    {'primary': '#2563eb', 'accent': '#059669', 'heading': '#1e3a5f', 'navBg': '#ffffff', 'footerBg': '#1e293b'},
    {'primary': '#dc2626', 'accent': '#f59e0b', 'heading': '#1f2937', 'navBg': '#ffffff', 'footerBg': '#1f2937'},
    {'primary': '#059669', 'accent': '#14b8a6', 'heading': '#064e3b', 'navBg': '#ffffff', 'footerBg': '#064e3b'},
    {'primary': '#e11d48', 'accent': '#059669', 'heading': '#1f2937', 'navBg': '#ffffff', 'footerBg': '#1f2937'},
    {'primary': '#7c3aed', 'accent': '#ec4899', 'heading': '#2e1065', 'navBg': '#ffffff', 'footerBg': '#2e1065'},
    {'primary': '#ea580c', 'accent': '#6366f1', 'heading': '#431407', 'navBg': '#ffffff', 'footerBg': '#431407'},
    {'primary': '#0891b2', 'accent': '#0ea5e9', 'heading': '#164e63', 'navBg': '#ffffff', 'footerBg': '#164e63'},
]


def _derive_palette(repo_name: str) -> Dict[str, str]:
    """Deterministic palette from any repo name (stable across runs)."""
    import hashlib
    idx = int(hashlib.md5(repo_name.encode()).hexdigest(), 16) % len(_FALLBACK_PALETTES)
    return _FALLBACK_PALETTES[idx]


def _derive_profile(repo_name: str) -> Dict[str, Any]:
    """Generate a sensible profile for a repo name not in PROFILES."""
    import re
    clean = re.sub(r'[-_\d]+$', '', repo_name)
    clean = clean.replace('-', ' ').replace('_', ' ').title().strip()
    if not clean:
        clean = repo_name.replace('-', ' ').replace('_', ' ').title().strip() or 'Lumicore'
    title = clean.split()[0] if clean.split() else clean
    return {
        'title': title,
        'tagline': f'{clean}, engineered for growth',
        'eyebrow': 'MODERN SAAS PLATFORM',
        'hero_desc': f'{clean} helps teams ship faster with a beautiful, blazing-fast interface, real-time analytics, and enterprise-grade security.',
        'features': [
            ('Intuitive Dashboard', 'Real-time metrics and management at your fingertips'),
            ('Secure by Default', 'Enterprise authentication, encryption, and audit logging'),
            ('Performance First', 'Optimized for speed, SEO, and Core Web Vitals'),
            ('Scalable Architecture', 'Built to handle growth from prototype to production'),
        ],
        'stats': [('99.99%', 'Uptime'), ('<2s', 'Load Time'), ('10K+', 'Users'), ('4.9/5', 'Rating')],
    }


def _derive_images(repo_name: str) -> Optional[Dict[str, list]]:
    """Deterministic image set for any repo name (stable across runs)."""
    import hashlib
    i = int(hashlib.md5(repo_name.encode()).hexdigest(), 16)
    keys = list(UNSPLASH.keys())
    hero = keys[i % len(keys)]
    show = keys[(i + 3) % len(keys)]
    feats = [keys[(i + 1) % len(keys)], keys[(i + 2) % len(keys)], keys[(i + 4) % len(keys)], keys[(i + 5) % len(keys)]]
    return {'hero': hero, 'showcase': show, 'features': feats}


def _derive_icons(repo_name: str) -> Dict[str, list]:
    """Deterministic Lucide icon set for any repo name."""
    import hashlib
    i = int(hashlib.md5(f'icon-{repo_name}'.encode()).hexdigest(), 16)
    feats = FALLBACK_ICONS['features']
    show = FALLBACK_ICONS['showcase']
    return {'features': feats, 'showcase': show}


def _patch_router_basename(frontend: Path) -> bool:
    """Patch App.jsx so BrowserRouter uses a gh-pages subpath basename.

    The generated apps hard-code <BrowserRouter> (basename '/'). On GitHub
    Pages a project page lives at /repo-name/, so no route matches and the
    Suspense tree stays empty. Detect the first URL segment at runtime.
    Returns True if patched.
    """
    app_candidate = frontend / 'src' / 'App.jsx'
    if not app_candidate.exists():
        return False
    text = app_candidate.read_text(encoding='utf-8')
    if '<BrowserRouter' not in text:
        return False
    if 'basename=' in text:
        return False
    replacement = (
        '<BrowserRouter basename={window.location.pathname.split(\"/\")[1] '
        '? \"/\" + window.location.pathname.split(\"/\")[1] : \"/\"}>'
    )
    patched = text.replace('<BrowserRouter>', replacement, 1)
    if patched == text:
        return False
    app_candidate.write_text(patched, encoding='utf-8')
    return True


def _resolve_style_blueprint(repo_name: str, ui_style: str, region: str = 'default'):
    """Deterministic design decision shared by the planning phase + restyle.

    Merge order: base palette → international region palette → Design Vault
    palette (exact design language) → UI-style overrides (dark/cyberpunk etc).
    Returns (palette, extra_css, resolved_style_name).
    """
    from agent.design_vault import VAULT_STYLES

    pal = PALETTES.get(repo_name) or _derive_palette(repo_name)
    region_tune = REGION_PALETTES.get(region, {})
    pal = {**pal, **region_tune}

    extra_css = ''
    vault_palette = {}
    if ui_style in VAULT_STYLES:
        vault_palette = VAULT_STYLES[ui_style].get('palette', {})
        extra_css = VAULT_STYLES[ui_style].get('css_extra', '')
        agent_logger.info(f"Design Vault style applied: {ui_style}")

    style_tune = UI_STYLE_PALETTE.get(ui_style, {})
    pal = {**pal, **vault_palette,
           **{k: v for k, v in style_tune.items() if v and k not in ('dark', 'text')}}
    if (style_tune.get('dark') or vault_palette.get('dark')) and not vault_palette:
        pal.setdefault('cardBg', '#0f172a')
        pal.setdefault('text', '#94a3b8')
    return pal, extra_css, ui_style


def resolve_design_blueprint(repo_name: str, ui_style: str, region: str = 'default',
                             brand_title: str = '') -> Dict[str, Any]:
    """Full international design plan produced BEFORE any code is written.

    docstring/planing artifact: what style, which region palette, which
    design language is used, and why — the single source of truth the
    generation pipeline reports and the DESIGN_PLAN.md documents.
    """
    from agent.design_vault import VAULT_STYLES

    pal, extra_css, resolved = _resolve_style_blueprint(repo_name, ui_style, region)
    fonts = {}
    if resolved in VAULT_STYLES:
        fonts = VAULT_STYLES[resolved].get('fonts', {})
    region_note = {
        'gcc': 'Gulf luxury: gold + emerald, deep neutral footer',
        'south-asia': 'South-Asian energy: saffron + green, warm canvas',
        'east-asia': 'East-Asian prosperity: red + gold, ink heading',
        'europe': 'European trust: refined blue + teal, clean light',
        'north-america': 'North-American bold: royal blue + red accent',
        'latam': 'LatAm warmth: coral + teal, energetic canvas',
        'africa': 'African earth: amber + green, grounded',
        'default': 'Global neutral (region-agnostic)',
    }
    font_heading = fonts.get('display', 'Poppins')
    font_sans = fonts.get('sans', 'Roboto')
    return {
        'project_name': repo_name,
        'ui_style': resolved,
        'target_region': region,
        'region_rationale': region_note.get(region, region_note['default']),
        'palette': pal,
        'fonts': {'display': font_heading, 'sans': font_sans},
        'css_primitives': extra_css,
        'vault_source': resolved if resolved in VAULT_STYLES else '',
        'brand_title': brand_title or _derive_profile(repo_name).get('title', repo_name),
    }


def write_design_plan(project_root: Path, blueprint: Dict[str, Any]) -> None:
    """Persist the international design plan into the delivered project."""
    pal = blueprint.get('palette', {})
    lines = [
        '# Design Plan',
        '',
        'This project ships an internationally planned design system — the style,',
        'color language, and target market were decided before a single page was built.',
        '',
        f"- **Project**: {blueprint.get('project_name')}",
        f"- **Brand**: {blueprint.get('brand_title')}",
        f"- **UI style**: {blueprint.get('ui_style')}",
        f"- **Target market**: {blueprint.get('target_region')} — {blueprint.get('region_rationale')}",
        f"- **Design Vault source**: {blueprint.get('vault_source') or 'built-in wheel'}",
        f"- **Display font**: {blueprint.get('fonts', {}).get('display')}",
        f"- **Body font**: {blueprint.get('fonts', {}).get('sans')}",
        '',
        '## Color system',
        '',
        '| Token | Value |',
        '|-------|-------|',
    ]
    for k, v in pal.items():
        if v and k != 'dark':
            lines.append(f'| `--t-{k}` | `{v}` |')
    lines += [
        '',
        'See `frontend/src/styles/design-tokens.json` for the machine-readable tokens.',
    ]
    (project_root / 'DESIGN_PLAN.md').write_text('\n'.join(lines), encoding='utf-8')


def restyle_project(project_dir: str, repo_name: str, ui_style: str = UI_STYLE_DEFAULT,
                    region: str = 'default',
                    palette_override: Optional[Dict[str, str]] = None) -> bool:
    """Apply professional consulting-style design to a generated project."""
    try:
        root = Path(project_dir)
        frontend = root / 'frontend'
        src = frontend / 'src'
        comps = src / 'components'
        pages = src / 'pages'

        if not frontend.exists():
            agent_logger.warning(f"No frontend/ at {project_dir}")
            return False

        pal, extra_css, resolved_style = _resolve_style_blueprint(repo_name, ui_style, region)
        ui_style = resolved_style
        allowed_palette_keys = {
          'primary', 'accent', 'heading', 'navBg', 'footerBg',
          'cardBg', 'text', 'muted', 'border',
        }
        for key, value in (palette_override or {}).items():
          if (
            key in allowed_palette_keys
            and isinstance(value, str)
            and len(value) in (4, 7)
            and value.startswith('#')
            and all(char in '0123456789abcdefABCDEF' for char in value[1:])
          ):
            pal[key] = value
        prof = PROFILES.get(repo_name) or _derive_profile(repo_name)

        # Ensure core build files exist (templates sometimes lack entry files)
        _ensure_build_files(frontend, repo_name, prof['title'])

        (frontend / 'index.html').write_text(_index_html(prof['title'], prof['tagline']), encoding='utf-8')
        (src / 'index.css').write_text(_index_css(pal, ui_style, extra_css), encoding='utf-8')
        (frontend / 'tailwind.config.js').write_text(_tailwind_config(pal), encoding='utf-8')

        # Gate-conformant app shell: provider stack + theme import + MotionCanvas
        (src / 'App.jsx').write_text(_app_jsx(repo_name), encoding='utf-8')

        # Semantic SEO: JSON-LD graph + OG/twitter meta already in _index_html
        (src / 'config' / 'structured-data.js').write_text(_structured_data_js(prof['title'], repo_name), encoding='utf-8')

        tokens_dir = src / 'styles'
        tokens_dir.mkdir(parents=True, exist_ok=True)
        (tokens_dir / 'design-tokens.json').write_text(
            _design_tokens_json(repo_name, pal, ui_style, region), encoding='utf-8')

        blueprint = resolve_design_blueprint(repo_name, ui_style, region, prof['title'])
        blueprint['palette'] = dict(pal)
        write_design_plan(root, blueprint)

        comps.mkdir(parents=True, exist_ok=True)
        (comps / 'LumicorePro.jsx').write_text(_lumicore_logo_jsx(), encoding='utf-8')
        (comps / 'UniqueLogo.jsx').write_text(_unique_logo_jsx(prof['title'], pal), encoding='utf-8')
        (comps / 'Navbar.jsx').write_text(_navbar_jsx(prof['title'], pal), encoding='utf-8')
        (comps / 'Footer.jsx').write_text(_footer_jsx(prof['title'], pal), encoding='utf-8')

        pages.mkdir(parents=True, exist_ok=True)
        (pages / 'Home.jsx').write_text(_home_jsx(
            prof['title'], prof['tagline'], prof['eyebrow'], prof['hero_desc'],
            prof['features'], prof['stats'], pal, repo_name, ui_style
        ), encoding='utf-8')

        _patch_router_basename(frontend)

        agent_logger.info(f"ProDesign applied to {repo_name} at {project_dir}")
        return True

    except Exception as e:
        agent_logger.error(f"ProDesign failed for {repo_name}: {e}")
        return False


def _ensure_build_files(frontend: Path, repo_name: str, title: str) -> None:
    """Create missing core build files so the frontend can always build."""
    pkg = frontend / 'package.json'
    if not pkg.exists():
        pkg.write_text(_json_mod.dumps({
            'name': repo_name,
            'private': True,
            'version': '1.0.0',
            'type': 'module',
            'scripts': {'dev': 'vite', 'build': 'vite build', 'preview': 'vite preview'},
            'dependencies': {
                'react': '^19.2.0',
                'react-dom': '^19.2.0',
                'react-router-dom': '^6.22.0',
                '@tanstack/react-query': '^5.59.0',
                'zustand': '^5.0.0',
                'lucide-react': '^1.31.0',
                'framer-motion': '^11.18.2',
                'i18next': '^25.0.0',
                'react-i18next': '^16.0.0',
                'axios': '^1.6.0',
            },
            'devDependencies': {
                '@vitejs/plugin-react': '^6.0.4',
                'vite': '^8.2.0',
                'tailwindcss': '^3.4.0',
                'autoprefixer': '^10.4.0',
                'postcss': '^8.4.0',
            },
        }, indent=2), encoding='utf-8')
        agent_logger.info(f"Created missing package.json for {repo_name}")
    else:
        # Pin-ensure step: guarantee architect-gate stack pins even on a
        # template-copied or previously self-healed (corrupted) package.json.
        _PIN_DEPENDENCIES = {
            'react': '^19.2.0', 'react-dom': '^19.2.0',
            '@tanstack/react-query': '^5.59.0', 'zustand': '^5.0.0',
            'react-router-dom': '^6.22.0', 'lucide-react': '^1.31.0',
            'axios': '^1.6.0',
        }
        _PIN_DEV_DEPENDENCIES = {'vite': '^8.2.0', 'tailwindcss': '^3.4.0'}
        try:
            raw = pkg.read_text(encoding='utf-8')
            # Strip any JS-comment lines the self-heal loop may have appended.
            clean = '\n'.join(l for l in raw.splitlines() if not l.lstrip().startswith('//'))
            data = _json_mod.loads(clean or '{}')
            deps = data.setdefault('dependencies', {})
            devdeps = data.setdefault('devDependencies', {})
            changed = False
            for name, ver in _PIN_DEPENDENCIES.items():
                if deps.get(name) != ver:
                    deps[name] = ver
                    changed = True
            for name, ver in _PIN_DEV_DEPENDENCIES.items():
                if devdeps.get(name) != ver:
                    devdeps[name] = ver
                    changed = True
            if changed or clean != raw:
                pkg.write_text(_json_mod.dumps(data, indent=2), encoding='utf-8')
                agent_logger.info(f"Pinned deps for {repo_name} (architect-gate stack pins ensured)")
        except Exception as e:
            # Unparseable → regenerate clean pinned scaffold.
            agent_logger.warning(f"Repairing unparseable package.json for {repo_name}: {e}")
            pkg.write_text(_json_mod.dumps({
                'name': repo_name,
                'private': True,
                'version': '1.0.0',
                'type': 'module',
                'scripts': {'dev': 'vite', 'build': 'vite build', 'preview': 'vite preview'},
                'dependencies': dict(_PIN_DEPENDENCIES),
                'devDependencies': dict(_PIN_DEV_DEPENDENCIES),
            }, indent=2), encoding='utf-8')

    vite_cfg = frontend / 'vite.config.js'
    if not vite_cfg.exists():
        vite_cfg.write_text(
            "import { defineConfig } from 'vite';\n"
            "import react from '@vitejs/plugin-react';\n"
            "import path from 'path';\n"
            "\n"
            "export default defineConfig({\n"
            "  plugins: [react()],\n"
            "  base: './',\n"
            "  resolve: {\n"
            "    alias: {\n"
            "      '@': path.resolve(import.meta.dirname, './src'),\n"
            "    },\n"
            "  },\n"
            "  server: {\n"
            "    port: 3000,\n"
            "    proxy: {\n"
            "      '/api': 'http://localhost:5000',\n"
            "    },\n"
            "  },\n"
            "});\n",
            encoding='utf-8')
        agent_logger.info(f"Created missing vite.config.js for {repo_name}")

    main_jsx = frontend / 'src' / 'main.jsx'
    if not main_jsx.exists():
        main_jsx.parent.mkdir(parents=True, exist_ok=True)
        main_jsx.write_text(
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            "import App from './App';\n"
            "import './index.css';\n"
            "\n"
            "ReactDOM.createRoot(document.getElementById('root')).render(\n"
            "  <React.StrictMode>\n"
            "    <App />\n"
            "  </React.StrictMode>\n"
            ");\n",
            encoding='utf-8')
        agent_logger.info(f"Created missing main.jsx for {repo_name}")

    app_jsx = frontend / 'src' / 'App.jsx'
    if not app_jsx.exists():
        app_jsx.parent.mkdir(parents=True, exist_ok=True)
        app_jsx.write_text(
            "import React, { Suspense, lazy } from 'react';\n"
            "import { BrowserRouter, Routes, Route } from 'react-router-dom';\n"
            "import AppProviders from './lib/AppProviders';\n"
            "import MotionCanvas from './components/common/MotionCanvas';\n"
            "import './lib/theme';\n"
            "\n"
            "const Home = lazy(() => import('./pages/Home'));\n"
            "\n"
            "function Loader() {\n"
            "  return (\n"
            "    <div className=\"flex items-center justify-center min-h-screen bg-canvas\">\n"
            "      <div className=\"skeleton-shimmer h-8 w-8 rounded-full\" />\n"
            "    </div>\n"
            "  );\n"
            "}\n"
            "\n"
            "const basename =\n"
            "  typeof window !== 'undefined' && window.location.pathname.split('/')[1]\n"
            "    ? '/' + window.location.pathname.split('/')[1]\n"
            "    : '/';\n"
            "\n"
            "export default function App() {\n"
            "  return (\n"
            "    <AppProviders>\n"
            "      <BrowserRouter basename={basename}>\n"
            "        <MotionCanvas className=\"fixed inset-0 -z-10\" />\n"
            "        <div className=\"cls-reserve\">\n"
            "          <Suspense fallback={<Loader />}>\n"
            "            <Routes>\n"
            "              <Route path=\"/*\" element={<Home />} />\n"
            "            </Routes>\n"
            "          </Suspense>\n"
            "        </div>\n"
            "      </BrowserRouter>\n"
            "    </AppProviders>\n"
            "  );\n"
            "}\n",
            encoding='utf-8')
        agent_logger.info(f"Created missing App.jsx for {repo_name}")

    postcss = frontend / 'postcss.config.js'
    if not postcss.exists():
        postcss.write_text(
            "export default {\n"
            "  plugins: {\n"
            "    tailwindcss: {},\n"
            "    autoprefixer: {},\n"
            "  },\n"
            "};\n",
            encoding='utf-8')
        agent_logger.info(f"Created missing postcss.config.js for {repo_name}")


def _app_jsx(repo_name: str) -> str:
    """Gate-conformant App shell: provider stack + theme import + MotionCanvas."""
    return '''import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppProviders from './lib/AppProviders';
import MotionCanvas from './components/common/MotionCanvas';
import './lib/theme';

const Home = lazy(() => import('./pages/Home'));

function Loader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950">
      <div className="skeleton-shimmer h-8 w-8 rounded-full" />
    </div>
  );
}

const basename =
  typeof window !== 'undefined' && window.location.pathname.split('/')[1]
    ? '/' + window.location.pathname.split('/')[1]
    : '/';

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter basename={basename}>
        <MotionCanvas className="fixed inset-0 -z-10" />
        <div className="cls-reserve">
          <Suspense fallback={<Loader />}>
            <Routes>
              <Route path="/*" element={<Home />} />
            </Routes>
          </Suspense>
        </div>
      </BrowserRouter>
    </AppProviders>
  );
}
'''


def _structured_data_js(title: str, repo_name: str) -> str:
    """Semantic SEO JSON-LD graph shipping all 14 required schema types."""
    site = f"https://malikusmangoraya.github.io/{repo_name}/"
    pname = title.replace("'", "\\'")
    return f'''/**
 * SRS semantic SEO �?? JSON-LD structured data graph (all required schema types).
 */
export const JSONLD = {{
  '@context': 'https://schema.org',
  '@graph': [
    {{ '@type': 'Organization', name: '{pname}', url: '{site}' }},
    {{ '@type': 'WebSite', name: '{pname}', url: '{site}' }},
    {{ '@type': 'WebPage', url: '{site}main', isPartOf: {{ '@type': 'WebSite' }} }},
    {{ '@type': 'Product', name: '{pname}', description: '{pname} core platform offering' }},
    {{ '@type': 'Offer', price: '0', priceCurrency: 'USD', availability: 'https://schema.org/InStock' }},
    {{ '@type': 'AggregateRating', ratingValue: '4.9', ratingCount: '1200' }},
    {{ '@type': 'BreadcrumbList', itemListElement: [{{ '@type': 'ListItem', position: 1, name: 'Home' }}] }},
    {{ '@type': 'FAQPage', mainEntity: [{{ '@type': 'Question', name: 'What is {pname}?', acceptedAnswer: {{ '@type': 'Answer', text: '{pname} is a professional web platform.' }} }}] }},
    {{ '@type': 'Service', name: '{pname}', provider: {{ '@type': 'Organization' }} }},
    {{ '@type': 'LocalBusiness', name: '{pname}', url: '{site}' }},
    {{ '@type': 'Person', jobTitle: 'Founder', name: '{pname} Team' }},
    {{ '@type': 'Article', headline: '{pname} platform guide', author: {{ '@type': 'Person' }} }},
    {{ '@type': 'Review', reviewRating: {{ '@type': 'Rating', ratingValue: '5' }}, author: {{ '@type': 'Person' }} }},
    {{ '@type': 'ImageObject', url: '{site}og.jpg', caption: '{pname} platform overview' }},
  ],
}};

export default JSONLD;
'''


def _shim() -> str:
    """Windows: npm/git live in .cmd/look in PATH."""
    import shutil
    if os.name == 'nt':
        for cmd in ('npm.cmd', 'npm'):
            p = shutil.which(cmd)
            if p:
                return p
    return 'npm'


def _spa_fallback_html(repo_name: str) -> str:
    """404.html SPA shim: bare path served by gh-pages on deep links."""
    pal = PALETTES.get(repo_name) or _derive_palette(repo_name)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Redirecting…</title>
  <style>
    body {{ margin: 0; font-family: 'Poppins', Roboto, sans-serif; background: {pal['navBg']}; color: #475569; display: grid; place-items: center; min-height: 100vh; text-align: center; }}
    a {{ color: {pal['primary']}; }}
  </style>
</head>
<body>
  <main>
    <h1 style="color:{pal['heading']}">Taking you home…</h1>
    <p><a href="./">Open {repo_name}</a></p>
  </main>
  <script>
    (function () {{
      var s = document.currentScript || document.scripts[document.scripts.length - 1];
      var here = s.getAttribute('data-here') || window.location.href;
      var path = here.replace(/^[^/]+\\/\\//, '');
      var segs = path.split('/').filter(Boolean);
      segs.shift();
      var clean = segs.join('/');
      if (clean && clean.indexOf('.') !== -1) {{
        window.location.replace('./' + clean);
      }}
    }})();
  </script>
</body>
</html>'''


def _push_to_ghpages(dist: Path, repo_name: str, token: str) -> bool:
    """Push any static folder to gh-pages branch and trigger rebuild. Returns pushed."""
    import subprocess, json, tempfile, shutil
    repo_url = f'https://x-access-token:{token}@github.com/malikusmangoraya/{repo_name}.git'
    tmp = Path(tempfile.mkdtemp(prefix=f'ghp-{repo_name}-'))

    pushed = False
    try:
        clone = subprocess.run(
            ['git', 'clone', '--depth', '1', '--branch', 'gh-pages', repo_url, str(tmp)],
            capture_output=True, text=True, timeout=60
        )
        if clone.returncode == 0:
            for item in tmp.iterdir():
                if item.name == '.git':
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
        else:
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir(parents=True)
            subprocess.run(['git', 'init', '-b', 'gh-pages'], cwd=str(tmp), capture_output=True, timeout=30)
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], cwd=str(tmp), capture_output=True, timeout=30)

        for item in dist.iterdir():
            if item.is_dir():
                shutil.copytree(item, tmp / item.name)
            else:
                shutil.copy2(item, tmp / item.name)

        subprocess.run(['git', 'add', '-A'], cwd=str(tmp), capture_output=True, timeout=30)
        subprocess.run(['git', '-c', 'user.name=lumicorepro', '-c', 'user.email=agent@lumicorepro.dev',
                        'commit', '-m', f'chore: deploy full app — {repo_name}'], cwd=str(tmp), capture_output=True, timeout=30)
        push = subprocess.run(['git', 'push', '-f', 'origin', 'gh-pages'], cwd=str(tmp), capture_output=True, text=True, timeout=90)
        pushed = push.returncode == 0
        if not pushed:
            stderr = (push.stderr or '')[:200] + (push.stdout or '')[:200]
            agent_logger.warning(f"Push failed for {repo_name}: {stderr}")
    except Exception as e:
        agent_logger.warning(f"Git push issue for {repo_name}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if pushed:
        import time
        time.sleep(2)
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(
                f'https://api.github.com/repos/malikusmangoraya/{repo_name}/pages',
                data=json.dumps({'source': {'branch': 'gh-pages', 'path': '/'}}).encode(),
                headers={'Authorization': f'token {token}', 'User-Agent': 'pro-design', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'},
                method='PUT'
            )
            try:
                urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    req2 = urllib.request.Request(
                        f'https://api.github.com/repos/malikusmangoraya/{repo_name}/pages',
                        data=json.dumps({'build_type': 'legacy', 'source': {'branch': 'gh-pages', 'path': '/'}}).encode(),
                        headers={'Authorization': f'token {token}', 'User-Agent': 'pro-design', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'},
                        method='POST'
                    )
                    try:
                        urllib.request.urlopen(req2)
                    except Exception as e2:
                        agent_logger.warning(f"Pages create failed {repo_name}: {e2}")
                elif e.code not in (409, 422):
                    agent_logger.warning(f"Pages config issue for {repo_name}: {e.code}")
        except Exception as e:
            agent_logger.warning(f"Pages config error for {repo_name}: {e}")

        try:
            req3 = urllib.request.Request(
                f'https://api.github.com/repos/malikusmangoraya/{repo_name}/pages/builds',
                data=b'',
                headers={'Authorization': f'token {token}', 'User-Agent': 'pro-design', 'Accept': 'application/vnd.github+json'},
                method='POST'
            )
            urllib.request.urlopen(req3)
            agent_logger.info(f"Pages rebuild triggered for {repo_name}")
        except Exception as e:
            agent_logger.warning(f"Pages rebuild trigger failed {repo_name}: {e}")

    return pushed


def build_and_deploy_ghpages(project_dir: str, repo_name: str, token: str) -> str:
    """Build dist and push to gh-pages branch. Returns live URL."""
    import subprocess
    from pathlib import Path

    root = Path(project_dir)
    frontend = root / 'frontend'

    if not (frontend / 'package.json').exists():
        agent_logger.warning(f"No package.json for {repo_name}")
        return ''

    npm = _shim()
    agent_logger.info(f"Building {repo_name}...")
    # Ensure base './' so assets resolve under a gh-pages subpath
    vite_cfg = frontend / 'vite.config.js'
    if vite_cfg.exists():
        text = vite_cfg.read_text(encoding='utf-8')
        if "base" not in text.replace(' ', ''):
            patched = text.replace("plugins: [react()],", "plugins: [react()],\n  base: './',", 1)
            if patched == text:
                patched = text.replace("defineConfig({", "defineConfig({\n  base: './',", 1)
            vite_cfg.write_text(patched, encoding='utf-8')
    try:
        if not (frontend / 'node_modules').exists():
            subprocess.run([npm, 'install', '--legacy-peer-deps'], cwd=str(frontend), capture_output=True, timeout=300)
        build_result = subprocess.run([npm, 'run', 'build'], cwd=str(frontend), capture_output=True, text=True, timeout=180)
        if build_result.returncode != 0:
            agent_logger.warning(f"Build stderr: {build_result.stderr[:300]}")
    except Exception as e:
        agent_logger.warning(f"Build step issue for {repo_name}: {e}")

    dist = frontend / 'dist'
    if not dist.exists():
        agent_logger.error(f"No dist/ for {repo_name} after build")
        return ''

    (dist / '404.html').write_text(_spa_fallback_html(repo_name), encoding='utf-8')
    (dist / '.nojekyll').write_text('', encoding='utf-8')

    pushed = _push_to_ghpages(dist, repo_name, token)
    return f'https://malikusmangoraya.github.io/{repo_name}/' if pushed else ''


def build_and_deploy_static(repo_name: str, token: str) -> str:
    """Generate standalone styled HTML + push to gh-pages. Returns live URL."""
    import tempfile
    from pathlib import Path

    html = _standalone_html(repo_name)
    dist = Path(tempfile.mkdtemp(prefix=f'static-{repo_name}-'))
    (dist / 'index.html').write_text(html, encoding='utf-8')
    (dist / '404.html').write_text(html, encoding='utf-8')
    (dist / '.nojekyll').write_text('', encoding='utf-8')
    (dist / 'favicon.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#0f172a"/><text x="16" y="22" font-size="16" text-anchor="middle" fill="#fff" font-family="Roboto,sans-serif" font-weight="700">' + repo_name[:2].upper() + '</text></svg>',
        encoding='utf-8'
    )

    pushed = _push_to_ghpages(dist, repo_name, token)
    return f'https://malikusmangoraya.github.io/{repo_name}/' if pushed else ''