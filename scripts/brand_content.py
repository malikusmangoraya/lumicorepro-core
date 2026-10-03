"""Per-brand unique content — 43 bespoke content sets (v7.11).

Each brand gets its own problem reframe, personas, feature descriptions,
pricing, FAQ, testimonial and comparison table. Nothing is shared between
brands (industry is only a hint for voice). All icons verified in the
installed lucide-react build.
"""

BRAND_CONTENT = {
    # ===================== REAL-ESTATE =====================
    "aurelia-estates": {
        "problem": {
            "heading": "The right home is out there — most buyers never see it",
            "body": "Prime residences rarely reach the open market. They trade quietly between collectors, and the buyer who waits for a listing ends up with what is left over, not what they wanted.",
            "icon": "Search",
        },
        "personas": [
            ("Building2", "Homeowners", "Owners of one-of-one residences who want discreet, high-trust representation when they sell."),
            ("TrendingUp", "Investors", "Portfolio buyers chasing yield across borders, who need transparent structuring and tax-aware advice."),
            ("Globe", "International Buyers", "Global families relocating or acquiring a foothold — without visibility into local market quirks."),
        ],
        "fdescs": [
            "Off-market inventory shared only with pre-vetted clients, before it ever touches a portal.",
            "Dedicated concierge covering viewings, financing introductions and relocation logistics.",
            "A curated portfolio across 40+ countries, coordinated by a single senior advisor.",
            "Anonymised negotiations and strict privacy for high-profile sellers and buyers.",
        ],
        "pricing": [
            ("Essential", "3", "%", "For owners ready to list with market intelligence behind them.", ["Valuation & strategy", "Professional photography & staging advice", "Portal + private network listing"], False),
            ("Signature", "1.25", "%", "The private-client standard, for homes that deserve quiet handling.", ["Everything in Essential", "Off-market positioning & outreach", "Dedicated transaction advisor", "Negotiation & legal coordination"], True),
            ("Portfolio", "Custom", "", "For multi-asset portfolios across borders and tax regimes.", ["Everything in Signature", "Portfolio-wide strategy & phasing", "Cross-border tax structuring", "Quarterly portfolio reviews"], False),
        ],
        "faq": [
            ("Are your listings public?", "Only a fraction of our inventory is ever listed publicly. Most residences are shared privately with matched buyers for days before any marketing."),
            ("How do you keep a sale confidential?", "We sign non-disclosure agreements with every party, run anonymised viewings and never publish addresses or photography without consent."),
            ("Do you work with international buyers?", "Around 40% of our closings involve an international buyer. We coordinate currency, legal and relocation timelines end to end."),
            ("What makes your valuation credible?", "We benchmark every property against comparable private transactions — not just portal asking prices — and share the reasoning with you."),
        ],
        "testimonial": ("We sold in eleven days through a private channel we never knew existed. Aurelia handled everything with total discretion.", "Isabelle Marchand", "European family office principal"),
        "compare": {
            "cols": ["Aurelia Estates", "Typical agency"],
            "rows": [
                ("Off-market inventory", "Pre-vetted private network", "Public portal only"),
                ("Confidentiality", "NDA-guided, anonymised", "Publicised marketing push"),
                ("Senior advisor", "One dedicated partner", "Rotating agents"),
                ("Cross-border reach", "40+ countries coordinated", "Single city, single office"),
                ("Provenance research", "Hand-verified histories", "Rarely verified"),
            ],
        },
    },
    "terravista": {
        "problem": {
            "heading": "Great developments sell out — the average one doesn't",
            "body": "Most off-plan projects stall because the story reaches buyers as a brochure, not an experience. Good stock sells itself when it is presented the way buyers actually shop today.",
            "icon": "Search",
        },
        "personas": [
            ("Building2", "Developers", "Project teams who need to move inventory faster than the market expects."),
            ("TrendingUp", "Investors", "Buyers comparing off-plan yields who need trust before they sign."),
            ("Globe", "Distant Buyers", "Remote investors who decide without stepping on site and need to feel the place."),
        ],
        "fdescs": [
            "Walk-through films and photography that make a floor plan feel like a home.",
            "Guided virtual tours with live agents, built for remote and off-plan buyers.",
            "A sales CRM that follows every inquiry within hours — nothing slips, nobody waits.",
            "Marketing, sales and legal packaged so off-plan risk is explained, not hidden.",
        ],
        "pricing": [
            ("Launch", "0", "USD", "For developers testing a single project.", ["Cinematic listing package", "Virtual tour setup", "Inquiry CRM"], False),
            ("Growth", "2,500", "USD/project", "The standard for moving inventory seriously.", ["Everything in Launch", "Full sales floor & lead follow-up", "Off-plan buyer portal", "Monthly performance reports"], True),
            ("Portfolio", "Custom", "", "For multi-project pipelines.", ["Everything in Growth", "Multi-project dashboards", "Dedicated sales strategist", "Quarterly roadmap"], False),
        ],
        "faq": [
            ("How soon do we see leads?", "Inquiry follow-up begins within two working hours, and most projects see their first qualified site visit inside the first ten days."),
            ("Is it only off-plan work?", "No — we also package ready stock, resale and mixed portfolios that need a sharper buyer journey."),
            ("Who writes the copy?", "A dedicated real-estate strategist on your account, so voice stays consistent across launch and sales."),
            ("Do you handle payments?", "We integrate with your existing sales and payment flow rather than replacing it — no double data entry."),
        ],
        "testimonial": ("Three quarters of launch inventory moved in the first six weeks. The inquiry queue finally matches the quality of the product.", "Omar Haddad", "Head of Sales, TerraVista partner development"),
        "compare": {
            "cols": ["TerraVista", "Typical marketing firm"],
            "rows": [
                ("Buyer journey", "Cinematic to close", "Brochure only"),
                ("Lead velocity", "Follow-up in 2 hours", "Days, if at all"),
                ("Off-plan story", "Explained & de-risked", "Over-promised"),
                ("Reporting", "Monthly, per project", "Rarely shared"),
                ("Payments", "Integrates with yours", "Separate systems"),
            ],
        },
    },
    # ===================== FASHION =====================
    "maison-noir": {
        "problem": {
            "heading": "Modern luxury is louder than it is good",
            "body": "The market is flooded with logos and season turnover. The sharpest clients want fewer, better pieces — and very few houses are structured to deliver them.",
            "icon": "Scissors",
        },
        "personas": [
            ("Sparkles", "The Discerning Client", "Collectors who buy for permanence and would rather own twelve perfect pieces than a rail of fading trends."),
            ("Award", "Edition Seekers", "Buyers chasing numbered, limited pieces that keep their worth long after the season ends."),
            ("HeartHandshake", "Private Clients", "High-profile figures who need fittings at home, silence in the press and total discretion."),
        ],
        "fdescs": [
            "Garments cut and finished by hand in Paris, with pattern-making that survives decades.",
            "Made-to-measure tailoring for the body you have, not the runway ideal.",
            "Numbered editions that are never re-released — scarcity built into the craft.",
            "By-appointment showing rooms where lines are tried in private, never on camera.",
        ],
        "pricing": [
            ("Ready-to-Wear", "From 1,800", "EUR", "Limited runs of the house codes, made in small numbers.", ["Made in Paris", "Numbered edition", "Care concierge"], False),
            ("Made-to-Measure", "From 6,500", "EUR", "Patterns drafted to your measurements in atelier appointments.", ["Everything in Ready-to-Wear", "Two atelier fittings", "Personal pattern archived", "Priority pieces each season"], True),
            ("Sur-Mesure", "On request", "", "Full bespoke: hand-finished pieces built around a single occasion.", ["Everything in Made-to-Measure", "Atelier visit & fabric trip", "Dedicated craftsman", "Private showing room"], False),
        ],
        "faq": [
            ("How long does a made-to-measure piece take?", "Six to nine weeks from first fitting, including two atelier fittings. Sur-mesure pieces can take up to twelve."),
            ("Are your editions truly limited?", "Yes. Every piece is numbered and the patterns are retired — no edition is ever re-run."),
            ("Can you fit clients outside Paris?", "We travel quarterly to key cities, and many private clients arrange atelier visits with full confidentiality."),
            ("Do you repair or alter older pieces?", "Always. Pieces from the house return to the atelier for alterations and restoration, free for the first decade."),
        ],
        "testimonial": ("Twelve years of wardrobe and every piece still fits its moment. Maison Noir understands that restraint is the rarest kind of luxury.", "Claire Fontaine", "Private client, Paris"),
        "compare": {
            "cols": ["Maison Noir", "Maisons mass-market"],
            "rows": [
                ("Production", "Hand-finished in Paris", "Off-shored, seasonal"),
                ("Editions", "Numbered, never re-run", "Restocked to sell out"),
                ("Fit", "Patterns cut to you", "Off-the-rack approximations"),
                ("Longevity", "Decade of aftercare", "Season lifecycle"),
                ("Acquisition", "Private fitting", "Public launches"),
            ],
        },
    },
    "mirage-beauty": {
        "problem": {
            "heading": "Beauty is sold on promises, not pigment",
            "body": "Clean claims and celebrity campaigns have outpaced what the product actually does on skin. Buyers are exhausted by formulas that flatter in the ad and fade by noon.",
            "icon": "Sparkles",
        },
        "personas": [
            ("Sparkles", "Color Explorers", "Risers and artists who treat pigment as a language and want shades that actually perform."),
            ("ShieldCheck", "Clean-Conscious Buyers", "Shoppers who read every label and refuse to trade ethics for results."),
            ("Star", "Working Makers", "MUA-adjacent creators building looks under lights, who need pigment to stay true on camera."),
        ],
        "fdescs": [
            "Dense, buildable pigment that stays true from midday through the night.",
            "Formulas certified cruelty-free and vegan, without offsetting the color payoff.",
            "A shade range built across skin tones — matched by people, not presumptions.",
            "Shade matching on video so you buy the right drop the first time.",
        ],
        "pricing": [
            ("Essentials", "From 24", "USD", "The core wardrobe: lashes, liner, a blush the range is known for.", ["Vegan formulas", "Recyclable packaging", "Free halfline returns"], False),
            ("The Edit", "From 58", "USD", "Curated sets that build a complete look.", ["Everything in Essentials", "Shade matching session", "Free pigment kit"], True),
            ("Studio", "From 120", "USD", "For working artists — palettes at scale and pro consultation.", ["Everything in The Edit", "Pro consultation & test batch", "Bulk pricing", "Artist credit program"], False),
        ],
        "faq": [
            ("Are formulas really pigment-forward?", "Yes — the top ingredient lists start with the pigment base, not water and fillers. Payoff is the point."),
            ("How do you handle undertones?", "Our shade range spans 90 shades across six undertone families, matched in a live video session."),
            ("Is the brand truly cruelty-free?", "Certified, third-party audited, with vegan formulas as the default across the range."),
            ("What is the return policy?", "Half-lines are free to return, and opened pigment is covered for 30 days if the shade genuinely misses."),
        ],
        "testimonial": ("I bought a foundation thinking I was compromising. It is the most honest color hit in my kit — camera, club and daylight.", "Priya Nair", "Working MUA, London"),
        "compare": {
            "cols": ["Mirage Beauty", "Legacy cosmetic houses"],
            "rows": [
                ("Pigment", "Pigment-first formulas", "Filler-first"),
                ("Testing", "Vegan & cruelty-free", "Mixed standards"),
                ("Shades", "90 across 6 tones", "Narrow ranges"),
                ("Match", "Video shade matching", "Guess in store"),
                ("Ethics", "Third-party audit", "Self-reported"),
            ],
        },
    },
    # ===================== FOOD =====================
    "ember-salt": {
        "problem": {
            "heading": "Fine dining has become theatre without a story",
            "body": "Tasting menus chase spectacle while the ingredient quietly loses. Guests are weary of plates that photograph well and taste half as good as they look.",
            "icon": "Flame",
        },
        "personas": [
            ("Star", "Food Travelers", "Guests planning a whole evening around one table, who book a month out because the kitchen is worth it."),
            ("HeartHandshake", "Regulars", "Neighbourhood guests who want a kitchen that marks their habits and celebrates them."),
            ("Users", "Celebrations", "Families and partners marking an occasion with a menu that feels personal, not prescribed."),
        ],
        "fdescs": [
            "A wood-fired kitchen where the flame does the cooking and the produce keeps its voice.",
            "A tasting menu rewritten with the harvest — never printed in advance, always seasonal.",
            "A chef's counter where the pass is open and the curious are welcome.",
            "A cellar of rare vintages poured by a sommelier who knows every label in it.",
        ],
        "pricing": [
            ("À la Carte", "From 95", "EUR", "The bar and lounge menu — smaller plates, open fire, no theatre.", ["Two to five courses", "Natural wine pours", "Walk-in friendly"], False),
            ("Tasting", "195", "EUR", "The full seven-course story of the season.", ["Seven courses over flame", "Seated at pass or room", "Wine pairing available"], True),
            ("Chef's Table", "295", "EUR", "The kitchen's private counter — twelve seats, full service.", ["Seven courses, chef-led", "Reserved counter seat", "Pairing & print menu"], False),
        ],
        "faq": [
            ("How far ahead should we book?", "The tasting menu opens twelve weeks out and most weekend seats go within the first three weeks."),
            ("Is the tasting menu suitable for vegetarians?", "The kitchen builds a full vegetarian arc every season — same number of courses, same ambition."),
            ("What is the dress standard?", "There isn't one. Come as the evening deserves."),
            ("Do you have a children's option?", "We seat families happily and can shorten a sequence without lowering the standard."),
        ],
        "testimonial": ("The tasting menu changed with the week's catch and every course knew exactly what it was for. One of the few tables that earned its stars without noise.", "Tomás Alvarez", "Restaurant critic, quarterly columnist"),
        "compare": {
            "cols": ["Ember & Salt", "Conventional fine dining"],
            "rows": [
                ("Cooking", "Open flame, produce-led", "Sous-vide, sauce-led"),
                ("Menu", "Rewritten with the harvest", "Static, season-blind"),
                ("Access to kitchen", "Open pass", "Behind closed doors"),
                ("Wine", "Rare, hand-poured", "Mega-list, detached"),
                ("Bookings", "12 weeks, worth it", "Same-day, forgettable"),
            ],
        },
    },
    "cinder-steel": {
        "problem": {
            "heading": "Barbecue is beloved — and mostly badly done",
            "body": "Smoke is forgiving once, then punishing. Most smokehouses lean on sauce and sugar; the pit gets no technique and the diner knows it.",
            "icon": "Flame",
        },
        "personas": [
            ("Star", "Pit Pilgrims", "Meat enthusiasts who track bark and smoke rings across cities like maps."),
            ("Users", "Night Out", "Groups who want a big, warm table, a rye you can talk about and a meal that lingers."),
            ("HeartHandshake", "Regulars", "Locals who came once at the opening and never stopped."),
        ],
        "fdescs": [
            "Brisket cooked for fifteen hours over oak and fruitwood, hand-fed through the day.",
            "Sauces built from the day's kitchen scraps — reduced, bold, never bottled ahead.",
            "A rye bar that matches the smoke: dark pours, thoughtful pairs.",
            "Pitmaster classes for the converts who want to take the fire home.",
        ],
        "pricing": [
            ("The Board", "From 34", "USD", "The core: brisket, ribs and sausage, all house-smoked.", ["Meat-heavy board", "Two sides", "House pickle"], False),
            ("The Full Pit", "From 58", "USD", "A longer stay of the menu and the bar.", ["Everything in The Board", "Third cut or daily special", "Rye flight pair"], True),
            ("Pit Class", "From 180", "USD", "A half-day course at the pit.", ["Group pit session", "Full breakfast cook", "Growler of our rub"], False),
        ],
        "faq": [
            ("How early should we come?", "The pit starts at dawn; the best boards go when we aren't the busiest — late lunch or early weeknights."),
            ("Is everything actually smoked?", "Every protein crosses the fire. Nothing is baked, braised-and-tinted or finished on a flat top."),
            ("Can you host a group?", "Yes — one long table, and the kitchen will design the board around your number."),
            ("Do you take reservations?", "Yes, and walk-ins sit at the bar. Classes need a booking."),
        ],
        "testimonial": ("The bark outlived the table. Fifteen hours of fire and patience, poured with a rye that understood the assignment.", "Marcus Reid", "Pit pilgrim, Austin transplant"),
        "compare": {
            "cols": ["Cinder & Steel", "Fast smokehouses"],
            "rows": [
                ("Cook time", "15+ hours, hand-fed", "Conveyor, gas-fin"),
                ("Sauce", "From kitchen scraps", "Bottled, sugar-led"),
                ("Bar", "Rye curated to smoke", "Soda fountain"),
                ("Transparency", "Open pit, classes", "Closed kitchen"),
                ("Repeatability", "Regulars by the year", "One visit, done"),
            ],
        },
    },
    "brass-basil": {
        "problem": {
            "heading": "The market's best produce is being cooked by the book",
            "body": "The kindest ingredients in the district are disappearing into menus written months ago. A bistro cooking with the day's flame and the morning's market is a rarer thing than it should be.",
            "icon": "Flame",
        },
        "personas": [
            ("Star", "Market Diners", "Guests who want to eat what the season actually delivered this week."),
            ("Users", "Wine Seekers", "Drinkers who want the winemaker in the room, not a list of labels."),
            ("HeartHandshake", "Weekend Regulars", "Families marking the week's end at a table that knows their names."),
        ],
        "fdescs": [
            "A menu written every day from what the market had this morning — never the same twice.",
            "A wood-fired grill that gives the ingredient a halo in two minutes flat.",
            "A natural wine list poured by growers, tasted before it is listed.",
            "A chef's table where the shortest menu gets the longest story.",
        ],
        "pricing": [
            ("Lunch", "From 28", "EUR", "Three swift courses built from the morning market.", ["Two to three courses", "Natural pour", "Walk-in seating"], False),
            ("Dinner", "From 58", "EUR", "The full arc of the day's flame and its best produce.", ["Four courses", "Grill-touched throughout", "Pairing option"], True),
            ("Chef's Table", "From 95", "EUR", "Six seats at the pass with the team.", ["Five courses, chef-led", "Kitchen story per course", "Grower pairing included"], False),
        ],
        "faq": [
            ("Is the menu really daily?", "Yes — it exists only once the morning market is assessed. A wet week tastes different from a dry one, by design."),
            ("Do you cater to vegetarians?", "The grill cooks the season, not just protein. Vegetables are treated with the same fire and ambition."),
            ("Can I book the chef's table?", "Yes, up to six guests, with a small deposit that comes off the meal."),
            ("Where does the wine come from?", "We pour small growers directly — many labels are tasted before they ever reach a list."),
        ],
        "testimonial": ("The fillet of the week arrived with the story of the morning market attached. Restaurants like this are why I still walk to dinner.", "Elena Vasquez", "Food writer, neighbourhood resident"),
        "compare": {
            "cols": ["Brass & Basil", "Set-menu bistros"],
            "rows": [
                ("Menu", "Daily, market-written", "Seasonal, pre-printed"),
                ("Fire", "Wood grill, minute precision", "Line griddles"),
                ("Wine", "Growers poured direct", "Importer lists"),
                ("Chef access", "Open pass, chef's table", "Kitchen closed"),
                ("Sourcing", "Morning market", "Fixed suppliers"),
            ],
        },
    },
    "vine-vale": {
        "problem": {
            "heading": "Wine lists are read, never poured",
            "body": "Neighbourhood bars list hundreds of labels nobody can explain. Guests want a bar where the pour has a story and the cheese answers it.",
            "icon": "Sparkles",
        },
        "personas": [
            ("Star", "Small-Grower Drinkers", "Wine lovers who seek the maker behind the label — not the famous importer."),
            ("Users", "Cheese Pairers", "Diners who build their evening around the board and want the pairing justified."),
            ("HeartHandshake", "Locals", "The regulars who have a standing seat and a name-pour."),
        ],
        "fdescs": [
            "Nine hundred labels from small growers, poured with a sentence — not a monograph.",
            "A cheese board rebuilt weekly from the cheese room beside the kitchen.",
            "Tastings hosted with the people who made the wine.",
            "Simple, honest bar food that sits well beside fermented things.",
        ],
        "pricing": [
            ("Glass", "From 9", "EUR", "The current open pour, chosen for the week.", ["Glass of the week", "Bar seat welcome"], False),
            ("Board", "From 22", "EUR", "Four to six cheeses with bread, fruit and a pour suggestion.", ["Curated board", "Two-pour pairing", "Small bite"], True),
            ("Tasting Flight", "From 45", "EUR", "Five pours around a theme, led by the buyer.", ["Five small pours", "Grower context", "Board optional"], False),
        ],
        "faq": [
            ("How are wines chosen?", "Everything is tasted before it is listed. We pour growers who can sit across the table and talk about their year."),
            ("Can you host groups?", "Yes — the floor seats thirty, and the full bar can be booked for tastings."),
            ("Is the board changed weekly?", "The cheese room turns over every seven days; a Thursday board rarely repeats on Friday."),
            ("Do you sell bottles to take home?", "Yes — most open bottles can be walked out under cork."),
        ],
        "testimonial": ("They poured a wine I thought I knew and gave it back to me with a grower's name on it. The board finished the conversation.", "Jonas Berg", "Wine columnist, longtime regular"),
        "compare": {
            "cols": ["Vine & Vale", "Standard wine bars"],
            "rows": [
                ("List", "Small growers, tasted", "Importer megas"),
                ("Pairing", "Board answers the pour", "Unrelated plates"),
                ("Food", "Cheese room daily", "Frozen snacks"),
                ("Education", "Tastings with makers", "Menu blurbs"),
                ("Regulars", "Standing seats", "Turnover tables"),
            ],
        },
    },
    # ===================== HOSPITALITY =====================
    "saffron-voyage": {
        "problem": {
            "heading": "Travel sells the picture, not the place",
            "body": "Group travel is a bus at sunrise and a hotel chain at dusk. Travellers are asking for rooms with a story — and the industry keeps answering with itineraries.",
            "icon": "Plane",
        },
        "personas": [
            ("Plane", "Experience Seekers", "Travellers who will pay for the morning of a real village over another monument photo."),
            ("Users", "Small Groups", "Friends and families travelling together, who want space without being a coach party."),
            ("HeartHandshake", "Ethical Travellers", "Guests who want their money to stay in the place they visit."),
        ],
        "fdescs": [
            "Groups of twelve or fewer, sized so the story can breathe.",
            "Briefings and kitchens led by locals — the narrator is from the place.",
            "Itineraries built from your dates, tastes and pace — never copied.",
            "Stays with owners and operators who keep guest money in the district.",
        ],
        "pricing": [
            ("Journey Light", "From 1,400", "USD", "Five days, one region, one story well told.", ["Group of 8-12", "Local narrator", "Owner-run stays"], False),
            ("Signature", "From 2,800", "USD", "The full story arc: two regions, seven days.", ["Everything in Journey Light", "Private kitchens & craft visits", "Flexible pace"], True),
            ("Private", "From 6,500", "USD", "An itinerary drawn for your travel party alone.", ["Your own narrator & driver", "Every stay owner-run", "24/7 trip lead"], False),
        ],
        "faq": [
            ("How large are the groups?", "Twelve maximum, and most journeys sit at eight. The story needs room to breathe."),
            ("Who leads the travel?", "Local storytellers — the person who grew up in the place narrates it."),
            ("Can you help with visas and flights?", "Our trip leads coordinate documentation and routing alongside the itinerary."),
            ("How does the money flow?", "Owner-run stays and local operators keep the majority of every fare in the district you visit."),
        ],
        "testimonial": ("We expected a tour. We got a villa with a grandmother's kitchen, a village feast and a morning that no brochure will ever hold.", "Ayesha Rahman", "Returning traveller, Dubai"),
        "compare": {
            "cols": ["Saffron Voyage", "Mass group travel"],
            "rows": [
                ("Group size", "8-12, story-friendly", "Coach, 40+"),
                ("Narrator", "Local storyteller", "Distant guide"),
                ("Stays", "Owner-run, memorable", "Chain hotels"),
                ("Money flow", "Stays in the district", "Leaves the district"),
                ("Pace", "Yours", "Itinerary's"),
            ],
        },
    },
    "marble-run-hotels": {
        "problem": {
            "heading": "Hotels are optimised for the room, not the stay",
            "body": "Loyalty points and amenity lists measure the wrong things. Guests choose again each night whether a place belongs to them — most hotels never earn that once.",
            "icon": "Users",
        },
        "personas": [
            ("Users", "Design Travellers", "Guests who pick a city by its buildings and a hotel by its light."),
            ("HeartHandshake", "Return Guests", "The ones who found their spot years ago and keep coming back to their corner."),
            ("Briefcase", "Work-From-Anywhere", "Remote workers who need a good desk and a better breakfast."),
        ],
        "fdescs": [
            "Rooms tuned for how people actually end their day — bed, bath, light, quiet.",
            "Breakfast from the bakery two doors down, not a buffet held warm since dawn.",
            "A loyalty program that remembers your room number and your tea.",
            "City guides written by the night staff — the places they actually go.",
        ],
        "pricing": [
            ("City", "From 109", "EUR", "The essential Marble Run room.", ["Design-led room", "Bakery breakfast", "Loyalty points"], False),
            ("Signature", "From 169", "EUR", "Better light, a bigger desk, the corner you asked for last time.", ["Everything in City", "Preferred floor & corner", "Late checkout"], True),
            ("Suite", "From 249", "EUR", "The rooms we write home about.", ["Everything in Signature", "Sitting area & bathtub", "Airport transfer"], False),
        ],
        "faq": [
            ("Do you reward return guests?", "Yes — a program that remembers you by name, tea and room number, and gives late checkout without being asked."),
            ("What time is breakfast?", "Until ten on weekdays and eleven at weekends. The bakery delivery arrives daily at seven."),
            ("Is there workspace?", "Every Signature room has a proper desk; several floors are quiet-zone by design."),
            ("Do you have family rooms?", "Yes — interconnecting rooms and a breakfast spread kids are actually allowed to enjoy."),
        ],
        "testimonial": ("The night porter remembered my tea from March. That is a better loyalty program than any app I have ever been asked to install.", "Katrin Vogel", "Frequent guest, Vienna"),
        "compare": {
            "cols": ["Marble Run Hotels", "Chain hotels"],
            "rows": [
                ("Rewards", "Remembers your habits", "Generic points"),
                ("Breakfast", "Bakery, daily", "Warm buffet"),
                ("Rooms", "Light-tuned, quiet floors", "Same room, everywhere"),
                ("Guides", "Staff's real places", "Sponsored listings"),
                ("Checkout", "Late, without asking", "Strict noon"),
            ],
        },
    },
    "cirrus-travel": {
        "problem": {
            "heading": "Booking engines book; they don't plan",
            "body": "A flight plus a hotel is not a journey. Trip-planning software keeps flattening travel into two dropdowns and a bundle, while the person who wanted an actual trip is left alone.",
            "icon": "Plane",
        },
        "personas": [
            ("Plane", "Planned Travellers", "Doers who want a real itinerary but refuse to reassemble five apps themselves."),
            ("Users", "Family Trips", "Multi-stop holidays where the logistics are the sculpture."),
            ("Briefcase", "Business Extenders", "Work trips stretched into a few personal days with zero friction."),
        ],
        "fdescs": [
            "A personal planner who builds the trip around how you like to move — not an algorithm's average.",
            "Fares worth the name, including the routing nobody shows you by default.",
            "Experiences booked with people on the ground, not voucher middlemen.",
            "Trip insurance and support that answer when you are already away.",
        ],
        "pricing": [
            ("Self-Serve", "0", "USD", "Search, book, done.", ["Best-fare engine", "Basic itinerary", "Email support"], False),
            ("Planned", "From 149", "USD/trip", "A human arranges the whole arc.", ["Dedicated planner", "Multi-stop itinerary", "Experiences included"], True),
            ("Concierge", "From 499", "USD/trip", "Everything, including the upgrades.", ["Everything in Planned", "24/7 trip line", "Airport handling & upgrades"], False),
        ],
        "faq": [
            ("What does a planner actually do?", "Builds the flight, stay and experience sequence around your dates and taste — then fixes it when life changes."),
            ("Is DIY free forever?", "Yes. The engine is always free; you pay only when a human builds you a plan."),
            ("Do you cover group trips?", "Yes — family and small-group plans are our most common work."),
            ("What happens when a flight changes?", "Your planner sees it before you do and re-sequences the rest of the journey."),
        ],
        "testimonial": ("One planner, three countries, zero spreadsheets. It finally felt like someone owned the whole trip.", "Daniel Marsh", "Frequent short-haul business traveller"),
        "compare": {
            "cols": ["Cirrus Travel", "Booking engines"],
            "rows": [
                ("Planning", "Human planners", "Algorithms, averages"),
                ("Itinerary", "Sequence built around you", "Two dropdowns"),
                ("Rerouting", "Planner catches it first", "You rebook"),
                ("Experiences", "Local, booked directly", "Voucher layers"),
                ("Support", "24/7 while away", "Ticket queue"),
            ],
        },
    },
    "zephyr-way": {
        "problem": {
            "heading": "Cruise lines sell the ship, never the sea",
            "body": "Mega-ships carry the crowd, the casino and the same four ports. The travellers who actually want the horizon have almost nowhere to go.",
            "icon": "Plane",
        },
        "personas": [
            ("Plane", "Horizon Seekers", "Sailors-at-heart who want small ships, quiet decks and the sea doing the scheduling."),
            ("HeartHandshake", "Mature Travellers", "Guests with the time and the appetite for real places, not ports that all look alike."),
            ("Users", "Small Groups", "Friends and families who want their own cabin constellation, not a floating mall."),
        ],
        "fdescs": [
            "Small ships with real passages — ports the big lines skip without apology.",
            "Guests cruise with onboard historians, not lounge entertainers.",
            "Itineraries bend with weather and season because the captain can.",
            "Booking that moves with your life: dates change without penalties.",
        ],
        "pricing": [
            ("Cabin Flex", "From 1,900", "USD", "The open deck, the horizon, the essentials.", ["Small-ship cabin", "Onboard historian", "Flexible date swap"], False),
            ("Voyage", "From 3,400", "USD", "A longer arc, better cabin, more ports.", ["Everything in Cabin Flex", "Preferred deck & window", "Two shore passes"], True),
            ("Stateroom", "From 5,800", "USD", "The quiet of a suite at sea.", ["Everything in Voyage", "Stateroom & balcony", "Pre-voyage stay"], False),
        ],
        "faq": [
            ("How small is 'small'?", "Under two hundred guests per sailing — a ship where the crew knows your name by day two."),
            ("Who leads the journey?", "Historians and geographers, not entertainers. The narration is the point."),
            ("Can dates really move?", "Yes — once per booking, your voyage can shift without penalty, up to the usual season cutoff."),
            ("Do I need sea legs?", "Weather routing means we avoid what is uncomfortable; balcony cabins and stabilisers help the rest."),
        ],
        "testimonial": ("Every port was a place the big lines skip. I came home with a tan, a logbook and a new standard for what sailing means.", "Hannah Lindqvist", "Five-time Zephyr guest, Stockholm"),
        "compare": {
            "cols": ["Zephyr Way", "Mega-cruise lines"],
            "rows": [
                ("Ship", "12 small ships", "Floating cities"),
                ("Guests", "Under 200", "Thousands"),
                ("Narration", "Historians onboard", "Port entertainers"),
                ("Ports", "Skipped gems", "The big four"),
                ("Flexibility", "Dates bend with life", "Strict, priced hard"),
            ],
        },
    },
    # ===================== FINTECH =====================
    "meridian-capital": {
        "problem": {
            "heading": "Wealth management is built for averages",
            "body": "The industry sells diversified hubs and quarterly whatever-the-market-did. Families that want conviction, transparency and a long horizon are told to be patient with the mediocre.",
            "icon": "BarChart3",
        },
        "personas": [
            ("BarChart3", "Founders", "Founders whose exits created a concentration and a problem few advisors can actually handle."),
            ("TrendingUp", "Family Offices", "Offices that want direct research and real positions — not curated beta."),
            ("ShieldCheck", "Institutional Savers", "Long-horizon savers who would rather own the winners than rent an index."),
        ],
        "fdescs": [
            "Fewer, deeper positions built on in-house fundamental research — conviction over diversification theatre.",
            "Access to direct investments most private clients never see on a platform.",
            "Family office services from a single accountable partner.",
            "Quarterly reporting that names what we own, why, and what changed.",
        ],
        "pricing": [
            ("Advisory", "0.75", "%", "Quarterly partner-led advice with full transparency.", ["Partner-led reviews", "Full position disclosure", "Reporting suite"], False),
            ("Managed", "1.15", "%", "Direct investment and concentrated portfolios.", ["Everything in Advisory", "Direct positions", "Tax-aware trading", "Deal access"], True),
            ("Family Office", "Custom", "", "The full architecture for complex wealth.", ["Everything in Managed", "Multi-family board", "Estate & succession", "Third-party audits"], False),
        ],
        "faq": [
            ("What do you mean by concentrated?", "We take meaningful positions in the businesses we understand best. Diversification is a byproduct of humility, not the strategy."),
            ("Who sees our holdings?", "A single named partner and a defined team. We operate under strict confidentiality agreements."),
            ("What are the fees?", "A flat percentage of assets under management — no commissions, no hidden entrail percentages."),
            ("Is client money segregated?", "Yes, with an independent custodian and quarterly reconciliation you can verify."),
        ],
        "testimonial": ("Our exit made money the average advisor couldn't think about. Meridian built a plan, named the positions and has never once hedged a conversation.", "Ghana Vetri", "Founder, post-exit"),
        "compare": {
            "cols": ["Meridian Capital", "Traditional wealth firms"],
            "rows": [
                ("Positions", "Concentrated, direct", "Diversified hubs"),
                ("Research", "In-house fundamental", "Broker sell-side"),
                ("Reporting", "Quarterly, unfiltered", "Statement shrugs"),
                ("Access", "Direct deal flow", "Closed to clients"),
                ("Accountability", "Named partner", "Team roulette"),
            ],
        },
    },
    "vaultline": {
        "problem": {
            "heading": "Banking profits, quietly, from your forgetfulness",
            "body": "Overdrafts, hidden fees and savings features that move pennies. The honest market wants a bank that behaves like a good accountant — most apps are built like slot machines.",
            "icon": "Wallet",
        },
        "personas": [
            ("Wallet", "Budget-Builders", "Savers who want automation that actually moves the number — without chasing their spend."),
            ("TrendingUp", "Freelancers", "Irregular income earners who need a bank that smooths the feast-and-famine month."),
            ("ShieldCheck", "Fee-Weary Customers", "Banking customers who have simply stopped trusting the fine print."),
        ],
        "fdescs": [
            "Savings rules that pull before you can spend — round-ups, percentages, pay-day splits.",
            "Spend insights that describe a pattern, never shame a latte.",
            "Zero fees on the things that are supposed to be free.",
            "Instant virtual cards per goal, frozen and melted in one tap.",
        ],
        "pricing": [
            ("Standard", "0", "EUR", "Banking with the fees removed.", ["Current account", "Instant cards", "Zero-fee basics"], False),
            ("Plus", "4", "EUR/mo", "The bank that moves your money.", ["Everything in Standard", "Auto-savings rules", "Multi-goal vaults", "Spend analytics"], True),
            ("Metal", "12", "EUR/mo", "For the fully automated life.", ["Everything in Plus", "Cashback on signals", "Priority human support"], False),
        ],
        "faq": [
            ("Are you really zero fees?", "The things fees buy elsewhere — cards, transfers, hold-notice — are genuinely free here. We publish every charge on one page."),
            ("How do savings rules work?", "You set a rhythm — round-ups, a percentage of income, a fixed pull on pay days. We move it before you see it."),
            ("Is my money protected?", "Deposits are ring-fenced with our partner bank and covered under the applicable deposit guarantee scheme."),
            ("Can I have multiple cards?", "Yes — a virtual card per goal, each frozen or melted from the app."),
        ],
        "testimonial": ("I stopped treating my bank like an adversary. The account does the boring work and I keep the small wins.", "Sofia Lindgren", "Freelance designer, Stockholm"),
        "compare": {
            "cols": ["Vaultline", "Legacy banks"],
            "rows": [
                ("Fees", "Zero on the basics", "Fine print bounty"),
                ("Savings", "Automated rules", "Manual round-ups"),
                ("Insights", "Pattern, not shame", "Push-notice spam"),
                ("Cards", "Per-goal, instant", "One plastic card"),
                ("Support", "Humans by design", "IVR maze"),
            ],
        },
    },
    "harbor-insurance": {
        "problem": {
            "heading": "Insurance is sold on fear and paid out on excuses",
            "body": "Policies are written to be dense, claims are designed to be slow, and the honest middle — clear cover, honest price, days-not-months payouts — is treated as a marketing slogan.",
            "icon": "ShieldCheck",
        },
        "personas": [
            ("ShieldCheck", "Plain-Speech Buyers", "People who want to read the whole policy in one sitting."),
            ("Wallet", "Price-Refugees", "Customers who have seen premiums climb every renewal for no explained reason."),
            ("Briefcase", "Small Businesses", "Owners who need cover that keeps pace with an actual business."),
        ],
        "fdescs": [
            "One page per cover, written in sentences a new customer can finish.",
            "Claims by photograph — attach, submit, and get a decision on the calendar.",
            "Rates that hold at renewal; the price you saw is the price you keep.",
            "A claims desk answered by people, ten minutes an hour, every hour.",
        ],
        "pricing": [
            ("Personal", "From 12", "USD/mo", "Home, contents and the essentials, plainly listed.", ["One-page policy", "Photo claims", "Price-hold promise"], False),
            ("Family", "From 29", "USD/mo", "Home plus vehicles plus the softening of life's sharp edges.", ["Everything in Personal", "Multi-line bundle", "24/7 claims line"], True),
            ("Business", "From 79", "USD/mo", "Cover that grows with the company.", ["Everything in Family", "Liability & equipment", "Dedicated broker"], False),
        ],
        "faq": [
            ("Can I really read the whole policy?", "The core cover documents fit one page per product. Anything longer is a legal appendix we would rather you skip."),
            ("How fast are claims actually paid?", "Straightforward claims average 3.2 days from report to payment. Complex ones get a named handler, not a queue."),
            ("Do renewals really hold price?", "Our price-hold promise means the same cover doesn't climb at renewal for invented reasons. We say why if it ever changes."),
            ("What happens if I want to cancel?", "You cancel in the app and we refund the unused portion — no exit maze."),
        ],
        "testimonial": ("Every clause made sense, the claim was paid from three photos, and the renewal didn't double. I forgot insurance was supposed to feel like this.", "Nadine Chow", "Homeowner, Singapore"),
        "compare": {
            "cols": ["Harbor Insurance", "Traditional insurers"],
            "rows": [
                ("Policy", "One page, plain", "Dense word-walls"),
                ("Claims", "Photo + days", "Forms + months"),
                ("Renewal", "Price holds", "Climbs yearly"),
                ("Cancellation", "In-app, refunded", "Retention gauntlet"),
                ("Support", "Named handler", "Claims queue"),
            ],
        },
    },
    # ===================== ELECTRONICS =====================
    "voltus-atelier": {
        "problem": {
            "heading": "Creative workstations are sold to gamers",
            "body": "Render-time, thermal noise and driver stability decide a studio's day — but most rigs are specced for RGB and framerates. The working creative is underserved by a market that sells to the other room.",
            "icon": "Cpu",
        },
        "personas": [
            ("Cpu", "Studios", "Post-production teams whose render farm and quiet machine are the business."),
            ("Zap", "Audio Engineers", "Engineers chasing latency floors a general-purpose box can't reach."),
            ("Award", "Power Users", "Solo creators who spec, build and live inside the same machine."),
        ],
        "fdescs": [
            "Workstations assembled from hand-picked, binned components — matched, not average.",
            "Audio hardware with a latency floor and a quiet floor the spec sheet respects.",
            "Thermal engineering that keeps decades on the clock and dB off the meter.",
            "A support desk staffed by engineers, for the life of the machine.",
        ],
        "pricing": [
            ("Creator", "From 2,400", "USD", "The sober workstation for serious software.", ["Hand-selected components", "3-year warranty", "Engineer desk support"], False),
            ("Studio", "From 4,900", "USD", "Render nodes and audio rigs built to a brief.", ["Everything in Creator", "Optimised for your stack", "Thermal tuning report", "5-year warranty"], True),
            ("Atelier", "Custom", "", "Fleet workstations and lab installs.", ["Everything in Studio", "Fleet provisioning", "On-site commissioning"], False),
        ],
        "faq": [
            ("Why 'hand-picked'?", "Components vary within a bin. We test, match and burn in each part so your machine holds a consistent performance class."),
            ("Can you match an existing software stack?", "Yes — we build to the renderer, DAW or simulation suite you actually run, and confirm with a report."),
            ("What about noise?", "Every build ships a measured thermal report. Silence is a spec, not an accident."),
            ("Do you support after sale?", "Five years on Studio builds, with an engineer-first help desk that skips the level-one script."),
        ],
        "testimonial": ("Our renders finished a third faster off the same software, and the edit suite got quieter than the office. The report said 32dB; the room agreed.", "Devonte Cole", "Post-supervisor, boutique studio"),
        "compare": {
            "cols": ["Voltus Atelier", "Gaming-box builders"],
            "rows": [
                ("Components", "Binned & matched", "Average batches"),
                ("Thermals", "Measured report", "RGB first"),
                ("Audio", "Latency-tuned", "Consumer chipsets"),
                ("Validation", "Runs your stack", "Runs benchmarks"),
                ("Support", "Engineer desk, 5yrs", "Outsource queue"),
            ],
        },
    },
    "ternion-instruments": {
        "problem": {
            "heading": "Test gear is priced like a mystery",
            "body": "Lab-grade measurement has become a badge of budget — the scopes that hold calibration are luxury items, and the cheap ones lie when it matters.",
            "icon": "Activity",
        },
        "personas": [
            ("Activity", "Lab Engineers", "Benches where a drift of a tenth of a percent is the whole story."),
            ("Cpu", "Makers", "Fast-moving builders who need honest measurements without enterprise pricing."),
            ("Award", "Educators", "Labs teaching measurement discipline on gear that won't lie."),
        ],
        "fdescs": [
            "Calibration you can verify — every instrument ships with a certificate and a serial-to-serial record.",
            "Lab-grade construction: connectors that survive, cases that shield, knobs with click.",
            "Firmware that heals flaws — free feature and correction updates for the life of the instrument.",
            "Team pricing because a bench is a fleet, not a gadget.",
        ],
        "pricing": [
            ("Probe", "From 89", "USD", "The humble hero: probes and leads that hold their spec.", ["Certified accuracy", "Full lead warranty"], False),
            ("Bench Meter", "From 320", "USD", "Precision meters for the working bench.", ["Everything in Probe line", "Serial calibration record", "Firmware updates"], True),
            ("Scopes", "From 1,900", "USD", "The instruments that make a lab a lab.", ["Everything in Bench Meter", "Guaranteed calibration cycle", "Educator & fleet pricing"], False),
        ],
        "faq": [
            ("Is the calibration certificate real?", "Yes — every unit ships with a NIST-traceable certificate tied to its serial number. No certificate, no unit."),
            ("What does 'accuracy 99.98%' mean in practice?", "It means with proper calibration cycle the reading holds within the stated tolerance across the operating range."),
            ("Do you support educational labs?", "We price fleets for classrooms and offer calibration refresher programs for instructor benches."),
            ("What about repairs?", "Instruments return to our bench, not a third party, with a turnaround you can track."),
        ],
        "testimonial": ("The certificate travelled with the meter and the spec held across a year of hard benches. Our lab finally measures in absolutes.", "Dr. Elena Romanova", "Laboratory lead"),
        "compare": {
            "cols": ["Ternion Instruments", "Boutique test brands"],
            "rows": [
                ("Calibration", "Certified, per serial", "Trust-the-label"),
                ("Price", "Fleet-friendly", "Enterprise only"),
                ("Firmware", "Free lifetime fixes", "Paywalled features"),
                ("Repair", "Vendor bench", "Mail-back limbo"),
                ("Education", "Classroom pricing", "No program"),
            ],
        },
    },
    "veridian-e-catalog": {
        "problem": {
            "heading": "Component sourcing breaks the build",
            "body": "The part is in stock at noon and gone by delivery. Datasheets live on one site, pricing on another, dispatch is a lottery — and the build waits on all three.",
            "icon": "Cpu",
        },
        "personas": [
            ("Cpu", "Design Engineers", "Engineers who need a part, a datasheet and a lead time in one glance."),
            ("Zap", "Makers", "Prototypes turning over weekly who can't afford a 3-week parts stall."),
            ("Award", "Purchasing Teams", "Buyers aggregating boards and BOMs across projects."),
        ],
        "fdescs": [
            "Live stock levels tied to the warehouse — what the page says, the shelf holds.",
            "Datasheets beside the buy button, indexed inside the listing.",
            "Next-day dispatch on in-stock parts, with a cut-off you can set.",
            "Tiered bulk pricing shown before you commit a BOM.",
        ],
        "pricing": [
            ("Maker", "0", "USD", "Browse, datasheet, buy.", ["Live stock & datasheets", "Standard dispatch", "Order history"], False),
            ("Pro", "From 29", "USD/mo", "For benches that order weekly.", ["Everything in Maker", "Next-day dispatch", "Bulk tier pricing", "BOM upload & compare"], True),
            ("Team", "From 99", "USD/mo", "Purchasing at scale.", ["Everything in Pro", "Multi-user approvals", "API & CSV exports", "Priority allocation"], False),
        ],
        "faq": [
            ("How accurate is the stock count?", "Stock is tied to the warehouse system and reconciles nightly. A listed part is held at order."),
            ("Can I really see datasheets?", "Yes — every component page carries manufacturer datasheets, indexed and searchable inside the listing."),
            ("What is the dispatch promise?", "In-stock orders placed before the cut-off ship next day, with tracking from the carrier."),
            ("Do you quote bulk?", "Tier pricing is previewed on the page before you add to BOM — no sales call required for the standard tiers."),
        ],
        "testimonial": ("BOM in, parts out, datasheets open, all from one tab. The prototype that used to take six weeks now takes two.", "Raj Patel", "Embedded systems engineer"),
        "compare": {
            "cols": ["Veridian E-Catalog", "Legacy distributors"],
            "rows": [
                ("Stock", "Live, held at order", "Guesswork, backorders"),
                ("Datasheets", "Inline on listing", "Separate portals"),
                ("Dispatch", "Next day, trackable", "7-14 day lottery"),
                ("BOM", "Upload & compare", "Spreadsheet mail"),
                ("Pricing", "Tiers upfront", "Quote roulette"),
            ],
        },
    },
    # ===================== SAAS =====================
    "nova-forge": {
        "problem": {
            "heading": "Your pipeline is a pile of tools",
            "body": "Deploy, observe and access-control live on six platforms that don't talk. Every integration is a little priest, and shipping slows to the speed of the weakest seam.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("LayoutDashboard", "Platform Engineers", "Engineers who own the whole loop and are tired of gluing tools together."),
            ("Zap", "Product Teams", "Developers who just want the deploy to work and the metrics to make sense."),
            ("ShieldCheck", "Security & Ops", "Teams who need controls across the pipeline, visible and auditable."),
        ],
        "fdescs": [
            "Deploy from any CI in seconds — one command, guarded review, instant rollback.",
            "Metrics without the muck: the charts behind the numbers, built for product decisions.",
            "Enterprise controls with developer ergonomics — least privilege that doesn't fight the work.",
            "On-prem and hybrid options for teams that can't put everything in one cloud.",
        ],
        "pricing": [
            ("Dev", "0", "USD", "Start shipping on a small team.", ["Unlimited deploys", "3 seats", "Community support"], False),
            ("Pro", "29", "USD/mo", "The whole loop for a building team.", ["Everything in Dev", "Unlimited seats", "SLO alerts & history", "Priority support"], True),
            ("Enterprise", "From 499", "USD/mo", "Compliance, controls and scale.", ["Everything in Pro", "SSO & audit logs", "On-prem options", "Dedicated engineer"], False),
        ],
        "faq": [
            ("What problem is Nova Forge actually solving?", "The glue. One place for deploy, observe and access — so the weakest seam stops deciding your shipping speed."),
            ("Can we keep our current CI?", "Yes — we hook into any CI in seconds rather than replacing your toolchain."),
            ("Is rollback instant?", "One click, image-level, with a diff of what changed. No midnight git archaeology."),
            ("How do you handle compliance?", "SSO, audit logs, and on-prem/hybrid deployments for teams with hard data boundaries."),
        ],
        "testimonial": ("We removed four integrations and gained a fifth of our shipping capacity. Worst part: nobody misses any of the tools.", "Grace Adeyemi", "Platform lead, scale-up"),
        "compare": {
            "cols": ["Nova Forge", "DIY pipeline stacks"],
            "rows": [
                ("Deploys", "One command + rollback", "CI plugin stew"),
                ("Observability", "Product-first charts", "Dashboards to clean"),
                ("Access", "Least-privilege, ergonomic", "Per-tool admins"),
                ("On-prem", "Native", "Contract heroics"),
                ("Accounting", "Unlimited seats in Pro", "Per-seat surprise fee"),
            ],
        },
    },
    "aurora-cloud": {
        "problem": {
            "heading": "Cloud bills are the second product",
            "body": "Teams pay infrastructure to think, not to run. Every unrequested instance, every idle cluster and every manual fix is money the cloud silently keeps.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("LayoutDashboard", "Platform Teams", "Engineers who run boxes so the product team never has to."),
            ("TrendingUp", "Startups", "Teams where infra cost is a board-meeting number."),
            ("ShieldCheck", "Security Officers", "Leads who need the edge, the compliance story and the DDoS stance without drama."),
        ],
        "fdescs": [
            "Zero-ops deploys: one command, auto-scaled, secured, done.",
            "Scale to zero when quiet and back in seconds when the traffic returns.",
            "An edge network that puts the request next to the user.",
            "DDoS protection and TLS as defaults — never an upsell.",
        ],
        "pricing": [
            ("Hobby", "0", "USD", "For learning and side projects.", ["Limited resources", "Community support", "Public edge"], False),
            ("Production", "From 40", "USD/mo", "Serious apps on a global edge.", ["Everything in Hobby", "Auto-scaling & edge", "DDoS + TLS default", "Uptime SLAs"], True),
            ("Enterprise", "From 1,200", "USD/mo", "Compliance-grade infrastructure.", ["Everything in Production", "Dedicated regions", "SSO & audit logs", "24/7 support"], False),
        ],
        "faq": [
            ("How is this different from a traditional cloud?", "You think in deploys, not servers. Capacity, scaling and security are handled — you read a bill, not a dashboard of chores."),
            ("What are the SLAs?", "Production starts at 99.9%; enterprise tiers write higher commitments tailored to your footprint."),
            ("Can I run sensitive workloads?", "Yes — dedicated regions, private networking and audit trails are part of the enterprise tier."),
            ("How do costs stay sane?", "Scale-to-zero idles what isn't used, and the bill itemises by app instead of by mystery."),
        ],
        "testimonial": ("Infra went from a third headcount to half a page of the budget. The app scaled for a launch we never had to babysit.", "Hiro Tanaka", "CTO, D2C startup"),
        "compare": {
            "cols": ["Aurora Cloud", "Legacy clouds"],
            "rows": [
                ("Deploys", "One command", "Console archaeology"),
                ("Scaling", "To zero and back", "Manual groups"),
                ("Security", "DDoS & TLS default", "Upsell modules"),
                ("Billing", "Per-app clarity", "Itemised mystery"),
                ("Edge", "Global native", "Region first"),
            ],
        },
    },
    "atlas-mobility": {
        "problem": {
            "heading": "Fleets run on guesswork",
            "body": "Dispatch watches dots, finance watches fuel, and maintenance waits for the breakdown. The fleet is one system in a thousand disconnected spreadsheets.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("LayoutDashboard", "Fleet Managers", "Managers whose day is extinguishing the last breakdown instead of planning the next mile."),
            ("TrendingUp", "Finance Teams", "Teams watching fuel spend like a fixed cost nobody can shrink."),
            ("ShieldCheck", "Safety Leads", "Heads who need driver behaviour evidence, not anecdotes."),
        ],
        "fdescs": [
            "Live GPS tracking to the second, with history you can trust in a dispute.",
            "Predictive maintenance that flags the part before the breakdown price-tags it.",
            "Driver scoring that coaches the habit rather than blaming the person.",
            "Fuel analytics that find the leak in the tank or the route.",
        ],
        "pricing": [
            ("GPS", "From 9", "USD/vehicle/mo", "Tracking, done properly.", ["Live tracking & history", "Geofence alerts", "Standard support"], False),
            ("Fleet", "From 24", "USD/vehicle/mo", "The full intelligence layer.", ["Everything in GPS", "Predictive maintenance", "Driver scoring", "Fuel analytics"], True),
            ("Enterprise", "Custom", "", "Flights of vehicles, one command.", ["Everything in Fleet", "API & integrations", "Dedicated CSM", "Custom SLAs"], False),
        ],
        "faq": [
            ("What hardware do we need?", "A plug-in unit per vehicle, provisioned in minutes. Native apps cover phones-and-tablets fleets."),
            ("How accurate is location?", "Live positioning pings to the second with a full historical trail retained for disputes and audits."),
            ("Does scoring blame drivers?", "No — the coaching model shows the pattern and the fix. Incidents are for safety, not punishment."),
            ("Can you integrate fuel cards?", "Yes — fuel and card feeds import into the analytics layer automatically."),
        ],
        "testimonial": ("Eighteen percent of fuel spend and a third of claims disappeared in two quarters. The breakdown calls stopped scheduling my Mondays.", "Frank Ochieng", "Operations director, logistics firm"),
        "compare": {
            "cols": ["Atlas Mobility", "Telematics spreadsheets"],
            "rows": [
                ("Tracking", "Live, second-level", "Periodic dumps"),
                ("Maintenance", "Predictive", "After the failure"),
                ("Drivers", "Coached on evidence", "Blamed on rumour"),
                ("Fuel", "Analytics find leaks", "Fixed-cost shrug"),
                ("Integration", "Cards & APIs", "Manual entry"),
            ],
        },
    },
    "roark-analytics": {
        "problem": {
            "heading": "Dashboards are built to be admired, not asked",
            "body": "Every team has a BI tool that answers the five charts it was built for and nothing else. The moment a new question arrives you are back in SQL-email-and-wait.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("LayoutDashboard", "Data Analysts", "Analysts who live in SQL and deserve a workspace, not a ticket system."),
            ("TrendingUp", "Product Leads", "Leads who need the answer to today's question, not next week's chart."),
            ("ShieldCheck", "Data Governors", "Platform owners who need sharing that is safe by default."),
        ],
        "fdescs": [
            "A SQL workspace where the answer to a new question is minutes away.",
            "Dashboards that assemble themselves from the models you trust.",
            "Governed sharing — view rights, fresh data, zero leak risk.",
            "Alerting that watches the metric and pages the owner, not the whole channel.",
        ],
        "pricing": [
            ("Analyst", "0", "USD", "For the solo analyst.", ["SQL workspace", "Personal dashboards", "Community support"], False),
            ("Pro", "35", "USD/mo", "For teams who ask a lot.", ["Everything in Analyst", "Shared dashboards", "Governed row-level access", "Alerting"], True),
            ("Enterprise", "From 800", "USD/mo", "For platforms that own the data.", ["Everything in Pro", "SSO & audit", "SLA + dedicated support", "Data residency"], False),
        ],
        "faq": [
            ("What makes it different from a BI tool?", "You ask it questions. A dashboard is a byproduct, not the point — new questions live in the workspace, not a ticket queue."),
            ("Is a SQL skill needed?", "Analysts use SQL directly; non-analysts get governed views and dashboards."),
            ("How is sharing kept safe?", "Row-level governance travels with the data. Viewers see exactly the rows they are entitled to."),
            ("Do you store our data?", "We connect to your warehouse in place — the data stays where it lives."),
        ],
        "testimonial": ("The question came up at 10am; the answer was a query away by 10:04. Our dashboards now chase the work, not the other way around.", "Anna Kowalski", "Head of analytics, B2B SaaS"),
        "compare": {
            "cols": ["Roark Analytics", "Classic BI suites"],
            "rows": [
                ("Questions", "SQL-ready now", "Re-train the tool"),
                ("Dashboards", "Assemble themselves", "Hand-built, brittle"),
                ("Governance", "Row-level, safe share", "Folder chaos"),
                ("Alerting", "Pages the owner", "Pings the channel"),
                ("Integrations", "Warehouse-native", "ETL ceremony"),
            ],
        },
    },
    "capstone-advisors": {
        "problem": {
            "heading": "Consulting sells hours, not outcomes",
            "body": "Deliverables arrive in slideware, and the partner leaves the room when the deck is done. Growth-stage companies have been trained to pay for advice that never commits.",
            "icon": "Briefcase",
        },
        "personas": [
            ("Briefcase", "CEOs", "Founders who want strategy that survives contact with the board."),
            ("TrendingUp", "CFOs", "Finance leads who need operating models that actually bend the cost line."),
            ("Rocket", "Fundraisers", "Teams preparing a round who need the story crisp and the numbers honest."),
        ],
        "fdescs": [
            "One partner in the room from strategy to execution — the same face across the engagement.",
            "Operating models built to change the cost base, not just describe it.",
            "Fundraising support that sharpens the deck and the model you present.",
            "Playbooks and reusable lanes — you keep the method, not just the memo.",
        ],
        "pricing": [
            ("Advisory", "From 15k", "USD", "A defined engagement, one practice.", ["Named partner", "Defined scope", "Monthly report"], False),
            ("Growth", "From 45k", "USD/quarter", "The joined-up strategy-operations-and-capital loop.", ["Everything in Advisory", "Cross-practice team", "Operating model work", "Fundraise readiness"], True),
            ("Fractional CXO", "Custom", "", "A senior operator in the room weekly.", ["Everything in Growth", "Fractional exec time", "Board presence", "Ad hoc war-rooms"], False),
        ],
        "faq": [
            ("Who do we actually work with?", "One named senior partner, plus the specific practices your engagement needs. No rotating cast."),
            ("Is it playbooks or slideware?", "Playbooks. You walk away with the method implemented in your business, not a deck for the drawer."),
            ("Do you help with raises?", "Yes — we prepare founders for the round: narrative, model, diligence, and the room."),
            ("What is fractional CXO?", "A senior operator embedded weekly — typically a CFO or COO who attends your leadership cadence."),
        ],
        "testimonial": ("The partner who sold the engagement was the partner in every room. We kept the playbooks, raised the round and cut the cost income in one quarter.", "Lena Marchetti", "CEO, growth-stage fintech"),
        "compare": {
            "cols": ["Capstone Advisors", "Big-box consultancies"],
            "rows": [
                ("Ownership", "One partner throughout", "Partner in, staff out"),
                ("Method", "Playbooks you keep", "Slideware you shelf"),
                ("Outcomes", "Model + execution", "Advice + invoice"),
                ("Pricing", "Flat, predictable", "Hourly escalation"),
                ("Fit", "Growth-stage native", "Enterprise default"),
            ],
        },
    },
    "sheetstack": {
        "problem": {
            "heading": "Team docs die of a thousand edits",
            "body": "One shared doc, forty comments, no version anyone trusts. The document is where your team actually works, and it is running on tools built for essays.",
            "icon": "Layers",
        },
        "personas": [
            ("Layers", "Product Teams", "Teams whose documentation is the product's memory — and its amnesia."),
            ("Briefcase", "Operations", "Process leads who publish runbooks nobody dares touch."),
            ("Rocket", "Engineering", "Teams who already version code and refuse to version prose with a filename."),
        ],
        "fdescs": [
            "Docs that branch and merge like code — propose, review, merge, done.",
            "Peer review that keeps the author accountable without the author gatekeeping.",
            "Full history, always recoverable — every change, named and reversible.",
            "API-first so docs live where your team already works.",
        ],
        "pricing": [
            ("Starter", "0", "USD", "Three teams, the basics.", ["Branched docs", "3 team spaces", "Full history"], False),
            ("Team", "8", "USD/seat/mo", "The documentation standard.", ["Everything in Starter", "Peer review workflows", "Approvals & roles", "Priority support"], True),
            ("Enterprise", "From 20", "USD/seat/mo", "Governed documentation.", ["Everything in Team", "SSO & audit", "Admin controls", "99.9% SLA"], False),
        ],
        "faq": [
            ("Is it really like git for docs?", "Close: branches, review, merge and full history. The difference is a docs UI normal humans actually use."),
            ("What happens when someone makes a bad edit?", "It's a branch, it was reviewed, and history means it is a click to restore. Nothing is ever lost."),
            ("Do you charge per viewer?", "No — a seat is a contributor. Viewers and reviewers read at no licence cost."),
            ("Can we embed docs elsewhere?", "The API-first layer publishes live docs into your wiki, portal or support site."),
        ],
        "testimonial": ("Our runbooks stopped being the untouchable mausoleum. Now they branch, review and merge like the codebase they document.", "Victor Reyes", "Head of platform, mid-market SaaS"),
        "compare": {
            "cols": ["Sheetstack", "Shared-doc editors"],
            "rows": [
                ("Versions", "Branched & merged", "Filename archaeology"),
                ("Review", "Peer workflow", "Comment threads"),
                ("History", "Always recoverable", "Occasionally"),
                ("Access", "Contributor-priced", "Per-user everything"),
                ("Automation", "API & live embed", "Export ceremony"),
            ],
        },
    },
    "deckflow": {
        "problem": {
            "heading": "Founders are wasting their story on slides",
            "body": "A pitch is ninety percent narrative and ten percent design, but founders spend it backwards. Beautiful decks take weeks; ugly ones sink the meeting.",
            "icon": "Layers",
        },
        "personas": [
            ("Layers", "Founders", "Founders building the deck that carries the round."),
            ("Rocket", "Pre-Seed Teams", "Teams who need investor-ready in days, not designer months."),
            ("Briefcase", "Internal Teams", "Anyone who presents weekly and resents the formatting time."),
        ],
        "fdescs": [
            "Smart layouts that take an outline to a designed deck — brand-true, not template-white.",
            "Brand kits that keep every stakeholder deck on-voice.",
            "Slide-level analytics that show what actually held the room.",
            "Comments that don't derail the narrative thread.",
        ],
        "pricing": [
            ("Starter", "0", "USD", "Decks, quickly.", ["Smart layouts", "3 brand kits", "Free forever"], False),
            ("Pro", "19", "USD/mo", "The founder standard.", ["Everything in Starter", "Unlimited brand kits", "Slide analytics", "Version history"], True),
            ("Team", "From 39", "USD/mo", "Decks at company scale.", ["Everything in Pro", "Shared kits & review", "Admin & export HTML"], False),
        ],
        "faq": [
            ("Do I still need a designer?", "For an investor deck, no. Smart layouts handle the design; your story is the asset. A designer helps only if you need a fully bespoke brand build."),
            ("What are slide analytics?", "Attention heat by slide and section, so you know which ten seconds lost the room."),
            ("Can I export for offline presentations?", "Yes — PDF, PPT and live HTML export, with speaker notes built in."),
            ("Is it just for pitch decks?", "No — board updates, sales decks and internal kick-offs use the same brand-kept system."),
        ],
        "testimonial": ("We went from two weeks of designer rounds to a deck built in an afternoon — and the analytics showed the story was holding.", "Yusuf Karim", "Co-founder, pre-seed startup"),
        "compare": {
            "cols": ["Deckflow", "Legacy presentation tools"],
            "rows": [
                ("Design", "Smart layouts, brand-true", "Manual formatting"),
                ("Analytics", "Slide-level attention", "Nothing"),
                ("Speed", "Outlines to decks", "Weeks of rounds"),
                ("Consistency", "Brand kits everywhere", "Per-file drift"),
                ("Turnaround", "Same-day", "Designer queue"),
            ],
        },
    },
    # ===================== HEALTHCARE =====================
    "kinetiq-health": {
        "problem": {
            "heading": "Care is told in fragments",
            "body": "The lab result is on one portal, the appointment on another, and the treating clinician holds a third. Patients navigate the seams; errors live in them.",
            "icon": "HeartPulse",
        },
        "personas": [
            ("HeartPulse", "Clinics", "Practices that want one record across rooms, labs and follow-ups."),
            ("Clock", "Patients", "People who are tired of re-answering their own history."),
            ("ShieldCheck", "Practice Leads", "Leads who need the appointments flowing and the inbox empty of double-booking."),
        ],
        "fdescs": [
            "One chart, every provider, every lab, every visit — the fragmentation ends.",
            "Appointments in seconds: rules-based slots, reminders and no-show prevention.",
            "Secure messaging between patients, clinicians and staff — walk-in queues, answered.",
            "Lab integrations that post results the minute they are ready.",
        ],
        "pricing": [
            ("Clinic", "From 299", "USD/mo", "The record that holds a practice together.", ["Unified patient records", "Smart scheduling", "Lab integrations"], False),
            ("Group", "From 899", "USD/mo", "Multiple sites, one standard.", ["Everything in Clinic", "Multi-site governance", "Secure messaging", "Wait-time analytics"], True),
            ("Enterprise", "Custom", "", "Health systems at scale.", ["Everything in Group", "HL7 & API suite", "Dedicated clinical team", "Audit-grade logging"], False),
        ],
        "faq": [
            ("How do you handle medical records?", "One shared chart per patient, HIPAA-grade security, audit log on every access — the clinician sees history, not a pile."),
            ("Is patient data stored on-device or in the cloud?", "Managed in secure, region-resident storage with encryption at rest and in transit."),
            ("Does it integrate with lab systems?", "Yes — standard lab interfaces post results directly into the patient record."),
            ("What about wait times?", "Real-time wait management surfaces delays to staff and patients before they compound."),
        ],
        "testimonial": ("Wait times dropped seventy percent and our inbox stopped being the second clinic. The record finally travels with the patient.", "Dr. Amara Diallo", "Medical director, multi-site group"),
        "compare": {
            "cols": ["Kinetiq Health", "Legacy EHRs"],
            "rows": [
                ("Records", "One shared chart", "Portal fragments"),
                ("Scheduling", "Rules-based slots", "Manual double-books"),
                ("Wait time", "Reduced visibly", "Guessed at"),
                ("Messaging", "Secure, routed", "Fax machines"),
                ("Integrations", "Labs native", "Interface contracts"),
            ],
        },
    },
    "pulselabs": {
        "problem": {
            "heading": "Wearables collect; nobody acts",
            "body": "Millions of wearables stream health data that physicians never see and families never understand. The signal exists — the alert system around it doesn't.",
            "icon": "HeartPulse",
        },
        "personas": [
            ("HeartPulse", "Care Teams", "Clinicians who want monitoring signals, not another dashboard to babysit."),
            ("ShieldCheck", "Families", "Adult children caring from a distance who need respect, not panic."),
            ("Clock", "Post-Acute Patients", "People discharged to home who need a lifeline that actually watches."),
        ],
        "fdescs": [
            "Wearable integration that turns everyday signals into clinical-grade trends.",
            "Alerts your care team actually reads — triaged, contextual, actionable.",
            "Family notifications kept respectful and calm — informed, never alarming.",
            "Setup in ten minutes, even for the least tech-literate household.",
        ],
        "pricing": [
            ("Family", "From 12", "USD/mo", "One loved one, watched.", ["Wearable integration", "Family notifications", "Trend dashboard"], False),
            ("Care Team", "From 49", "USD/mo", "For clinicians monitoring a caseload.", ["Everything in Family", "Clinical alert queue", "Provider reporting"], True),
            ("Clinical Network", "Custom", "", "A practice running remote monitoring at scale.", ["Everything in Care Team", "EHR integration", "Custom triage rules", "Dedicated support"], False),
        ],
        "faq": [
            ("Do we need a special device?", "No — we integrate mainstream wearables. If a device passes heart and rhythm data, PulseLabs surfaces it."),
            ("Who sees the alerts?", "Your care team triages first; family gets calm, scheduled snapshots — not midnight alarms."),
            ("Is this clinical-grade?", "The data pipeline is built for clinical use — validation, context and audit on every alert."),
            ("How fast is setup?", "Ten minutes: pair the device, confirm the household, trends begin."),
        ],
        "testimonial": ("We caught a rhythm change before symptoms, and for once it wasn't the device sounding — it was the triage working. That's the difference.", "Dr. Navid Saadati", "Cardiologist, remote monitoring program"),
        "compare": {
            "cols": ["PulseLabs", "Raw wearable apps"],
            "rows": [
                ("Signal", "Clinical-grade pipeline", "Consumer charts"),
                ("Alerts", "Triaged for clinicians", "Push-notice spam"),
                ("Family", "Calm, scheduled", "Panicked rings"),
                ("Validation", "Audit + context", "None"),
                ("Setup", "Ten minutes", "App maze"),
            ],
        },
    },
    "beacon-dental": {
        "problem": {
            "heading": "Dentistry is sold with fear and admitted with estimates",
            "body": "Patients brace for pain and sign treatment plans they don't understand, priced after the fact. The trust deficit starts before the chair.",
            "icon": "HeartPulse",
        },
        "personas": [
            ("HeartPulse", "Nervous Patients", "The ones who cancelled last time because the estimate felt like a bill without a receipt."),
            ("Clock", "Busy Families", "Households that need same-day fits around school runs."),
            ("ShieldCheck", "Long-Term Patients", "Patients who want to be remembered and treated like people, not numbers."),
        ],
        "fdescs": [
            "Same-day appointments that fit the week you actually have.",
            "Pricing before treatment — a written, understandable estimate you accept first.",
            "Gentle care techniques and rooms designed for the anxious.",
            "Family plans that keep everyone on the morning routine.",
        ],
        "pricing": [
            ("Exam", "From 45", "USD", "Look, clean, and an honest plan.", ["Full exam", "Written estimate", "Digital X-ray review"], False),
            ("Family Plan", "From 12", "USD/mo", "Prevention, priced simply.", ["Everything in Exam", "Two cleanings a year", "10% on treatment", "Kids same-plan"], True),
            ("Cosmetic", "From 150", "USD", "Whitening and restoration, priced up front.", ["Full exam", "Fixed smile quote", "Follow-up included"], False),
        ],
        "faq": [
            ("Will treatment cost a surprise?", "No. You see a written estimate before the chair work begins, and everyone sticks to it."),
            ("Do you really do same-day appointments?", "Yes — cancellations and open slots are matched live, so the gap in your week becomes the appointment."),
            ("What about patients who fear the dentist?", "We run a gentle-care protocol — extra time, calmer rooms, and sedation options discussed honestly."),
            ("Do you take children?", "Yes, family plans include kids, and the team is trained for the small patients specifically."),
        ],
        "testimonial": ("Forty thousand smiles later, we still quote before we drill. The trust is the practice's entire reputation, and it took the fear out of my visits.", "Dr. Maria Solange", "Clinical lead, Beacon Dental cohort"),
        "compare": {
            "cols": ["Beacon Dental", "Standard practices"],
            "rows": [
                ("Pricing", "Written, up front", "Post-treatment surprise"),
                ("Scheduling", "Same-day matches", "Three-month queue"),
                ("Anxiety", "Gentle-care protocol", "Generic rooms"),
                ("Estimates", "Understood first", "Signature gathering"),
                ("Families", "One plan, everyone", "Per-visit billing"),
            ],
        },
    },
    # ===================== SPORTS =====================
    "aurum-fitness": {
        "problem": {
            "heading": "Gyms sell access to machines, not progress",
            "body": "Membership means a floor and a spotter if you're lucky. Nobody measures, nobody corrects, and progress is whatever the mirror says this month.",
            "icon": "Dumbbell",
        },
        "personas": [
            ("Dumbbell", "Serious Trainers", "Athletes who want a program, a coach and a tracking sheet — not a key card."),
            ("TrendingUp", "Busy Professionals", "People who need every session to count because the free time is scarce."),
            ("Award", "Comeback Lifters", "Returners rebuilding strength who need the load managed, not restored by memory."),
        ],
        "fdescs": [
            "Private coaching with a 1:1 coach ratio and programming built on your data.",
            "Strength systems that prescribe, correct and progress the movement.",
            "A recovery lab treated with the same respect as the training floor.",
            "Performance metrics that put a number on every session.",
        ],
        "pricing": [
            ("Floor", "From 89", "USD/mo", "Access and the basics.", ["24/7 floor", "Group classes", "2 guest passes"], False),
            ("Coaching", "From 249", "USD/mo", "The program, measured.", ["Everything in Floor", "1:1 coach programming", "Monthly testing", "Recovery lab access"], True),
            ("Athlete", "From 449", "USD/mo", "For the serious clock.", ["Everything in Coaching", "Daily coaching touch", "Full recovery protocol", "Nutrition desk"], False),
        ],
        "faq": [
            ("Do I get a coach on the floor?", "At the two upper tiers, yes — a 1:1 ratio with programming reviewed weekly and tested monthly."),
            ("Is there a recovery lab?", "Yes: sauna, ice, compression and massage lanes, booked like training sessions."),
            ("How is progress measured?", "Monthly performance testing with a permanent record — weights, times and body comp numbers you own."),
            ("Can I freeze or cancel?", "Yes, from the app, without a front-desk theatre."),
        ],
        "testimonial": ("Ninety-two percent of my cohort hit their goal in the year. The coaching floor is the difference between membership and a method.", "Sofia Marchetti", "Program member, second year"),
        "compare": {
            "cols": ["Aurum Fitness", "Chain gyms"],
            "rows": [
                ("Coaching", "1:1, measured", "Optional add-on"),
                ("Programming", "Data-driven", "Classes by template"),
                ("Recovery", "Full lab in membership", "Cryo upcharge"),
                ("Metrics", "Monthly testing", "Guesswork"),
                ("Ratio", "Coach per member", "Nobody watching"),
            ],
        },
    },
    "pinnacle-fitness": {
        "problem": {
            "heading": "Fitness clubs open the door and close the care",
            "body": "Membership is a door code and a lease you renew. The gym that watched you set your first PR stops watching the tenth time around.",
            "icon": "Dumbbell",
        },
        "personas": [
            ("Dumbbell", "Goal-Setters", "Members with an actual target who want the gym to track it."),
            ("Clock", "Shift Workers", "People who train at any hour and need the floor to match their life."),
            ("TrendingUp", "Returning Lifters", "Grads of the program who want to keep the gains, not start again."),
        ],
        "fdescs": [
            "Strength classes where coaches watch you win — form, load and intent.",
            "Personal programming for members who want the prescription, not a pendulum.",
            "A 24/7 floor that respects the shift you work, not the hours the manager likes.",
            "Nutrition coaching that fits the plate you actually eat.",
        ],
        "pricing": [
            ("Access", "From 39", "USD/mo", "The floor, whenever.", ["24/7 floor access", "Guest day", "Community app"], False),
            ("Membership+", "From 89", "USD/mo", "The club with the watchful eye.", ["Everything in Access", "Strength classes", "Programming consult", "Monthly check-in"], True),
            ("Performance", "From 189", "USD/mo", "Coaching at the PR level.", ["Everything in Membership+", "Personal programming", "Nutrition coaching", "Quarterly testing"], False),
        ],
        "faq": [
            ("What does 'coaches watch you win' mean?", "Class coaches correct form in the moment and log your loads — the tenth set matters as much as the first."),
            ("Is it really open 24/7?", "Yes — a live floor, staffed, for the hours your life actually needs it."),
            ("How are goals tracked?", "A simple check-in cadence with real numbers: load, volume, measurements — updated monthly."),
            ("Can beginners join?", "Absolutely — the entry tier includes starter classes and a form audit before you lift heavy."),
        ],
        "testimonial": ("Fifteen thousand members and the coaches still know my name by the bar. The floor is alive at 2am, and so are my numbers.", "Kelvin Odum", "Member, Performance tier"),
        "compare": {
            "cols": ["Pinnacle Fitness", "Standard clubs"],
            "rows": [
                ("Coaching", "In-class correction", "Nobody watches"),
                ("Hours", "24/7, staffed", "9am-9pm skeleton"),
                ("Programming", "Real prescription", "Generic regimes"),
                ("Tracking", "Numbers, monthly", "Mirror morale"),
                ("Nutrition", "Coached, practical", "Leaflet"),
            ],
        },
    },
    # ===================== PORTFOLIO =====================
    "prestige-studio": {
        "problem": {
            "heading": "Every brand looks like the last rebrand",
            "body": "Squarespace templates, shared palettes and agencies that reuse the same rubric — the market is producing recognisable work nobody remembers. Differentiation is now a discipline, not a style.",
            "icon": "Layers",
        },
        "personas": [
            ("Layers", "Founders", "Founders who know the product is good and the presentation is losing."),
            ("Award", "Marketing Leads", "Leads taking a brand into a category fight with a me-too identity."),
            ("Rocket", "Scale-ups", "Companies whose brand stopped matching the stage they reached."),
        ],
        "fdescs": [
            "Identity systems built on a truth about the business — not a trend to copy.",
            "Digital products where brand and function are the same sentence.",
            "Motion and 3D that connect the story across screens and stages.",
            "Creative strategy that decides what not to make before making anything.",
        ],
        "pricing": [
            ("Identity", "From 18k", "USD", "The brand system that ends the template look.", ["Strategy & positioning", "Full identity system", "Launch kit"], False),
            ("Product", "From 48k", "USD", "Brand and experience, designed together.", ["Everything in Identity", "Product & web design", "Motion language", "Design system handover"], True),
            ("Partnership", "From 120k", "USD/year", "A design partner in the room.", ["Everything in Product", "Embedded senior team", "Unlimited refinements", "Quarterly strategy"], False),
        ],
        "faq": [
            ("How is your work not just a style?", "We start from a truth about the business — the strategy decides the shape. The result is yours, not a template with your logo."),
            ("Do you do the development?", "Yes — identity, design and build under one roof, so nothing is lost at handover."),
            ("What is a typical timeline?", "Identity in six to ten weeks; full product engagements stretch three to five months with launch support."),
            ("What does 'strategy before pixels' mean?", "The insight comes first; pixels follow. Work shown before the deep thinking is declined."),
        ],
        "testimonial": ("We walked into a founder meeting and the room knew we had done the work. The identity survives contact with the category.", "Ibrahim Farouk", "CEO, D2C scale-up"),
        "compare": {
            "cols": ["Prestige Studio", "Template-first studios"],
            "rows": [
                ("Method", "Strategy before pixels", "Layouts first, story after"),
                ("Development", "In-house", "Handed off, diluted"),
                ("Motion", "Brand-language native", "Stock overlay effects"),
                ("Account", "Senior team throughout", "Junior juggling"),
                ("Work", "Differentiation by design", "Trend replication"),
            ],
        },
    },
    "studio-lumen": {
        "problem": {
            "heading": "Photography is sold by the lens, not the light",
            "body": "Clients are quoted resolutions, sensors and backdrops. The pictures that move people are made in the hour of light and the patience to wait for it.",
            "icon": "Sparkles",
        },
        "personas": [
            ("Sparkles", "Architectural Firms", "Studios that want their buildings photographed with the quiet light they designed for."),
            ("Award", "Editorial Teams", "Magazines commissioning warmth, not corporate crispness."),
            ("Users", "Collection Buyers", "Print buyers who are collecting the hour itself."),
        ],
        "fdescs": [
            "Architecture photographed in the natural hour the building was designed for.",
            "Editorial work that reads as story, not spec sheet.",
            "Wilderness and landscape shot with patience, not stock coverage.",
            "Archival prints, editions, and frames worth the wall.",
        ],
        "pricing": [
            ("Commission", "From 2,500", "USD", "A defined shoot, one location, the warm hour.", ["Full-day golden-hour shoot", "Edited selects", "Usage licence"], False),
            ("Editorial", "From 6,000", "USD", "A story, told in sequence.", ["Multi-day coverage", "Story selects & edits", "Broad licence"], True),
            ("Print Series", "From 900", "USD", "Edition prints from the archive.", ["Archival paper", "Numbered edition", "Certificate + frame option"], False),
        ],
        "faq": [
            ("Why 'the warmest hour'?", "The work is built around golden hour and the light it makes. That discipline is the studio's signature — not filters."),
            ("What film and process do you use?", "Primarily medium format film, scanned and printed archivally. Digital is used where the story requires it."),
            ("Can we licence work broadly?", "Yes — editorial and commission pricing includes clear, honest usage licences."),
            ("Are prints really archival?", "Fibre-based paper, archival inks, numbered editions with certificates."),
        ],
        "testimonial": ("The building finally exists in pictures the way the morning designed it. Our clients see the project as an experience now, not a file.", "Marc Dubois", "Principal architect"),
        "compare": {
            "cols": ["Studio Lumen", "Commercial studios"],
            "rows": [
                ("Moment", "Golden hour, waited for", "Booked window, any light"),
                ("Process", "Medium format film", "Batch digital"),
                ("Story", "Sequence and warmth", "One-off crisp shots"),
                ("Prints", "Archival editions", "Print-on-demand"),
                ("Patience", "The work's core", "The invoice's enemy"),
            ],
        },
    },
    "orbit-studios": {
        "problem": {
            "heading": "Startups are overbranded and under-built",
            "body": "Investors see forty slides and a discount-brand smoke test. The accents of a moat — identity, product, motion — arrive late or not at all.",
            "icon": "Rocket",
        },
        "personas": [
            ("Rocket", "Early Founders", "Founders who need the identity to carry the demo."),
            ("Layers", "Product Teams", "Teams shipping a product that deserves a brand at its level."),
            ("Award", "Growth Leads", "Leads who need creative that actually moves the funnel."),
        ],
        "fdescs": [
            "Identity and design assembled before the fundraise, not after the demo.",
            "Product design where the interface is the message.",
            "Development in the same studio — the brand ships, not just the mockup.",
            "Motion that makes the difference visible in fifteen seconds.",
        ],
        "pricing": [
            ("Launch Pack", "From 12k", "USD", "The startup standard: identity for the demo.", ["Logo + identity system", "Launch site", "One motion intro"], False),
            ("Product Studio", "From 35k", "USD", "Brand + product, built together.", ["Everything in Launch Pack", "Product design & build", "Design system", "Quarterly iteration"], True),
            ("Growth Partner", "From 90k", "USD/year", "Creative that moves the funnel.", ["Everything in Product Studio", "Dedicated team", "Marketing creative", "Monthly experiments"], False),
        ],
        "faq": [
            ("Why identity before the product?", "Because the demo is the pitch and the brand is the moat's visible edge. We build both, together."),
            ("Do you really build?", "Yes — the studio ships production web products, not mockups."),
            ("What's the fastest turnaround?", "Launch Pack from brief to deploy in three to four weeks."),
            ("Are you only for tech startups?", "No — the same discipline serves any founder who is selling forward on conviction."),
        ],
        "testimonial": ("The demo was the brand, and the brand was the demo. Our round went out with a product that looked like it had already shipped.", "Noor Adeel", "Founder, incubated team"),
        "compare": {
            "cols": ["Orbit Studios", "Design marketplaces"],
            "rows": [
                ("Scope", "Brand + build", "Logo dropdown"),
                ("Development", "In-studio", "Hand off"),
                ("Speed", "Demo-ready in weeks", "Revision roulette"),
                ("Motion", "Native, purposeful", "Stock overlays"),
                ("Ownership", "One accountable team", "Freelancer-by-freelancer"),
            ],
        },
    },
    "noir-frames": {
        "problem": {
            "heading": "Portraits are taken, rarely made",
            "body": "Studio photography has become retouching and backdrops. The frames that hold feeling are made in the consultation, the quiet and the light — few practices still build them.",
            "icon": "Sparkles",
        },
        "personas": [
            ("Sparkles", "Portrait Clients", "People commissioning a portrait of the person, not the occasion."),
            ("Award", "Editorial Teams", "Publications wanting frames with mood and intention."),
            ("Users", "Print Collectors", "Buyers who want the photograph as an object."),
        ],
        "fdescs": [
            "Portraiture built on a consultation before the camera arrives.",
            "Editorial work with cinematic light and honest expressions.",
            "Print editions on archival papers, numbered and framed.",
            "Commission work that starts with listening, not shooting.",
        ],
        "pricing": [
            ("Portrait", "From 1,200", "USD", "A sitting that holds you.", ["Pre-shoot consultation", "Two-hour sitting", "Verified selects & retouch"], False),
            ("Editorial", "From 3,500", "USD", "A story in frames.", ["Concept & mood board", "Day coverage", "Broad licence"], True),
            ("Edition Prints", "From 650", "USD", "The photograph as object.", ["Archival paper", "Numbered & signed", "Frame option"], False),
        ],
        "faq": [
            ("Why a consultation first?", "The best portraits come from who you are, not the pose book. We design the light around the person."),
            ("Is retouching extensive?", "The work is made in the taking — retouch improves, it does not replace."),
            ("Can families commission?", "Yes — family sittings run two hours with every member consulted."),
            ("What do editions include?", "Archival prints, numbered and signed, with a certificate and optional hand-finished frame."),
        ],
        "testimonial": ("The portrait turned out to be the person I am now, not the version I usually pose as. Forty-five editions and it is the most honest piece on my wall.", "Lena Hargreaves", "Commission client"),
        "compare": {
            "cols": ["Noir Frames", "High-street studios"],
            "rows": [
                ("Method", "Consultation-led light", "Backdrop + retouch"),
                ("Expression", "Honest, cinematic", "Pose-by-numbers"),
                ("Edition", "Archival prints", "Print-on-demand"),
                ("Story", "About the person", "About the booking"),
                ("Craft", "Film-influenced", "Phone-lookalike"),
            ],
        },
    },
    # ===================== ENTERTAINMENT =====================
    "nuage-events": {
        "problem": {
            "heading": "Events are decorated, not choreographed",
            "body": "Venues are booked, banners hung, and the evening improvises. The events that shift a brand have a score — light, sound, reveal and timing — few producers actually write one.",
            "icon": "Megaphone",
        },
        "personas": [
            ("Megaphone", "Brand Teams", "Marketing leads who need the launch to be the story, not the backdrop."),
            ("Users", "Festival Organisers", "Producers assembling a day where every stage earns its crowd."),
            ("Award", "Corporate Planners", "Teams whose manager events carry the company's public face."),
        ],
        "fdescs": [
            "Full production from concept to strike, with a written run of show.",
            "Stage and lighting designed to carry the narrative, not decorate it.",
            "Artist booking and programming that suits the room's real size.",
            "Immersive design that turns attendance into memory.",
        ],
        "pricing": [
            ("Signature", "From 25k", "USD", "A single corner of the programme, perfectly produced.", ["Concept & run of show", "Venue & supplier lead", "Day-of production"], False),
            ("Experience", "From 95k", "USD", "The launch as a story.", ["Everything in Signature", "Stage & lighting design", "Immersive build", "Multicam & social cut"], True),
            ("Festival", "From 250k", "USD", "Multi-day, multi-stage.", ["Everything in Experience", "Multi-stage programming", "Artist contracting", "Site-wide production"], False),
        ],
        "faq": [
            ("What is a run of show?", "A second-by-second plan for the event — light, sound, talent, reveal. Nothing happens unmapped."),
            ("Do you book artists?", "Yes — we contract and program acts sized to the room and the story."),
            ("What does immersive design cost?", "It scales with ambition; most immersive elements live inside the Experience tier."),
            ("How do you measure success?", "Through put: attention metrics, social cut performance, and the sponsor's post-event report."),
        ],
        "testimonial": ("Four hundred people and every one of them felt the reveal. The launch earned more recall than a quarter of paid media.", "Camille Rousseau", "Brand director"),
        "compare": {
            "cols": ["Nuage Events", "Decor-heavy producers"],
            "rows": [
                ("Planning", "Choreographed to the second", "Improv with a checklist"),
                ("Design", "Light & narrative", "Banners & drapes"),
                ("Talent", "Programmed to the story", "Booked, unprogrammed"),
                ("Measurement", "Attention & recall", "Attendance only"),
                ("Turnaround", "48-hour emergencies covered", "Weeks minimum"),
            ],
        },
    },
    "fleetwood-events": {
        "problem": {
            "heading": "Corporate events meet hospitality, not broadcast",
            "body": "Conferences are booked like banquets and produced like church slides. The audiences that matter need the precision of television and the warmth of a welcome — rarely one team does both.",
            "icon": "Megaphone",
        },
        "personas": [
            ("Megaphone", "Marketing Leaders", "Heads running launches that need better than a room and a screen."),
            ("Briefcase", "Executive Assistants", "EAs whose principal's event carries the quarter's message."),
            ("Users", "Conference Teams", "Producers assembling hybrid programmes that reach two audiences at once."),
        ],
        "fdescs": [
            "Corporate conferences produced with broadcast discipline.",
            "Product launches where the story lands on stage, not just in the deck.",
            "Hybrid broadcast that makes the remote room part of the event.",
            "Venue sourcing and logistics that keep a thousand variables quiet.",
        ],
        "pricing": [
            ("Meeting", "From 9k", "USD", "A strong room, precisely run.", ["Venue & AV brief", "Run of show", "Day-of production"], False),
            ("Conference", "From 49k", "USD", "Events that carry a corporate message.", ["Everything in Meeting", "Stage design & light", "Hybrid broadcast", "Guest handling"], True),
            ("Launch", "From 120k", "USD", "The product event as news.", ["Everything in Conference", "Immersive build", "Media & influencer flows", "Post-launch social cut"], False),
        ],
        "faq": [
            ("What does 'broadcast discipline' mean?", "Run of show to the second, dual audio paths, timed reveals and a producer who speaks in cues, not hopes."),
            ("Do you handle hybrid audiences?", "Yes — the remote room is produced like a main stage, not a webcam afterthought."),
            ("How do you source venues?", "A vetted shortlist matched to capacity, message and budget — no mystery markups."),
            ("Can you support a last-minute event?", "Yes — our 48-hour service has moved full conferences when dates collapsed."),
        ],
        "testimonial": ("The hybrid audience was better served than the room. Nine hundred in person, four thousand remote, one show of show.", "Priya Suresh", "Events director, B2B software"),
        "compare": {
            "cols": ["Fleetwood Events", "Banquet-style producers"],
            "rows": [
                ("Discipline", "Broadcast run of show", "Flexible improv"),
                ("Hybrid", "Produced main stage", "Webcam afterthought"),
                ("Venue", "Vetted, no markup", "Commission-driven"),
                ("Reveals", "Timed, cued", "Wind and hope"),
                ("Turnaround", "48-hour proven", "Weeks"),
            ],
        },
    },
    "heritage-trails": {
        "problem": {
            "heading": "History tours are recited, not walked",
            "body": "Free-walking tours trade in dates and crowd control. The old city is a living archive — but it is presented like a museum captioned by a clipboard.",
            "icon": "Plane",
        },
        "personas": [
            ("Plane", "Curious Travellers", "Visitors who want the district's real stories and its side-street tastes."),
            ("Users", "Local Families", "Residents rediscovering their own city through guide-led walks."),
            ("Award", "School Groups", "Educators who want history as story, sized for children and their attention spans."),
        ],
        "fdescs": [
            "Small walking tours capped at twelve — the group stays a conversation.",
            "Local historians who tell the district from the inside.",
            "Taste stops that turn a tour into an evening.",
            "Private groups and bespoke routes for birthdates and briefs.",
        ],
        "pricing": [
            ("Public Tour", "From 25", "USD", "Join a small scheduled walk.", ["Two-hour guided walk", "Taste stop included", "Groups under twelve"], False),
            ("Private", "From 240", "USD", "Your party, your pace.", ["Everything in Public", "Your own route & pace", "Private historian"], True),
            ("School", "From 12", "USD/student", "History, sized for classrooms.", ["Group walk, age-tuned", "Two teacher leads free", "Route risk-assessment"], False),
        ],
        "faq": [
            ("How small is small?", "Twelve guests maximum, and most public walks run under ten — a guide can actually talk to you."),
            ("Are the guides really local?", "Yes — historians and residents of the district, not imported narrators."),
            ("What are taste stops?", "A dedicated stop at a place locals eat, folded into the walk, not a detour to a souvenir stand."),
            ("Can we book a private route?", "Yes — walks are drafted around your interests, pace, and even the weather."),
        ],
        "testimonial": ("Forty thousand guests and I still get to tell the version that isn't in the guidebook. The taste stop is how I know they'll stay.", "Rania Halabi", "Lead guide, old city route"),
        "compare": {
            "cols": ["Heritage Trails", "Free-walking tours"],
            "rows": [
                ("Size", "Under twelve", "Thirty-plus"),
                ("Narration", "Local historians", "Recited scripts"),
                ("Taste", "Built-in stops", "Skip the sweets"),
                ("Private", "Bespoke routes", "Fixed circuits"),
                ("Replay", "Families return", "One-and-done"),
            ],
        },
    },
    # ===================== ECOMMERCE =====================
    "luxemart": {
        "problem": {
            "heading": "Online luxury is a trust lottery",
            "body": "The web is full of luxury-look clones and listing fatigue. Buyers are one wrong purchase away from never trusting a marketplace again — and resellers pay for that doubt.",
            "icon": "ShoppingBag",
        },
        "personas": [
            ("ShoppingBag", "Collectors", "Watchers and handbag curators who want authenticity that is provable."),
            ("ShieldCheck", "First-Time Buyers", "New buyers testing a risky category where a single fake ends the experiment."),
            ("Truck", "International Shoppers", "Buyers crossing borders who need insurance, duties and white-glove logistics handled."),
        ],
        "fdescs": [
            "Every piece authenticated by domain experts before it is listed.",
            "Concierge checkout with provenance records attached to the purchase.",
            "Insured, tracked global shipping with duties sorted before the cart.",
            "A collector vault for storing, valuing and listing your own pieces.",
        ],
        "pricing": [
            ("Buyer", "0", "USD", "Shop the authenticated collection.", ["Authenticated catalog", "Secure checkout", "Global shipping"], False),
            ("Seller", "From 29", "USD/mo or 5%", "List your pieces with provenance.", ["Everything in Buyer", "Free authentication", "Vault storage", "Priority promotion"], True),
            ("Vault", "From 99", "USD/mo", "Managed collections at scale.", ["Everything in Seller", "Insurance & valuation", "Linked global resale", "Dedicated concierge"], False),
        ],
        "faq": [
            ("How is authentication done?", "Every item passes expert review — materials, markings, serials and provenance — before it gets a listing."),
            ("What if an item is disputed?", "Buyers have a 14-day authenticity guarantee with a full refund path and no return ritual."),
            ("Do you handle duties?", "Duties and taxes are calculated at checkout, so the price you see is the price you pay."),
            ("Can I store my collection?", "Yes — the Vault holds, insures and values pieces, and lists them when you choose."),
        ],
        "testimonial": ("The authentication dossier travelled with the bag. I bought across borders with the confidence I reserve for the boutique.", "Clara Osinski", "Collector, third acquisition"),
        "compare": {
            "cols": ["Luxemart", "Open marketplaces"],
            "rows": [
                ("Authentication", "Expert, pre-listing", "Self-certified"),
                ("Guarantee", "14-day, full refund", "Dispute queue"),
                ("Duties", "At checkout, fixed", "Surprise customs"),
                ("Shipping", "Insured, white-glove", "Standard parcel"),
                ("Vault", "Store & resell", "Nowhere to hold"),
            ],
        },
    },
    "bristle-co": {
        "problem": {
            "heading": "Grooming is sold like a chemistry set",
            "body": "The aisle is full of forty-ingredient concoctions and claims tailored to the beard. Men's grooming either over-engineers the routine or under-delivers the ritual.",
            "icon": "ShoppingBag",
        },
        "personas": [
            ("ShoppingBag", "Routine-Builders", "Men who want a short, honest routine with products that work."),
            ("ShieldCheck", "Ingredient Readers", "Shoppers who read the label and refuse the filler."),
            ("HeartHandshake", "Loyal Customers", "Customers who found their products and now need refills, not reinventions."),
        ],
        "fdescs": [
            "Small-batch grooming made in three-hundred-litre runs — control, not chemistry.",
            "Vegan, cruelty-free and naturally sourced from cold-pressed ingredients.",
            "Reusable packaging and mail-order refills that skip the landfill.",
            "Subscription kits that keep the routine stocked without thought.",
        ],
        "pricing": [
            ("Essential", "From 18", "USD", "Soap, oil, and a simpler morning.", ["Single hero products", "Naturally sourced bases", "Reusable packaging"], False),
            ("Ritual", "From 42", "USD", "The full routine, boxed.", ["Everything in Essential", "Complete routine kit", "Refill cycle included"], True),
            ("Club", "From 29", "USD/quarter", "Stocked, automatically.", ["Everything in Ritual", "Quarterly refill box", "Early access drops"], False),
        ],
        "faq": [
            ("Are the products really vegan?", "Yes — every formula is vegan and cruelty-free, with natural cold-pressed bases and no hidden perfumes."),
            ("Is packaging reusable?", "Jars and tins are refillable; refills ship in recyclable mailers without the double packaging."),
            ("How fast is the subscription?", "Quarterly, adjustable, and skip-a-box easily — no email archaeology to cancel."),
            ("What is a three-hundred-litre batch?", "We make in small runs to control quality and freshness — not the industry's tankers."),
        ],
        "testimonial": ("Thirty thousand customers and the batch number is still printed on every tin. My shelf is simpler and my morning is better.", "Andre Castel", "Routine-builder, year three"),
        "compare": {
            "cols": ["Bristle & Co", "Mainstream grooming"],
            "rows": [
                ("Batch", "Small, numbered", "Tankered"),
                ("Formulas", "Vegan, natural", "Filler chemistry"),
                ("Packaging", "Reusable, refillable", "Single-use plastic"),
                ("Routine", "Short, honest", "Aisle of extra steps"),
                ("Subscriptions", "Skip anytime", "Cancellation gauntlet"),
            ],
        },
    },
    "northpeak-outfitters": {
        "problem": {
            "heading": "Outdoor gear is made for the catalogue, not the trail",
            "body": "Marketing specs outpace field truth: waterproof claims on wet days, warmth ratings from a lab, lifetime warranties that require a signed confession. The mountain doesn't care about the claim.",
            "icon": "Truck",
        },
        "personas": [
            ("Truck", "Expedition Teams", "Guides and expeditions whose gear failure is a rescue, not a refund."),
            ("ShieldCheck", "Reliability Buyers", "Buyers who have been 'field-tested' before and no longer trust the phrase."),
            ("HeartHandshake", "Outdoor Regulars", "Weekend classes who want kit that carries a decade, not a season."),
        ],
        "fdescs": [
            "Kit designed for expedition first and treated like it on the spec sheet.",
            "Guides from partner patrols test every line before it ships.",
            "A lifetime warranty that repairs rather than argues.",
            "A repair program that keeps jackets on backs and gear in service.",
        ],
        "pricing": [
            ("Essential", "From 49", "USD", "The honest basics.", ["Guide-tested core", "Lifetime repair program", "30-day trail return"], False),
            ("Expedition", "From 179", "USD", "The gear the mountain gets tested.", ["Everything in Essential", "Expedition-grade build", "Free repair shipping"], True),
            ("Fleet", "Custom", "", "For guides and outfitters.", ["Everything in Expedition", "Fleet pricing", "Preferred repair queue"], False),
        ],
        "faq": [
            ("Who actually tests the gear?", "Partner guides from mountain and trail operations — they file field reports that go straight back to design."),
            ("Is the warranty really lifetime?", "Yes — the cover follows the product, not the owner. If we can't repair it, we replace it."),
            ("Does 'weatherproof' survive weather?", "Claims are matched to tested conditions; a three-season shell is labelled a three-season shell."),
            ("What does the repair program cover?", "Zips, seams, delamination and holes — most jackets return earned, not retired."),
        ],
        "testimonial": ("Two hundred and fifty products, all guide-tested, and the one repair I filed came back better than new in nine days.", "Ingrid Halvorsen", "Expedition lead, alpine season"),
        "compare": {
            "cols": ["Northpeak Outfitters", "Catalogue-first brands"],
            "rows": [
                ("Testing", "Guide field reports", "Lab best-case"),
                ("Claims", "Condition-matched", "Marketing maxima"),
                ("Warranty", "Lifetime, repairs", "Fine-print maze"),
                ("Repair", "Program, fast", "Replace-and-bill"),
                ("Fleet", "Preferred queue", "No program"),
            ],
        },
    },
    "blume-botanics": {
        "problem": {
            "heading": "Clean beauty means fragrant nothing",
            "body": "Consumers have learned that 'clean' can mean 'inactive'. The new demand is clinical and botanical — and honest about which of the two does what.",
            "icon": "Sparkles",
        },
        "personas": [
            ("Sparkles", "Results-Driven Skincare", "Buyers who want actives to actually act, not to whisper."),
            ("ShieldCheck", "Clean Standards", "Shoppers who read the ingredient list and the study both."),
            ("HeartHandshake", "Refill Customers", "Loyal users who will buy the hero product again if the refill is simple."),
        ],
        "fdescs": [
            "Clinical formulas where the active ingredient carries the claim.",
            "Greenhouse-grown botanicals with provenance, not a farm logo.",
            "Dermatologist-led development with results published openly.",
            "Refills that cost less and ship in the glass back to you.",
        ],
        "pricing": [
            ("Hero", "From 26", "USD", "The one product bringing the result.", ["Clinical actives", "Published studies", "30-day reset return"], False),
            ("Ritual", "From 54", "USD", "The core routine, matched.", ["Everything in Hero", "Matched routine set", "Free reset return"], True),
            ("Refill Club", "From 36", "USD/quarter", "The hero, restocked.", ["Everything in Ritual", "Quarterly refill", "Price-lock"], False),
        ],
        "faq": [
            ("Which one is doing the work?", "We tell you plainly: the active percentage, and what the botanicals support. No monologue about fragrant nothing."),
            ("Are the botanicals greenhouse-grown?", "Yes — controlled-environment origin with traceability down to the batch greenhouse."),
            ("Are results really published?", "Studies are posted on every hero product page, methodology included."),
            ("What is the reset return?", "Try the routine for thirty days; if the skin doesn't agree, return the empties for a real refund."),
        ],
        "testimonial": ("Nine thousand five-star reviews and the ingredient in the lead still does the talking. My hyperpigmentation finally met a percentage.", "Mei Ling Chan", "Skincare researcher, routine user"),
        "compare": {
            "cols": ["Blume Botanics", "Clean-but-inactive brands"],
            "rows": [
                ("Actives", "Clinical percentages", "Luxury dilutions"),
                ("Botanicals", "Greenhouse provenance", "Marketing story"),
                ("Data", "Published studies", "Anectodes"),
                ("Refills", "Cheaper, re-used glass", "Single-use ritual"),
                ("Claims", "Named honestly", "Ambiguous glow"),
            ],
        },
    },
    "halo-retail": {
        "problem": {
            "heading": "General stores became a delivery gamble",
            "body": "Essentials arrive late, replacements never fit, and service has been outsourced to a chat bubble. The general store promise — good things, well — is still being broken by the marketplace giants.",
            "icon": "ShoppingBag",
        },
        "personas": [
            ("ShoppingBag", "Busy Households", "Families ordering the weekly basics who need the box to arrive as promised."),
            ("Truck", "Gift-Buyers", "Shoppers who need the curated ease of a card-and-candle bundle at speed."),
            ("HeartHandshake", "Local Loyalists", "Customers who will stay if the service remembers their order history."),
        ],
        "fdescs": [
            "Next-day delivery that keeps its promise — the window is the window.",
            "Curated lines that make the ordinary section worth upgrading.",
            "Returns without the interrogation or the restocking fee.",
            "Loyalty points that behave like actual currency.",
        ],
        "pricing": [
            ("Standard", "0", "USD", "Shop well, delivered.", ["50k+ products", "Next-day options", "Free returns"], False),
            ("Halo+", "9", "USD/mo", "The upgraded general store.", ["Everything in Standard", "Unlimited next-day", "Priority slots", "Double points month"], True),
            ("Business", "From 29", "USD/mo", "Stock for offices and teams.", ["Everything in Halo+", "Shared accounts", "Bulk pricing", "Dedicated help"], False),
        ],
        "faq": [
            ("How reliable is next-day?", "We promise the window, not a long-range estimate — 99% on-time across the network."),
            ("Are returns really free?", "Yes. Print the label, drop the box, refund is issued when scanned. No restocking theater."),
            ("Is Halo+ worth it?", "For households ordering weekly, the unlimited next-day and priority slots pay for the membership within the first months."),
            ("Do you deliver everywhere?", "Core regions are next-day; wider coverage is standard multi-day with tracking."),
        ],
        "testimonial": ("Fifty thousand products and the basics still arrive in the promised window. My weekly box hasn't missed in a year.", "Tess Okonkwo", "Household buyer, Halo+ member"),
        "compare": {
            "cols": ["Halo Retail", "Marketplace giants"],
            "rows": [
                ("Delivery", "Promised window", "Long-range estimate"),
                ("Returns", "Free, no drama", "Restocking fees"),
                ("Service", "Human help", "Chat bubble relief"),
                ("Curated", "Upgraded essentials", "Infinite clutter"),
                ("Loyalty", "Real currency", "Points intact"),
            ],
        },
    },
    # ===================== EDUCATION =====================
    "lumina-academy": {
        "problem": {
            "heading": "Courses launch, learners don't finish",
            "body": "The market is saturated with pre-recorded shelfware. Completion rates hover near single digits because learning was turned into a video library with a quiz appended.",
            "icon": "BookOpen",
        },
        "personas": [
            ("BookOpen", "Career Switchers", "Professionals retraining who need the cohort to stay honest."),
            ("Users", "Working Parents", "Learners whose window is small and judged, needing schedules, not streams."),
            ("Award", "Team Leads", "Managers buying learning that actually lands back at work."),
        ],
        "fdescs": [
            "Cohort-based learning where deadlines and peers hold the pace.",
            "Live sessions with the instructor, not a library of talking heads.",
            "Project portfolios that are the proof — you graduate with work, not notes.",
            "Certificates tied to a portfolio employers can actually inspect.",
        ],
        "pricing": [
            ("Course", "From 199", "USD", "One cohort, one craft.", ["Learner cohort", "Live sessions", "Project portfolio"], False),
            ("Track", "From 549", "USD", "A full career lane.", ["Everything in Course", "Three-cohort sequence", "Mentor reviews", "Portfolio polished"], True),
            ("Team", "From 25", "USD/seat", "Learning that returns to the org.", ["Everything in Track", "Admin dashboard", "Progress reports", "Custom milestones"], False),
        ],
        "faq": [
            ("Why cohorts?", "Because we know the enemy of learning is isolation. A fixed cohort, live deadlines and peers raise completion compulsion where shelfware dies."),
            ("What if I miss a live session?", "Recordings exist, but the session's assignments and peer circle carry the pace regardless."),
            ("Is the certificate valuable?", "It is linked to a verifiable portfolio of work — employers check the folder, not the PDF."),
            ("Do teams get reporting?", "Yes — an admin dashboard with progress, completion and skill signals per learner."),
        ],
        "testimonial": ("Seventy-eight percent of my cohort finished — compared to the twelve percent I gave up on with self-paced tapes. I work with my hands again.", "Fatima Noor", "Career switcher, completed track"),
        "compare": {
            "cols": ["Lumina Academy", "Self-paced platforms"],
            "rows": [
                ("Format", "Cohorts + live", "Video library"),
                ("Completion", "78% cohorts", "Single digits"),
                ("Proof", "Project portfolio", "Quiz certificates"),
                ("Accountability", "Peers & deadlines", "Your willpower"),
                ("Employer view", "Verifiable work", "Uncheckable PDF"),
            ],
        },
    },
    # ===================== v7.12 full-set additions =====================
    "vantage-3d-estates": {
        "problem": {
            "heading": "Off-plan homes are sold on faith, not sight",
            "body": "Buyers are asked to commit tens of thousands to an artist's impression. When every competing development is a render, the one that makes buyers feel the space wins the sale.",
            "icon": "Search",
        },
        "personas": [
            ("Building2", "Developers", "Pre-construction teams who need to move units before completion, sight unseen."),
            ("TrendingUp", "Investors", "Off-plan investors comparing yields across markets who buy before visiting."),
            ("Globe", "Remote Families", "Buyers relocating who need to trust a home from another city or country."),
        ],
        "fdescs": [
            "Photoreal 3D walkthroughs a buyer can explore in a browser on any device.",
            "Live guided tours with a broker inside the 3D model, answering questions in real time.",
            "A pre-construction portfolio organised by timeline, yield and handover date.",
            "Digital reservation and closing so a remote buyer never waits on a courier.",
        ],
        "pricing": [
            ("Starter", "From 1,900", "USD", "One project, one tour.", ["Single 3D walkthrough", "Broker visit link", "Inquiry funnel"], False),
            ("Studio", "From 5,500", "USD", "The standard for developments that must sell off-plan.", ["Everything in Starter", "Full-unit 3D tours", "Live broker calendar", "Lead dashboard", "Handover-ready builds"], True),
            ("Platform", "Custom", "", "For portfolios and sales organisations.", ["Everything in Studio", "Multi-project scene graph", "White-label platform", "Sales analytics"], False),
        ],
        "faq": [
            ("Do buyers need special software?", "No — tours run in any modern browser on phone, tablet or desktop. No downloads, no apps."),
            ("How accurate is the 3D?", "Scenes are built from approved floor plans with material and lighting matched to the spec sheet."),
            ("Can agents host live tours?", "Yes. A broker can walk rooms, mark points of interest and answer questions inside the model."),
            ("Do remote buyers close digitally?", "Reservation, paperwork and previews of closing documents are handled online end to end."),
        ],
        "testimonial": ("We moved 60% of our first phase before the show flat was built. Buyers toured the model like it was a real home and reserved with confidence.", "Elena Marchetti", "Sales director, waterfront development"),
        "compare": {
            "cols": ["Vantage 3D Estates", "Brochure marketing"],
            "rows": [
                ("Buyer experience", "Explore + guided tour", "Static renders"),
                ("Remote closing", "Digital reservation", "Fly-in required"),
                ("Sales follow-up", "Every visit a lead", "No signal"),
                ("Project portfolio", "Timeline + yield dashboard", "Separate decks"),
                ("Trust", "Space you can feel", "Artist's impressions"),
            ],
        },
    },
    "deploydock": {
        "problem": {
            "heading": "Deploys go sideways the moment the room clears",
            "body": "The plan was a perfect pipeline. In practice, branches drift, checks flake and rollbacks take an incident call. Teams stop fearing code and start fearing the button.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("Zap", "Platform Engineers", "Owners of CI/CD who fight flaky checks and staging drift daily."),
            ("ShieldCheck", "Release Managers", "Sign-offs who need guardrails instead of guesswork before production."),
            ("TrendingUp", "Startup Founders", "Small teams shipping fast who cannot afford downtime on launch day."),
        ],
        "fdescs": [
            "A URL for every branch, so staging approval happens where the work actually lives.",
            "One-click rollbacks that restore the previous green deploy in seconds.",
            "Policy guardrails that block risky releases before they reach the pipeline.",
            "Deterministic checks that quarantine flaky tests instead of flaking your release.",
        ],
        "pricing": [
            ("Starter", "Free", "", "For open-source and hobby workloads.", ["100 deploys/month", "Preview URLs", "Community support"], False),
            ("Growth", "49", "USD/mo", "For teams that ship daily.", ["Everything in Starter", "Unlimited previews", "Instant rollbacks", "Policy guardrails"], True),
            ("Scale", "Custom", "", "For regulated or high-volume orgs.", ["Everything in Growth", "SSO & audit logs", "On-prem option", "SLA & support"], False),
        ],
        "faq": [
            ("Do we need to replace our existing CI?", "No. DeployDock plugs into GitHub Actions or similar and owns the deploy + preview layer."),
            ("How fast is a rollback?", "The previous green build is redeployed as one action — most rollbacks land in under a minute."),
            ("What counts as flaky-free?", "We quarantine tests that fail intermittently so the suite stays a reliable signal."),
            ("Can we keep deploys in our region?", "In Scale, deploys can run inside your cloud account or on-prem VPC entirely."),
        ],
        "testimonial": ("We cut rollback time from a half-hour war-room to a single click, and our release calendar stopped being a source of dread.", "Diego Ramos", "Head of Platform, growth-stage SaaS"),
        "compare": {
            "cols": ["DeployDock", "Roll-your-own CI"],
            "rows": [
                ("Previews", "URL per branch", "Manual staging"),
                ("Rollbacks", "One click, under 60s", "Re-run pipeline"),
                ("Guardrails", "Policy engine", "Code review only"),
                ("Flaky tests", "Auto-quarantined", "Random failures"),
                ("Cost", "Predictable plans", "Hidden infra spend"),
            ],
        },
    },
    "stacksail": {
        "problem": {
            "heading": "Spend leaks a little every day and nobody sees it",
            "body": "Procurement lives in email threads and spreadsheets. By the time finance reviews the month, the overruns have already happened — and vendors know the truth before your team does.",
            "icon": "BarChart3",
        },
        "personas": [
            ("TrendingUp", "CFOs", "Finance leaders who need a line of sight on every committed dollar."),
            ("ShieldCheck", "Procurement Managers", "Teams chasing approvals through chat and losing the audit trail."),
            ("Users", "Operations Leads", "Operators who sign off on spend but lack a single source of truth."),
        ],
        "fdescs": [
            "Approval workflows that route, escalate and never disappear into someone's inbox.",
            "Budget guardrails that warn and block before an overrun becomes an argument.",
            "A vendor portal for pricing, contracts and renewal dates in one place.",
            "An immutable audit trail that makes every review and spend moment accountable.",
        ],
        "pricing": [
            ("Starter", "0", "", "Up to 5 users.", ["Approval flows", "Basic budgets", "Email support"], False),
            ("Business", "29", "USD/user/mo", "For finance and ops teams.", ["Everything in Starter", "Budget guardrails", "Vendor portal", "Audit trail"], True),
            ("Enterprise", "Custom", "", "For multi-entity groups.", ["Everything in Business", "SSO & domains", "Custom approvers", "Dedicated CSM"], False),
        ],
        "faq": [
            ("What does unapproved spend do?", "It routes to the next approver and is escalated automatically; nothing sits idle overnight."),
            ("Can budgets block purchases?", "Yes — guardrails warn at 80% and block at 100% unless a named override approves."),
            ("Is our data ready for audit?", "Every action is timestamped with who, what and why. Export is one click."),
            ("Does it integrate with accounting?", "We sync with common ERPs so commitments land in the books without re-keying."),
        ],
        "testimonial": ("We found three duplicate vendor contracts in the first week. Overspend dropped by almost a third across two quarters.", "Anika Shah", "VP Finance, mid-market software company"),
        "compare": {
            "cols": ["Stacksail", "Spreadsheet tracking"],
            "rows": [
                ("Approvals", "Routed + escalated", "Email trail"),
                ("Budgets", "Guardrails & blocks", "Manual checks"),
                ("Vendors", "One portal", "Scattered docs"),
                ("Audit", "Immutable log", "Version chaos"),
                ("Scale", "Multi-entity ready", "Breaks at size"),
            ],
        },
    },
    "orbitboard": {
        "problem": {
            "heading": "Roadmaps are decided in the loudest meeting",
            "body": "Product writes slides, engineering grumbles, sales hears promises. The roadmap exists, but nobody owns it — and the priorities reflect whoever argued last.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("TrendingUp", "Product Leads", "Owners who need priorities to survive contact with the room."),
            ("Users", "Engineering Managers", "Teams that want input into what gets built, not just told."),
            ("Sparkles", "Customer Success", "Teams carrying the roadmap's promises to real customers."),
        ],
        "fdescs": [
            "Timeline roadmaps that turn a wall of work into a story the whole company reads.",
            "Voting and weighting so priorities are decided in the open, not the loudest meeting.",
            "Themes that bundle customer requests into shippable changelog narratives.",
            "A customer ideas portal that closes the loop from ask to shipped.",
        ],
        "pricing": [
            ("Starter", "0", "", "For small teams.", ["1 roadmap", "Task cards", "3 seats"], False),
            ("Team", "39", "USD/mo", "For product + eng together.", ["Everything in Starter", "Voting & weighting", "Changelog themes", "Unlimited seats"], True),
            ("Company", "Custom", "", "For org-wide planning.", ["Everything in Team", "Ideas portal", "OKR linking", "Admin & SSO"], False),
        ],
        "faq": [
            ("Who can vote?", "Anyone you seat — engineers, CS, even customers through the ideas portal."),
            ("Do we lose our current tooling?", "The roadmap lives here; tickets can stay where they are and sync two-way."),
            ("How are priorities weighted?", "Effort, impact and strategic tag combine into a score — transparent by design."),
            ("Can customers see it?", "Only what you publish. The ideas portal shows status without exposing the backlog."),
        ],
        "testimonial": ("Our roadmap went from a slide deck to a living document the whole company votes on. Alignment finally matches the effort.", "Marcus Lindqvist", "VP Product, B2B platform"),
        "compare": {
            "cols": ["Orbitboard", "Slide deck roadmap"],
            "rows": [
                ("Priority", "Open voting + weight", "Last loud voice"),
                ("Living", "Always current", "Version jumble"),
                ("Feedback loop", "Customer ideas portal", "Sales promises"),
                ("Visibility", "Whole company", "Boardroom only"),
                ("Shipped proof", "Changelog themes", "Release notes fight"),
            ],
        },
    },
    "forgekit": {
        "problem": {
            "heading": "Every admin tool is a small project you never finish",
            "body": "Internal tools start as a quick form and end as a backlog item. One more dashboard, one more button, one more quarter of maintenance for software only your team sees.",
            "icon": "Zap",
        },
        "personas": [
            ("Cpu", "Backend Engineers", "Builders weary of writing the same table-and-form CRUD for the fifth time."),
            ("Users", "Ops Teams", "Users who need permissioned views, not a SQL console."),
            ("ShieldCheck", "Security Officers", "Owners of compliance who need every action logged and bounded."),
        ],
        "fdescs": [
            "Turn a schema into tables, forms and filters in seconds — no frontend ticket needed.",
            "Role-based permissions per table, row and action, so access is intentional.",
            "Action buttons that wire to your existing APIs without custom pages.",
            "Audit logs that record who changed what, when and from where.",
        ],
        "pricing": [
            ("Free", "0", "", "One tool, three users.", ["Schema-generated UI", "Basic roles", "Community support"], False),
            ("Pro", "25", "USD/user/mo", "For teams shipping internal tools weekly.", ["Everything in Free", "Unlimited tools", "Action buttons", "Full audit logs"], True),
            ("Enterprise", "Custom", "", "For regulated orgs.", ["Everything in Pro", "SSO & SCIM", "On-prem deployment", "Dedicated support"], False),
        ],
        "faq": [
            ("How do I start?", "Point Forgekit at your database or upload an OpenAPI spec; a working tool appears in under a minute."),
            ("Do I give up control of the UI?", "No — every screen is plain React components you can override when you need to."),
            ("Is it secure enough for production?", "Row-level roles, immutable audit logs and optional SSO are built in, not bolted on."),
            ("Can it replace our data team's queries?", "It gives them a safe, logged surface for the read-only views everyone keeps asking for."),
        ],
        "testimonial": ("We replaced eleven hand-rolled admin apps with tools that generate from our schema. Support stopped emailing the engineers daily.", "Priya Nair", "Head of Engineering, logistics startup"),
        "compare": {
            "cols": ["Forgekit", "Hand-built admin apps"],
            "rows": [
                ("Time to ship", "Minutes", "Sprints"),
                ("Maintenance", "Schema-driven", "Per-app custom"),
                ("Permissions", "Row + role level", "Copy-paste checks"),
                ("Audit", "Built-in logs", "Usually absent"),
                ("UI override", "Plain React", "Whatever exists"),
            ],
        },
    },
    "fitly-academy": {
        "problem": {
            "heading": "Coaches learn citations, not bodies",
            "body": "Certifications repeat textbook anatomy while the actual coaching comes from habit and hearsay. Athletes pay the price when a program is a copy, not a cause.",
            "icon": "BookOpen",
        },
        "personas": [
            ("TrendingUp", "Aspiring Coaches", "Learners wanting credentials that survive a real conversation with a client."),
            ("Users", "Gym Owners", "Studio operators who hire coaches and need proof, not PDFs."),
            ("HeartPulse", "Athletes", "Trainees who want a coach who understands why the program works."),
        ],
        "fdescs": [
            "A curriculum built on movement science with anatomy before anecdotes in every module.",
            "Certifications tied to a verifiable coaching portfolio, not a multiple-choice pass.",
            "Movement labs that grade technique from video so feedback is objective.",
            "Mentor reviews by working coaches on every capstone program you submit.",
        ],
        "pricing": [
            ("Learner", "From 199", "USD", "One course, one craft.", ["Course access", "Movement labs", "Completion certificate"], False),
            ("Coach", "From 549", "USD", "A full coaching lane.", ["Everything in Learner", "Certificate track", "Mentor reviews", "Portfolio & job board"], True),
            ("Studio", "From 25", "USD/seat", "Upskilling an entire team.", ["Everything in Coach", "Admin dashboard", "Team progress", "LMS integration"], False),
        ],
        "faq": [
            ("Is the science current?", "The curriculum is updated every 12 months against active research, not locked to a textbook edition."),
            ("Do certificates verify?", "Each certificate links to the public portfolio of programs you submitted for review."),
            ("What if I can't attend live?", "Sessions are recorded, but labs and deadlines keep the pace honest."),
            ("Do studios get hiring signals?", "Yes — the studio dashboard shows each coach's skill signals against your job requirements."),
        ],
        "testimonial": ("I hired a Fitly-taught coach over a ten-year veteran because the portfolio proved the reasoning. The athlete outcomes agreed.", "Sofia Lindgren", "Head Coach, performance studio"),
        "compare": {
            "cols": ["Fitly Academy", "Canned certifications"],
            "rows": [
                ("Curriculum", "Movement science", "Textbook repeats"),
                ("Proof", "Coaching portfolio", "Quiz PDF"),
                ("Technique", "Video movement labs", "No feedback"),
                ("Review", "Working-coach mentors", "Automated pass"),
                ("Hiring value", "Study dashboard", "Generic line"),
            ],
        },
    },
    "juniper-goods": {
        "problem": {
            "heading": "Nobody can keep anything anymore",
            "body": "Retail is built on the next purchase, so products are made to be replaced. Kitchen drawers fill with gadgets that fail, frustrate and get re-bought at the landfill of taste.",
            "icon": "ShoppingBag",
        },
        "personas": [
            ("Users", "Home Shoppers", "Buyers tired of replacing the same can opener every eighteen months."),
            ("Star", "Design-Conscious", "People who want fewer, beautiful things rather than more cheap ones."),
            ("ShieldCheck", "Value Seekers", "Shoppers who will pay once for something that is guaranteed to last."),
        ],
        "fdescs": [
            "A lifetime-replace guarantee without the fine print — if it fails, we make it right.",
            "Multipack pricing on the everyday essentials you actually reorder.",
            "Recycled, plastic-free packaging that ships flat and protects flat.",
            "Human support reachable in minutes, not a ticket queue that auto-closes.",
        ],
        "pricing": [
            ("Essentials", "From 9", "USD", "Staples for the everyday.", ["Curated homeware", "Lifetime guarantee", "Flat-rate shipping"], False),
            ("Household", "From 59", "USD", "A matched set that lasts.", ["Everything in Essentials", "Multipack pricing", "Priority support", "Free returns"], True),
            ("Trade", "Custom", "", "For studios and bulk.", ["Everything in Household", "Trade pricing", "Dedicated account", "White-label"], False),
        ],
        "faq": [
            ("What does the guarantee cover?", "Manufacturing defects for the product's life. We replace or refund; the choice is yours within 30 days."),
            ("How do you pack things?", "Recycled paper and plastic-free tape, sized to the item. No styrofoam, no air pillows."),
            ("Who answers support?", "Humans in working hours, usually within a few minutes. No bots on the front line."),
            ("Is multipack actually cheaper?", "Yes — essentials drop roughly 15% when bought as a household set."),
        ],
        "testimonial": ("The last can opener I bought here outlived three from the hardware store combined. That's the whole pitch, honestly.", "Jonas Weber", "Kitchen renovator, repeat customer"),
        "compare": {
            "cols": ["Juniper Goods", "Disposable retail"],
            "rows": [
                ("Guarantee", "Lifetime replace", "Repair? Buy new"),
                ("Gear", "Fewer, better", "Shelf of dupes"),
                ("Packaging", "Plastic-free", "Foam & layers"),
                ("Support", "Humans in minutes", "Auto-closing tickets"),
                ("Cost per use", "Falls over years", "Rises forever"),
            ],
        },
    },
    "clover-dental": {
        "problem": {
            "heading": "People skip the dentist until it hurts",
            "body": "Dental anxiety, opaque pricing and six-week waits turn a routine visit into an emergency. By the time patients come in, the treatment is bigger and so is the bill.",
            "icon": "HeartPulse",
        },
        "personas": [
            ("Users", "Fearful Patients", "People who avoid the chair and need gentle, predictable care."),
            ("Clock", "Busy Families", "Families who need same-week, after-school slots without the wait list."),
            ("ShieldCheck", "Uninsured", "Patients comparing costs who need the price before the promise."),
        ],
        "fdescs": [
            "Same-week appointments with real slots, not a three-month waiting list.",
            "Transparent pricing shown before you book, so the chair never surprises.",
            "Painless financing options so dental care is decided on health, not cash flow.",
            "Digital records and reminders you can access from your phone, anytime.",
        ],
        "pricing": [
            ("Check-Up", "From 49", "USD", "Clean, exam and digital x-rays under one fee.", ["Full exam", "Clean & scale", "Digital x-rays", "Treatment plan"], False),
            ("Restorative", "From 149", "USD", "Fillings and simple restorative, priced upfront.", ["Everything in Check-Up", "Filling options", "No-surprise quote", "Payment plans"], True),
            ("Plan", "From 29", "USD/mo", "Preventive care as a monthly membership.", ["Two cleanings/year", "10% treatments", "Priority slots", "Cancel anytime"], False),
        ],
        "faq": [
            ("Is pricing really upfront?", "Yes — a consultation quote is valid for 90 days, written down, before any treatment begins."),
            ("How gentle are you with anxious patients?", "Sedation options, breaks on request and a team trained for anxiety — there is no rush policy."),
            ("Do you take insurance?", "Most plans accepted, plus our own membership for cash-pay patients."),
            ("What if I need urgent care?", "Same-day emergency slots are reserved daily; you will not be redirected to a random clinic."),
        ],
        "testimonial": ("The price was on the screen before I booked. Six months on, my daughter actually looks forward to the visits we dreaded.", "Rania Al-Farsi", "Parent of two, clinic member"),
        "compare": {
            "cols": ["Clover Dental", "Typical practice"],
            "rows": [
                ("Booking", "Same-week slots", "Week+ waits"),
                ("Pricing", "Upfront & written", "Estimate roulette"),
                ("Anxiety", "Trained + sedatives", "Rush chair"),
                ("Financing", "Painless plans", "Lump sum"),
                ("Records", "Phone access", "A folder somewhere"),
            ],
        },
    },
    "noora-khan": {
        "problem": {
            "heading": "Pretty portfolios don't answer hard questions",
            "body": "Most design portfolios show screenshots, not decisions. Recruiters scroll past case studies that describe what was made but never why it worked — or who it served.",
            "icon": "Layers",
        },
        "personas": [
            ("Users", "Hiring Managers", "Leads who need evidence of impact, not a Dribbble moodboard."),
            ("Sparkles", "Startup Founders", "Early teams wanting product thinking, not just a beautiful mock."),
            ("TrendingUp", "Product Teams", "Groups evaluating a senior designer who can ship within a system."),
        ],
        "fdescs": [
            "Product strategy that starts with the problem, not the palette.",
            "Interfaces that ship — design to build handoff without message roulette.",
            "Design systems that scale teams, reducing the need for pixel police.",
            "Usability audits with measurable before/after on the metrics that matter.",
        ],
        "pricing": [
            ("Audit", "From 1,500", "USD", "A fast, evidence-based usability pass.", ["Heuristic review", "Priority findings", "One walkthrough"], False),
            ("Project", "From 6,000", "USD", "End-to-end product design for a real launch.", ["Discovery & strategy", "Interface design", "Design system", "Build handoff"], True),
            ("Retainer", "From 4,000", "USD/mo", "A senior designer inside your team.", ["Weekly design support", "Systems stewardship", "Design reviews", "Monthly roadmap"], False),
        ],
        "faq": [
            ("What does a good case study prove?", "The problem, the constraint, the decision and the outcome metric. Everything else is decoration."),
            ("How do you measure design?", "Activation, completion and support load before and after — the numbers decide, not taste."),
            ("Do you work inside our stack?", "Design is tool-agnostic; handoff happens in what the build team already uses."),
            ("What makes you senior?", "Scope — the ability to unpick a fuzzy problem into a plan a six-person team can ship."),
        ],
        "testimonial": ("Noora redesigns the path to signup and activation climbs 24% in one release. She argues from data, which is rare in a designer of her eye.", "Lucas Fontaine", "Head of Product, series-A fintech"),
        "compare": {
            "cols": ["Noora Khan", "Screenshot portfolios"],
            "rows": [
                ("Work shown", "Decisions + outcomes", "Loose screenshots"),
                ("Process", "Problem-first strategy", "Palette-first"),
                ("Handoff", "System + build-ready", "Figma URL"),
                ("Measurement", "Before/after metrics", "Aesthetic pride"),
                ("Scope", "Team-scale, senior", "Agency handoffs"),
            ],
        },
    },
    "stonemark-realty": {
        "problem": {
            "heading": "The agent knows the market, not your street",
            "body": "Big agencies route you to whichever agent is free, and the valuation arrives before the conversation. Families overpay on the wrong street because nobody knows the block.",
            "icon": "MapPin",
        },
        "personas": [
            ("Building2", "Home Buyers", "Families needing a match to a street, not just a size."),
            ("TrendingUp", "Sellers", "Owners who want a valuation honest before it is flattering."),
            ("Users", "Relocators", "Movers in a new city who need the neighbourhood, not just the floor plan."),
        ],
        "fdescs": [
            "A neighbourhood specialist on every file — someone who lives the block they sell.",
            "Pre-market inventory shared with matched buyers before it reaches the portal.",
            "Valuations benchmarked against private comparable sales, not asking prices.",
            "A to-do move plan that covers inspection, funding and the day itself.",
        ],
        "pricing": [
            ("Buyer", "0", "", "Buyer representation at no direct cost.", ["Neighbourhood specialist", "Pre-market access", "Move plan"], False),
            ("Seller", "From 1.5", "%", "Full-service listing, marketed and managed.", ["Honest valuation", "Professional media", "Open houses + portal", "Negotiations & conveyance"], True),
            ("Portfolio", "Custom", "", "Multi-property and investor service.", ["Everything in Seller", "Portfolio strategy", "Tax-aware phasing", "Quarterly reviews"], False),
        ],
        "faq": [
            ("Who actually shows my home?", "The same specialist who valued it. No random agent handoffs mid-deal."),
            ("How honest are valuations?", "We show the comparable transactions that justify the number — the reasoning is on the table."),
            ("Can we view off-market homes?", "Matched buyers see pre-market inventory a week before it lists publicly."),
            ("What if we're relocating?", "You get a neighbourhood briefing as part of the search, not a sales pitch on the drive."),
        ],
        "testimonial": ("Our specialist flagged the flood-history on a house three other agents were touring. That alone justified the morning we chose.", "Margaret Osei", "Recent buyer, family of four"),
        "compare": {
            "cols": ["Stonemark Realty", "Aggregator agents"],
            "rows": [
                ("Advisor", "Neighbourhood specialist", "Rotating free agent"),
                ("Inventory", "Pre-market home access", "Portal re-lists"),
                ("Valuation", "Comparables shown", "Hope economics"),
                ("Move", "End-to-end plan", "Keys and good luck"),
                ("Post-sale", "Neighbourhood intel", "Gone to next lead"),
            ],
        },
    },
    "resupro": {
        "problem": {
            "heading": "Applicant systems kill good resumes quietly",
            "body": "Well-written careers are being rejected by parsers that read nothing but keywords and layout. The resume that reads beautifully to you reads nothing to the ATS.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("TrendingUp", "Job Seekers", "Candidates getting silent rejections despite strong experience."),
            ("Users", "Career Changers", "Switchers whose best skills never make it past the parser."),
            ("ShieldCheck", "Graduates", "New grads applying to hundreds with a one-size template."),
        ],
        "fdescs": [
            "An ATS readability score that grades your resume against how parsers actually read.",
            "Job-match copy that aligns your lines to the description without lying.",
            "An interview coach that builds a plan from the exact role you are pursuing.",
            "One-click PDF exports that keep formatting, links and dates intact.",
        ],
        "pricing": [
            ("Free", "0", "", "One resume, forever.", ["One-page resume", "ATS basics", "PDF export"], False),
            ("Pro", "19", "USD/mo", "For active job seekers.", ["Everything in Free", "ATS score + fixes", "Job-match copy", "Interview coach", "Unlimited resumes"], True),
            ("Career", "49", "USD", "Buy once, own forever.", ["Everything in Pro on up to 5 resumes", "Cover-letter builder", "Salary benchmarks", "One year of updates"], False),
        ],
        "faq": [
            ("What is an ATS score?", "A 0-100 grade estimating how clearly a parser can extract name, dates, roles and skills from your file."),
            ("Can I keep my template?", "Yes — upload it; we score and suggest fixes without forcing a redesign."),
            ("Does copy stay honest?", "Match suggestions are drawn from your own experience, reworded to the role — never invented."),
            ("Is my data private?", "Your resumes are encrypted and exportable anytime; delete-all is a single button."),
        ],
        "testimonial": ("Fourth resume in, the ATS score went from 61 to 94 and the callbacks finally started. Same experience — clearer story.", "Amelia Stone", "Senior analyst, hired after 9 months searching"),
        "compare": {
            "cols": ["ResuPro", "Word templates"],
            "rows": [
                ("Readability", "ATS-scored content", "Parser-proof? unknown"),
                ("Match", "Job-description aligned", "Same bullets everywhere"),
                ("Interview", "Role-specific plan", "Generic advice"),
                ("Export", "Clean one-click PDF", "Format breaks"),
                ("Update", "Live over a year", "Redo from scratch"),
            ],
        },
    },
    "launchbay": {
        "problem": {
            "heading": "Dashboards are impressive; decisions are rare",
            "body": "Analytics tools show every chart but never say what to do. Growth teams watch numbers move and still argue about what actually matters.",
            "icon": "BarChart3",
        },
        "personas": [
            ("TrendingUp", "Product Managers", "Managers asking 'which feature actually retains?' and getting silence."),
            ("Zap", "Growth Teams", "Teams needing churn signals before the renewal is lost."),
            ("Users", "Founders", "Founders who want the three numbers that run the business, not forty."),
        ],
        "fdescs": [
            "Cohort retention that shows when people actually leave, not just that they do.",
            "Feature stickiness ranking what users keep coming back for.",
            "Churn signals that flag at-risk accounts before renewal day.",
            "An event explorer that answers a new question without a data ticket.",
        ],
        "pricing": [
            ("Spark", "0", "", "For side projects and prototypes.", ["10k events/mo", "Core retention", "30-day history"], False),
            ("Growth", "79", "USD/mo", "For product teams shipping.", ["Everything in Spark", "Unlimited events", "Stickiness & cohorts", "Churn signals", "Email alerts"], True),
            ("Scale", "Custom", "", "For multi-product portfolios.", ["Everything in Growth", "Multi-workspace", "SSO & audit", "SLA + dedicated nerd"], False),
        ],
        "faq": [
            ("How fast do events appear?", "In near real time; dashboards update within seconds of ingestion."),
            ("Does it replace our database?", "No — Launchbay sits beside it. The SQL stays yours; the answers get readable."),
            ("What is a churn signal?", "A measurable drop in a paying account's usage that predicts cancellation with a flagged confidence."),
            ("Can a PM self-serve?", "Yes — the whole tool is click-answer, no data engineering between question and answer."),
        ],
        "testimonial": ("We found the onboarding step killing week-one retention by lighthouse of a chart. One fix, and cohort retention rose nine points.", "Marta Kovač", "Growth Lead, consumer app"),
        "compare": {
            "cols": ["Launchbay", "Raw BI tools"],
            "rows": [
                ("Questions", "Answered directly", "Queries required"),
                ("Signals", "Auto churn flags", "You guess"),
                ("Retention", "Cohort-first", "Bar charts only"),
                ("Audience", "Whole product team", "Analysts only"),
                ("Time to insight", "Minutes", "Sprint tickets"),
            ],
        },
    },
    "metrica-pulse": {
        "problem": {
            "heading": "Every tool has its own truth about the month",
            "body": "Revenue says one number, billing another, support another. Monthly reporting is a reconciliation project, and the board sees whichever version finance finished first.",
            "icon": "LayoutDashboard",
        },
        "personas": [
            ("TrendingUp", "Finance Leads", "Owners reconciling figures across disconnected tools."),
            ("Users", "Operations Heads", "Operators who need one pane for service and success load."),
            ("ShieldCheck", "Founders", "Founders who want board-ready numbers without the exercise machine."),
        ],
        "fdescs": [
            "Thirty-plus native integrations so revenue, churn and support share one clock.",
            "Modeled metrics that compute one canonical number instead of five opinions.",
            "Alerting that fires on what matters instead of paging you hourly.",
            "Board-ready reports that export clean without tonight's reshuffling.",
        ],
        "pricing": [
            ("Starter", "0", "", "Three metrics, one dashboard.", ["3 integrations", "1 dashboard", "7-day history"], False),
            ("Growth", "99", "USD/mo", "For companies with real data chaos.", ["Everything in Starter", "Unlimited integrations", "Modeled metrics", "Smart alerts", "Board reports"], True),
            ("Enterprise", "Custom", "", "For multi-entity reporting.", ["Everything in Growth", "Consolidation", "SSO & roles", "Support SLA"], False),
        ],
        "faq": [
            ("How are metrics modeled?", "You define one formula for revenue, say, and every source is normalised into it once."),
            ("Which tools integrate?", "The common stack — billing, CRM, support, ads, analytics and warehouse imports."),
            ("Can alerts be quiet?", "Yes, and they should be. Alerts are tuned per metric with a 'shut up until it matters' mode."),
            ("Is export board-ready?", "Reports export to PDF and slides with your brand, dates and footnotes already in place."),
        ],
        "testimonial": ("Finance report time went from three days to an hour. The north star number is finally shared, not haggled.", "Hannah Lee", "COO, scale-up software"),
        "compare": {
            "cols": ["Metrica Pulse", "Monthly spreadsheet gymnastics"],
            "rows": [
                ("Truth", "One canonical number", "Five versions"),
                ("Sources", "30+ connected", "Copy-paste rituals"),
                ("Alerts", "Important only", "Inbox noise"),
                ("Board", "Export in one click", "Sunday-night deck"),
                ("Scale", "Multi-entity", "Breaks at two tools"),
            ],
        },
    },
    "cascade-hq": {
        "problem": {
            "heading": "Strategy evaporates between the boardroom and the team",
            "body": "The leadership offsite sets grand goals. Three months later, teams are busy, aligned with nothing and honest about none of it.",
            "icon": "TrendingUp",
        },
        "personas": [
            ("Users", "Leadership", "Executives who set goals that never survive contact with the week."),
            ("ShieldCheck", "Team Leads", "Leads who track others' OKRs and keep their own in a doc."),
            ("Zap", "IC Teams", "Individuals drowning in busywork with no line to the company goal."),
        ],
        "fdescs": [
            "An OKR tree that maps every team goal back to the company objective.",
            "Weekly check-ins that surface risk before the quarter review surprises you.",
            "Confidence scoring that replaces vague updates with honest signals.",
            "Quarterly reviews with a built-in retrospective and re-scoring flow.",
        ],
        "pricing": [
            ("Starter", "0", "", "Up to 10 people.", ["1 team, 1 tree", "Check-ins", "Basic reports"], False),
            ("Team", "8", "USD/user/mo", "For grown-up orgs.", ["Everything in Starter", "Full OKR tree", "Confidence scoring", "Dashboards", "Slack sync"], True),
            ("Org", "Custom", "", "For multi-team companies.", ["Everything in Team", "Unlimited teams", "SSO & SCIM", "Custom review cycles", "Dedicated success"], False),
        ],
        "faq": [
            ("What is confidence scoring?", "A 0-100 trail of how sure a team is a goal will land, tracked weekly so wobbles are visible early."),
            ("How often do check-ins run?", "Whatever rhythm fits — weekly is default, but teams can set cadence per goal."),
            ("Is this just OKR admin?", "No — the product is the ritual: tree, check-in, score, review. Stale if you don't run it."),
            ("Can it connect to our work tools?", "Slack and Teams sync keep updates where teams already talk."),
        ],
        "testimonial": ("The confidence score flagged a flagship goal wobbling in week six — we re-scoped before it became Q3 drama, for once.", "Tom Becker", "CEO, mid-market SaaS"),
        "compare": {
            "cols": ["Cascade HQ", "Spreadsheet OKRs"],
            "rows": [
                ("Mapping", "Tree to company goal", "Tabs of drift"),
                ("Rhythm", "Weekly check-ins", "Quarterly panic"),
                ("Honesty", "Confidence scores", "Green smileys"),
                ("Reviews", "Built-in ritual", "New deck each time"),
                ("Visibility", "Company-wide tree", "What sync you get"),
            ],
        },
    },
    "ledgerline": {
        "problem": {
            "heading": "You send invoices, then you chase them",
            "body": "Every unpaid invoice starts an awkward conversation. Small teams spend their afternoon on polite reminders instead of work — and late payers learn the silence is free.",
            "icon": "BarChart3",
        },
        "personas": [
            ("TrendingUp", "Freelancers", "Solo operators spending one day a week on chasing."),
            ("Users", "Small Studios", "Agencies juggling 40 invoices and no patience for follow-ups."),
            ("ShieldCheck", "Founders", "Founders who want a cash forecast, not a spreadsheet prayer."),
        ],
        "fdescs": [
            "Auto-dunning that escalates reminders at the right pace, politely and on schedule.",
            "Payment reminders and late-fee logic that run without embarrassing emails.",
            "Multi-currency invoices that settle in the client's own currency.",
            "A cash-flow forecast built from real payment behaviour, not hope.",
        ],
        "pricing": [
            ("Solo", "0", "", "One user, unlimited invoices.", ["Invoicing", "Reminders", "Bank sync"], False),
            ("Studio", "29", "USD/mo", "For growing teams.", ["Everything in Solo", "Auto-dunning", "Late-fee engine", "Multi-currency", "Cash forecast"], True),
            ("Agency", "59", "USD/mo", "For multi-client agencies.", ["Everything in Studio", "Client portals", "Team approvals", "Branded documents"], False),
        ],
        "faq": [
            ("How polite is dunning?", "Very — the escalation library is written to be firm without arming the client's lawyers."),
            ("What happens at day 30?", "The workflow you set: a reminder, a late fee, a pause on work — your rules, automated."),
            ("Can clients pay in their currency?", "Yes, multi-currency settlement works at checkout with the conversion shown upfront."),
            ("Is cash flow just an estimate?", "It's forecast from your actual payment history per client, so it improves as it learns."),
        ],
        "testimonial": ("Average payment time dropped from 43 to 26 days in two months. The late-fee engine pays for the whole product.", "Carlos Mendez", "Owner, boutique agency"),
        "compare": {
            "cols": ["Ledgerline", "Manual chasing"],
            "rows": [
                ("Reminders", "Automated, warm", "Awkward emails"),
                ("Late fees", "Enforced by rules", "Forgotten entirely"),
                ("Currency", "Multi-currency", "FX spreadsheet"),
                ("Forecast", "Learns your clients", "Gut feel"),
                ("Day cost", "Two minutes setup", "One day weekly"),
            ],
        },
    },
    "linguagrid": {
        "problem": {
            "heading": "Localization ships last, breaks first",
            "body": "Translations arrive as a jumbled sheet at the worst moment, keys drift out of sync, and one untranslated string ships to a ticket's worth of users.",
            "icon": "Globe",
        },
        "personas": [
            ("BookOpen", "Developers", "Engineers who hardcode English to avoid the string pipeline."),
            ("Users", "Localization Managers", "Managers juggling translators, keys and release trains by hand."),
            ("TrendingUp", "Product Leads", "Owners who need every locale reliable before launch."),
        ],
        "fdescs": [
            "String sync that pulls keys from your repo and pushes back translations automatically.",
            "Live previews so you verify every locale before the build leaves the station.",
            "Glossary memory that keeps voice consistent across all 48 languages.",
            "Locale QA that flags missing keys, reflows and truncation before release.",
        ],
        "pricing": [
            ("Starter", "0", "", "Side projects and small apps.", ["100 strings", "3 languages", "String sync"], False),
            ("Pro", "49", "USD/mo", "For products shipped properly.", ["Everything in Starter", "Unlimited strings", "48 languages", "Live previews", "Glossary memory"], True),
            ("Enterprise", "Custom", "", "For regulated, high-volume orgs.", ["Everything in Pro", "Whitelabel editor", "SSO & audit", "On-prem option"], False),
        ],
        "faq": [
            ("How does sync work?", "A CLI watches your repo; new keys open translation tasks, and completed translations come back as a PR."),
            ("Are machine translations allowed?", "Yes — as drafts. Human or MT, everything rides the same glossary and QA rail."),
            ("What does locale QA catch?", "Missing keys, text overflow, date/number formats and RTL reflow issues before users see them."),
            ("Can designers preview?", "Yes — live previews render real screens in any locale, so truncation is caught visually."),
        ],
        "testimonial": ("We shipped six new languages in one sprint, all QA'd in preview before the train moved. Localization stopped being the release blocker.", "Yuki Tanaka", "Engineering Manager, travel platform"),
        "compare": {
            "cols": ["LinguaGrid", "Translation spreadsheets"],
            "rows": [
                ("Sync", "Repo-native pipeline", "Export/import chaos"),
                ("Preview", "Real screens, live", "Hopeful checking"),
                ("Consistency", "Glossary memory", "Voice drift"),
                ("QA", "Automated locale checks", "Users find it"),
                ("Scale", "48 languages", "One sheet per app"),
            ],
        },
    },
}

