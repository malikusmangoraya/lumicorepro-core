"""Per-industry Home-section content — v7.10.

Adds the missing 2026 anatomy for Home.jsx across all 43 projects:
  - problem reframe (names the friction + the cost of the old way)
  - persona / use-case grid (who the brand is for, industry-accurate)

Pricing teaser + FAQ rows reuse `industry_content.IC[industry]` directly.
All icons are from the verified installed lucide-react set.
"""

# ---- problem reframe: friction + cost, then the fix in `build_index` copy ----
PROBLEMS = {
    "real-estate": {
        "heading": "The right home is out there — most buyers never see it",
        "body": "Open-portal listings move first for viewings and last for truth: key details buried, pricing postured, off-market stock invisible. The cost is months of wasted weekends and a home you settle for instead of choose.",
        "icon": "Search",
    },
    "fashion": {
        "heading": "Off-the-rack fits everyone, and flatters no one",
        "body": "Seasonal fast fashion trains you to buy small joys that last six washes. The cost is a wardrobe full of almost-right pieces and nothing that truly belongs to you.",
        "icon": "Scissors",
    },
    "food": {
        "heading": "Great produce deserves better than a printed menu",
        "body": "Most kitchens buy on price, plate by rote and serve whatever the spreadsheet dictates. The cost is dinner that is predictable when the day was not.",
        "icon": "Flame",
    },
    "hospitality": {
        "heading": "Trips are sold in brochures and fall apart on the ground",
        "body": "Generic itineraries optimise for commission, not memory — the hotel is far from where you actually want to be. The cost is a holiday that looks good in the album and felt thin in real life.",
        "icon": "Compass",
    },
    "portfolio": {
        "heading": "Brands stall when every agency ships the same look",
        "body": "Templates and trend-chasing make you blend in exactly when you need to stand out. The cost is marketing spend that moves awareness but not the business.",
        "icon": "PenTool",
    },
    "fintech": {
        "heading": "Banking profits from confusion — that is the whole trick",
        "body": "Hidden fees, opaque rates and interfaces engineered to make you click. The cost: you manage money around the bank's incentives instead of your own.",
        "icon": "Wallet",
    },
    "electronics": {
        "heading": "Parts catalogues hide the two things that matter: stock and specs",
        "body": "Mediocre catalogues list the part but bury the datasheet, the lead time and the real availability. The cost is design cycles that stall on a component that was never actually in stock.",
        "icon": "Cpu",
    },
    "sports": {
        "heading": "Most gyms sell memberships, not results",
        "body": "Open floors with zero programming leave motivation to do all the work. The cost is a year of invoices and a plateau you cannot name.",
        "icon": "Dumbbell",
    },
    "entertainment": {
        "heading": "Events go wrong in the second nobody rehearsed",
        "body": "Under-planned logistics surface as queues, dead air and technical hiccups — the audience feels it instantly. The cost is a brand moment that flattens into 'it was fine'.",
        "icon": "Sparkles",
    },
    "ecommerce": {
        "heading": "Online retail that wins the click and loses the trust",
        "body": "Ghost stock, inflated discounts and returns that fight you turn first-time buyers into everyone else's customers. The cost is a transaction today and a lost buyer for life.",
        "icon": "ShoppingBag",
    },
    "healthcare": {
        "heading": "Care that fits eight minutes a visit fits no one well",
        "body": "Rushed appointments and opaque notes leave patients rebooking the same fear. The cost is health decisions made on half-understood information.",
        "icon": "HeartPulse",
    },
    "education": {
        "heading": "Courses sell completion and ship consumption",
        "body": "Hours of passive video with no mentor, no cohort and no project. The cost is a certificate you watched for, and skills you never actually practised.",
        "icon": "BookOpen",
    },
    "saas": {
        "heading": "Software stacks solve your stack, not your problem",
        "body": "Point tools put the 'ops' in operations — context-switching, glue-code and tool sprawl. The cost is hours spent running your tooling instead of your product.",
        "icon": "LayoutDashboard",
    },
}

