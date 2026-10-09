import ButtonMotion from '@/components/ui/ButtonMotion';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, Phone, MapPin, Send, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

export default function Contact() {
  const { t } = useTranslation();
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main id="main-content" className="flex-1 px-6 py-16 max-w-5xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
            Get In Touch
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight">
            Let's Discuss Your Next Project
          </h1>
          <p className="text-slate-400 text-sm">
            Have a question or looking to scale? Our team is ready to assist.
          </p>
        </div>

        <div className="grid gap-10 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-5">
              <h3 className="font-semibold text-lg text-white">{t('Contact.contact_information', t('Contact.contact_information', 'Contact Information'))}</h3>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Mail className="h-4 w-4" />
                </div>
                <span>{t('Contact.hello_apex_com', t('Contact.hello_apex_com', 'hello@apex.com'))}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Phone className="h-4 w-4" />
                </div>
                <span>{t('Contact.1_555_019_2834', t('Contact.1_555_019_2834', '+1 (555) 019-2834'))}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-300">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                  <MapPin className="h-4 w-4" />
                </div>
                <span>{t('Contact.750_innovation_way_suite_400', t('Contact.750_innovation_way_suite_400', '750 Innovation Way, Suite 400'))}</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
            {submitted ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <CheckCircle2 className="h-12 w-12 text-emerald-400" />
                <h3 className="text-lg font-semibold text-white">{t('Contact.message_received', t('Contact.message_received', 'Message Received!'))}</h3>
                <p className="text-sm text-slate-400 max-w-xs">
                  Thank you for reaching out. A specialist will get back to you within 24 hours.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('Contact.your_name', t('Contact.your_name', 'Your Name'))}</label>
                  <input
                    type="text"
                    required
                    placeholder="Jane Doe"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="jane@company.com"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">{t('Contact.message', t('Contact.message', 'Message'))}</label>
                  <textarea
                    required
                    rows="4"
                    placeholder="How can we help your business?"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <ButtonMotion
                  type="submit"
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400 transition-all"
                >
                  Send Message <Send className="h-4 w-4" />
                </ButtonMotion>
              </form>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
