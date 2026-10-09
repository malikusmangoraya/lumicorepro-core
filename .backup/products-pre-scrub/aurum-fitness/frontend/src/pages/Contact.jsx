import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, Phone, MapPin, Clock, Send, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Contact() {
  const { t } = useTranslation();
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-16">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-7xl mx-auto px-6">
            <span className="inline-flex items-center gap-2 section-eyebrow">
              <span className="h-1.5 w-1.5 rounded-full bg-primary inline-block" />
              CONTACT
            </span>
            <h1
              className="mt-3 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: 'var(--t-heading)' }}
            >
              Start a conversation
            </h1>
            <p className="mt-6 text-lg text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
              Tell us what you need and the Aurum Fitness team will reply within one business day.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-5 gap-12">
            <div className="lg:col-span-3">
              <div className="card-panel p-8" data-reveal>
                {submitted ? (
                  <div className="text-center py-12">
                    <span
                      className="mx-auto mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-white"
                      style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                    >
                      <CheckCircle2 className="h-7 w-7" />
                    </span>
                    <h2 className="text-2xl font-black mb-2" style={{ color: 'var(--t-heading)' }}>{t('Contact.message_received', t('Contact.message_received', 'Message received'))}</h2>
                    <p className="text-slate-500 dark:text-slate-400">
                      Thank you, {form.name || 'there'}. A member of the team will be in touch shortly.
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium mb-1.5" style={{ color: 'var(--t-heading)' }}>{t('Contact.full_name', t('Contact.full_name', 'Full name'))}</label>
                      <input
                        id="name" name="name" type="text" required autoComplete="name"
                        value={form.name} onChange={handleChange}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium mb-1.5" style={{ color: 'var(--t-heading)' }}>{t('Contact.email', t('Contact.email', 'Email'))}</label>
                      <input
                        id="email" name="email" type="email" required autoComplete="email"
                        value={form.email} onChange={handleChange}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <div>
                      <label htmlFor="message" className="block text-sm font-medium mb-1.5" style={{ color: 'var(--t-heading)' }}>{t('Contact.how_can_we_help', t('Contact.how_can_we_help', 'How can we help?'))}</label>
                      <textarea
                        id="message" name="message" rows="5" required
                        value={form.message} onChange={handleChange}
                        className="w-full rounded-xl border border-[var(--t-border)] bg-surface px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--t-primary)]"
                      />
                    </div>
                    <button type="submit" className="btn-primary inline-flex items-center gap-2 text-sm px-6 py-3">
                      Send message <Send className="h-4 w-4" />
                    </button>
                  </form>
                )}
              </div>
            </div>

            <div className="lg:col-span-2 space-y-8">
              <div className="flex items-start gap-4" data-reveal>
                <span
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <MapPin className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">{t('Contact.visit', t('Contact.visit', 'Visit'))}</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>The Ironworks, 22 Dock Road</p>
                </div>
              </div><div className="flex items-start gap-4" data-reveal>
                <span
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Phone className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">{t('Contact.call', t('Contact.call', 'Call'))}</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>+1 312 555 0155</p>
                </div>
              </div><div className="flex items-start gap-4" data-reveal>
                <span
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Mail className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">{t('Contact.email', t('Contact.email', 'Email'))}</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>train@aurumfitness.com</p>
                </div>
              </div><div className="flex items-start gap-4" data-reveal>
                <span
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
                  style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
                >
                  <Clock className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">{t('Contact.hours', t('Contact.hours', 'Hours'))}</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--t-heading)' }}>Mon–Sun, 5am–11pm</p>
                </div>
              </div>
              <div className="glass-md rounded-2xl p-6" data-reveal>
                <p className="text-sm text-slate-600 dark:text-slate-300">Free trial session available for first-time visitors.</p>
              </div>
              <div
                className="rounded-2xl h-40 flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, var(--t-primary), var(--t-accent))' }}
              >
                <div className="text-center text-white">
                  <MapPin className="h-7 w-7 mx-auto mb-1" />
                  <p className="text-sm font-semibold">The Ironworks, 22 Dock Road</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
