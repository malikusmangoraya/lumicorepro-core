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
}

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
    """Generate a unique geometric SVG logo for the project."""
    p = palette['primary']
    a = palette['accent']
    h = sum(ord(c) for c in name)
    shapes = [
        f'<polygon points="24,4 42,14 42,34 24,44 6,34 6,14" fill="{p}" opacity="0.95"/>'
        f'<polygon points="24,12 34,18 34,30 24,36 14,30 14,18" fill="white" opacity="0.9"/>'
        f'<polygon points="24,18 29,21 29,27 24,30 19,27 19,21" fill="{a}"/>',
        f'<rect x="8" y="8" width="32" height="32" rx="4" fill="{p}" transform="rotate(45 24 24)" opacity="0.95"/>'
        f'<circle cx="24" cy="24" r="10" fill="white" opacity="0.9"/>'
        f'<circle cx="24" cy="24" r="6" fill="{a}"/>',
        f'<polygon points="24,4 44,20 38,44 10,44 4,20" fill="{p}" opacity="0.95"/>'
        f'<polygon points="24,14 34,22 31,36 17,36 14,22" fill="white" opacity="0.9"/>'
        f'<polygon points="24,20 28,23 27,29 21,29 20,23" fill="{a}"/>',
        f'<rect x="4" y="4" width="40" height="40" rx="12" fill="{p}" opacity="0.95"/>'
        f'<rect x="12" y="12" width="24" height="24" rx="6" fill="white" opacity="0.9"/>'
        f'<rect x="18" y="18" width="12" height="12" rx="3" fill="{a}"/>',
    ]
    shape = shapes[h % len(shapes)]
    return f'<svg viewBox="0 0 48 48" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg">{shape}</svg>'


def _unique_logo_jsx(name: str, palette: Dict[str, str]) -> str:
    svg = _svg_logo(name, palette)
    words = name.replace('-', ' ').split()
    primary = words[0] if words else name
    accent = ' '.join(words[1:]) if len(words) > 1 else ''
    accent_span = f'''<span style={{{{ color: '{palette["primary"]}' }}}} className="ml-0.5">{accent}</span>''' if accent else ''
    return f'''import React from 'react';
import {{ Link }} from 'react-router-dom';

export default function UniqueLogo({{ size = 'md' }}) {{
  const sz = {{ sm: 24, md: 32, lg: 40 }}[size] || 32;
  return (
    <Link to="/" className="inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-90">
      <div style={{{{ width: sz, height: sz }}}} className="shrink-0">
        {svg}
      </div>
      <span className="font-extrabold text-xl tracking-tight" style={{{{ color: '{palette["heading"]}' }}}}>
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
    <meta name="description" content="{tagline} — built with LumicorePro AI Agent." />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''


def _index_css(palette: Dict[str, str]) -> str:
    p = palette['primary']
    a = palette['accent']
    h = palette['heading']
    r, g, b = int(p[1:3], 16), int(p[3:5], 16), int(p[5:7], 16)
    return f'''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  body {{
    @apply bg-white antialiased;
    font-family: 'Poppins', sans-serif;
    color: #1e293b;
  }}
  h1, h2, h3, h4, h5, h6 {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
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
}}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #f1f5f9; }}
::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}

@media (max-width: 768px) {{
  .section-heading {{ font-size: 1.5rem; }}
}}
'''


def _design_tokens_json(repo_name: str, palette: Dict[str, str]) -> str:
    import json
    tokens = {
        'style': 'consulting_pro',
        'name': 'Consulting Professional',
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
    return f'''/** @type {{import('tailwindcss').Config}} */