# ---- persona / use-case grid: (icon, title, description) x3 per industry ----
PERSONAS = {
    "real-estate": [
        ("Building2", "Homeowners", "Move up, downsize or relocate with listings matched to the way you actually live."),
        ("TrendingUp", "Investors", "Yield, appreciation and liquidity modelled per property before you commit capital."),
        ("Globe", "International Buyers", "Remote viewings, funds and legal handled seamlessly across borders and time zones."),
    ],
    "fashion": [
        ("Sparkles", "The Discerning Buyer", "Limited runs and made-to-measure pieces that quietly get the compliments."),
        ("Gem", "The Gift-Giver", "Commissioned, personal pieces that make a wedding or milestone impossible to forget."),
        ("Briefcase", "The Executive", "A measured wardrobe built with one adviser, one fitting, one standard."),
    ],
    "food": [
        ("Users", "The Local", "A neighbourhood table where the menu follows the market, every single day."),
        ("Calendar", "The Host", "Private rooms and chef's counters for the dinners people retell for years."),
        ("Star", "The Collector", "Cellar-led pairings and rare pours for those who taste with the winemaker."),
    ],
    "hospitality": [
        ("HeartHandshake", "The Couple", "Anniversary trips designed around pace and privacy, guided and unhurried."),
        ("Users", "The Family", "Multi-generational itineraries that move at children's speeds with adults' interests."),
        ("Compass", "The Solo Traveller", "Small groups and local guides that make going alone feel like arriving somewhere."),
    ],
    "portfolio": [
        ("Rocket", "The Founder", "Launch identity and site in a focused sprint, ready before the raise."),
        ("Briefcase", "The CMO", "A brand system and creative partner with the taste to justify the budget."),
        ("Layers", "The Product Team", "Design and code in one team, shipped together, no handover wobble."),
    ],
    "fintech": [
        ("PiggyBank", "The Saver", "Automatic savings rules that work while you sleep — no willpower required."),
        ("Plane", "The Traveller", "Fee-free spending abroad at the real rate, with cards that simply work."),
        ("Briefcase", "The Freelancer", "Separate pots, instant invoicing and tax-ready summaries every month."),
    ],
    "electronics": [
        ("Cpu", "The Engineer", "Full specs, live stock and compliance docs beside every part, no hunting."),
        ("Lightbulb", "The Maker", "Dev boards and breadboard essentials dispatched same-day for weekend builds."),
        ("Factory", "The Purchaser", "Volume pricing, kitted supply and procurement integration for production lines."),
    ],
    "sports": [
        ("User", "The Beginner", "An induction and a programme built for where you are, not where the adverts assume."),
        ("Trophy", "The Athlete", "Periodised programming and weekly review toward a goal you can name."),
        ("Activity", "The Hobbyist", "Coached classes that fit a busy life and actually move the numbers."),
    ],
    "entertainment": [
        ("Megaphone", "The Brand", "Launch events designed so the product, not the logistics, is the headline."),
        ("Users", "The Festival", "Multi-stage production and crowd management that scale without losing the feeling."),
        ("Mic", "The Artist", "Sound, staging and show-calling that make a live moment land."),
    ],
    "ecommerce": [
        ("ShoppingBag", "The Shopper", "A tightly edited catalogue — everything carried is worth carrying."),
        ("Zap", "The Member", "Early drops, member pricing and next-day delivery for the returning buyer."),
        ("Briefcase", "The Wholesaler", "Trade pricing, net terms and custom orders treated with the same care."),
    ],
    "healthcare": [
        ("User", "The Individual", "Unhurried consultations with written plans you can actually follow."),
        ("Users", "The Family", "Shared records, paediatric-friendly care and one coordinator for the household."),
        ("HeartPulse", "The Chronic Care Patient", "Monitoring and follow-up between appointments, so care is continuous."),
    ],
    "education": [
        ("Rocket", "The Career Changer", "Live cohorts and real projects that bridge from your current role to the next."),
        ("Users", "The Team", "Group programmes with shared milestones and instructor-led sessions."),
        ("GraduationCap", "The Student", "Structured paths with mentors who stay until the portfolio is done."),
    ],
    "saas": [
        ("Code", "The Developer", "Ship from any CI, roll back in one click, and see real-time metrics."),
        ("LayoutDashboard", "The Product Team", "Custom views, governed sharing and insights without the dashboard sprawl."),
        ("ShieldCheck", "The Enterprise", "SSO, audit logs and dedicated infrastructure that pass procurement review."),
    ],
}

FALLBACK = "saas"


def problem(industry: str) -> dict:
    return PROBLEMS.get(industry, PROBLEMS[FALLBACK])


def personas(industry: str) -> list:
    return PERSONAS.get(industry, PERSONAS[FALLBACK])