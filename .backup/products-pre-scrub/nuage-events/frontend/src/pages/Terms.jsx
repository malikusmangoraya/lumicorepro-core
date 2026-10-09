import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Terms() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-10">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-4xl mx-auto px-6">
            <p className="section-eyebrow">{t('Terms.legal_agreement', t('Terms.legal_agreement', 'LEGAL AGREEMENT'))}</p>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-[1.05] mb-4"
              style={{ color: 'var(--t-heading)' }}>
              Terms of Service
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Last updated: 17 September 2026. Applies to all services provided by Nuage Events.
            </p>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-4xl mx-auto px-6 space-y-10">
            <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Agreement to terms
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  These terms govern your use of the website and services operated by {BRAND}
                  (&ldquo;we&rdquo;, &ldquo;us&rdquo;). By accessing the site or creating an account you agree to be bound
                  by these terms. If you do not agree, please do not use the service.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Use of the service
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li>{t('Terms.you_must_be_at_least_18_years_old_or_have_parent_guardian_co', t('Terms.you_must_be_at_least_18_years_old_or_have_parent_guardian_co', 'You must be at least 18 years old or have parent/guardian consent.'))}</li>
                  <li>{t('Terms.you_are_responsible_for_the_accuracy_of_your_account_informa', t('Terms.you_are_responsible_for_the_accuracy_of_your_account_informa', 'You are responsible for the accuracy of your account information and for keeping credentials secure.'))}</li>
                  <li>{t('Terms.you_must_not_misuse_the_service_no_unlawful_activity_no_spam', t('Terms.you_must_not_misuse_the_service_no_unlawful_activity_no_spam', 'You must not misuse the service: no unlawful activity, no spam or abuse, no interference with other users or our infrastructure.'))}</li>
                  <li>{t('Terms.we_may_suspend_accounts_that_violate_these_terms_with_notice', t('Terms.we_may_suspend_accounts_that_violate_these_terms_with_notice', 'We may suspend accounts that violate these terms, with notice where practicable.'))}</li>
                </ul>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Intellectual property
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  All content on this site — text, design, graphics, branding and software — is owned by
                  {BRAND} or its licensors and protected by applicable law. You may not reproduce, resell
                  or redistribute our materials without written permission, except for your own lawful use
                  of the service.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Payments & cancellations
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  All charges are shown clearly before you confirm any purchase. Payments are processed by
                  our payment partners; we do not store your card details. Subscriptions renew as described
                  at checkout unless cancelled before the renewal date. Refunds are handled in line with the
                  policy on the relevant product page and applicable law.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Disclaimers & liability
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  The service is provided &ldquo;as is&rdquo; without warranties of any kind, to the fullest extent
                  permitted by law. To the extent permitted by law, {BRAND} shall not be liable for indirect,
                  incidental or consequential damages. Nothing in these terms limits liability that cannot
                  be limited by law.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Changes & governing law
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We may update these terms from time to time; material changes will be notified on this page.
                  Continued use after a change means acceptance of the updated terms. These terms are
                  governed by the laws of the jurisdiction in which {BRAND} is established.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Contact
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Questions about these terms? Email us at{' '}
                  <a className="font-medium underline underline-offset-2" style={{ color: 'var(--t-primary)' }}
                     href="mailto:legal@{DOMAIN}">legal@{DOMAIN}</a>.
                </p>
              </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
