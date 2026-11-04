import React from 'react';
import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';

const SECTIONS = [
  {
    title: 'The service',
    body: 'BlogForge generates draft articles from a keyword and optional audience, tone and length settings, then stores them in your workspace. The software is provided as a deployable package; the operator of this instance is responsible for its availability and configuration.',
  },
  {
    title: 'Accounts',
    body: 'You must provide accurate account details and keep your credentials secure. You are responsible for activity under your account. We may suspend accounts that abuse the service, attempt to bypass credit limits, or generate unlawful content.',
  },
  {
    title: 'Credits',
    body: 'One credit is reserved per generation attempt. Credits are refunded automatically when generation fails before an article is produced. Credits have no cash value and are non-transferable. In this build, top-ups are granted instantly for evaluation; paid plans require a connected payment provider.',
  },
  {
    title: 'Your content',
    body: 'You retain ownership of the keywords and content you submit, and of the articles generated for you, subject to the terms of the AI provider used. You are responsible for reviewing generated text for accuracy before publishing.',
  },
  {
    title: 'AI output disclaimer',
    body: 'Generated content may be incomplete, outdated or incorrect. It is not professional, legal, financial or medical advice. Always review and edit drafts before publishing.',
  },
  {
    title: 'Acceptable use',
    body: 'Do not use the service to generate spam, plagiarized content, disinformation, harassment, or material that infringes third-party rights. Do not attempt to disrupt the service or access other users\u2019 data.',
  },
  {
    id: 'refunds',
    title: 'Refund policy',
    body: 'Evaluation credits are refunded automatically to your balance when a generation fails to produce an article, so no money changes hands in this build. When a payment provider is connected and paid plans are offered, unused credits on the most recent subscription will be refundable within 14 days of purchase by contacting the operator, in line with applicable consumer-protection rules (EU distance-selling, UK CRA 2015 and similar).',
  },
  {
    title: 'Liability',
    body: 'The service is provided \u201cas is\u201d without warranties of any kind. To the maximum extent permitted by law, the operator is not liable for indirect or consequential damages arising from use of the service.',
  },
  {
    title: 'Changes',
    body: 'These terms may be updated as the product evolves. Material changes will be reflected on this page with a new date. Continued use after a change constitutes acceptance.',
  },
];

export default function Terms() {
  return (
    <div className="pb-24">
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-16">
        <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-primary/10 text-brand-accent border border-brand-primary/30">
          <FileText className="w-3.5 h-3.5" /> Legal
        </span>
        <h1 className="mt-6 text-3xl sm:text-4xl font-extrabold text-white">Terms of Service</h1>
        <p className="mt-3 text-sm text-slate-500">Last updated: 21 October 2026</p>
        <p className="mt-5 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">This template describes the reference deployment and is not legal advice. Operators must verify it against the live service, payment setup, jurisdiction, and applicable consumer-protection requirements.</p>
        <div className="mt-10 space-y-8">
          {SECTIONS.map(({ id, title, body }) => (
            <div key={title} id={id}>
              <h2 className="text-lg font-bold text-white mb-2">{title}</h2>
              <p className="text-sm text-slate-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/40 p-5 text-sm text-slate-400">
          See also the <Link to="/privacy" className="text-brand-accent hover:text-white">Privacy Policy</Link>.
        </div>
      </section>
    </div>
  );
}
