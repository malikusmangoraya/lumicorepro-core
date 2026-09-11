"""
CopyWriter — industry-specific persuasive marketing copy for generated sites.

Every generated project gets conversion-focused copy (hero, value props,
testimonials, SEO meta) instead of generic placeholder text. Copy is tuned per
industry; unknown industries fall back to a strong generalist set.
"""

from typing import Any, Dict

# Industry aliases → canonical keys
INDUSTRY_ALIASES = {
    "restaurant": "restaurant", "cafe": "restaurant", "bakery": "restaurant",
    "food": "restaurant", "hotel": "restaurant", "coffee": "restaurant",
    "bar": "restaurant", "catering": "restaurant",
    "ecommerce": "ecommerce", "shop": "ecommerce", "store": "ecommerce",
    "fashion": "ecommerce", "retail": "ecommerce", "clothing": "ecommerce",
    "electronics": "ecommerce", "furniture": "ecommerce", "jewelry": "ecommerce",
    "realestate": "realestate", "property": "realestate", "real estate": "realestate",
    "real-estate": "realestate", "housing": "realestate", "apartment": "realestate",
    "healthcare": "healthcare", "medical": "healthcare", "clinic": "healthcare",
    "hospital": "healthcare", "dental": "healthcare", "doctor": "healthcare",
    "pharmacy": "healthcare",
    "fitness": "fitness", "gym": "fitness", "yoga": "fitness", "sports": "fitness",
    "personal trainer": "fitness",
    "education": "education", "school": "education", "academy": "education",
    "training": "education", "lms": "education", "college": "education", "university": "education",
    "travel": "travel", "tourism": "travel", "agency-travel": "travel",
    "portfolio": "portfolio", "personal": "portfolio", "photography": "portfolio",
    "photographer": "portfolio", "designer": "portfolio", "agency": "portfolio",
    "architect": "portfolio",
    "lawfirm": "lawfirm", "law": "lawfirm", "legal": "lawfirm",
    "salon": "beauty", "beauty": "beauty", "spa": "beauty", "barber": "beauty",
    "automotive": "automotive", "car": "automotive", "auto": "automotive",
    "vehicle": "automotive", "mechanic": "automotive",
    "wedding": "wedding", "events": "wedding", "event": "wedding",
    "event planner": "wedding",
    "saas": "saas", "software": "saas", "startup": "saas", "tech": "saas",
    "dashboard": "saas", "ai": "saas",
    "fintech": "fintech", "finance": "fintech", "banking": "fintech",
    "nonprofit": "nonprofit", "ngo": "nonprofit", "charity": "nonprofit",
    "foundation": "nonprofit",
}

