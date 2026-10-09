import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Privacy() {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main>
        <section className="relative overflow-hidden pt-16 lg:pt-24 pb-10">
          <div className="absolute inset-0 -z-10 hero-aurora" />
          <div className="max-w-4xl mx-auto px-6">
            <p className="section-eyebrow">{t('Privacy.compliance_trust', t('Privacy.compliance_trust', 'COMPLIANCE & TRUST'))}</p>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-[1.05] mb-4"
              style={{ color: 'var(--t-heading)' }}>
              Privacy Policy
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
                  Introduction
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {BRAND} (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;us&rdquo;) respects your privacy.
                  This policy explains what information we collect when you visit our website, create an
                  account, or use our services, how we use it, and the choices you have.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Information we collect
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li><strong>{t('Privacy.account_details', t('Privacy.account_details', 'Account details'))}</strong> — name, email address and, where provided, billing information.</li>
                  <li><strong>{t('Privacy.usage_data', t('Privacy.usage_data', 'Usage data'))}</strong> — pages viewed, features used and device/technical data (IP address, browser, OS).</li>
                  <li><strong>{t('Privacy.communications', t('Privacy.communications', 'Communications'))}</strong> — emails, support conversations and enquiry forms you send us.</li>
                  <li><strong>{t('Privacy.cookies', t('Privacy.cookies', 'Cookies'))}</strong> — small files that help the site remember your preferences and understand aggregate usage.</li>
                </ul>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  How we use information
                </h2>
                <ul className="list-disc pl-6 space-y-2 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  <li>{t('Privacy.to_provide_and_improve_the_products_and_services_you_request', t('Privacy.to_provide_and_improve_the_products_and_services_you_request', 'To provide and improve the products and services you request.'))}</li>
                  <li>{t('Privacy.to_send_service_notices_transactional_updates_and_only_with_', t('Privacy.to_send_service_notices_transactional_updates_and_only_with_', 'To send service notices, transactional updates and — only with consent — marketing.'))}</li>
                  <li>{t('Privacy.to_personalise_your_experience_and_keep_the_site_secure', t('Privacy.to_personalise_your_experience_and_keep_the_site_secure', 'To personalise your experience and keep the site secure.'))}</li>
                  <li>{t('Privacy.to_comply_with_legal_obligations_and_enforce_our_terms_of_se', t('Privacy.to_comply_with_legal_obligations_and_enforce_our_terms_of_se', 'To comply with legal obligations and enforce our Terms of Service.'))}</li>
                </ul>
                <p className="mt-4 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We process data on the legal bases of performance of a contract, legitimate interest
                  (operation and improvement of our service), consent (where you opt in), and legal compliance.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Sharing & security
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We never sell your personal data. We share it only with service providers who help us
                  operate (hosting, payments, analytics), always under contract and only to the extent
                  needed. Your data is encrypted in transit and at rest, access-controlled and reviewed
                  regularly.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Retention & your rights
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We keep personal data only as long as needed for the purposes above or as required by law,
                  then delete or anonymise it. Depending on your jurisdiction you may have the right to
                  access, rectify, erase, restrict or port your data, and to withdraw consent at any time.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Cookies & local storage
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  We use essential cookies to run the site and optional analytics cookies to understand
                  aggregate usage. You can disable non-essential cookies in your browser at any time.
                  This site works in all browsers even with cookies disabled.
                </p>
              </div>
              <div className="card-panel p-8" data-reveal>
                <h2 className="text-xl font-bold mb-3" style={{ color: 'var(--t-heading)' }}>
                  Contact
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  Questions about this policy or your data? Email us at{' '}
                  <a className="font-medium underline underline-offset-2" style={{ color: 'var(--t-primary)' }}
                     href="mailto:{EMAIL}@{DOMAIN}">privacy@{DOMAIN}</a>.
                </p>
              </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
