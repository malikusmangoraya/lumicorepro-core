import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { translate, useLocale } from '../i18n.js';

const SECTIONS = [
  {
    title: 'What we collect',
    body: 'When you create an account we store your name, email address and a bcrypt hash of your password. When you generate an article we store the keyword, audience, tone, length, the generated content and its SEO metadata under your user id. We also keep a credit ledger (balance, granted, used).',
  },
  {
    title: 'Why we collect it',
    body: 'Account data authenticates you and scopes your workspace. Article data powers your history and exports. The credit ledger meters usage and prevents abuse. We do not use your content to train models.',
  },
  {
    title: 'Where it is stored',
    body: 'In the PostgreSQL database configured for this deployment. Sessions use a signed JWT kept in your browser localStorage. No analytics or advertising cookies are set by this application.',
  },
  {
    id: 'cookies',
    title: 'Cookies',
    body: 'The only browser storage used for the cookie-consent banner is a single preference entry (bf_cookie_consent) that records whether you accepted or declined, plus your saved language preference. No tracking, analytics, advertising or third-party cookies are set by this application.',
  },
  {
    title: 'Third-party providers',
    body: 'When you generate with a configured AI provider (OpenAI, OpenRouter, DeepSeek or Gemini), your keyword, tone, length and audience are sent to that provider to produce the article. Without a provider key the application uses a built-in demo generator and sends nothing externally.',
  },
  {
    title: 'Retention and deletion',
    body: 'Articles remain until you delete them from History, and deleting your account cascades to its articles and credit row. Backups, if enabled by your deployment, follow the retention configured there.',
  },
  {
    title: 'Your rights',
    body: 'You can access and export your articles at any time, correct your profile details, or request deletion of your account and content by contacting the operator of this deployment. GDPR and similar rights apply where relevant.',
  },
  {
    title: 'Contact',
    body: 'Privacy questions: hello@blogforge.app. This page describes the reference deployment; the operator of any fork is responsible for their own policy.',
  },
];

export default function Privacy() {
  const locale = useLocale();
  return (
    <div className="pb-24">
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-16">
        <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
          <ShieldCheck className="w-3.5 h-3.5" /> Privacy
        </span>
        <h1 className="mt-6 text-3xl sm:text-4xl font-extrabold text-white">Privacy Policy</h1>
        <p className="mt-3 text-sm text-slate-500">Last updated: 21 October 2026</p>
        <p role="note" className="mt-5 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">{translate(locale, 'rtlNotice')}</p>
        <p className="mt-4 text-sm text-slate-400">This is a reference-deployment notice, not legal advice or a compliance certification. Operators must verify and adapt it to their actual data practices and applicable law before launch.</p>
        <div className="mt-10 space-y-8">
          {SECTIONS.map(({ id, title, body }) => (
            <div key={title} id={id}>
              <h2 className="text-lg font-bold text-white mb-2">{title}</h2>
              <p className="text-sm text-slate-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/40 p-5 text-sm text-slate-400">
          See also the <Link to="/terms" className="text-brand-accent hover:text-white">Terms of Service</Link>.
        </div>
      </section>
    </div>
  );
}