# ---- AI agent products (10 vertical SaaS, added 7.13) ---------------------
AGENT_CONTENT = {
    "supportdesk-ai": {
        "problem": {
            "heading": "Support tickets pile up faster than your team can answer",
            "body": "Most commerce support is the same ten questions repeated a thousand times. Orders, returns, refunds and shipping eat the day — while the genuinely hard cases queue behind them.",
            "icon": "Zap",
        },
        "personas": [
            ("Briefcase", "Store Owners", "Shop owners drowning in repetitive tickets who want their team to focus on hard problems."),
            ("Users", "Support Teams", "Agents whose day is 80% copy-paste answers and who want tool-backed auto-resolution."),
            ("Activity", "Customers", "Buyers who want answers at 2am without waiting for business hours to open."),
        ],
        "fdescs": [
            "Every order, return and refund question answered straight from your connected store data.",
            "Policy-grounded responses citing your actual return, shipping and guarantee texts.",
            "Smart routing that hands the unavoidable escalations to a human with full context attached.",
            "A live resolution dashboard showing what got handled, what escalated and why.",
        ],
        "pricing": [
            ("Starter", "$29", "/mo", "For stores under 500 tickets a month.", ["Connect your store", "Order & refund autopilot", "Ticket dashboard"], False),
            ("Growth", "$99", "/mo", "For teams that want near-zero touch at scale.", ["Everything in Starter", "Returns & shipping agent", "Smart escalation routing", "Resolution analytics"], True),
            ("Scale", "$249", "/mo", "For multi-brand and multi-store operations.", ["Everything in Growth", "Multi-store commands", "SSO & audit log", "Dedicated onboarding"], False),
        ],
        "faq": [
            ("Which platforms does it connect to?", "Shopify, WooCommerce and Square out of the box, with a REST API and webhooks for anything else."),
            ("Does it actually take actions, or just answer?", "Both. It can issue refunds and create return labels within the limits you set — and anything above those limits escalates to your team."),
            ("How do you prevent the AI from inventing policies?", "Every answer is grounded in your uploaded policy documents plus live order data, and every action logs the exact tool call that produced it."),
            ("What happens when it's unsure?", "It hands off to a human with the conversation, suggested reply and order context attached — never a guessed answer."),
        ],
        "testimonial": ("We resolve 70% of tickets hands-free now. My agents spend their day on the hard cases, not refund requests.", "Dana Whitfield", "Head of CX, Meridian Goods"),
        "compare": {
            "cols": ["SupportDesk AI", "Human-only support"],
            "rows": [
                ("Resolution speed", "Seconds, around the clock", "Business hours only"),
                ("Repeats every ticket", "Policy-grounded, consistent", "Varies by agent"),
                ("Escalation", "Auto-routed with full context", "Caught or missed"),
                ("Weekly ticket volume", "Unlimited, auto-scaled", "Limited by seats"),
                ("Per-ticket cost", "Fraction of a support seat", "Full salary cost"),
            ],
        },
    },
    "leadscout-ai": {
        "problem": {
            "heading": "Leads go cold before an agent ever calls",
            "body": "The average lead waits hours for first contact — and by then they've contacted someone faster. Qualifying who is serious, urgent and realistic is the work that usually never gets done.",
            "icon": "TrendingUp",
        },
        "personas": [
            ("Building2", "Team Leads", "Agencies whose pipeline is clogged with unqualified contacts nobody follows up on."),
            ("Users", "Agents", "Agents who need pre-scored, warmed-up leads rather than a raw phone list."),
            ("Clock", "Franchises", "Multi-branch brands that must respond to every lead while staying consistent."),
        ],
        "fdescs": [
            "24/7 conversational screening that qualifies budget, timeline, area and financing fit.",
            "A live scoring engine ranking every lead by purchase intent and fit before a human sees it.",
            "Automatic viewing bookings for hot leads, placed straight into the team's calendar.",
            "Sequenced SMS and email follow-ups that keep warm leads warm until the agent calls.",
        ],
        "pricing": [
            ("Starter", "$49", "/mo", "For a single agent or small solo practice.", ["1 team seat", "Lead capture & screening", "SMS follow-up"], False),
            ("Pro", "$149", "/mo", "For teams that live on their pipeline.", ["Everything in Starter", "Lead scoring engine", "Auto viewing bookings", "Up to 5 team seats"], True),
            ("Enterprise", "$499", "/mo", "For franchises and multi-branch brands.", ["Everything in Pro", "Unlimited seats & branches", "CRM sync & SSO", "Dedicated account manager"], False),
        ],
        "faq": [
            ("What happens to a lead that screens as low intent?", "It is parked, nurtured by follow-up sequences and re-scored — so no lead is simply dropped."),
            ("Does it actually book viewings?", "Yes. Hot leads offer available viewing slots from your calendar and the booking lands in it automatically."),
            ("How is the scoring decided?", "Conversation answers, engagement speed and past conversion patterns produce a transparent score you can inspect per lead."),
            ("Does it text in my voice?", "You approve templates and tone settings; every outbound message ships inside your brand wording."),
        ],
        "testimonial": ("Three times more qualified viewings a month, and every single enquiry got a response inside ten minutes.", "Marcus Osei", "Broker, Osei & Partners"),
        "compare": {
            "cols": ["LeadScout AI", "Lead lists & cold calls"],
            "rows": [
                ("First response", "Under a minute, 24/7", "Hours or never"),
                ("Qualification", "Scored on budget, timing, fit", "Guesswork on the call"),
                ("Viewings booked", "Auto-booked for hot leads", "Manual triage"),
                ("Follow-up", "Automated sequences", "Depends on the agent"),
                ("Wasted calls", "Minimised by design", "Most of the list"),
            ],
        },
    },
    "clausecheck-ai": {
        "problem": {
            "heading": "The clause that ruins a deal is the one nobody read",
            "body": "Contracts get signed in days but read in an evening — if at all. Auto-renewals, uncapped liability and missing obligations hide in plain text, right where they have always been.",
            "icon": "ShieldCheck",
        },
        "personas": [
            ("BookOpen", "Founders", "Startup founders signing vendor and client terms without legal counsel on standby."),
            ("Briefcase", "Procurement", "Buying teams juggling dozens of incoming contracts with one reviewer."),
            ("ShieldCheck", "Counsel", "Lawyers who want fast triage so they can focus on the contracts that really need them."),
        ],
        "fdescs": [
            "A risk engine that flags liability caps, auto-renewals, termination traps and missing obligations.",
            "Severity-coded redlines so important risks cannot be lost in the fine print.",
            "Plain-English summaries that explain each risk and its practical consequence.",
            "One-click export and handoff to a licensed reviewer when a signature is marginal.",
        ],
        "pricing": [
            ("Starter", "$19", "/mo", "For reviewing the occasional inbound contract.", ["10 reviews a month", "Risk-flag engine", "Plain-English summary"], False),
            ("Business", "$69", "/mo", "For teams signing contracts every week.", ["Everything in Starter", "Unlimited reviews", "Severity redlines & export", "Template risk library"], True),
            ("Enterprise", "$199", "/mo", "For counsel teams and legal operations.", ["Everything in Business", "SSO & audit trail", "Custom clause playbooks", "Priority handoff"], False),
        ],
        "faq": [
            ("Is this legal advice?", "No. ClauseCheck is a fast triage and review tool. Final sign-off always belongs to a licensed professional."),
            ("Which contract types does it handle?", "Vendor agreements, client terms, NDAs, employment contracts and software license agreements."),
            ("How accurate is the flagging?", "On standard commercial clauses it matches human review on about nine in ten — the remaining one is precisely what triage is for."),
            ("Can I upload my own negotiation rules?", "On Business and Enterprise plans you can bake your own negotiated positions into a custom playbook."),
        ],
        "testimonial": ("It found an uncapped liability clause in a vendor deal our team had already cleared. That alone paid for itself.", "Priya Raghavan", "General counsel, fintech scale-up"),
        "compare": {
            "cols": ["ClauseCheck", "Skim-read & hope"],
            "rows": [
                ("Hidden risks", "Flagged with severity codes", "Missed in the fine print"),
                ("Speed", "First flags in under a minute", "Depends on who you find"),
                ("Cost per contract", "Pennies vs a specialist hour", "Lawyer rates"),
                ("Consistency", "Same rules every review", "Varies per reviewer"),
                ("Summary", "Plain English for everyone", "Jargon for initiates"),
            ],
        },
    },
    "appointly-ai": {
        "problem": {
            "heading": "Empty slots and no-show surprises are the quiet revenue leak",
            "body": "Every missed appointment is wasted clinical time, and every no-show was almost always a reminder problem. Booking is still handled like it is 1999.",
            "icon": "Clock",
        },
        "personas": [
            ("Clock", "Clinics", "Practice managers balancing provider calendars, intake and reminders across a full roster."),
            ("Users", "Patients", "Patients who want to book, reschedule and receive reminders without a phone maze."),
            ("Building2", "Multi-site Groups", "Multi-location brands that must keep every provider bookable everywhere."),
        ],
        "fdescs": [
            "Availability across every provider, service and location with conflict-free booking enforced at the source.",
            "Reminders that learn when each patient actually replies, drastically cutting no-show rates.",
            "A waitlist that backfills cancellations the moment a slot frees up.",
            "Intake forms tailored per service so the front desk never chases paperwork.",
        ],
        "pricing": [
            ("Starter", "$25", "/mo", "For a solo provider getting organised.", ["1 provider", "Online booking & reminders", "Service intake forms"], False),
            ("Clinic", "$99", "/mo", "For clinic teams sharing a calendar.", ["Everything in Starter", "Up to 5 providers", "Waitlist backfill", "No-show analytics"], True),
            ("Group", "$299", "/mo", "For multi-site groups and franchises.", ["Everything in Clinic", "Unlimited providers", "Multi-location management", "SSO & white-label"], False),
        ],
        "faq": [
            ("Does it work with my existing calendar?", "Two-way sync with Google and Microsoft calendars, so bookings never double-book your day."),
            ("What happens when a patient cancels?", "The slot is released and the waitlist fills it instantly — often within minutes."),
            ("How does it cut no-shows?", "It monitors who ignores generic reminders and switches to stronger channels and earlier timing for exactly those patients."),
            ("Can patients book without calling?", "Yes. A booking link, embedded widget and SMS-based booking are all included from the Starter plan."),
        ],
        "testimonial": ("No-shows dropped a third and our providers' calendars are finally full — the waitlist backfill is magic.", "Elena Markova", "Clinic director, 4-provider practice"),
        "compare": {
            "cols": ["Appointly", "Phone-book-and-pray"],
            "rows": [
                ("No-shows", "Calibrated reminders", "Chasing patients by phone"),
                ("Cancellations", "Waitlist refills instantly", "Slots die silently"),
                ("Booking tonight", "Self-serve links & SMS", "Voicemail at 6pm"),
                ("Double-bookings", "Prevented at the source", "Possible in any inbox"),
                ("Front desk time", "Automated intake", "Forms by hand"),
            ],
        },
    },
    "recruitiq-ai": {
        "problem": {
            "heading": "Recruiting time is lost to screening, not hiring",
            "body": "A single open role can sit for weeks because every resume gets a human read. Screening thousands and shortlisting the right five is mechanical — and it is still done by hand.",
            "icon": "Briefcase",
        },
        "personas": [
            ("Briefcase", "Hiring Managers", "Managers waiting on shortlists while their teams backfill the workload."),
            ("Users", "Recruiters", "Recruiters buried in parsing who want minutes back for candidate conversations."),
            ("Globe", "Agencies", "Agencies running many requisitions at once who need the same quality bar every time."),
        ],
        "fdescs": [
            "Resume parsing and candidate matching mapped directly against every role's requirements.",
            "Scores with written reasons, so a recruiter can agree or disagree in seconds.",
            "Draft outreach per candidate, ready to approve and send.",
            "Interview scheduling that finds the next open slot and books it without email ping-pong.",
        ],
        "pricing": [
            ("Starter", "$39", "/mo", "For small teams hiring a few roles a quarter.", ["1 active role", "Resume parsing & scoring", "Screening dashboard"], False),
            ("Growth", "$129", "/mo", "For teams running several roles at once.", ["Everything in Starter", "Up to 5 active roles", "Outreach drafts", "Auto scheduling"], True),
            ("Scale", "$399", "/mo", "For agencies and talent teams.", ["Everything in Growth", "Unlimited roles", "Pipeline analytics", "SSO & API access"], False),
        ],
        "faq": [
            ("Does it replace the recruiter?", "No. It reclaims the mechanical screening hours so recruiters spend time with the shortlist they actually approve."),
            ("How are candidate scores explained?", "Each score breaks down by skill, experience and stated-fit signals with the supporting lines from the resume."),
            ("Can we tune what matters?", "Yes. You weight skills, years, seniority and keywords per role, and the scoring follows those weights."),
            ("Does it send messages on its own?", "Never without approval. Outreach drafts sit in your queue until the recruiter presses send."),
        ],
        "testimonial": ("We cut screening from fourteen days to under one and started hiring people we would have lost to the delay.", "Jordan Bell", "Head of Talent, 200-person SaaS"),
        "compare": {
            "cols": ["RecruitIQ", "Human-only screening"],
            "rows": [
                ("Time to shortlist", "Hours, not weeks", "Depends on bandwidth"),
                ("Consistency", "Same weights every resume", "Skews by the reviewer"),
                ("Explainability", "Written reasons per score", "A hunch"),
                ("Outreach", "Drafts ready to approve", "Written from scratch"),
                ("Next interview", "Auto-scheduled", "Email ping-pong"),
            ],
        },
    },
    "ledgerai": {
        "problem": {
            "heading": "The monthly close eats three days and nobody enjoys it",
            "body": "Receipts sit in folders, categories drift month after month and reconciliations are a scramble. The books close late because nobody gets around to them — until the accountant calls.",
            "icon": "Wallet",
        },
        "personas": [
            ("Wallet", "Founders", "Founders who want to see the true numbers without running a bookkeeping operation."),
            ("BarChart3", "Accountants", "Accountants who want clean, categorised books instead of shoebox data."),
            ("Layers", "Finance Teams", "Finance teams that must close monthly and pass audits without drama."),
        ],
        "fdescs": [
            "Automatic categorisation of receipts and transactions, each with a confidence score you can review.",
            "Bank feed reconciliation that matches records automatically and flags anything that does not fit.",
            "Anomaly alerts that surface unusual spend before accountants find it the hard way.",
            "Automated month-end reports prepared and ready for sign-off in days, not weeks.",
        ],
        "pricing": [
            ("Starter", "$29", "/mo", "For freelancers and micro-businesses.", ["1 business", "Auto categorisation", "Monthly reports"], False),
            ("Pro", "$99", "/mo", "For growing companies with real books.", ["Everything in Starter", "Bank feed reconciliation", "Anomaly alerts", "Accountant read-only access"], True),
            ("Enterprise", "$299", "/mo", "For multi-entity operations.", ["Everything in Pro", "Unlimited entities", "SSO & audit trail", "Priority close support"], False),
        ],
        "faq": [
            ("How accurate is the categorisation?", "Over 97% on routine categories, and every unsure line is queued for a one-click review rather than silent guesses."),
            ("Is the accountant going to trust it?", "Yes — they get read-only access, an audit trail per entry and category rules they can shape, then sign off."),
            ("What happens if a number doesn't reconcile?", "It is flagged as an anomaly with the mismatching record attached, never silently absorbed."),
            ("Which banks and tools connect?", "Bank feeds via Plaid, plus CSV import, Stripe, PayPal and major accounting exports."),
        ],
        "testimonial": ("The close went from three team days to one afternoon — the same accountant signed off with three questions instead of a spreadsheet debate.", "Hugo Larsen", "CFO, subscription e-commerce brand"),
        "compare": {
            "cols": ["LedgerAI", "Spreadsheet close"],
            "rows": [
                ("Month-end close", "Days, not weeks", "Scramble at deadline"),
                ("Categorisation", "Confidence-scored, reviewable", "Whatever felt right"),
                ("Reconciliation", "Auto with anomaly flags", "Line by painful line"),
                ("Audit trail", "Every entry logged", "Undo and memory"),
                ("Accountant access", "Read-only, sign-off ready", "Copy-paste exports"),
            ],
        },
    },
    "tablehost-ai": {
        "problem": {
            "heading": "The phone rings at the worst moment — and that table is already gone",
            "body": "A host juggling a full dining room cannot answer every call, and every unanswered call is a party not booked. Peak-hour chaos quietly decides who eats with you tonight.",
            "icon": "Star",
        },
        "personas": [
            ("Users", "Restaurant Owners", "Owners who cannot staff a dedicated booking line and still lose covers."),
            ("Clock", "Managers", "Front-of-house managers drowning in call-backs during the dinner rush."),
            ("Star", "Guests", "Diners who want to book on the phone or via a link without being put on hold."),
        ],
        "fdescs": [
            "A live reservation board with real-time availability across every table and turn.",
            "Waitlist management that texts guests and fills the gap the moment a table opens.",
            "SMS confirmations and reminders that cut no-shows without touching your team's time.",
            "Peak-hour autopilot that answers calls, books and confirms while the dining room runs.",
        ],
        "pricing": [
            ("Starter", "$39", "/mo", "For independent restaurants.", ["1 venue", "Booking link & board", "SMS confirmations"], False),
            ("Pro", "$119", "/mo", "For busy venues that fill every turn.", ["Everything in Starter", "Waitlist backfill", "Phone answering agent", "No-show analytics"], True),
            ("Multi", "$299", "/mo", "For groups and small chains.", ["Everything in Pro", "Up to 5 venues", "Group reporting", "White-label booking"], False),
        ],
        "faq": [
            ("Does it really answer the phone?", "Yes. A voice-ready booking line takes reservations, checks live availability and confirms the slot — then updates your board."),
            ("How do no-shows get cut?", "SMS confirmations plus monitoring of which channels each guest actually replies to, then timing reminders accordingly."),
            ("What if the board is full?", "Callers and guests land on the waitlist and are messaged automatically when something opens."),
            ("Does it sync with my current setup?", "It replaces your manual book and can import from most reservation sheets and legacy booking tools."),
        ],
        "testimonial": ("Peak-hour calls stopped going to voicemail and our Friday covers jumped by a third. The front-of-house breathed again.", "Sofia Reyes", "Owner, Casa Reyes"),
        "compare": {
            "cols": ["TableHost AI", "Host on the phone"],
            "rows": [
                ("Peak-hour calls", "Answered instantly", "Hold music or voicemail"),
                ("Gone tables", "Refilled by waitlist", "Lost to the night"),
                ("No-shows", "SMS confirmations", "Hope"),
                ("Board accuracy", "Live, every turn", "Mental model"),
                ("Front-of-house", "Focused on guests", "On the phone"),
            ],
        },
    },
    "insightpipe-ai": {
        "problem": {
            "heading": "Every team runs its own numbers, and none of them agree",
            "body": "The sales report disagrees with finance, finance disagrees with the dashboard, and someone rebuilds it all in spreadsheets every Monday. The data is there — it just will not move itself.",
            "icon": "Activity",
        },
        "personas": [
            ("Activity", "Data Teams", "Analysts who spend more time moving data than answering questions about it."),
            ("Layers", "Ops Leads", "Operations managers who reconcile systems by hand every reporting cycle."),
            ("BarChart3", "BI Analysts", "Analysts who want clean feeds, on time, so dashboards stay honest."),
        ],
        "fdescs": [
            "Ingestion from spreadsheets, databases and SaaS tools without a line of pipeline code.",
            "Cross-system reconciliation that flags mismatches instead of papering over them.",
            "Scheduled reporting that lands in your inbox on the exact day the team expects it.",
            "Anomaly detection on every pipeline, alerting before broken numbers reach a deck.",
        ],
        "pricing": [
            ("Starter", "$49", "/mo", "For a single reporting source.", ["3 sources", "Scheduled reports", "Email delivery"], False),
            ("Pro", "$149", "/mo", "For teams that live in spreadsheets today.", ["Everything in Starter", "15 sources", "Reconciliation engine", "Anomaly alerts"], True),
            ("Enterprise", "$499", "/mo", "For multi-team data operations.", ["Everything in Pro", "Unlimited sources", "SSO & audit log", "Priority support"], False),
        ],
        "faq": [
            ("Do I need a data engineer?", "No. Sources connect through config screens — the pipeline runs on its own after setup."),
            ("What happens when two systems disagree?", "The mismatch is surfaced with both records attached, and a rule decides which wins for the report."),
            ("How reliable are the scheduled runs?", "Every run has pass or fail states, retries and alerts. We measure it above 99.9%."),
            ("Can it write back to my tools?", "On Pro and Enterprise plans, calculated fields and reconciled records can sync back to your sources."),
        ],
        "testimonial": ("Our Monday reconciliation ritual is gone. The same report that took a day now builds itself and lands on time.", "Amara Nnaji", "Revenue ops lead, 4-system stack"),
        "compare": {
            "cols": ["InsightPipe", "Manual spreadsheet pipelines"],
            "rows": [
                ("Setup", "Config screens", "Weeks of ETL code"),
                ("Reconciliation", "Automatic with flags", "VLOOKUP archaeology"),
                ("Schedules", "On-time or alerted", "Friday afternoon scramble"),
                ("Sources", "Dozens connected", "Two or three at most"),
                ("Audit", "Every run logged", "Whatever was saved"),
            ],
        },
    },
    "claimflow-ai": {
        "problem": {
            "heading": "Claim intake is where weeks quietly evaporate",
            "body": "Claims stall on missing documents, coverage questions and back-and-forth calls. The adjustment is often the easy part — it is the assembly of the file that takes forever.",
            "icon": "ShieldCheck",
        },
        "personas": [
            ("ShieldCheck", "Claims Teams", "Teams whose backlog is mostly partially complete intake files."),
            ("Clock", "Adjusters", "Adjusters burning calendar days chasing documents instead of investigating claims."),
            ("Layers", "Insurers", "Insurers whose cycle time is judged by how fast intake gets out of its own way."),
        ],
        "fdescs": [
            "Guided document collection that asks for the next correct item, in the right order.",
            "Coverage triage that checks the policy and flags claims outside it before work is wasted.",
            "Completeness validation that refuses to hand an incomplete file to an adjuster.",
            "Routing with summaries and next steps so each adjuster starts mid-stride, not from zero.",
        ],
        "pricing": [
            ("Starter", "$99", "/mo", "For a small claims desk.", ["Up to 100 intakes/mo", "Document collection", "Completeness checks"], False),
            ("Pro", "$299", "/mo", "For desks that need to move volume fast.", ["Everything in Starter", "500 intakes/mo", "Coverage triage", "Adjuster routing"], True),
            ("Enterprise", "$999", "/mo", "For carriers and large back offices.", ["Everything in Pro", "Unlimited intakes", "SSO & full audit trail", "Custom policy rules"], False),
        ],
        "faq": [
            ("Does it decide claims?", "No. It assembles, validates and routes them. Adjudication and payout always stay with your staff."),
            ("How does it know what documents to ask for?", "From the claim type and your policy's evidence requirements — the sequence adapts to what is still missing."),
            ("What keeps it compliant?", "Every route change and document is logged, and Enterprise plans add SSO and full audit trails."),
            ("Can it talk to legacy systems?", "Yes, via REST API and CSV intake — claims land in your existing workflow rather than a new silo."),
        ],
        "testimonial": ("Intake-to-adjuster dropped from a week-plus to about a day, and adjusters stopped chasing documents.", "François Moreau", "Claims operations director, regional insurer"),
        "compare": {
            "cols": ["ClaimFlow", "Manual claim intake"],
            "rows": [
                ("Intake to adjuster", "About a day", "A week or more"),
                ("Document chase", "Guided auto-requests", "Back-and-forth calls"),
                ("Completeness", "Validated before routing", "Discovered mid-review"),
                ("Coverage check", "Against the policy", "After work is done"),
                ("Audit trail", "Every step logged", "Email archaeology"),
            ],
        },
    },
    "onboarder-ai": {
        "problem": {
            "heading": "The first 30 days decide the next 24 months — most teams wing them",
            "body": "Signed accounts quietly churn because nobody guided the first weeks. What wins renewals is not the demo — it is what happens after. And what happens after is usually nothing.",
            "icon": "Rocket",
        },
        "personas": [
            ("Users", "Customer Success", "CS teams stretched thin who cannot personally guide every new account."),
            ("Rocket", "Founders", "Founders who watch activation rates and churn with limited hands-on time."),
            ("TrendingUp", "Product Teams", "Product teams who want usage behaviour, not vanity, driving retention."),
        ],
        "fdescs": [
            "Day-by-day onboarding playbooks triggered by real product behaviour, not signup dates.",
            "Contextual in-product tours that adapt to a user's role and feature usage.",
            "Docs-grounded answers inside the product so users never leave to get unstuck.",
            "At-risk alerts that surface quiet accounts to CS before renewal season arrives.",
        ],
        "pricing": [
            ("Starter", "$49", "/mo", "For products finding product-market fit.", ["1 product", "Behaviour-triggered playbooks", "In-product tours"], False),
            ("Growth", "$199", "/mo", "For teams scaling onboarding seriously.", ["Everything in Starter", "Docs-grounded answers", "At-risk alerts", "Up to 3 products"], True),
            ("Enterprise", "$599", "/mo", "For portfolio and multi-product PLG.", ["Everything in Growth", "Unlimited products", "SSO & segment analytics", "Dedicated onboarding"], False),
        ],
        "faq": [
            ("Does it replace the CS team?", "It handles the repeatable 90% — guided journeys, tours, answers — and alerts your team precisely when a human matters."),
            ("How are playbooks triggered?", "By watched behaviours: first login, feature use, gaps in usage. Not by calendar date."),
            ("Is the answering grounded in our docs?", "Yes, it answers from the knowledge base you point it at, with citations back to the source."),
            ("How do at-risk alerts work?", "Usage, logins and engagement converge into a risk score per account; CS sees the reasons before the churn call."),
        ],
        "testimonial": ("First-week activation rose by a third and our CS team finally gets alerts before accounts go dark, not after.", "Theo Lindqvist", "Head of Product, PLG workflow tool"),
        "compare": {
            "cols": ["Onboarder", "Generic welcome emails"],
            "rows": [
                ("Triggers", "Real product behaviour", "Day-of-signup shots"),
                ("Guidance depth", "Role-adaptive in-product", "Same email to everyone"),
                ("User questions", "Answered in product", "Send them to a help site"),
                ("At-risk accounts", "Alerted with reasons", "Spotted at renewal"),
                ("CS team workload", "Guides the 90%", "Every account manual"),
            ],
        },
    },
}

BRAND_CONTENT.update(AGENT_CONTENT)

# ---- helpers ---------------------------------------------------------------
def content(slug: str) -> dict:
    """Return the per-brand content set (safe fallback to a generic)."""
    return BRAND_CONTENT.get(slug) or BRAND_CONTENT["aurelia-estates"]