COPY_BANK: Dict[str, Dict[str, Any]] = {
    "restaurant": {
        "tagline": "Where every plate tells a story",
        "headline": "Fresh flavours, cooked to order, served with heart",
        "subheadline": "From fire-kissed grills to hand-rolled desserts — an experience your guests will book again and again.",
        "cta": "Book a Table",
        "meta_description": "Reserve your table today and taste the difference: locally sourced ingredients, chef-crafted recipes, and service that turns first-timers into regulars.",
        "og_description": "Brand-new menu, warm ambience, and tables that fill fast. Reserve now.",
        "keywords": "restaurant booking, best restaurant, reservations, chef specials, local dining",
        "testimonial": "Booked online in seconds, seated on arrival — the food exceeded every expectation.",
        "value_props": [
            {"title": "Reserve in seconds", "text": "Live availability and instant confirmations, so you never wait on hold."},
            {"title": "Chef-crafted menus", "text": "Seasonal specials and signature dishes your customers can browse before they arrive."},
            {"title": "Reviews that convert", "text": "Built-in ratings and photos turn happy diners into your best marketers."},
        ],
    },
    "ecommerce": {
        "tagline": "Shop smarter, delivered faster",
        "headline": "Everything your store needs to sell more, 24/7",
        "subheadline": "A lightning-fast storefront with secure checkout, smart search, and real-time orders — engineered to turn browsers into buyers.",
        "cta": "Start Shopping",
        "meta_description": "Discover a premium shopping experience: secure checkout, fast delivery, smart search, and 24/7 online ordering built to scale with your brand.",
        "og_description": "A faster, smarter online store. Browse, buy, and track in minutes.",
        "keywords": "online store, ecommerce website, secure checkout, shop online, fast delivery",
        "testimonial": "Checkout was seamless and my order arrived two days early. Best online shopping experience yet.",
        "value_props": [
            {"title": "Friction-free checkout", "text": "One-page checkout with saved details, promo codes, and every payment gateway your customers expect."},
            {"title": "Smart product search", "text": "Filters, instant results, and recommendations that lift average order value."},
            {"title": "Order tracking built-in", "text": "Customers always know where their parcel is — fewer queries, more trust."},
        ],
    },
    "realestate": {
        "tagline": "Your property, perfectly presented",
        "headline": "Listings that sell faster, presented beautifully",
        "subheadline": "Professional property showcase with virtual tours, mortgage-ready lead capture, and tools that make every listing stand out.",
        "cta": "Explore Listings",
        "meta_description": "Browse premium property listings with virtual tours, verified photos, and instant lead capture. Find buyers and tenants faster with a listing site that presents like a showcase.",
        "og_description": "Beautifully presented listings with virtual tours and instant lead alerts.",
        "keywords": "real estate, property listings, virtual tour, house for sale, rent apartment",
        "testimonial": "Our listings get 3x more inquiries since the showcase site launched.",
        "value_props": [
            {"title": "Showcase-grade visuals", "text": "Full-screen galleries and virtual tours that present every property in its best light."},
            {"title": "Qualified leads instantly", "text": "Smart enquiry forms capture name, budget, and intent — so you never chase tire-kickers."},
            {"title": "Sold in weeks, not months", "text": "SEO-ready listings and shareable pages get your properties in front of the right buyers."},
        ],
    },
    "healthcare": {
        "tagline": "Care that fits your life",
        "headline": "Book appointments in seconds — get care without the wait",
        "subheadline": "Online scheduling, doctor profiles, and reminders that keep practices full and patients happy.",
        "cta": "Book Appointment",
        "meta_description": "Book your next appointment online in seconds. Browse verified doctor profiles, choose a time that suits you, and receive instant reminders.",
        "og_description": "Skip the waiting room. Book verified care online in seconds.",
        "keywords": "doctor booking, online appointment, clinic, telehealth, healthcare scheduling",
        "testimonial": "I booked in under a minute and got a reminder the night before. Hardly waited a second at the clinic.",
        "value_props": [
            {"title": "24/7 online booking", "text": "Patients book any time, day or night — no busy phone lines, no missed calls."},
            {"title": "Verified doctor profiles", "text": "Qualifications, experience, and real patient ratings build instant trust."},
            {"title": "Fewer no-shows", "text": "Automated SMS and email reminders keep your schedule full and productive."},
        ],
    },
    "fitness": {
        "tagline": "Stronger every single day",
        "headline": "Transform your body — train with purpose",
        "subheadline": "Memberships, class schedules, and trainer profiles in one place, so nobody has an excuse to skip a session.",
        "cta": "Join Today",
        "meta_description": "Find your new routine: flexible memberships, live class schedules, and expert trainers. Start your fitness journey today.",
        "og_description": "Flexible memberships, live schedules, and trainers ready to push you further.",
        "keywords": "gym membership, fitness classes, personal training, workout plan, join gym",
        "testimonial": "Signed up online, booked my first class in the same click. Two months in, I've never been more consistent.",
        "value_props": [
            {"title": "Memberships that sell", "text": "Clear tiers, transparent pricing, and signup in two clicks — zero friction to join."},
            {"title": "Live class schedules", "text": "Up-to-the-minute timetables and instant booking keep classes full every day."},
            {"title": "Trainers who attract", "text": "Professional profiles and results stories turn your coaches into your brand's best marketing."},
        ],
    },
    "education": {
        "tagline": "Learn anything, from anywhere",
        "headline": "Courses that teach — students that succeed",
        "subheadline": "Enrol online, track progress, and earn certificates with a learning platform built for modern students.",
        "cta": "Browse Courses",
        "meta_description": "Enrol in expert-led courses, track your progress, and earn recognised certificates — all from any device.",
        "og_description": "Expert courses with progress tracking and certificates. Start learning in minutes.",
        "keywords": "online courses, learn online, course enrolment, certificates, e-learning",
        "testimonial": "Enrolled in minutes and the progress tracking kept me motivated to finish.",
        "value_props": [
            {"title": "Instant enrolment", "text": "No paperwork — students start learning the moment they pay."},
            {"title": "Progress that sticks", "text": "Dashboards, certificates, and reminders keep completion rates high."},
            {"title": "Trustworthy reviews", "text": "Real student ratings help new learners pick the right course first try."},
        ],
    },
    "travel": {
        "tagline": "Pack light. Travel far.",
        "headline": "Book the trip you've been dreaming about",
        "subheadline": "Curated packages, live availability, and instant booking — your next adventure is a few clicks away.",
        "cta": "Plan My Trip",
        "meta_description": "Explore curated travel packages, compare itineraries, and book securely online. Your dream trip starts here.",
        "og_description": "Curated packages and instant booking. Your next adventure awaits.",
        "keywords": "tour packages, travel booking, holidays, itinerary, adventure trips",
        "testimonial": "Booked the whole family holiday online — itinerary, hotels, and flights in minutes.",
        "value_props": [
            {"title": "Packages people crave", "text": "Curated itineraries with clear pricing that make choosing effortless."},
            {"title": "Live availability", "text": "No stale pricing, no 'sorry, sold out' — customers book with confidence."},
            {"title": "Reviews that reassure", "text": "Verified traveller photos and ratings build trust before the booking."},
        ],
    },
    "portfolio": {
        "tagline": "Work that speaks for itself",
        "headline": "I help brands turn visitors into clients — beautifully",
        "subheadline": "A portfolio that shows your craft at its best, with case studies that persuade before a single call.",
        "cta": "See My Work",
        "meta_description": "A professional portfolio with case studies, client results, and work that converts visitors into enquiries.",
        "og_description": "Case studies, client results, and work you'll want to hire.",
        "keywords": "portfolio, case studies, freelance designer, hire designer, creative work",
        "testimonial": "Their portfolio told the whole story — we hired without a second call.",
        "value_props": [
            {"title": "Results-first case studies", "text": "Before/after and measurable outcomes prove the value, not just the aesthetics."},
            {"title": "One-click enquiries", "text": "A streamlined contact path means a new brief every time someone falls in love with your work."},
            {"title": "Built to be remembered", "text": "A polished, focused design that makes you look like the obvious choice."},
        ],
    },
    "lawfirm": {
        "tagline": "Clear counsel. Proven results.",
        "headline": "Serious legal counsel for your most important matters",
        "subheadline": "Practice-area expertise, transparent pricing, and a consult request process that makes hiring a lawyer feel effortless.",
        "cta": "Request a Consult",
        "meta_description": "Experienced legal counsel with clear practice areas and transparent pricing. Request a consultation online today.",
        "og_description": "Clear practice areas, transparent pricing, and easy online consults.",
        "keywords": "law firm, legal counsel, attorney, consultation, practice areas",
        "testimonial": "Consult request was easy, the response was fast, and the counsel was worth every cent.",
        "value_props": [
            {"title": "Clarity from the start", "text": "Transparent practice areas and pricing mean no surprises on the first call."},
            {"title": "Easy consultation requests", "text": "Clients describe their matter once and get a considered response — fast."},
            {"title": "Authority you can see", "text": "Results, credentials, and testimonials that convince before the phone rings."},
        ],
    },
    "beauty": {
        "tagline": "You're already beautiful. Let's enhance it.",
        "headline": "Book your glow-up in seconds",
        "subheadline": "Online bookings, service menus, and stylist profiles — the modern salon experience clients talk about.",
        "cta": "Book Now",
        "meta_description": "Book beauty services online in seconds. Browse our menu, pick your stylist, and lock in your appointment.",
        "og_description": "Menus, stylists, and bookings — your glow-up is one click away.",
        "keywords": "salon booking, beauty services, stylist, spa, book appointment",
        "testimonial": "Picked my stylist online, booked in ten seconds, and walked into a full diary. Perfect.",
        "value_props": [
            {"title": "Menus that entice", "text": "Beautiful service listings with pricing set the expectation before they arrive."},
            {"title": "Stylist matching", "text": "Profiles and portfolios help clients pick the right pair of hands."},
            {"title": "Full diaries", "text": "Online booking with reminders means fewer empty chairs and no-shows."},
        ],
    },
    "automotive": {
        "tagline": "Driven by quality",
        "headline": "Find your next drive — inspected, certified, ready",
        "subheadline": "Browse, compare, and enquire on quality vehicles with transparent specs and trade-in ready tools.",
        "cta": "Browse Vehicles",
        "meta_description": "Quality vehicles with transparent specs, certified inspections, and instant enquiry. Find your next drive today.",
        "og_description": "Quality vehicles, transparent specs, instant enquiry.",
        "keywords": "car dealership, buy car, certified vehicles, trade-in, vehicle enquiry",
        "testimonial": "Specs, photos, and honest pricing online — enquiry answered within the hour.",
        "value_props": [
            {"title": "Transparent listings", "text": "Full specs, real photos, and honest pricing sell the car before the test drive."},
            {"title": "Instant enquiries", "text": "Prospects share contact and trade-in details in one form — no phone tag."},
            {"title": "Trust that closes", "text": "Inspection badges and reviews make 'certified' actually mean something."},
        ],
    },
    "wedding": {
        "tagline": "Celebrate it your way",
        "headline": "The wedding plan that feels effortless",
        "subheadline": "Packages, galleries, and instant booking — the joyous planning experience couples actually enjoy.",
        "cta": "Check Availability",
        "meta_description": "Explore wedding packages, view real event galleries, and check availability online. Planning made effortless.",
        "og_description": "Packages and galleries that make planning the fun part.",
        "keywords": "wedding planner, event packages, wedding gallery, availability, event booking",
        "testimonial": "We planned the entire wedding online — the gallery sold us before the first call.",
        "value_props": [
            {"title": "Packages with clarity", "text": "Tiered options with honest pricing take the guesswork out of the biggest day."},
            {"title": "Real galleries", "text": "Past-event photos prove the magic before couples ever call."},
            {"title": "Effortless booking", "text": "Availability and enquiry forms that turn 'someday' into a booked date."},
        ],
    },
    "saas": {
        "tagline": "Ship faster, scale further",
        "headline": "The platform your team will thank you for",
        "subheadline": "Launch in days with pricing, onboarding, and analytics built in — the infrastructure you need to grow.",
        "cta": "Start Free Trial",
        "meta_description": "Launch a high-converting SaaS site with flexible pricing, real-time analytics, and security baked into every page.",
        "og_description": "Pricing, onboarding, and analytics built in — launch in days.",
        "keywords": "saas website, software platform, pricing page, free trial, analytics",
        "testimonial": "We shipped our pricing page in a weekend and trials started flowing the same week.",
        "value_props": [
            {"title": "Launches in days", "text": "Pricing, billing, and onboarding pages that turn interest into users fast."},
            {"title": "Analytics that matter", "text": "Conversion and usage dashboards that drive decisions, not vanity metrics."},
            {"title": "Enterprise-grade trust", "text": "Security, compliance, and uptime that unlock bigger customers."},
        ],
    },
    "fintech": {
        "tagline": "Your money, moving smarter",
        "headline": "Financial tools that feel effortless and secure",
        "subheadline": "Streamlined applications, transparent fees, and bank-grade security — trust built line by line.",
        "cta": "Get Started",
        "meta_description": "Modern financial technology with transparent fees, fast applications, and bank-grade security — built to earn trust.",
        "og_description": "Transparent, secure, and effortless — the fintech experience customers want.",
        "keywords": "fintech, financial services, digital banking, secure payments, transparent fees",
        "testimonial": "Applied online in one sitting — transparent, secure, and genuinely fast.",
        "value_props": [
            {"title": "Applications in minutes", "text": "Fast, form-friendly flows that don't scare away the very customers you want."},
            {"title": "Radically transparent fees", "text": "Clear pricing builds the trust that financial products live or die on."},
            {"title": "Security that sells", "text": "Bank-grade encryption and compliance signposts reassure at every step."},
        ],
    },
    "nonprofit": {
        "tagline": "Change starts with a single gift",
        "headline": "Give with confidence. See the impact you made.",
        "subheadline": "Story-driven campaigns, easy donation flows, and transparent impact reports that turn visitors into supporters.",
        "cta": "Donate Now",
        "meta_description": "Support a cause that matters. Donate securely online, see real impact updates, and be part of the change.",
        "og_description": "Donate securely and follow the impact your gift makes.",
        "keywords": "nonprofit, donate online, charity, impact, fundraising",
        "testimonial": "Donating took thirty seconds and I get real updates on where it went.",
        "value_props": [
            {"title": "Donations that flow", "text": "A secure, two-click giving experience that respects supporters' goodwill."},
            {"title": "Stories that move", "text": "Campaign narratives that turn 'that's sad' into 'I'll help'."},
            {"title": "Impact you can show", "text": "Progress updates turn one-time donors into lifelong supporters."},
        ],
    },
    "general": {
        "tagline": "Quality you can feel",
        "headline": "Professional. Polished. Ready for business.",
        "subheadline": "A website that presents your brand at its best — built to convert visitors into customers.",
        "cta": "Get in Touch",
        "meta_description": "A modern, professional website that presents your brand with clarity, speed, and polish — built to convert.",
        "og_description": "Professional, fast, and built to turn visitors into customers.",
        "keywords": "professional website, business website, modern design, fast, reliable",
        "testimonial": "From first draft to launch, everything worked exactly as promised.",
        "value_props": [
            {"title": "Professional by design", "text": "Clean, modern layouts that make your brand look like an industry leader."},
            {"title": "Fast by default", "text": "Optimised performance on every device keeps visitors — and Google — happy."},
            {"title": "Built to convert", "text": "Clear messaging and calls-to-action guide every visitor toward a decision."},
        ],
    },
}


def resolve_industry(industry: Any = None) -> str:
    """Map a raw industry string to a canonical copy-bank key."""
    key = str(industry or "general").strip().lower().replace("-", " ").replace("_", " ")
    return INDUSTRY_ALIASES.get(key, "general")


def copy_for(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Return the copy block for a build plan, merged with project metadata.

    Falls back to the generalist copy set and always returns a safe dict.
    """
    spec = (plan or {}).get("spec", {}) or {}
    industry = resolve_industry(spec.get("industry") or (plan or {}).get("industry"))
    copy = dict(COPY_BANK.get(industry, COPY_BANK["general"]))
    copy["industry"] = industry
    copy["project_name"] = (plan or {}).get("project_name", "website")
    copy["website_type"] = spec.get("website_type", "business")
    return copy