import React from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '../components/ui/LanguageSelector';
import CurrencySelector from '../components/ui/CurrencySelector';

export default function Terms() {
  const { t } = useTranslation();
  return (
    <main id="main-content" className="mx-auto w-full max-w-3xl px-6 py-20">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-3">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight">
          {t('legal.terms.title', t('Terms.terms_of_service', 'Terms of Service'))}
        </h1>
        <div className="flex items-center gap-2">
          <LanguageSelector />
          <CurrencySelector />
        </div>
      </div>

      <p className="mb-8 text-sm opacity-80">
        {t('legal.terms.updated', t('Terms.last_updated_1_january_2026', 'Last updated: 1 January 2026'))}
      </p>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.terms.acceptance', t('Terms.acceptance_of_terms', 'Acceptance of terms'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.terms.acceptanceBody',
            t('Terms.by_accessing_apex_digital_you_agree_to_these_terms_if_you_do', 'By accessing Apex Digital you agree to these terms. If you do not agree, please stop using the site.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.terms.use', t('Terms.permitted_use', 'Permitted use'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.terms.useBody',
            t('Terms.you_may_browse_and_use_this_site_for_lawful_purposes_you_may', 'You may browse and use this site for lawful purposes. You may not scrape, overload, reverse engineer, or attempt to gain unauthorised access to any part of it.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.terms.availability', 'Availability')}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.terms.availabilityBody',
            t('Terms.we_aim_for_continuous_availability_but_do_not_guarantee_unin', 'We aim for continuous availability but do not guarantee uninterrupted access. Maintenance and third-party dependencies may cause downtime.')
          )}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.terms.liability', t('Terms.limitation_of_liability', 'Limitation of liability'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.terms.liabilityBody',
            t('Terms.to_the_maximum_extent_permitted_by_law_apex_digital_is_not_l', 'To the maximum extent permitted by law, Apex Digital is not liable for indirect or consequential loss arising from use of this site.')
          )}
        </p>
      </section>

      <section>
        <h2 className="mb-2 text-xl font-semibold">
          {t('legal.terms.governing', t('Terms.governing_law', 'Governing law'))}
        </h2>
        <p className="leading-relaxed opacity-90">
          {t(
            'legal.terms.governingBody',
            t('Terms.these_terms_are_governed_by_the_laws_applicable_in_our_place', 'These terms are governed by the laws applicable in our place of establishment, without regard to conflict-of-law rules.')
          )}
        </p>
      </section>
    </main>
  );
}
