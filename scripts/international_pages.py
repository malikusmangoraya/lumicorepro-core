"""Generate industry-specific, international-standard About/Services/Pricing/Contact
pages for every project, using the brand card + industry content.

Replaces the generic SaaS boilerplate pages with on-brand, on-industry copy,
tokens, motion classes and real functionality (accordion, form).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_map import BRANDS
from industry_content import content as industry_content

GEN = Path(__file__).resolve().parent.parent / "generated-projects"


def js(s) -> str:
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def domain_of(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower()) + ".com"


def icon_import(names):
    uniq = list(dict.fromkeys(names))
    return ", ".join(uniq)


# ---------------------------------------------------------------- shared pieces
def cta_band(name: str, cta: str, cta2: str, secondary_to="/about") -> str:
    return f"""<section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 card-lift"
              data-reveal
              style={{{{ background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)', boxShadow: '0 30px 60px rgba(0,0,0,0.25)' }}}}
            >
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Ready to start with {js(name)}?
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Talk to the team, get a clear plan, and see exactly what the first step looks like.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3 text-sm font-bold transition-all duration-200 hover:-translate-y-0.5"
                  style={{{{ color: 'var(--t-primary)' }}}}
                >
                  {js(cta)} <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="{secondary_to}"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  {js(cta2)}
                </Link>
              </div>
            </div>
          </div>
        </section>"""


def hero_band(eyebrow: str, heading: str, sub: str) -> str:
    return f"""<section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              {js(eyebrow)}
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{{{ color: 'var(--t-heading)' }}}}
            >
              {js(heading)}
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              {js(sub)}
            </p>
          </div>
        </section>"""


# ------------------------------------------------------------------- About.jsx
def about_page(brand: dict) -> str:
    c = industry_content(brand["industry"])
    name = brand["name"]
    story = c["story"].replace("{name}", name)

    mission = (
        f"We exist to make {brand['industry'].replace('-', ' ')} feel effortless and worth "
        f"recommending — measured by results, retained by trust, and built to an international standard."
    )

    checks = "".join(
        f"""<li className="flex items-start gap-3" data-reveal>
                  <Check className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm font-medium" style={{{{ color: 'var(--t-heading)' }}}}>{js(v)}</span>
                </li>"""
        for v in [brand["feata"], brand["featb"], brand["featc"]]
    )

    stat_cards = "".join(
        f"""<div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                <p className="text-3xl font-black" style={{{{ color: 'var(--t-primary)' }}}}>{js(val)}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{js(lbl)}</p>
              </div>"""
        for val, lbl in [
            (brand["stat1"], brand["stat1l"]),
            (brand["stat2"], brand["stat2l"]),
            (brand["stat3"], brand["stat3l"]),
            (brand["stat4"], brand["stat4l"]),
        ]
    )

    pillar_cards = "".join(
        f"""<div className="card-panel p-7 h-full card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
                >
                  <{ic} className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{{{ color: 'var(--t-heading)' }}}}>{js(title)}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{js(desc)}</p>
              </div>"""
        for ic, title, desc in c["pillars"]
    )

    icons = [p[0] for p in c["pillars"]] + ["Check", "ArrowRight"]
    return f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ {icon_import(icons)} }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const stats = [
  {{ value: '{js(brand['stat1'])}', label: '{js(brand['stat1l'])}' }},
  {{ value: '{js(brand['stat2'])}', label: '{js(brand['stat2l'])}' }},
  {{ value: '{js(brand['stat3'])}', label: '{js(brand['stat3l'])}' }},
  {{ value: '{js(brand['stat4'])}', label: '{js(brand['stat4l'])}' }},
];

export default function About() {{
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        {hero_band(brand['eyebrow'], brand['tagline'], brand['sub'])}

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
            <div>
              <h2 className="section-heading">A brand built on standards</h2>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">
                <strong style={{{{ color: 'var(--t-heading)' }}}}>{js(name)}</strong> {js(story)}
              </p>
              <p className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed">{js(mission)}</p>
              <ul className="mt-8 space-y-3">
                {checks}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {stat_cards}
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">What guides us</p>
              <h2 className="section-heading">Principles we do not trade away</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {pillar_cards}
            </div>
          </div>
        </section>

        {cta_band(name, brand['cta'], brand['cta2'], '/services')}
      </main>
      <Footer />
    </div>
  );
}}
"""


# ---------------------------------------------------------------- Services.jsx
def services_page(brand: dict) -> str:
    c = industry_content(brand["industry"])
    name = brand["name"]

    service_cards = "".join(
        f"""<div className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                  style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
                >
                  <{ic} className="h-6 w-6" />
                </span>
                <h3 className="font-bold text-lg mb-2" style={{{{ color: 'var(--t-heading)' }}}}>{js(title)}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed grow">{js(desc)}</p>
                <Link to="/contact" className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                  Enquire <ArrowRight className="h-4 w-4" />
                </Link>
              </div>"""
        for ic, title, desc in c["services"]
    )

    step_cards = "".join(
        f"""<div className="text-center card-lift" data-reveal>
                <span
                  className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                  style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
                >
                  <{ic} className="h-7 w-7" />
                </span>
                <h3 className="font-bold mb-1" style={{{{ color: 'var(--t-heading)' }}}}>{i + 1}. {js(title)}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs mx-auto">{js(desc)}</p>
              </div>"""
        for i, (ic, title, desc) in enumerate(c["process"])
    )

    faq_items = ",\n  ".join(
        f"{{ q: '{js(q)}', a: '{js(a)}' }}" for q, a in c["faq"]
    )

    icons = [s[0] for s in c["services"]] + [p[0] for p in c["process"]] + ["ArrowRight", "Check"]
    return f"""import React, {{ useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import {{ {icon_import(icons)} }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const faqs = [
  {faq_items},
];

export default function Services() {{
  const [open, setOpen] = useState(0);

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        {hero_band('WHAT WE DO', f"{brand['name']}, in full", brand['sub'])}

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {service_cards}
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">How it works</p>
              <h2 className="section-heading">A process built to remove surprises</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
              {step_cards}
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-3xl mx-auto px-6">
            <div className="max-w-2xl mb-10">
              <p className="section-eyebrow">Questions</p>
              <h2 className="section-heading">Answers before you ask</h2>
            </div>
            <div className="space-y-3">
              {{faqs.map((f, i) => (
                <div key={{i}} className="card-panel overflow-hidden">
                  <button
                    type="button"
                    onClick={{() => setOpen(open === i ? -1 : i)}}
                    aria-expanded={{open === i}}
                    className="w-full flex items-center justify-between gap-4 p-5 text-left"
                  >
                    <span className="font-semibold text-sm" style={{{{ color: 'var(--t-heading)' }}}}>{{f.q}}</span>
                    <span className="text-primary text-xl leading-none">{{open === i ? '−' : '+'}}</span>
                  </button>
                  {{open === i && (
                    <p className="px-5 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{{f.a}}</p>
                  )}}
                </div>
              ))}}
            </div>
          </div>
        </section>

        {cta_band(name, brand['cta'], brand['cta2'], '/pricing')}
      </main>
      <Footer />
    </div>
  );
}}
"""


# ----------------------------------------------------------------- Pricing.jsx
def pricing_page(brand: dict) -> str:
    c = industry_content(brand["industry"])
    name = brand["name"]

    tiers = "".join(
        _tier(name_, price, period, tagline, feats, featured, brand)
        for name_, price, period, tagline, feats, featured in c["pricing"]
    )

    return f"""import React from 'react';
import {{ Link }} from 'react-router-dom';
import {{ Check, ArrowRight, ShieldCheck }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Pricing() {{
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        {hero_band('PRICING', 'Clear pricing, no surprises', f"Choose the {brand['industry'].replace('-', ' ')} plan that fits — upgrade, downgrade or cancel at any time.")}

        <section className="pb-16">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
            {tiers}
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-4xl mx-auto px-6">
            <div className="glass-md rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-4 justify-center text-center sm:text-left" data-reveal>
              <ShieldCheck className="h-6 w-6 text-primary shrink-0" />
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Prices shown in USD and exclude local taxes. Every plan is backed by a
                straightforward guarantee — if it is not right for you, we will make it right.
              </p>
            </div>
          </div>
        </section>

        {cta_band(name, brand['cta'], brand['cta2'], '/services')}
      </main>
      <Footer />
    </div>
  );
}}
"""


def _tier(tname, price, period, tagline, feats, featured, brand):
    feats_js = "".join(
        f"""<li className="flex items-start gap-3">
                  <Check className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                  <span className="text-sm text-slate-600 dark:text-slate-300">{js(f)}</span>
                </li>"""
        for f in feats
    )
    featured_cls = "card-panel p-8 h-full flex flex-col relative card-lift ring-2 ring-[var(--t-primary)]" if featured else "card-panel p-8 h-full flex flex-col card-lift"
    badge = (
        """<span
                className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full px-3 py-1 text-xs font-bold text-white"
                style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
              >
                Most popular
              </span>"""
        if featured
        else ""
    )
    return f"""<div className="{featured_cls}" data-reveal>
              {badge}
              <p className="section-eyebrow">{js(tname)}</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black tracking-tight" style={{{{ color: 'var(--t-heading)' }}}}>{js(price)}</span>
                <span className="text-sm text-slate-500 dark:text-slate-400 mb-1">{js(period)}</span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{js(tagline)}</p>
              <ul className="mt-6 space-y-3 grow">
                {feats_js}
              </ul>
              <Link
                to="/contact"
                className="{('btn-primary' if featured else 'btn-outline')} mt-8 inline-flex items-center justify-center gap-2 text-sm px-6 py-3"
              >
                {js(brand['cta'])} <ArrowRight className="h-4 w-4" />
              </Link>
            </div>"""


# ----------------------------------------------------------------- Contact.jsx
def contact_page(brand: dict) -> str:
    c = industry_content(brand["industry"])
    name = brand["name"]
    email = c["contact"]["email"] + domain_of(name)

    details = "".join(
        f"""<div className="flex items-start gap-4" data-reveal>
                <span
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
                >
                  <{ic} className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">{js(label)}</p>
                  <p className="text-sm font-medium" style={{{{ color: 'var(--t-heading)' }}}}>{js(val)}</p>
                </div>
              </div>"""
        for ic, label, val in [
            ("MapPin", "Visit", c["contact"]["address"]),
            ("Phone", "Call", c["contact"]["phone"]),
            ("Mail", "Email", email),
            ("Clock", "Hours", c["contact"]["hours"]),
        ]
    )

    return f"""import React, {{ useState }} from 'react';
import {{ Mail, Phone, MapPin, Clock, Send, CheckCircle2 }} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Contact() {{
  const [form, setForm] = useState({{ name: '', email: '', message: '' }});
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => setForm({{ ...form, [e.target.name]: e.target.value }});
  const handleSubmit = (e) => {{
    e.preventDefault();
    setSubmitted(true);
  }};

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        {hero_band('CONTACT', 'Start a conversation', f"Tell us what you need and the {js(name)} team will reply within one business day.")}

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-5 gap-12">
            <div className="lg:col-span-3">
              <div className="card-panel p-8" data-reveal>
                {{submitted ? (
                  <div className="text-center py-12">
                    <span
                      className="mx-auto mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                      style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
                    >
                      <CheckCircle2 className="h-7 w-7" />
                    </span>
                    <h2 className="text-2xl font-black mb-2" style={{{{ color: 'var(--t-heading)' }}}}>Message received</h2>
                    <p className="text-slate-500 dark:text-slate-400">
                      Thank you, {{form.name || 'there'}}. A member of the team will be in touch shortly.
                    </p>
                  </div>
                ) : (
                  <form onSubmit={{handleSubmit}} className="space-y-5">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium mb-1.5" style={{{{ color: 'var(--t-heading)' }}}}>Full name</label>
                      <input
                        id="name" name="name" type="text" required autoComplete="name"
                        value={{form.name}} onChange={{handleChange}}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium mb-1.5" style={{{{ color: 'var(--t-heading)' }}}}>Email</label>
                      <input
                        id="email" name="email" type="email" required autoComplete="email"
                        value={{form.email}} onChange={{handleChange}}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <div>
                      <label htmlFor="message" className="block text-sm font-medium mb-1.5" style={{{{ color: 'var(--t-heading)' }}}}>How can we help?</label>
                      <textarea
                        id="message" name="message" rows="5" required
                        value={{form.message}} onChange={{handleChange}}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <button type="submit" className="btn-primary inline-flex items-center gap-2 text-sm px-6 py-3">
                      Send message <Send className="h-4 w-4" />
                    </button>
                  </form>
                )}}
              </div>
            </div>

            <div className="lg:col-span-2 space-y-8">
              {details}
              <div className="glass-md rounded-2xl p-6" data-reveal>
                <p className="text-sm text-slate-600 dark:text-slate-300">{js(c['contact']['note'])}</p>
              </div>
              <div
                className="rounded-2xl h-40 flex items-center justify-center"
                style={{{{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}}}
              >
                <div className="text-center text-white">
                  <MapPin className="h-7 w-7 mx-auto mb-1" />
                  <p className="text-sm font-semibold">{js(c['contact']['address'])}</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}}
"""


def main() -> int:
    wanted = set(sys.argv[1:])
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    n = 0
    for proj in projects:
        brand = BRANDS.get(proj.name, BRANDS["build"])
        pages = proj / "frontend" / "src" / "pages"
        if not pages.exists():
            continue
        (pages / "About.jsx").write_text(about_page(brand), encoding="utf-8")
        (pages / "Services.jsx").write_text(services_page(brand), encoding="utf-8")
        (pages / "Pricing.jsx").write_text(pricing_page(brand), encoding="utf-8")
        (pages / "Contact.jsx").write_text(contact_page(brand), encoding="utf-8")
        n += 1
    print(f"International pages regenerated: About/Services/Pricing/Contact x {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())