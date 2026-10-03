"""Generate a bespoke, international-standard Home.jsx for every project.

v7.11: full 2026 anatomy with per-brand unique content (43/43 bespoke sets from
brand_content.py): hero -> proof -> problem reframe -> features -> personas ->
stats -> pricing teaser -> comparison -> testimonial -> FAQ -> final CTA.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand_map import BRANDS
from brand_content import BRAND_CONTENT


def brand_content_for(slug: str, brand_name: str) -> dict:
    """Resolve the per-brand content set from a project slug + brand name.

    BRANDS is keyed by directory slug; BRAND_CONTENT is keyed by a slugified
    brand name (e.g. 'Ember & Salt' -> 'ember-salt', 'TerraVista' -> 'terravista').
    """
    key = re.sub(r"[^a-z0-9]+", "-", brand_name.lower()).strip("-")
    return BRAND_CONTENT.get(key, BRAND_CONTENT["aurelia-estates"])

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-agent"))
from agent.intelligence.design_decision_engine import decide_design

GEN = Path(__file__).resolve().parent.parent / "generated-projects"

FEATURE_ICON_N = {
    "fashion": ["Sparkles", "ShieldCheck", "Award", "HeartHandshake"],
    "food": ["Zap", "Star", "Layers", "HeartHandshake"],
    "real-estate": ["MapPin", "Building2", "ShieldCheck", "TrendingUp"],
    "fintech": ["BarChart3", "ShieldCheck", "TrendingUp", "Lock"],
    "electronics": ["Cpu", "Zap", "Layers", "Award"],
    "ecommerce": ["ShoppingBag", "Star", "Truck", "ShieldCheck"],
    "hospitality": ["MapPin", "Star", "Users", "Sparkles"],
    "portfolio": ["Layers", "Sparkles", "Zap", "Award"],
    "sports": ["Zap", "TrendingUp", "Users", "Award"],
    "entertainment": ["Sparkles", "Users", "Zap", "Star"],
    "education": ["BookOpen", "Users", "Award", "Zap"],
    "healthcare": ["HeartPulse", "ShieldCheck", "Users", "Clock"],
    "saas": ["LayoutDashboard", "Zap", "ShieldCheck", "TrendingUp"],
}

TEMPLATE = """import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { __ICONS__ } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const [openFaq, setOpenFaq] = useState(0);
  const descs = ['__D1__', '__D2__', '__D3__', '__D4__'];
  const features = [
    { icon: __J1__, title: '__F1__', desc: descs[0] },
    { icon: __J2__, title: '__F2__', desc: descs[1] },
    { icon: __J3__, title: '__F3__', desc: descs[2] },
    { icon: __J4__, title: '__F4__', desc: descs[3] },
  ];
  const stats = [
    { value: '__S1__', label: '__S1L__' },
    { value: '__S2__', label: '__S2L__' },
    { value: '__S3__', label: '__S3L__' },
    { value: '__S4__', label: '__S4L__' },
  ];
  const values = ['__V1__', '__V2__', '__V3__'];

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-20 lg:pb-28">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="__HERO_GRID__">
            <div className="__HERO_CONTENT__">
              <span className="inline-flex items-center gap-2 section-eyebrow">
                <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
                __EYEBROW__
              </span>
              <h1
                className="__HERO_H1__ mb-6 mt-3"
                style={{
                  color: 'var(--t-heading)',
                  background: 'linear-gradient(115deg, var(--t-heading) 40%, var(--t-primary) 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                __HERO_T__
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-8 max-w-xl">
                __HERO_SUB__
              </p>
              <div className="__CTA_WRAP__">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  __CTA_A__ <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  __CTA_B__
                </Link>
              </div>
              <ul className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                <li className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <CheckCircle2 className="h-4 w-4 text-primary" /> Internationally ranked, 4.9/5
                </li>
                <li className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                  <CheckCircle2 className="h-4 w-4 text-primary" /> Trusted in 40+ countries
                </li>
              </ul>
            </div>
            <div className="hidden lg:flex flex-col gap-6">
              <div className="glass-md rounded-2xl p-8 card-lift" data-reveal>
                <p className="section-eyebrow mb-3">Why __NAME__</p>
                <p className="text-4xl font-black tracking-tight" style={{ color: 'var(--t-heading)' }}>
                  __S1__
                  <span className="text-xl font-bold text-primary"> __S1L__</span>
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">__HERO_SUB__</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>__S2__</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">__S2L__</p>
                </div>
                <div className="glass-md rounded-2xl p-6 card-lift" data-reveal>
                  <p className="text-3xl font-black" style={{ color: 'var(--t-primary)' }}>__S3__</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">__S3L__</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
              <span>As seen in</span>
              <span className="opacity-80">Forbes</span>
              <span className="opacity-80">Bloomberg</span>
              <span className="opacity-80">The Times</span>
              <span className="opacity-80">DesignWeek</span>
              <span className="opacity-80">Monocle</span>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-eyebrow">The problem</p>
              <h2 className="section-heading mb-4">__PROBLEM_HEAD__</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed max-w-xl">
                __PROBLEM_BODY__
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="glass-md rounded-2xl p-8 card-lift max-w-sm w-full" data-reveal>
                <span
                  className="inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white mb-5"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <__PROBLEM_ICON__ className="h-7 w-7" />
                </span>
                <p className="font-bold text-lg" style={{ color: 'var(--t-heading)' }}>
                  __NAME__ fixes this
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  __HERO_SUB__
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">Capabilities</p>
              <h2 className="section-heading">What working with __NAME__ feels like</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Four disciplines, one standard: international, uncompromising, and completely yours.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, i) => (
                <div key={i} className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>
                  <span
                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"
                    style={{
                      background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))',
                      boxShadow: '0 10px 24px rgba(0,0,0,0.18)',
                    }}
                  >
                    <feature.icon className="h-6 w-6" />
                  </span>
                  <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--t-heading)' }}>
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">Who it is for</p>
              <h2 className="section-heading">Made for people like you</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                However you come to __NAME__, the standard is the same.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              __PERSONA_CARDS__
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <p className="section-eyebrow">By the numbers</p>
              <h2 className="section-heading">Results you can put in a report</h2>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
              {stats.map((stat, i) => (
                <div key={i} className="text-center card-lift" data-reveal>
                  <p
                    className="text-4xl lg:text-5xl font-black tracking-tight"
                    style={{
                      color: 'var(--t-primary)',
                      background: 'linear-gradient(115deg, var(--t-primary), var(--t-accent))',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    {stat.value}
                  </p>
                  <p className="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 lg:py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="max-w-2xl mb-14">
              <p className="section-eyebrow">Pricing</p>
              <h2 className="section-heading">Clear pricing, no surprises</h2>
              <p className="mt-3 text-slate-500 dark:text-slate-400">
                Start light, upgrade when the results justify it.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              __PRICING_CARDS__
            </div>
            <div className="mt-10 text-center">
              <Link to="/pricing" className="btn-outline text-sm px-7 py-3">
                Compare all plans <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        __COMPARISON__

        <section className="py-20 lg:py-28">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            <div className="relative">
              <div
                className="absolute inset-0 -z-10 rounded-3xl opacity-40"
                style={{
                  background:
                    'radial-gradient(circle at 30% 30%, var(--t-primary), transparent 55%), radial-gradient(circle at 70% 70%, var(--t-accent), transparent 55%)',
                }}
              />
              <div className="glass-md rounded-3xl p-10" data-reveal>
                <span
                  className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-6"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Quote className="h-6 w-6" />
                </span>
                <blockquote
                  className="text-xl font-medium leading-relaxed mb-6"
                  style={{ color: 'var(--t-heading)' }}
                >
                  __T_QUOTE__
                </blockquote>
                <div className="flex items-center gap-4">
                  <span
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white text-sm font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                  >
                    __T_INITIALS__
                  </span>
                  <div>
                    <p className="font-semibold text-sm">__T_NAME__</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">__T_ROLE__</p>
                  </div>
                  <span className="ml-auto flex items-center gap-0.5 text-amber-500">
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                    <Star className="h-4 w-4 fill-current" />
                  </span>
                </div>
              </div>
            </div>
            <div>
              <p className="section-eyebrow">The __NAME__ difference</p>
              <h2 className="section-heading">Crafted for the people you serve</h2>
              <ul className="mt-8 space-y-6">
                {values.map((value, i) => (
                  <li key={i} className="flex items-start gap-4 card-lift" data-reveal>
                    <span
                      className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                      style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                    >
                      <Check className="h-4 w-4" />
                    </span>
                    <p className="text-base font-medium" style={{ color: 'var(--t-heading)' }}>
                      {value}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="py-20 bg-surface border-y border-[var(--t-border)]">
          <div className="max-w-3xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <p className="section-eyebrow">FAQ</p>
              <h2 className="section-heading">Questions, answered</h2>
            </div>
            <div className="space-y-4">
              __FAQ_ITEMS__
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="max-w-5xl mx-auto px-6">
            <div
              className="rounded-3xl overflow-hidden text-center px-6 py-16 card-lift"
              data-reveal
              style={{
                background: 'linear-gradient(125deg, var(--t-primary) 0%, var(--t-accent) 100%)',
                boxShadow: '0 30px 60px rgba(0,0,0,0.25)',
              }}
            >
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-3">
                Start the conversation
              </h2>
              <p className="text-white/85 max-w-xl mx-auto mb-8">
                Tell us where you want to go — we will map the route, the milestones, and the
                first step today.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3 text-sm font-bold transition-all duration-200 hover:-translate-y-0.5"
                  style={{ color: 'var(--t-primary)' }}
                >
                  __CTA_A__ <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/about"
                  className="inline-flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-bold text-white border border-white/40 transition-all duration-200 hover:bg-white/10"
                >
                  __CTA_B__
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
"""


def build_index(proj: Path, brand: dict, industry: str) -> str:
    hero_key = "typographic_hero"
    try:
        dec = decide_design({"industry": industry})
        hero_key = dec.get("hero") or hero_key
    except Exception as e:
        print(f"  decide_design warn {proj.name}: {e}")

    center = hero_key in ("minimal_composition", "cinematic_video")
    hero_h1 = {
        "typographic_hero": "text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]",
        "minimal_composition": "text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.98]",
        "cinematic_video": "text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.02]",
    }.get(hero_key, "text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]")

    hero_grid = "max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
    hero_content = "max-w-2xl"
    cta_wrap = "flex flex-wrap gap-4"
    if center:
        hero_grid = "max-w-7xl mx-auto px-6 flex flex-col items-center text-center"
        hero_content = "max-w-3xl mx-auto flex flex-col items-center"
        cta_wrap = "flex flex-wrap gap-4 justify-center"

    feats = FEATURE_ICON_N.get(industry, FEATURE_ICON_N["saas"])
    j1, j2, j3, j4 = feats

    # ---- v7.11 anatomy: per-brand unique content (43 bespoke sets) ----
    name = brand["name"]
    bc = brand_content_for(proj.name, name)
    prob = bc["problem"]
    pers = bc["personas"][:3]
    fdescs = bc["fdescs"][:4]
    pricing_rows = bc["pricing"][:3]
    faq_rows = bc["faq"][:4]
    t_quote, t_name, t_role = bc["testimonial"]
    cmp_cols = bc["compare"]["cols"]
    cmp_rows = bc["compare"]["rows"]

    esc = lambda s: str(s).replace("\\", "\\\\").replace("'", "\\'")
    pct = lambda s: str(s).replace("%", "%%")
    escpct = lambda s: esc(pct(s))

    persona_cards = "\n".join(
        render_persona(i, icon, pct(title), pct(desc))
        for i, (icon, title, desc) in enumerate(pers)
    )
    pricing_cards = "\n".join(
        render_pricing(i, pct(r[0]), pct(r[1]), pct(r[2]), pct(r[3]), [pct(f) for f in r[4][:3]], r[5])
        for i, r in enumerate(pricing_rows)
    )
    faq_items = "".join(render_faq(i, pct(q), pct(a)) for i, (q, a) in enumerate(faq_rows))
    compare_block = render_compare(
        ["", pct(cmp_cols[0]), pct(cmp_cols[1])],
        [(pct(a), pct(b), pct(c)) for a, b, c in cmp_rows],
    )
    initials = "".join(w[0] for w in t_name.split()[:2]).upper()

    base_icons = [j1, j2, j3, j4, "Quote", "Star", "ArrowRight", "CheckCircle2",
                  "Check", "Plus", "Minus", prob["icon"]]
    for icon, _t, _d in pers:
        base_icons.append(icon)
    icons = list(dict.fromkeys(base_icons))

    return (
        TEMPLATE.replace("__ICONS__", ", ".join(icons))
        .replace("__J1__", j1).replace("__J2__", j2)
        .replace("__J3__", j3).replace("__J4__", j4)
        .replace("__F1__", esc(brand["feat1"])).replace("__F2__", esc(brand["feat2"]))
        .replace("__F3__", esc(brand["feat3"])).replace("__F4__", esc(brand["feat4"]))
        .replace("__D1__", escpct(fdescs[0])).replace("__D2__", escpct(fdescs[1]))
        .replace("__D3__", escpct(fdescs[2])).replace("__D4__", escpct(fdescs[3]))
        .replace("__S1__", esc(brand["stat1"])).replace("__S2__", esc(brand["stat2"]))
        .replace("__S3__", esc(brand["stat3"])).replace("__S4__", esc(brand["stat4"]))
        .replace("__S1L__", esc(brand["stat1l"])).replace("__S2L__", esc(brand["stat2l"]))
        .replace("__S3L__", esc(brand["stat3l"])).replace("__S4L__", esc(brand["stat4l"]))
        .replace("__V1__", esc(brand["feata"])).replace("__V2__", esc(brand["featb"]))
        .replace("__V3__", esc(brand["featc"]))
        .replace("__NAME__", pct(name))
        .replace("__EYEBROW__", pct(brand["eyebrow"]))
        .replace("__HERO_T__", pct(brand["hero"]))
        .replace("__HERO_SUB__", pct(brand["sub"]))
        .replace("__CTA_A__", pct(brand["cta"]))
        .replace("__CTA_B__", pct(brand["cta2"]))
        .replace("__HERO_GRID__", hero_grid)
        .replace("__HERO_CONTENT__", hero_content)
        .replace("__CTA_WRAP__", cta_wrap)
        .replace("__HERO_H1__", hero_h1)
        .replace("__PROBLEM_HEAD__", pct(prob["heading"]))
        .replace("__PROBLEM_BODY__", pct(prob["body"]))
        .replace("__PROBLEM_ICON__", prob["icon"])
        .replace("__PERSONA_CARDS__", persona_cards)
        .replace("__PRICING_CARDS__", pricing_cards)
        .replace("__COMPARISON__", compare_block)
        .replace("__T_QUOTE__", pct(t_quote))
        .replace("__T_NAME__", pct(t_name))
        .replace("__T_ROLE__", pct(t_role))
        .replace("__T_INITIALS__", initials)
        .replace("__FAQ_ITEMS__", faq_items)
    )


def render_persona(i: int, icon: str, title: str, desc: str) -> str:
    return (
        '                <div key="%s" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal>\n'
        '                  <span\n'
        '                    className="inline-flex h-12 w-12 items-center justify-center rounded-xl text-white mb-5"\n'
        "                    style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}\n"
        '                  >\n'
        '                    <%s className="h-6 w-6" />\n'
        '                  </span>\n'
        '                  <h3 className="font-bold text-lg mb-2" style={{"color": "var(--t-heading)"}}>%s</h3>\n'
        '                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">%s</p>\n'
        '                </div>'
    ) % (i, icon, title, desc)


def render_pricing(i: int, pname: str, price: str, per: str, blurb: str, feats: list, featured: bool) -> str:
    popular = (
        '                    <span\n'
        '                      className="mb-4 self-start rounded-full px-3 py-1 text-[11px] font-bold text-white"\n'
        "                      style={{ background: 'var(--t-primary)' }}\n"
        '                    >\n'
        '                      Most popular\n'
        '                    </span>\n'
    ) if featured else ""
    rows = "\n".join(
        '                    <li className="flex items-center gap-2">\n'
        '                      <Check className="h-4 w-4 text-primary shrink-0" />\n'
        '                      %s\n'
        '                    </li>' % f
        for f in feats
    )
    border = "border: '2px solid var(--t-primary)'" if featured else "border: '1px solid var(--t-border)'"
    return (
        '                <div key="%s" className="card-panel p-7 h-full flex flex-col card-lift" data-reveal style={{%s}}>\n'
        '%s'
        '                  <h3 className="font-bold text-lg" style={{"color": "var(--t-heading)"}}>%s</h3>\n'
        '                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">%s</p>\n'
        '                  <p className="mt-4 text-3xl font-black tracking-tight" style={{"color": "var(--t-primary)"}}>\n'
        '                    %s <span className="text-sm font-semibold text-slate-400">/ %s</span>\n'
        '                  </p>\n'
        '                  <ul className="mt-6 flex-1 space-y-2 text-sm text-slate-500 dark:text-slate-400">\n'
        '%s\n'
        '                  </ul>\n'
        '                  <Link to="/pricing" className="btn-outline mt-6 text-sm w-full text-center">\n'
        '                    View plan\n'
        '                  </Link>\n'
        '                </div>'
    ) % (i, border, popular, pname, blurb, price, per, rows)


def render_faq(i: int, q: str, a: str) -> str:
    return (
        '\n              <div key="%s" className="card-panel overflow-hidden" data-reveal>\n'
        '                <button\n'
        '                  type="button"\n'
        '                  onClick={() => setOpenFaq(openFaq === %s ? -1 : %s)}\n'
        '                  aria-expanded={openFaq === %s}\n'
        '                  aria-controls="faq-panel-%s"\n'
        '                  className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"\n'
        '                >\n'
        '                  <span className="font-semibold" style={{"color": "var(--t-heading)"}}>%s</span>\n'
        '                  {openFaq === %s ? (\n'
        '                    <Minus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />\n'
        '                  ) : (\n'
        '                    <Plus className="h-5 w-5 shrink-0" style={{"color": "var(--t-primary)"}} />\n'
        '                  )}\n'
        '                </button>\n'
        '                {openFaq === %s && (\n'
        '                  <p id="faq-panel-%s" className="px-6 pb-6 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">\n'
        '                    %s\n'
        '                  </p>\n'
        '                )}\n'
        '              </div>'
    ) % (i, i, i, i, i, q, i, i, i, a)


def render_compare(cols: list, rows: list) -> str:
    """Two-column brand-vs-alternative table, per-brand rows."""
    a, b, c = cols
    head = (
        '        <section className="py-20 bg-surface border-y border-[var(--t-border)]">\n'
        '          <div className="max-w-5xl mx-auto px-6">\n'
        '            <div className="text-center max-w-2xl mx-auto mb-12">\n'
        '              <p className="section-eyebrow">Why choose us</p>\n'
        '              <h2 className="section-heading">The difference, side by side</h2>\n'
        '            </div>\n'
        '            <div className="card-panel overflow-hidden" data-reveal>\n'
        '              <table className="w-full text-left text-sm">\n'
        '                <thead>\n'
        '                  <tr className="border-b border-[var(--t-border)]">\n'
        '                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">%s</th>\n'
        '                    <th className="px-5 py-4 text-base font-bold" style={{"color": "var(--t-primary)"}}>%s</th>\n'
        '                    <th className="px-5 py-4 font-semibold text-slate-500 dark:text-slate-400">%s</th>\n'
        '                  </tr>\n'
        '                </thead>\n'
        '                <tbody>\n'
    ) % (a, b, c)
    body = "\n".join(
        '                  <tr className="border-b border-[var(--t-border)] last:border-0">\n'
        '                    <td className="px-5 py-4 font-medium" style={{"color": "var(--t-heading)"}}>%s</td>\n'
        '                    <td className="px-5 py-4">\n'
        '                      <span className="inline-flex items-start gap-2 font-medium text-slate-700 dark:text-slate-200">\n'
        '                        <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />\n'
        '                        %s\n'
        '                      </span>\n'
        '                    </td>\n'
        '                    <td className="px-5 py-4">\n'
        '                      <span className="inline-flex items-start gap-2 text-slate-500 dark:text-slate-400">\n'
        '                        <Minus className="h-4 w-4 mt-0.5 shrink-0" />\n'
        '                        %s\n'
        '                      </span>\n'
        '                    </td>\n'
        '                  </tr>'
        % (label, ours, theirs)
        for label, ours, theirs in rows
    )
    return (
        head
        + body
        + '\n                </tbody>\n'
        + '              </table>\n'
        + '            </div>\n'
        + '          </div>\n'
        + '        </section>'
    )


def main() -> int:
    wanted = set(sys.argv[1:])
    projects = [p for p in GEN.iterdir() if (p / "frontend" / "package.json").exists()]
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    for proj in projects:
        brand = BRANDS.get(proj.name, BRANDS["build"])
        out = build_index(proj, brand, brand["industry"])
        (proj / "frontend" / "src" / "pages" / "Home.jsx").write_text(out, encoding="utf-8")
    print("Home.jsx regenerated:", len(projects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())