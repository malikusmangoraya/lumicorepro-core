"""Industry-specific content for international About/Services/Pricing/Contact pages.

Keyed by industry (matches brand_map.py). All icon names are verified to exist
in the installed lucide-react build. `{name}` in copy is replaced by the brand.
"""

IC = {
    "real-estate": {
        "services": [
            ("Home", "Buy & Sell", "Represented sales and acquisitions of prime residential property, handled end-to-end with discretion."),
            ("Key", "Rentals & Lettings", "Long-let and short-let management for landlords and international tenants, fully managed."),
            ("Building2", "New Developments", "Off-plan and new-build projects, from launch marketing through to completion and handover."),
            ("Calculator", "Valuation & Advisory", "Independent valuations, market studies and investment advice backed by live transaction data."),
        ],
        "process": [
            ("Compass", "Discover", "We begin with a private consultation to understand the brief, the budget and the timing."),
            ("Eye", "View", "A shortlist of hand-verified residences, arranged around your schedule, in person or virtually."),
            ("Handshake", "Close", "Negotiation, due diligence and completion coordinated by a single point of contact."),
        ],
        "pillars": [
            ("ShieldCheck", "Verified Listings", "Every residence is inspected and title-checked before it reaches your shortlist."),
            ("Users", "Private Clients", "Most of our business comes from referrals — discretion is the default, not an extra."),
            ("Award", "Market Leaders", "Recognised across prime markets for record-setting sales and honest advice."),
        ],
        "story": "was founded on a simple belief: that buying a home should feel considered, not transactional. Today we advise private clients, families and investors across prime markets, pairing institutional-grade research with the service of a boutique.",
        "pricing": [
            ("Essential", "$1,900", "per sale", "For sellers who want reach", ["Professional photography", "Floorplans & EPC", "Listing on 4 portals", "Buyer pre-qualification", "Negotiation support"], False),
            ("Signature", "$3,900", "per sale", "Our most-chosen service", ["Everything in Essential", "Cinematic listing film", "Drone & twilight shoot", "Dedicated client manager", "Premium portal placement", "Open-house events"], True),
            ("Portfolio", "Custom", "annual", "For investors & landlords", ["Everything in Signature", "Multi-property dashboard", "Yield & market reporting", "Tenant sourcing & vetting", "Quarterly portfolio review"], False),
        ],
        "faq": [
            ("What areas do you cover?", "We advise across prime urban markets and selected international destinations. Book a consultation and we will confirm coverage for your specific property."),
            ("How long does a sale usually take?", "Well-presented properties typically go under offer within four to six weeks. Your adviser will give you a realistic timeline at valuation."),
            ("Do you handle the legal side?", "We coordinate with your chosen solicitor or can introduce vetted legal partners in each market."),
            ("What are your fees?", "Fees are agreed up front and tiered by service level. There are no hidden charges — the quote you receive is the quote you pay."),
        ],
        "contact": {"address": "18 Mayfair Row, London W1", "phone": "+44 20 7946 0100", "email": "privateclients@", "hours": "Mon–Sat, 9am–7pm", "note": "Private viewings arranged outside hours on request."},
    },
    "fashion": {
        "services": [
            ("Scissors", "Couture Atelier", "Hand-finished garments cut and sewn in our atelier, with fittings led by the head cutter."),
            ("Gem", "Fine Jewellery", "Made-to-order pieces in responsibly sourced stones and recycled precious metals."),
            ("Palette", "Made to Measure", "Suits, coats and eveningwear drafted to your measurements and kept on file."),
            ("ShoppingBag", "Ready to Wear", "Seasonal collections available in-store and online, in limited runs."),
        ],
        "process": [
            ("MessagesSquare", "Consult", "A conversation about how you dress, what you need and what you want to feel."),
            ("Ruler", "Measure", "A full set of measurements and a first toile, refined until the fit is yours."),
            ("Sparkles", "Finish", "Hand-finished detailing, final fitting and your garment delivered in a keepsake box."),
        ],
        "pillars": [
            ("Leaf", "Responsible Sourcing", "Fabrics and stones traced to responsible suppliers, with certifications on request."),
            ("Award", "Atelier Craft", "Skilled makers, many with decades at the bench — craft you can feel in the seams."),
            ("HeartHandshake", "Personal Service", "One adviser, one relationship, kept for years rather than a season."),
        ],
        "story": "began with a narrow idea: make fewer things, and make them properly. We keep our collections small, our fabrics traceable and our fittings unhurried, so that every piece earns its place in your wardrobe for years.",
        "pricing": [
            ("Ready to Wear", "$290", "per piece", "Seasonal essentials", ["Limited-run garments", "Responsible fabrics", "Standard alterations", "30-day returns", "Care guide included"], False),
            ("Made to Measure", "$1,450", "per garment", "Our most-chosen service", ["Bespoke pattern", "Two fittings included", "Fabric library access", "Monogram on request", "Lifetime alterations", "Keepsake garment box"], True),
            ("Couture", "From $4,900", "per commission", "One-of-one pieces", ["Everything in Made to Measure", "Head-cutter led design", "Hand embroidery & beading", "Private atelier fittings", "Exclusive fabric sourcing"], False),
        ],
        "faq": [
            ("How long does a commission take?", "Ready-to-wear ships immediately. Made-to-measure takes four to six weeks; couture commissions eight to ten, depending on detail."),
            ("Do you ship internationally?", "Yes — insured worldwide delivery with duties calculated at checkout. Returns are accepted within 30 days on unworn pieces."),
            ("Can I use my own fabric?", "Absolutely. Bring your fabric or choose from our traceable library; we will advise on drape and lining."),
            ("Do you offer alterations?", "Standard alterations are included on made-to-measure, and offered for life at cost on couture pieces."),
        ],
        "contact": {"address": "7 Rue Saint-Honoré, Paris", "phone": "+33 1 42 60 01 00", "email": "atelier@", "hours": "Tue–Sat, 10am–6pm", "note": "Fittings by appointment to guarantee a private room."},
    },
    "food": {
        "services": [
            ("Utensils", "Tasting Menu", "A seasonal multi-course menu that changes with the market and the harvest."),
            ("Flame", "Open Fire Kitchen", "Wood-fired cooking at the heart of the room — every dish touches live flame."),
            ("Wine", "Cellar & Pairings", "A curated cellar of small growers, with pairings chosen to match each course."),
            ("Calendar", "Private Dining", "A private room and bespoke menus for celebrations and corporate dinners."),
        ],
        "process": [
            ("Leaf", "Source", "We buy what the day offers — fish, produce and meat from named suppliers we know."),
            ("ChefHat", "Cook", "Cooked to order over fire and finished at the pass, never held under a lamp."),
            ("Sparkles", "Serve", "Served by a team that can tell you exactly where every plate came from."),
        ],
        "pillars": [
            ("Leaf", "Seasonal Sourcing", "Produce from a tight radius, changed as often as the seasons demand."),
            ("Users", "Chef-Led", "The kitchen sets the menu — not a central office or a spreadsheet."),
            ("Award", "Critically Acclaimed", "Recognised by guides and guests alike for honest, ingredient-first cooking."),
        ],
        "story": "started as a small kitchen with one rule: cook only what is good that day. That rule still governs the menu, which is written each morning around what our suppliers bring, and cooked over flame with very little else.",
        "pricing": [
            ("Set Lunch", "$38", "per person", "Two courses, midweek", ["Seasonal starter", "Main course", "Freshly baked bread", "Filter coffee", "Midweek availability"], False),
            ("Tasting Menu", "$95", "per person", "Our most-chosen service", ["Seven courses", "Wood-fired throughout", "Bread & butter service", "Optional wine pairing", "Dietary menus on request"], True),
            ("Chef's Table", "$180", "per person", "Six seats, one counter", ["Everything in Tasting", "Extended ten-course menu", "Front-row kitchen seats", "Meet the chef", "Reserved cellar pours"], False),
        ],
        "faq": [
            ("Do you cater for dietary needs?", "Yes. Tell us when booking and the kitchen will write a full alternative menu — vegetarian, vegan and allergen-aware."),
            ("Is there a dress code?", "None. Come as you are; the room is warm and informal."),
            ("Can I book for a large group?", "Our private room seats up to twenty. For larger events we create a bespoke menu and layout."),
            ("Do you take walk-ins?", "A handful of bar seats are kept for walk-ins each evening, first come, first served."),
        ],
        "contact": {"address": "42 Market Street, City Centre", "phone": "+1 415 555 0142", "email": "reservations@", "hours": "Tue–Sun, from 5pm", "note": "Walk-in bar seats released daily at 5pm."},
    },
    "hospitality": {
        "services": [
            ("Plane", "Flights & Transfers", "Best-fare flights and private transfers, timed so your trip begins without friction."),
            ("Bed", "Handpicked Stays", "Hotels, riads and lodges personally inspected before they reach your itinerary."),
            ("Compass", "Guided Experiences", "Local guides and private experiences you would never find on an agency shelf."),
            ("Calendar", "Bespoke Itineraries", "A single plan built around your pace, your interests and your budget."),
        ],
        "process": [
            ("Target", "Brief", "We start with how you like to travel — pace, comfort level and what you want to remember."),
            ("MapPin", "Plan", "A draft itinerary with honest notes on travel times, weather and trade-offs."),
            ("Globe", "Travel", "You travel; we stay on call in the background, adjusting as the day demands."),
        ],
        "pillars": [
            ("HeartHandshake", "Local Partners", "We work with local operators and pay them fairly — the trips feel better for it."),
            ("Leaf", "Low-Impact Travel", "Small groups, considered routes and a stated carbon pledge on every trip."),
            ("ShieldCheck", "24/7 Support", "A real person on the phone, in your timezone, for the entire journey."),
        ],
        "story": "was built by people who got tired of trips that looked good in a brochure and fell apart on the ground. We travel every route we sell, use the guides we name, and answer the phone ourselves when something changes.",
        "pricing": [
            ("Explorer", "$1,200", "per person", "Short curated trips", ["4-day itinerary", "Handpicked stays", "Airport transfers", "Local guide days", "Email support"], False),
            ("Signature", "$3,400", "per person", "Our most-chosen service", ["Everything in Explorer", "7–10 day itinerary", "Private guides & drivers", "Two signature experiences", "24/7 in-trip support", "Carbon offset included"], True),
            ("Private", "Custom", "per journey", "Fully bespoke travel", ["Everything in Signature", "Designed from scratch", "Private villas & charters", "Dedicated trip designer", "Flexible dates & changes"], False),
        ],
        "faq": [
            ("What group sizes do you run?", "Signature trips are capped at twelve travellers, so guides stay heard and stays stay intimate."),
            ("What if my plans change?", "Flexible-date policies let you move most bookings up to 21 days before departure. Private trips are fully adjustable."),
            ("Are meals included?", "Breakfast is included throughout, plus the meals named in the itinerary. Your designer will flag anything extra."),
            ("Do you offset carbon?", "Yes — every Signature and Private journey includes a verified offset, and we publish the calculation."),
        ],
        "contact": {"address": "9 Harbour Walk, Suite 4", "phone": "+1 646 555 0188", "email": "journeys@", "hours": "Mon–Fri, 9am–6pm", "note": "In-trip support runs 24/7 for travelling guests."},
    },
    "portfolio": {
        "services": [
            ("PenTool", "Brand & Identity", "Naming, identity systems and guidelines that hold up from a favicon to a billboard."),
            ("Code", "Web & Product", "Design and build of marketing sites and product interfaces, shipped by the team that designed them."),
            ("Film", "Motion & Film", "Brand films, product motion and social cutdowns directed end to end."),
            ("Camera", "Photography", "Art-directed stills for launch campaigns, product and editorial."),
        ],
        "process": [
            ("MessagesSquare", "Discover", "We interrogate the brief, the market and the competition before a single pixel moves."),
            ("Layers", "Design", "Concepts, systems and iterations, reviewed with you in the open — no big reveal."),
            ("Rocket", "Launch", "Build, handover and support, so the work survives contact with the real world."),
        ],
        "pillars": [
            ("Award", "Awarded Work", "Recognised by industry juries and, more importantly, by the markets we enter."),
            ("Users", "Senior Team", "The people in the pitch are the people on the project. No bait and switch."),
            ("Target", "Strategy First", "Design decisions are argued from the business problem, not personal taste."),
        ],
        "story": "is an independent practice built for founders who compete on taste. We keep the team small and senior, we take fewer projects than we could, and we measure our work by what it does for the client's business.",
        "pricing": [
            ("Sprint", "$9,000", "per project", "A focused design sprint", ["Discovery workshop", "One direction, refined", "Core brand kit", "Landing page design", "Two review rounds"], False),
            ("Studio", "$28,000", "per project", "Our most-chosen service", ["Everything in Sprint", "Full identity system", "Website design & build", "Motion & asset library", "Brand guidelines", "30-day post-launch support"], True),
            ("Partner", "Custom", "retainer", "Ongoing creative partner", ["Everything in Studio", "Embedded senior team", "Continuous design & QA", "Quarterly strategy", "Priority scheduling"], False),
        ],
        "faq": [
            ("How long does a project take?", "A sprint runs two to three weeks. Full identity and site projects typically run six to ten weeks."),
            ("Who owns the work?", "You do — full IP transfers on final payment, along with source files and guidelines."),
            ("Do you work with startups?", "Yes. We reserve capacity each quarter for early-stage founders and can stage payments."),
            ("Can you work with our in-house team?", "Often the best arrangement. We embed alongside your team and hand over cleanly."),
        ],
        "contact": {"address": "Studio 12, 5th Avenue", "phone": "+1 212 555 0175", "email": "hello@", "hours": "Mon–Fri, 10am–6pm", "note": "New project enquiries answered within one business day."},
    },
    "fintech": {
        "services": [
            ("Wallet", "Accounts & Savings", "Everyday accounts with automated savings rules and no hidden monthly fees."),
            ("TrendingUp", "Investments", "Low-cost portfolios built around your goals, not a sales target."),
            ("CreditCard", "Payments & Cards", "Instant virtual cards, real-time controls and spending insights that land immediately."),
            ("ShieldCheck", "Security", "Bank-grade encryption, biometric access and proactive fraud monitoring."),
        ],
        "process": [
            ("FileText", "Apply", "A short online application — most customers are approved in minutes."),
            ("BadgeCheck", "Verify", "Identity checks handled securely, once, so you can move without friction later."),
            ("Zap", "Activate", "Your account and card go live straight away, with support one tap away."),
        ],
        "pillars": [
            ("Lock", "Bank-Grade Security", "Deposits protected, data encrypted and accounts watched around the clock."),
            ("Percent", "Transparent Fees", "One clear price, no hidden charges, and no fee for the things you use most."),
            ("Users", "Human Support", "Real people on chat and phone — never a loop of automated menus."),
        ],
        "story": "exists because basic banking should not be complicated or expensive. We stripped out the fees customers hate, automated the savings they forget, and wrapped it in security and support that respect your time.",
        "pricing": [
            ("Standard", "$0", "per month", "Everyday banking", ["Free current account", "Virtual & physical card", "Instant transfers", "Spend insights", "24/7 chat support"], False),
            ("Plus", "$9", "per month", "Our most-chosen service", ["Everything in Standard", "Automated savings rules", "Fee-free spending abroad", "Priority phone support", "Joint accounts", "Higher limits"], True),
            ("Private", "$29", "per month", "For larger balances", ["Everything in Plus", "Dedicated relationship manager", "Investment & FX desk", "Concierge banking", "Custom limits & reporting"], False),
        ],
        "faq": [
            ("Is my money protected?", "Eligible deposits are protected under the relevant deposit-guarantee scheme, up to the statutory limit."),
            ("How long does opening an account take?", "Most applications are approved within minutes; verification may add a short delay at peak times."),
            ("Are there fees for spending abroad?", "Plus and Private customers spend fee-free worldwide at the interbank rate."),
            ("Can I close my account easily?", "Yes — in-app, at any time, with balances transferred to an account of your choice."),
        ],
        "contact": {"address": "100 Financial District, Floor 20", "phone": "+1 888 555 0130", "email": "support@", "hours": "Support 24/7", "note": "Lost-card hotline available around the clock."},
    },
    "electronics": {
        "services": [
            ("Cpu", "Components", "A deep catalogue of parts with live stock counts and real lead times."),
            ("CircuitBoard", "Dev Boards", "Development and prototyping boards for engineers, students and makers."),
            ("Gauge", "Test & Measure", "Meters, scopes and sensors calibrated before dispatch."),
            ("Truck", "Fast Fulfilment", "Same-day dispatch on in-stock orders, with tracked delivery worldwide."),
        ],
        "process": [
            ("Compass", "Specify", "Search by spec, compare parts side by side and check stock in real time."),
            ("Wrench", "Build", "Order with confidence — every part ships with datasheets and compliance docs."),
            ("BadgeCheck", "Validate", "Test on arrival and return anything that does not meet spec, no questions asked."),
        ],
        "pillars": [
            ("BadgeCheck", "Quality Assured", "Parts sourced through authorised channels, never grey-market substitutes."),
            ("FileText", "Full Datasheets", "Complete documentation beside every listing — no hunting across the web."),
            ("Zap", "Same-Day Dispatch", "Order before the cut-off and it leaves the warehouse the same day."),
        ],
        "story": "was started by engineers frustrated by catalogues that hid stock levels and buried the datasheets. We put the specification, the stock and the documentation on the same page, and dispatch same-day when we say we will.",
        "pricing": [
            ("Maker", "Free", "to join", "For individuals & students", ["Live stock & pricing", "Datasheets on every part", "Standard dispatch", "Email support", "Bulk quote requests"], False),
            ("Engineer", "$19", "per month", "Our most-chosen service", ["Everything in Maker", "Volume & contract pricing", "Same-day dispatch cut-off", "Priority technical support", "Saved BOMs & reorder", "Extended returns"], True),
            ("Enterprise", "Custom", "annual", "For teams & production", ["Everything in Engineer", "Dedicated account manager", "Scheduled & kitted supply", "Custom part sourcing", "API & procurement integration"], False),
        ],
        "faq": [
            ("Are parts genuine?", "Yes — we buy through authorised distribution and provide compliance documentation on request."),
            ("How fast is delivery?", "In-stock orders placed before 4pm dispatch the same day, with tracked next-day options at checkout."),
            ("Do you offer bulk pricing?", "Yes. Add quantities to a quote or open an Engineer account for automatic volume pricing."),
            ("What is your returns policy?", "Unused parts can be returned within 30 days; faulty items are replaced immediately under warranty."),
        ],
        "contact": {"address": "Unit 5, Tech Park, North Road", "phone": "+44 161 555 0164", "email": "sales@", "hours": "Mon–Fri, 8am–6pm", "note": "Technical support line staffed by engineers, not scripts."},
    },
    "sports": {
        "services": [
            ("Dumbbell", "Strength Training", "Coached strength sessions programmed around measurable progression."),
            ("Activity", "Conditioning", "Engine-building conditioning that respects recovery as much as effort."),
            ("HeartPulse", "Recovery", "Recovery lab access — mobility, cold, and sleep coaching under one roof."),
            ("Target", "Personal Coaching", "One-to-one programming reviewed weekly against your data."),
        ],
        "process": [
            ("Gauge", "Assess", "A baseline assessment so every programme starts from evidence, not guesswork."),
            ("TrendingUp", "Programme", "A periodised plan with targets, tracked and adjusted as you progress."),
            ("Trophy", "Perform", "Testing and review, so you can see the progress and plan the next block."),
        ],
        "pillars": [
            ("Trophy", "Proven Results", "Members hit measurable goals — we publish the numbers rather than the hype."),
            ("Users", "Expert Coaches", "Qualified coaches on every floor, correcting form before it becomes injury."),
            ("Clock", "Open Access", "Train when it suits you, with early, late and weekend hours."),
        ],
        "story": "was built for people who are serious about training but tired of gyms that sell memberships rather than results. Our floors are coached, our programmes are written down, and progress is measured — not assumed.",
        "pricing": [
            ("Access", "$49", "per month", "Train on your terms", ["Full floor access", "Open gym hours", "Induction session", "Mobile app tracking", "No contract lock-in"], False),
            ("Coached", "$129", "per month", "Our most-chosen service", ["Everything in Access", "Weekly coached classes", "Personalised programme", "Quarterly assessment", "Recovery lab access", "Nutrition guidance"], True),
            ("Performance", "$299", "per month", "One-to-one, fully bespoke", ["Everything in Coached", "Weekly 1:1 coaching", "Fully bespoke programming", "Priority class booking", "Physio & recovery plan"], False),
        ],
        "faq": [
            ("Do I need experience?", "No — every new member gets an induction and a programme matched to their current level."),
            ("Is there a joining fee?", "No joining fee and no long contract. Membership is month-to-month and can be paused."),
            ("Can I freeze my membership?", "Yes, for up to eight weeks a year via the member app at no cost."),
            ("Do you have classes?", "Over sixty classes a week, from strength and conditioning to mobility and recovery."),
        ],
        "contact": {"address": "The Ironworks, 22 Dock Road", "phone": "+1 312 555 0155", "email": "train@", "hours": "Mon–Sun, 5am–11pm", "note": "Free trial session available for first-time visitors."},
    },
    "entertainment": {
        "services": [
            ("Music", "Live Production", "Full event production — staging, sound, lighting and show-calling."),
            ("Film", "Stage & Screen", "Video content, screens and broadcast for live and hybrid audiences."),
            ("Ticket", "Ticketing & Access", "Registration, ticketing and guest management that scale without queues."),
            ("Sparkles", "Immersive Design", "Creative direction and set design that turn a room into an experience."),
        ],
        "process": [
            ("MessagesSquare", "Concept", "We start with the feeling you want in the room, then design backwards from it."),
            ("Layers", "Produce", "Production schedules, vendors and rehearsals managed by one accountable team."),
            ("Rocket", "Deliver", "Run-of-show executed to the second, with contingency for everything."),
        ],
        "pillars": [
            ("Award", "Award-Winning", "Recognised productions across launches, festivals and galas."),
            ("Zap", "On-Time, Every Time", "Doors open when we say they will — programming rehearsed to the cue."),
            ("Users", "Specialist Crew", "Sound, light and stage specialists who have worked the biggest stages."),
        ],
        "story": "produces live experiences where the audience leaves having felt something. We take on the impossible logistics, choreograph them to the second, and hand you a show that runs whether or not the lights decide to cooperate.",
        "pricing": [
            ("Event", "$6,500", "per event", "Intimate gatherings", ["Up to 200 guests", "Sound & lighting package", "Stage management", "On-site crew", "Run-of-show document"], False),
            ("Production", "$18,000", "per event", "Our most-chosen service", ["Everything in Event", "Up to 1,000 guests", "Full stage & set build", "Broadcast or screens", "Artist liaison", "Rehearsal day included"], True),
            ("Bespoke", "Custom", "per project", "Large-scale productions", ["Everything in Production", "Creative direction included", "Multi-day productions", "Custom immersive set", "Dedicated production team"], False),
        ],
        "faq": [
            ("How far ahead should we book?", "For large productions, three to six months. We can mobilise smaller events in under four weeks."),
            ("Do you handle venues?", "Yes — we source, negotiate and manage venues, or work with the space you already have."),
            ("Can you produce hybrid events?", "Yes. We run broadcast-grade streams and in-room production from a single show call."),
            ("What about bad weather?", "Every outdoor production ships with a weather contingency plan built into the run-of-show."),
        ],
        "contact": {"address": "The Warehouse, 3 Canal Street", "phone": "+1 305 555 0199", "email": "production@", "hours": "Mon–Sat, 9am–8pm", "note": "Event-day production line opens from 6am."},
    },
    "ecommerce": {
        "services": [
            ("ShoppingBag", "Curated Range", "A tightly edited collection — only products that meet our bar."),
            ("Truck", "Fast Delivery", "Next-day dispatch and tracked shipping on every in-stock order."),
            ("ShieldCheck", "Secure Checkout", "Encrypted payments with a guarantee that your details stay yours."),
            ("BadgeCheck", "Authenticity Promise", "Every item verified before it ships, with a certificate where relevant."),
        ],
        "process": [
            ("Eye", "Browse", "A clean catalogue with real specs, honest reviews and clear stock."),
            ("ShoppingBag", "Order", "A checkout that takes seconds, with payment options that suit you."),
            ("Truck", "Delivered", "Tracked, insured delivery with a returns process that does not fight you."),
        ],
        "pillars": [
            ("BadgeCheck", "Guaranteed Quality", "We stand behind every product and every price on the site."),
            ("Truck", "Reliable Delivery", "Dispatch promises kept on 99% of orders, tracked end to end."),
            ("HeartHandshake", "Easy Returns", "Thirty-day returns with a prepaid label and no interrogation."),
        ],
        "story": "is a modern store built around a simple promise: sell only things worth buying, and look after the customer long after the sale. We edit hard, we ship fast, and we make returns painless because trust is the whole business.",
        "pricing": [
            ("Standard", "Free", "to shop", "Pay as you go", ["Full catalogue access", "Standard delivery", "30-day returns", "Email support", "Secure checkout"], False),
            ("Plus", "$39", "per year", "Our most-chosen service", ["Everything in Standard", "Free next-day delivery", "Early access to drops", "Extended 60-day returns", "Member-only pricing", "Priority support"], True),
            ("Business", "Custom", "annual", "For trade & bulk", ["Everything in Plus", "Volume trade pricing", "Dedicated account manager", "Net payment terms", "Custom orders & branding"], False),
        ],
        "faq": [
            ("How fast is delivery?", "In-stock orders placed before 3pm ship the same day, with next-day delivery available at checkout."),
            ("What is the returns window?", "Thirty days, extended to sixty for Plus members, with a prepaid return label included."),
            ("Are products genuine?", "Every item is verified before dispatch; anything needing certification ships with documentation."),
            ("Do you ship internationally?", "Yes, to over 190 countries, with duties calculated transparently at checkout."),
        ],
        "contact": {"address": "Fulfilment House, 14 Commerce Way", "phone": "+1 800 555 0121", "email": "care@", "hours": "Support 7am–10pm", "note": "Order tracking and returns handled online in seconds."},
    },
    "saas": {
        "services": [
            ("Rocket", "Deployment", "Ship from any CI to production in seconds, with rollback one click away."),
            ("BarChart3", "Analytics", "Real-time metrics that answer questions instead of just drawing charts."),
            ("ShieldCheck", "Security", "SSO, audit logs and role-based access enforced by default."),
            ("LayoutDashboard", "Dashboards", "Custom views for every team, shareable and governed without friction."),
        ],
        "process": [
            ("Zap", "Connect", "Connect your repo and existing tools in minutes — no migration project."),
            ("Code", "Integrate", "Use the API and webhooks to fit the platform into how your team works."),
            ("TrendingUp", "Scale", "Grow from a side project to enterprise load without re-platforming."),
        ],
        "pillars": [
            ("ShieldCheck", "Enterprise-Grade", "Security and compliance controls that pass procurement reviews."),
            ("Zap", "Fast Setup", "Productive on day one, not after a six-week onboarding programme."),
            ("Users", "Dedicated Support", "Engineers on support, with response times we publish and keep."),
        ],
        "story": "was built by engineers who were tired of stitching together tools to ship software. We put deployment, observability and access control on one platform, priced it to scale down as well as up, and put engineers on the support desk.",
        "pricing": [
            ("Starter", "$0", "per month", "For individuals & side projects", ["1 project", "Community support", "Core deploys & metrics", "7-day log retention", "Shared infrastructure"], False),
            ("Team", "$29", "per user / month", "Our most-chosen service", ["Everything in Starter", "Unlimited projects", "SSO & role-based access", "90-day log retention", "Priority support", "Audit logs"], True),
            ("Enterprise", "Custom", "annual", "For scale & compliance", ["Everything in Team", "Dedicated infrastructure", "SAML/SCIM provisioning", "Custom data retention", "99.99% SLA", "Solutions engineer"], False),
        ],
        "faq": [
            ("Is there a free plan?", "Yes — the Starter plan is free forever, with no credit card required and no trial clock."),
            ("Can I self-host?", "Enterprise customers can run the platform in their own cloud or on-premises environment."),
            ("How does billing work?", "Per-seat monthly or annual billing. Annual plans save 20%, and you can change plans at any time."),
            ("What support is included?", "Team includes priority support with published SLAs; Enterprise adds a named solutions engineer."),
        ],
        "contact": {"address": "Remote-first — HQ, 20 Innovation Way", "phone": "+1 888 555 0177", "email": "sales@", "hours": "Support 24/7", "note": "Security and procurement packs available on request."},
    },
    "healthcare": {
        "services": [
            ("Stethoscope", "Consultations", "Unhurried appointments with clinicians who listen before they prescribe."),
            ("Calendar", "Appointments", "Same-day and next-day booking, online or by phone, with reminders."),
            ("HeartPulse", "Monitoring", "Ongoing monitoring and follow-up so nothing falls between appointments."),
            ("FileText", "Records & Results", "Your results and notes, explained plainly and stored securely."),
        ],
        "process": [
            ("Calendar", "Book", "Book online in under a minute, choosing the clinician and time that suit you."),
            ("Stethoscope", "Consult", "A full consultation with clear explanations and a written plan."),
            ("HeartPulse", "Follow-Up", "Scheduled follow-up and monitoring, so treatment is a process, not an event."),
        ],
        "pillars": [
            ("ShieldCheck", "Confidential", "Your records are private, encrypted and never shared without consent."),
            ("Users", "Expert Clinicians", "Registered, experienced practitioners who keep their knowledge current."),
            ("HeartPulse", "Patient-First", "Care designed around your comfort and understanding, not throughput."),
        ],
        "story": "was founded to make good care feel human again. We give clinicians the time to listen, explain every result in plain language, and follow up properly — because healthcare works best as a relationship, not a transaction.",
        "pricing": [
            ("Consultation", "$75", "per visit", "Pay as you go", ["30-minute appointment", "Written treatment plan", "Prescription if needed", "Results explained", "Secure record access"], False),
            ("Care Plan", "$39", "per month", "Our most-chosen service", ["Everything in Consultation", "Priority same-day booking", "Unlimited follow-up messages", "Annual health review", "Monitoring & reminders", "Family add-ons available"], True),
            ("Family", "$89", "per month", "Cover for the household", ["Everything in Care Plan", "Up to four family members", "Paediatric-friendly clinicians", "Shared family records", "Dedicated care coordinator"], False),
        ],
        "faq": [
            ("Are your clinicians registered?", "Yes — all practitioners are fully registered and hold current professional indemnity cover."),
            ("Can I get an appointment quickly?", "Care Plan members get priority same-day booking; standard appointments are usually next-day."),
            ("Is my data secure?", "Records are encrypted, access-controlled and handled in line with data-protection law."),
            ("Do you offer video appointments?", "Yes, video and in-person consultations are both available at booking."),
        ],
        "contact": {"address": "The Medical Centre, 5 Wellness Road", "phone": "+1 800 555 0166", "email": "care@", "hours": "Mon–Sat, 8am–8pm", "note": "Out-of-hours advice line for registered patients."},
    },
    "education": {
        "services": [
            ("GraduationCap", "Courses", "Structured courses from working experts, built to be finished, not abandoned."),
            ("Users", "Cohorts", "Small cohorts that learn together, with live sessions and peer feedback."),
            ("BookOpen", "Curriculum", "A practical curriculum with projects that build into a real portfolio."),
            ("Award", "Certification", "Recognised certificates that prove what you can do, not just what you watched."),
        ],
        "process": [
            ("Target", "Enrol", "Choose a course and join a cohort whose pace matches your life."),
            ("BookOpen", "Learn", "Learn by doing — lessons, live sessions and projects reviewed by mentors."),
            ("Trophy", "Certify", "Complete your project portfolio and earn a certificate you can show."),
        ],
        "pillars": [
            ("Users", "Community", "A cohort and alumni network that keeps working long after the course ends."),
            ("Award", "Accredited", "Certification backed by industry partners and mapped to real roles."),
            ("Globe", "Accessible", "Online-first delivery, flexible payment plans and lifetime access to materials."),
        ],
        "story": "exists to close the gap between what courses promise and what learners finish. Our cohorts are small, our projects are real, and our mentors stay with you until the portfolio is done — because completion is the whole point.",
        "pricing": [
            ("Self-Paced", "$199", "per course", "Learn on your schedule", ["Lifetime course access", "All lessons & materials", "Practice projects", "Community access", "Certificate on completion"], False),
            ("Cohort", "$599", "per course", "Our most-chosen service", ["Everything in Self-Paced", "Live weekly sessions", "Small-group mentoring", "Project reviews", "Portfolio & career clinic", "Alumni network"], True),
            ("Career", "$1,900", "per programme", "Diploma & job support", ["Everything in Cohort", "Multi-course diploma", "1:1 mentor matching", "Interview preparation", "Employer introductions", "Guaranteed project review"], False),
        ],
        "faq": [
            ("Do I need prior experience?", "Most courses start from fundamentals; each listing states any prerequisites clearly."),
            ("Can I pay in instalments?", "Yes — Cohort and Career programmes offer interest-free instalment plans at checkout."),
            ("How much time is needed?", "Expect four to six hours a week for cohort courses; self-paced is entirely up to you."),
            ("Is the certificate recognised?", "Our certificates are issued with industry partners and can be verified by employers online."),
        ],
        "contact": {"address": "Online-first — Learning Hub, 8 Campus Way", "phone": "+1 888 555 0144", "email": "admissions@", "hours": "Mon–Fri, 9am–7pm", "note": "Admissions team answers questions about cohorts and funding."},
    },
}

FALLBACK = "saas"


def content(industry: str) -> dict:
    return IC.get(industry, IC[FALLBACK])