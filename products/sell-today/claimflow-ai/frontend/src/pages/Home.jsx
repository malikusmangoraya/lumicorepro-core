import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight, LayoutDashboard, ShieldCheck, Zap, TrendingUp , Bell, Clock, FileText, Check } from 'lucide-react';
import Navbar from '../components/Navbar';
import { Stats, Problem, Features, UseCases, Results, Testimonials, Pricing, Faq, Cta } from '../components/sections/GrowthSections';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();

  const descs = [
    'A short, plain-language form that adapts to the policy and the loss.',
    'Every submission gets a timeline the claimant can actually read.',
    'Reviewers work a queue instead of chasing email threads.',
    'Updates go out on their own, so nobody has to ask for status.',
  ];
  const features = [
    { icon: FileText, title: 'Guided Claim Intake', desc: descs[0] },
    { icon: Clock, title: 'Automatic Status Tracking', desc: descs[1] },
    { icon: ShieldCheck, title: 'Reviewer Queues', desc: descs[2] },
    { icon: Bell, title: 'Claimant Notifications', desc: descs[3] },
  ];
  const stats = [
    { value: '11 days', label: 'Faster time to decision' },
    { value: '38%', label: 'Fewer incomplete submissions' },
    { value: '2.4x', label: 'Faster reviewer throughput' },
    { value: '99.98%', label: 'Platform uptime' },
  ];
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content">
                <section className="relative overflow-hidden pt-14 lg:pt-20 pb-16 lg:pb-24">
          <div className="absolute inset-0 -z-10">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,var(--t-primary)_0%,transparent_60%)] opacity-20" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,var(--t-accent)_0%,transparent_60%)] opacity-20" />
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1586281380349-632531db7ed4?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center bg-no-repeat scale-110" style={{ filter: 'blur(2px) grayscale(20%) brightness(0.85)' }} />
          </div>
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
            <div className="lg:col-span-6">
              <span className="section-eyebrow">
                {t('Home.modern_saas_platform', t('Home.modern_saas_platform', 'CLAIMS OPERATIONS'))}
              </span>
              <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
                <span style={{ color: 'var(--t-heading)' }}>Claims intake</span>{' '}
                <span style={{ color: 'var(--t-primary)' }}>without the backlog</span>
              </h1>
              <p className="mt-6 text-lg text-slate-500 dark:text-slate-300 leading-relaxed max-w-lg">
                {t('Home.lead', t('Home.lead', 'Guided filing, automatic status tracking and reviewer queues in one place.'))}
              </p>
              <ol className="mt-9 space-y-3">
                {features.slice(0, 3).map((f, i) => (
                  <li key={f.title} className="flex items-start gap-3" data-reveal>
                    <span
                      className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                      style={{ background: 'var(--t-primary)' }}
                    >
                      {i + 1}
                    </span>
                    <span className="text-sm text-slate-600 dark:text-slate-300">{f.title}</span>
                  </li>
                ))}
              </ol>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link to="/contact" className="btn-primary text-sm px-6 py-3">
                  {t('Home.start_free', t('Home.start_free', 'Start Free'))}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline text-sm px-6 py-3">
                  {t('Home.see_demo', t('Home.see_demo', 'See a Live Demo'))}
                </Link>
              </div>
            </div>
            <div className="lg:col-span-6">
              <div className="glass-md rounded-2xl p-7 card-lift" data-reveal>
                <div className="flex items-center justify-between">
                  <p className="section-eyebrow">
                    {t('Home.live_queue', t('Home.live_queue', 'Live claim queue'))}
                  </p>
                  <span className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    {t('Home.realtime', t('Home.realtime', 'Realtime'))}
                  </span>
                </div>
                <ul className="mt-5 space-y-3">
                  {features.map((f, i) => (
                    <li
                      key={f.title}
                      className="flex items-center gap-3 rounded-xl border border-[var(--t-border)] px-4 py-3"
                    >
                      <span className="text-xs font-bold" style={{ color: 'var(--t-primary)' }}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className="text-sm text-slate-600 dark:text-slate-300">{f.title}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6 grid grid-cols-3 gap-3 border-t border-[var(--t-border)] pt-5">
                  {stats.slice(0, 3).map((s) => (
                    <div key={s.value}>
                      <p className="text-2xl font-extrabold" style={{ color: 'var(--t-primary)' }}>
                        {s.value}
                      </p>
                      <p className="text-[0.7rem] text-slate-500 dark:text-slate-400">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
        <Stats />
        <Problem />

        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">{t('Home.what_we_offer', t('Home.what_we_offer', 'What We Offer'))}</span>
              <h2 className="section-heading">Why choose Claimflow?</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                <div className="p-6">
                  <div
                    className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #374151, #dc2626)' }}
                  >
                    <LayoutDashboard className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#111827' }}>
                    Intuitive Dashboard
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Real-time metrics and management at your fingertips
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b/?auto=format&fit=crop&w=1200&q=80"
                    alt="Intuitive Dashboard — feature preview"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div
                    className="absolute inset-0 flex items-end p-3"
                    style={{ background: 'linear-gradient(to top, rgba(2,6,23,.4), transparent)' }}
                  />
                </div>
              </div>
              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                <div className="p-6">
                  <div
                    className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #374151, #dc2626)' }}
                  >
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#111827' }}>
                    Secure by Default
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Enterprise authentication, encryption, and audit logging
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1476480862126-209bfaa8edc8/?auto=format&fit=crop&w=1200&q=80"
                    alt="Secure by Default — feature preview"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div
                    className="absolute inset-0 flex items-end p-3"
                    style={{ background: 'linear-gradient(to top, rgba(2,6,23,.4), transparent)' }}
                  />
                </div>
              </div>
              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                <div className="p-6">
                  <div
                    className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #374151, #dc2626)' }}
                  >
                    <Zap className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#111827' }}>
                    Performance First
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Optimized for speed, SEO, and Core Web Vitals
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e/?auto=format&fit=crop&w=1200&q=80"
                    alt="Performance First — feature preview"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div
                    className="absolute inset-0 flex items-end p-3"
                    style={{ background: 'linear-gradient(to top, rgba(2,6,23,.4), transparent)' }}
                  />
                </div>
              </div>
              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                <div className="p-6">
                  <div
                    className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #374151, #dc2626)' }}
                  >
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#111827' }}>
                    Scalable Architecture
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Built to handle growth from prototype to production
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1586281380349-632531db7ed4/?auto=format&fit=crop&w=1200&q=80"
                    alt="Scalable Architecture — feature preview"
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div
                    className="absolute inset-0 flex items-end p-3"
                    style={{ background: 'linear-gradient(to top, rgba(2,6,23,.4), transparent)' }}
                  />
                </div>
              </div>
            </div>
            <img
              src="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b/?auto=format&fit=crop&w=1200&q=80"
              alt="Claimflow features"
              className="w-full h-52 object-cover rounded-xl"
              loading="lazy"
            />
          </div>
        </section>

        <section className="py-16 px-6">
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#374151' }}
              >
                {'99.99%'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.uptime', t('Home.uptime', 'Uptime'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#374151' }}
              >
                {'<2s'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.load_time', t('Home.load_time', 'Load Time'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#374151' }}
              >
                {'10K+'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.users', t('Home.users', 'Users'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#374151' }}
              >
                {'4.9/5'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.rating', t('Home.rating', 'Rating'))}</div>
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <img
                src="https://images.unsplash.com/photo-1517836357463-d25dfeac3438/?auto=format&fit=crop&w=1200&q=80"
                alt="Claimflow platform showcase"
                className="w-full rounded-2xl object-cover shadow-xl"
                style={{ maxHeight: 420 }}
                loading="lazy"
              />
            </div>
            <div>
              <span className="section-eyebrow">{t('Home.platform_preview', t('Home.platform_preview', 'Platform Preview'))}</span>
              <h2 className="section-heading mb-4">{t('Home.built_for_the_modern_growth', t('Home.built_for_the_modern_growth', 'Built for the modern growth'))}</h2>
              <p className="text-slate-500 leading-relaxed mb-6">
                Every detail is engineered for performance, scalability, and a flawless user
                experience — from first click to everyday operations.
              </p>
              <Link to="/about" className="btn-primary">
                Learn More <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div
            className="max-w-3xl mx-auto text-center rounded-2xl p-12"
            style={{ background: 'linear-gradient(135deg, #111827, #374151)' }}
          >
            <h2 className="text-3xl font-extrabold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-white/70 mb-8">
              Trusted by teams who chose Claimflow to do more with less.
            </p>
            <Link
              to="/contact"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3 font-semibold transition-all hover:shadow-xl"
              style={{ color: '#374151' }}
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