export default {{
  content: ['./index.html', './src/**/*.{{js,jsx}}'],
  theme: {{
    extend: {{
      colors: {{
        primary: '{p}',
        accent: '{a}',
        heading: '{h}',
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


def _navbar_jsx(title: str, palette: Dict[str, str]) -> str:
    p = palette['primary']
    return f'''import React, {{ useState }} from 'react';
import {{ Link, useLocation }} from 'react-router-dom';
import {{ Menu, X }} from 'lucide-react';
import UniqueLogo from './UniqueLogo';

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
    <nav className="sticky top-0 z-50 border-b border-slate-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <UniqueLogo />
        <div className="hidden md:flex items-center gap-8">
          {{links.map(l => (
            <Link key={{l.path}} to={{l.path}} className="text-sm font-medium hover:text-primary transition-colors" style={{{{ color: loc.pathname === l.path ? '{p}' : '#475569' }}}}>
              {{l.label}}
            </Link>
          ))}}
          <Link to="/contact" className="btn-primary text-sm">{title} Free Demo</Link>
        </div>
        <button onClick={{() => setOpen(!open)}} className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100" aria-label="Menu">
          {{open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}}
        </button>
      </div>
      {{open && (
        <div className="md:hidden border-t border-slate-100 bg-white px-6 pb-4 pt-2">
          {{links.map(l => (
            <Link key={{l.path}} to={{l.path}} onClick={{() => setOpen(false)}} className="block py-2 text-sm font-medium text-slate-600 hover:text-primary">
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
import UniqueLogo from './UniqueLogo';

export default function Footer() {{
  const [email, setEmail] = useState('');
  const [sub, setSub] = useState(false);
  return (
    <footer className="text-white" style={{{{ backgroundColor: '{palette["footerBg"]}' }}}}>
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-4">
          <div className="space-y-4">
            <UniqueLogo />
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
          <p>&copy; {{new Date().getFullYear()}} {title}. All rights reserved.</p>
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
              features: list, stats: list, palette: Dict[str, str]) -> str:
    p = palette['primary']
    h = palette['heading']

    feat_rows = []
    for tidx, (ftitle, fdesc) in enumerate(features):
        feat_rows.append(f'''              <div className="group rounded-xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:shadow-lg">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold text-white" style={{{{ backgroundColor: '{p}' }}}}>
                  {tidx + 1}
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{{{ color: '{h}' }}}}>{ftitle}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{fdesc}</p>
              </div>''')
    feat_jsx = '\n'.join(feat_rows)

    stat_rows = []
    for sval, slabel in stats:
        stat_rows.append(f'''            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{{{ color: '{p}' }}}}>{'{'}'{sval}'{'}'}</div>
              <div className="text-sm text-slate-500">{slabel}</div>
            </div>''')
    stat_jsx = '\n'.join(stat_rows)

    return f'''import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ ArrowRight }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {{
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <section className="relative overflow-hidden py-20 lg:py-28">
          <div className="absolute inset-0 -z-10" style={{{{ background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)' }}}} />
          <div className="max-w-6xl mx-auto px-6">
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
            </div>
          </div>
        </section>

        <section className="py-20 px-6 bg-white">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">What We Offer</span>
              <h2 className="section-heading">Why Choose {title}?</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
{feat_jsx}
            </div>
          </div>
        </section>

        <section className="py-16 px-6" style={{{{ backgroundColor: '#f8fafc' }}}}>
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
{stat_jsx}
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-3xl mx-auto text-center rounded-2xl p-12" style={{{{ backgroundColor: '{h}' }}}}>
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

    feat_rows = ''
    for i, (ft, fd) in enumerate(features):
        feat_rows += f'''
        <div class="card">
          <div class="card-icon">{i + 1}</div>
          <h3>{ft}</h3>
          <p>{fd}</p>
        </div>'''

    stat_rows = ''
    for sv, sl in stats:
        sv_esc = sv.replace('<', '&lt;').replace('>', '&gt;')
        stat_rows += f'''
        <div class="stat"><div class="stat-num">{sv_esc}</div><div class="stat-label">{sl}</div></div>'''

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — {tagline}</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,&quot;%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='{p}'/%3E%3Ctext x='16' y='22' font-size='14' text-anchor='middle' fill='white' font-family='Arial' font-weight='bold'%3E{initials}%3C/text%3E%3C/svg%3E" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Roboto', sans-serif; color: #475569; background: #ffffff; line-height: 1.6; }}
    h1, h2, h3, h4, .eyebrow, .logo-text {{ font-family: 'Poppins', sans-serif; }}
    a {{ text-decoration: none; }}
    .container {{ max-width: 1140px; margin: 0 auto; padding: 0 24px; }}

    .nav {{ position: sticky; top: 0; z-index: 50; background: rgba(255,255,255,0.95); backdrop-filter: blur(8px); border-bottom: 1px solid #eef2f7; }}
    .nav-inner {{ display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; max-width: 1140px; margin: 0 auto; }}
    .logo {{ display: flex; align-items: center; gap: 10px; }}
    .logo-badge {{ width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(135deg, {p}, {a}); display: flex; align-items: center; justify-content: center; color: #fff; font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 18px; box-shadow: 0 4px 12px {p}33; }}
    .logo-text {{ font-weight: 700; font-size: 20px; color: {h}; }}
    .nav-links {{ display: flex; align-items: center; gap: 32px; }}
    .nav-links a {{ font-size: 14px; font-weight: 500; color: #64748b; transition: color .2s; }}
    .nav-links a:hover {{ color: {p}; }}
    .btn {{ display: inline-flex; align-items: center; gap: 8px; border-radius: 8px; font-weight: 600; font-size: 14px; padding: 12px 22px; transition: all .2s; cursor: pointer; border: none; font-family: 'Poppins', sans-serif; }}
    .btn-primary {{ background: {p}; color: #fff; }}
    .btn-primary:hover {{ box-shadow: 0 8px 20px {p}44; transform: translateY(-1px); }}
    .btn-outline {{ border: 1.5px solid {p}; color: {p}; background: transparent; }}
    .btn-outline:hover {{ background: {p}; color: #fff; }}

    .hero {{ padding: 96px 0 84px; background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); }}
    .eyebrow {{ display: inline-block; font-size: 13px; font-weight: 700; letter-spacing: 2.5px; color: {p}; text-transform: uppercase; margin-bottom: 16px; background: {p}14; padding: 6px 14px; border-radius: 999px; }}
    .hero h1 {{ font-size: clamp(34px, 5vw, 54px); font-weight: 800; letter-spacing: -1px; color: {h}; line-height: 1.15; margin-bottom: 20px; }}
    .hero p {{ font-size: 18px; color: #64748b; max-width: 560px; margin-bottom: 32px; }}
    .hero-cta {{ display: flex; flex-wrap: wrap; gap: 14px; }}

    .features {{ padding: 88px 0; }}
    .sec-head {{ text-align: center; margin-bottom: 48px; }}
    .sec-head h2 {{ font-size: 32px; font-weight: 700; color: {h}; margin-bottom: 10px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }}
    .card {{ background: #fff; border: 1px solid #eef2f7; border-radius: 14px; padding: 28px 24px; transition: box-shadow .25s, transform .25s; }}
    .card:hover {{ box-shadow: 0 12px 30px #0f172a14; transform: translateY(-4px); }}
    .card-icon {{ width: 44px; height: 44px; border-radius: 10px; background: linear-gradient(135deg, {p}, {a}); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-family: 'Poppins', sans-serif; margin-bottom: 16px; }}
    .card h3 {{ font-size: 17px; color: {h}; margin-bottom: 8px; }}
    .card p {{ font-size: 14px; color: #64748b; }}

    .stats {{ padding: 56px 0; background: #f8fafc; }}
    .stats-inner {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 28px; text-align: center; }}
    .stat-num {{ font-family: 'Poppins', sans-serif; font-size: 36px; font-weight: 800; color: {p}; }}
    .stat-label {{ font-size: 14px; color: #64748b; margin-top: 4px; }}

    .cta {{ padding: 88px 0; }}
    .cta-box {{ background: linear-gradient(135deg, {h}, {p}); color: #fff; border-radius: 18px; padding: 64px 40px; text-align: center; }}
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
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #4ade80; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
    .footer-bottom {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; border-top: 1px solid #ffffff1a; padding-top: 22px; font-size: 13px; color: #94a3b8; }}
    .footer-bottom a {{ color: #cbd5e1; margin-left: 16px; }}
    .footer-bottom a:hover {{ color: #fff; }}
    @media (max-width: 900px) {{ .footer-top {{ grid-template-columns: 1fr 1fr; }} .nav-links {{ display: none; }} }}
    @media (max-width: 560px) {{ .footer-top {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header class="nav">
    <div class="nav-inner">
      <a class="logo" href=".">
        <div class="logo-badge">{initials}</div>
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
      <span class="eyebrow">{eyebrow}</span>
      <h1>{tagline}</h1>
      <p>{hero_desc}</p>
      <div class="hero-cta">
        <a class="btn btn-primary" href="#cta">Get Started &rarr;</a>
        <a class="btn btn-outline" href="#features">Explore Solutions</a>
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
            <div class="logo-badge">{initials}</div>
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
        <p>&copy; 2026 {title}. All rights reserved.</p>
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
    clean = repo_name.replace('-', ' ').replace('_', ' ').title()
    return {
        'title': clean.split()[0] if clean.split() else clean,
        'tagline': f'{clean} — Professional Web Platform',
        'eyebrow': 'PROFESSIONAL PLATFORM',
        'hero_desc': f'Build and scale {clean} with modern architecture, real-time analytics, and enterprise-grade reliability.',
        'features': [
            ('Intuitive Dashboard', 'Real-time metrics and management at your fingertips'),
            ('Secure by Default', 'Enterprise authentication, encryption, and audit logging'),
            ('Performance First', 'Optimized for speed, SEO, and Core Web Vitals'),
            ('Scalable Architecture', 'Built to handle growth from prototype to production'),
        ],
        'stats': [('99.99%', 'Uptime'), ('<2s', 'Load Time'), ('10K+', 'Users'), ('4.9/5', 'Rating')],
    }


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


def restyle_project(project_dir: str, repo_name: str) -> bool:
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

        pal = PALETTES.get(repo_name) or _derive_palette(repo_name)
        prof = PROFILES.get(repo_name) or _derive_profile(repo_name)

        (frontend / 'index.html').write_text(_index_html(prof['title'], prof['tagline']), encoding='utf-8')
        (src / 'index.css').write_text(_index_css(pal), encoding='utf-8')
        (frontend / 'tailwind.config.js').write_text(_tailwind_config(pal), encoding='utf-8')

        tokens_dir = src / 'styles'
        tokens_dir.mkdir(parents=True, exist_ok=True)
        (tokens_dir / 'design-tokens.json').write_text(_design_tokens_json(repo_name, pal), encoding='utf-8')

        comps.mkdir(parents=True, exist_ok=True)
        (comps / 'UniqueLogo.jsx').write_text(_unique_logo_jsx(prof['title'], pal), encoding='utf-8')
        (comps / 'Navbar.jsx').write_text(_navbar_jsx(prof['title'], pal), encoding='utf-8')
        (comps / 'Footer.jsx').write_text(_footer_jsx(prof['title'], pal), encoding='utf-8')

        pages.mkdir(parents=True, exist_ok=True)
        (pages / 'Home.jsx').write_text(_home_jsx(
            prof['title'], prof['tagline'], prof['eyebrow'], prof['hero_desc'],
            prof['features'], prof['stats'], pal
        ), encoding='utf-8')

        _patch_router_basename(frontend)

        agent_logger.info(f"ProDesign applied to {repo_name} at {project_dir}")
        return True

    except Exception as e:
        agent_logger.error(f"ProDesign failed for {repo_name}: {e}")
        return False


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