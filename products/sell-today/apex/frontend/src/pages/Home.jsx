import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight, LayoutDashboard, ShieldCheck, Zap, TrendingUp, Check, Minus } from 'lucide-react';
import Navbar from '../components/Navbar';
import { Stats, Problem, Features, UseCases, Results, Testimonials, Pricing, Faq, Cta } from '../components/sections/GrowthSections';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();

  const descs = [
    'Plans that update themselves as work moves, so nobody chases a status.',
    'Invoices that chase themselves politely, on the schedule you set.',
    'One board the whole company reads, updated as the work lands.',
    'A branded space per client, with the same login they already have.',
  ];
  const features = [
    { icon: LayoutDashboard, title: 'Project Plans That Stay Current', desc: descs[0] },
    { icon: Zap, title: 'Self-Sending Invoicing', desc: descs[1] },
    { icon: TrendingUp, title: 'Team Insight Boards', desc: descs[2] },
    { icon: ShieldCheck, title: 'Client Portals', desc: descs[3] },
  ];
  const stats = [
    { value: '6 hrs', label: 'Saved every week' },
    { value: '3.1x', label: 'Faster invoicing' },
    { value: '9 days', label: 'Faster time to first value' },
    { value: '99.99%', label: 'Platform uptime' },
  ];
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">

        {/* ===== HERO: calm SaaS split, real imagery ===== */}
        <section className="relative overflow-hidden pt-14 lg:pt-0">
          <div className="absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,var(--t-primary)_0%,transparent_70%)] opacity-15" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,var(--t-accent)_0%,transparent_70%)] opacity-15" />
            <div className="absolute inset-0 bg-[url('/images/scene-4.jpg')] bg-cover bg-center bg-no-repeat scale-110" style={{ filter: 'blur(2px) grayscale(15%) brightness(0.8)' }} />
          </div>

          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="lg:col-span-6">
              <span className="section-eyebrow">
                {t('Home.modern_saas_platform', 'WORK OPERATING SYSTEM')}
              </span>
              <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
                <span style={{ color: 'var(--t-heading)' }}>The whole operation,</span>{' '}
                <span className="bg-gradient-to-r from-[var(--t-primary)] to-[var(--t-accent)] bg-clip-text text-transparent">
                  on one calm screen.
                </span>
              </h1>
              <p className="mt-6 text-lg text-slate-500 dark:text-slate-300 leading-relaxed max-w-lg">
                {t('Home.lead', 'Projects, invoices and team insight from a single workspace.')}
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm inline-flex items-center gap-2 px-6 py-3">
                  {t('Home.start_free', 'Start Free')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm inline-flex items-center gap-2 px-6 py-3">
                  {t('Home.see_demo', 'See a Live Demo')}
                </Link>
              </div>

              <dl className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-5 border-t border-[var(--t-border)] pt-7">
                {stats.slice(0, 4).map((s) => (
                  <div key={s.value} className="data-[revealed=false]:opacity-0" data-reveal>
                    <dt className="sr-only">{s.label}</dt>
                    <dd className="text-2xl font-extrabold" style={{ color: 'var(--t-primary)' }}>
                      {s.value}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{s.label}</p>
                  </div>
                ))}
              </dl>
            </div>

            <div className="lg:col-span-6" data-reveal>
              <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 dark:ring-white/5">
                <img
                  src="/images/scene-1.jpg"
                  alt="Calm dashboard workspace from Apex Digital"
                  loading="eager"
                  className="w-full h-full object-cover"
                  style={{ maxHeight: '480px' }}
                />
                <div className="absolute bottom-0 left-0 right-0 p-5 bg-gradient-to-t from-black/60 to-transparent">
                  <div className="flex items-center gap-3 text-white">
                    <div className="h-10 w-10 rounded-full bg-[var(--t-primary)] flex items-center justify-center text-white text-sm font-bold">
                      AD
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Apex Digital</p>
                      <p className="text-xs opacity-80">One calm screen</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-4 -left-4 rounded-xl bg-surface/90 backdrop-blur p-4 shadow-lg border border-[var(--t-border)] flex items-center gap-3 data-[revealed=false]:opacity-0" data-reveal>
                <div className="h-10 w-10 rounded-lg bg-[var(--t-primary)] flex items-center justify-center text-white">
                  <LayoutDashboard className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--t-heading)' }}>Everything in one place</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Projects + invoices + insight</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <Stats />
        <Problem />

        {/* ===== BRAND BAR ===== */}
        <section className="border-y border-[var(--t-border)] bg-surface/60 py-10">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
              <span>{t('Home.as_seen_in', 'As seen in')}</span>
              {['Forbes', 'Bloomberg', 'The Times', 'DesignWeek', 'Monocle'].map((m) => (
                <span key={m} className="opacity-80">{t(`Home.${m.toLowerCase()}`, m)}</span>
              ))}
            </div>
          </div>
        </section>

        {/* ===== WHY CHOOSE ===== */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">{t('Home.what_we_offer', 'What We Offer')}</span>
              <h2 className="section-heading">{t('Home.why_choose_apex_digital', 'Why choose Apex Digital?')}</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: LayoutDashboard, title: 'Intuitive Dashboard', desc: 'Real-time metrics and management at your fingertips', img: '/images/scene-6.jpg' },
                { icon: ShieldCheck, title: 'Secure by Default', desc: 'Enterprise authentication, encryption, and audit logging', img: '/images/scene-5.jpg' },
                { icon: Zap, title: 'Performance First', desc: 'Optimized for speed, SEO, and Core Web Vitals', img: '/images/scene-2.jpg' },
                { icon: TrendingUp, title: 'Scalable Architecture', desc: 'Built to handle growth from prototype to production', img: '/images/scene-3.jpg' },
              ].map((f, i) => (
                <div key={i} className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                  <div className="p-6">
                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg" style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}>
                      <f.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--t-heading)' }}>
                      {f.title}
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      {f.desc}
                    </p>
                  </div>
                  <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                    <img
                      src={f.img}
                      alt={`${f.title} — feature preview`}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 flex items-end p-3" style={{ background: 'linear-gradient(to top, rgba(2,6,23,.4), transparent)' }} />
                  </div>
                </div>
              ))}
            </div>
            <img
              src="/images/scene-6.jpg"
              alt="Apex Digital features"
              className="w-full h-52 object-cover rounded-xl"
              loading="lazy"
            />
          </div>
        </section>

        {/* ===== STATS STRIP ===== */}
        <section className="py-16 px-6">
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: '99.99%', label: t('Home.uptime', 'Uptime') },
              { value: '<2s', label: t('Home.load_time', 'Load Time') },
              { value: '10K+', label: t('Home.users', 'Users') },
              { value: '4.9/5', label: t('Home.rating', 'Rating') },
            ].map((s, i) => (
              <div key={i} className="text-center data-[revealed=false]:opacity-0" data-reveal>
                <div className="text-3xl sm:text-4xl font-extrabold mb-1" style={{ color: 'var(--t-primary)' }}>
                  {s.value}
                </div>
                <div className="text-sm text-slate-500 dark:text-slate-400">{s.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ===== PLATFORM SHOWCASE ===== */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <img
                src="/images/scene-1.jpg"
                alt="Apex Digital platform showcase"
                className="w-full rounded-2xl object-cover shadow-xl"
                style={{ maxHeight: 420 }}
                loading="lazy"
              />
            </div>
            <div>
              <span className="section-eyebrow">{t('Home.platform_preview', 'Platform Preview')}</span>
              <h2 className="section-heading mb-4">{t('Home.built_for_the_modern_growth', 'Built for the modern growth')}</h2>
              <p className="text-slate-500 dark:text-slate-300 leading-relaxed mb-6">
                Every detail is engineered for performance, scalability, and a flawless user
                experience — from first click to everyday operations.
              </p>
              <Link to="/about" className="btn-primary inline-flex items-center gap-2">
                Learn More <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* ===== CTA ===== */}
        <section className="py-20 px-6">
          <div className="max-w-3xl mx-auto text-center rounded-2xl p-12 shadow-2xl ring-1 ring-white/10 dark:ring-white/5" style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }} data-reveal>
            <div className="absolute inset-0 -z-10 opacity-10" style={{
              backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 50%, white 1px, transparent 1px)',
              backgroundSize: '24px 24px'
            }} />

            <h2 className="text-3xl font-extrabold text-white mb-4">
              {t('Home.ready_to_transform_your_business', 'Ready to Transform Your Business?')}
            </h2>
            <p className="text-white/70 mb-8">
              Trusted by teams who chose Apex Digital to do more with less.
            </p>
            <Link
              to="/contact"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3 font-semibold transition-all hover:shadow-xl"
              style={{ color: 'var(--t-primary)' }}
            >
              Start Free Trial <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        <Features />
        <UseCases />
        <Results />
        <Testimonials />
        <Pricing />
        <Faq />
        <Cta />

      </main>
      <Footer />
    </div>
  );
}
