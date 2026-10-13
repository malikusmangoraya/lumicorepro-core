import React from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, Phone } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import VehicleInquiryForm from '../components/vehicle/VehicleInquiryForm';

export default function Contact() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main id="main-content" className="mx-auto w-full max-w-6xl px-6 py-16 lg:py-24">
        <header className="mx-auto mb-12 max-w-2xl text-center">
          <p className="section-eyebrow">Private viewings & enquiries</p>
          <h1 className="section-heading mt-3">Tell us what you would love to drive</h1>
          <p className="mt-4 text-slate-500">Ask about a listed vehicle or tell us what you are searching for. An Apex advisor will follow up to discuss availability and next steps.</p>
        </header>
        <div className="grid items-start gap-10 lg:grid-cols-2">
          <section className="space-y-6 border border-[var(--t-border)] bg-surface p-6" aria-labelledby="contact-info-heading">
            <h2 id="contact-info-heading" className="text-lg font-semibold">{t('Contact.contact_information', 'Contact information')}</h2>
            <p className="flex items-center gap-3 text-sm"><Mail className="h-4 w-4 text-[var(--t-primary)]" aria-hidden="true" />hello@apex.com</p>
            <p className="flex items-center gap-3 text-sm"><Phone className="h-4 w-4 text-[var(--t-primary)]" aria-hidden="true" />+1 (555) 019-2834</p>
            <p className="flex items-center gap-3 text-sm"><MapPin className="h-4 w-4 text-[var(--t-primary)]" aria-hidden="true" />750 Innovation Way, Suite 400</p>
            <p className="text-xs leading-relaxed text-slate-500">Contact details shown here are the current site configuration; please confirm them before publishing.</p>
          </section>
          <VehicleInquiryForm />
        </div>
      </main>
      <Footer />
    </div>
  );
}
