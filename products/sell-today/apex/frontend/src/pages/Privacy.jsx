import React from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '../components/ui/LanguageSelector';
import CurrencySelector from '../components/ui/CurrencySelector';

export default function Privacy() {
  const { t } = useTranslation();
  return (
    <main id="main-content" className="mx-auto w-full max-w-3xl px-6 py-20">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold tracking-tight">
          {t('legal.privacy.title', t('Privacy.privacy_policy', 'Privacy Policy'))}
        </h1>
        <div className="flex items-center gap-2">
          <LanguageSelector />
          <CurrencySelector />
        </div>
      </div>

      <p className="mb-8 text-sm opacity-80">
        {t('legal.privacy.updated', t('Privacy.last_updated_1_january_2026', 'Last updated: 1 January 2026'))}
      </p>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.privacy.controller', t('Privacy.who_we_are', 'Who we are'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.privacy.controllerBody',
            t('Privacy.apex_digital_we_us_operates_this_website_we_are_the_data_con', 'Apex Digital ("we", "us") operates this website. We are the data controller for the personal information you provide through this site.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.privacy.data', t('Privacy.what_we_collect', 'What we collect'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.privacy.dataBody',
            t('Privacy.we_collect_only_what_you_choose_to_give_us_contact_details_y', 'We collect only what you choose to give us: contact details you submit in a form, account details if you register, and anonymous usage statistics. We do not sell personal data.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.privacy.cookies', 'Cookies')}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.privacy.cookiesBody',
            t('Privacy.we_use_essential_cookies_to_remember_your_language_and_curre', 'We use essential cookies to remember your language and currency preference, and optional analytics cookies only with your consent. You can withdraw consent at any time.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.privacy.rights', t('Privacy.your_rights', 'Your rights'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.privacy.rightsBody',
            t('Privacy.under_the_gdpr_you_may_request_access_to_correction_of_or_de', 'Under the GDPR you may request access to, correction of, or deletion of your personal data, and you may object to processing. Contact us and we will respond within 30 days.')
          )}
        </p>
      </section>

      <section>
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.privacy.contact', 'Contact')}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t('legal.privacy.contactBody', t('Privacy.write_to_us_from_the_contact_page_and_we_will_action_your_re', 'Write to us from the contact page and we will action your request.'))}
        </p>
      </section>
    </main>
  );
}
