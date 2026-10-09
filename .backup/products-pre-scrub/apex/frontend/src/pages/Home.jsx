import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowRight, LayoutDashboard, ShieldCheck, Zap, TrendingUp } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Home() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden py-16 lg:py-24">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="max-w-2xl">
              <span className="section-eyebrow">{t('Home.modern_saas_platform', t('Home.modern_saas_platform', 'MODERN SAAS PLATFORM'))}</span>
              <h1
                className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight mb-6"
                style={{ color: '#2e1065' }}
              >
                Conversion engineering for B2B teams.
              </h1>
              <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-lg">
                Apex Digital gives teams analytics, automation and enterprise-grade security.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/contact" className="btn-primary">
                  Get Started <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/services" className="btn-outline">
                  View Services
                </Link>
              </div>
              <ul className="mt-8 space-y-3 max-w-sm">
                <li className="flex items-center gap-3">
                  <span
                    className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <LayoutDashboard className="h-4 w-4" />
                  </span>
                  <span className="text-sm font-medium text-slate-700">
                    Enterprise-grade security and compliance
                  </span>
                </li>
                <li className="flex items-center gap-3">
                  <span
                    className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <Zap className="h-4 w-4" />
                  </span>
                  <span className="text-sm font-medium text-slate-700">
                    Global support across time zones, 24/7
                  </span>
                </li>
                <li className="flex items-center gap-3">
                  <span
                    className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <TrendingUp className="h-4 w-4" />
                  </span>
                  <span className="text-sm font-medium text-slate-700">
                    Seamless integrations with your stack
                  </span>
                </li>
              </ul>
            </div>
            <div className="hidden lg:block relative">
              <img
                src="https://images.unsplash.com/photo-1568605114967-8130f3a36994/?auto=format&fit=crop&w=1200&q=80"
                alt="Apex Digital product overview"
                className="w-full h-96 lg:h-105 rounded-2xl object-cover shadow-2xl"
                loading="eager"
              />
              <div className="absolute -bottom-6 -left-6 rounded-xl bg-white p-4 shadow-xl border border-slate-100 flex items-center gap-3">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold text-slate-700">
                  Trusted by 50,000+ businesses worldwide
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <span className="section-eyebrow">{t('Home.what_we_offer', t('Home.what_we_offer', 'What We Offer'))}</span>
              <h2 className="section-heading">{t('Home.why_choose_apex_digital', t('Home.why_choose_apex_digital', 'Why choose Apex Digital?'))}</h2>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="card-panel group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
                <div className="p-6">
                  <div
                    className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl text-white shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <LayoutDashboard className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#2e1065' }}>
                    Intuitive Dashboard
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Real-time metrics and management at your fingertips
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1600585154526-990dced4db0d/?auto=format&fit=crop&w=1200&q=80"
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
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#2e1065' }}>
                    Secure by Default
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Enterprise authentication, encryption, and audit logging
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1553729459-efe14ef6055d/?auto=format&fit=crop&w=1200&q=80"
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
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <Zap className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#2e1065' }}>
                    Performance First
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Optimized for speed, SEO, and Core Web Vitals
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1533750349088-cd871a92f312/?auto=format&fit=crop&w=1200&q=80"
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
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
                  >
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: '#2e1065' }}>
                    Scalable Architecture
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    Built to handle growth from prototype to production
                  </p>
                </div>
                <div className="relative mt-5 overflow-hidden rounded-lg" style={{ height: 120 }}>
                  <img
                    src="https://images.unsplash.com/photo-1547658719-da2b51169166/?auto=format&fit=crop&w=1200&q=80"
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
              src="https://images.unsplash.com/photo-1600585154526-990dced4db0d/?auto=format&fit=crop&w=1200&q=80"
              alt="Apex Digital features"
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
                style={{ color: '#7c3aed' }}
              >
                {'99.99%'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.uptime', t('Home.uptime', 'Uptime'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#7c3aed' }}
              >
                {'<2s'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.load_time', t('Home.load_time', 'Load Time'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#7c3aed' }}
              >
                {'10K+'}
              </div>
              <div className="text-sm text-slate-500">{t('Home.users', t('Home.users', 'Users'))}</div>
            </div>
            <div className="text-center">
              <div
                className="text-3xl sm:text-4xl font-extrabold mb-1"
                style={{ color: '#7c3aed' }}
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
                src="https://images.unsplash.com/photo-1466692476868-aef1dfb1e735/?auto=format&fit=crop&w=1200&q=80"
                alt="Apex Digital platform showcase"
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
            style={{ background: 'linear-gradient(135deg, #2e1065, #7c3aed)' }}
          >
            <h2 className="text-3xl font-extrabold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-white/70 mb-8">
              Trusted by teams who chose Apex Digital to do more with less.
            </p>
            <Link
              to="/contact"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3 font-semibold transition-all hover:shadow-xl"
              style={{ color: '#7c3aed' }}
            >
              Start Free Trial <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
