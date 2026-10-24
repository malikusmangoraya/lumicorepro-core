import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PrivacyPolicyPage from '../../pages/PrivacyPolicy';
import TermsOfServicePage from '../../pages/TermsOfService';
import RefundPolicyPage from '../../pages/RefundPolicy';

const renderPage = (element, path) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={path} element={element} />
        <Route path="/" element={<div>home-page</div>} />
      </Routes>
    </MemoryRouter>
  );

describe('PrivacyPolicy page', () => {
  it('renders the legal heading, compliance badge and last-updated stamp', () => {
    renderPage(<PrivacyPolicyPage />, '/privacy');

    expect(screen.getByRole('heading', { level: 1, name: 'Privacy Policy' })).toBeTruthy();
    expect(screen.getByText('GDPR & CCPA Compliant')).toBeTruthy();
    expect(screen.getByText(/Last updated: September 2026/)).toBeTruthy();
  });

  it('renders all eight numbered legal sections', () => {
    renderPage(<PrivacyPolicyPage />, '/privacy');

    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(8);
    expect(
      screen.getByRole('heading', { level: 2, name: /1\. Information We Collect/ })
    ).toBeTruthy();
    expect(
      screen.getByRole('heading', { level: 2, name: /8\. Contact Our Data Protection Officer/ })
    ).toBeTruthy();
  });

  it('lists the collected data categories and GDPR/CCPA user rights', () => {
    renderPage(<PrivacyPolicyPage />, '/privacy');

    expect(screen.getByText(/Account Information:/)).toBeTruthy();
    expect(screen.getByText(/AI Generation Inputs:/)).toBeTruthy();
    expect(screen.getByText(/Payment Information:/)).toBeTruthy();
    expect(screen.getAllByText(/^Right (to|of) /)).toHaveLength(6);
    expect(screen.getByText(/Right to erasure/)).toBeTruthy();
    expect(screen.getByText('privacy@lumicorepro.com')).toBeTruthy();
  });

  it('navigates home from the back button', () => {
    renderPage(<PrivacyPolicyPage />, '/privacy');

    fireEvent.click(screen.getByRole('button', { name: /back to home/i }));

    expect(screen.getByText('home-page')).toBeTruthy();
  });
});

describe('TermsOfService page', () => {
  it('renders the legal heading and international-standards badge', () => {
    renderPage(<TermsOfServicePage />, '/terms');

    expect(screen.getByRole('heading', { level: 1, name: 'Terms of Service' })).toBeTruthy();
    expect(screen.getByText('International Standard Terms')).toBeTruthy();
    expect(screen.getByText(/Governing global use of the LumiCorePro software/)).toBeTruthy();
  });

  it('renders all five terms sections', () => {
    renderPage(<TermsOfServicePage />, '/terms');

    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(5);
    expect(
      screen.getByRole('heading', { level: 2, name: /2\. Intellectual Property & Code Ownership/ })
    ).toBeTruthy();
    expect(screen.getByRole('heading', { level: 2, name: /5\. Limitation of Liability/ })).toBeTruthy();
  });

  it('covers code ownership and the acceptable-use restrictions', () => {
    renderPage(<TermsOfServicePage />, '/terms');

    expect(screen.getByText(/You own 100% of the customized code/)).toBeTruthy();
    expect(screen.getByText(/Generate malicious software/)).toBeTruthy();
    expect(screen.getByText(/Violate international sanctions/)).toBeTruthy();
    expect(screen.getAllByRole('listitem')).toHaveLength(4);
  });

  it('navigates home from the back button', () => {
    renderPage(<TermsOfServicePage />, '/terms');

    fireEvent.click(screen.getByRole('button', { name: /back to home/i }));

    expect(screen.getByText('home-page')).toBeTruthy();
  });
});

describe('RefundPolicy page', () => {
  it('renders the heading and sets the page SEO title', () => {
    renderPage(<RefundPolicyPage />, '/refund');

    expect(screen.getByRole('heading', { level: 1, name: 'Refund Policy' })).toBeTruthy();
    expect(screen.getByText('14-Day Refund Window')).toBeTruthy();
    expect(document.title).toBe('Refund Policy — LumicorePro');
    expect(document.querySelector('meta[name="robots"]').getAttribute('content')).toBe(
      'noindex,nofollow'
    );
  });

  it('renders all five sections and the four refund steps', () => {
    renderPage(<RefundPolicyPage />, '/refund');

    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(5);
    expect(
      screen.getByRole('heading', { level: 1, name: 'Refund Policy' })
    ).toBeTruthy();
    expect(screen.getByText(/Choose "Request Refund" next to the applicable order/)).toBeTruthy();
    expect(screen.getByText(/Approved refunds are returned to the original payment method/)).toBeTruthy();
    expect(screen.getAllByRole('listitem')).toHaveLength(8);
  });

  it('explains non-refundable items and payment timelines', () => {
    renderPage(<RefundPolicyPage />, '/refund');

    expect(screen.getByText(/Digital template license purchases/)).toBeTruthy();
    expect(screen.getByText('5-10 business days (card)')).toBeTruthy();
    expect(screen.getByText('~24 hours (PayPal balance)')).toBeTruthy();
    expect(screen.getAllByText('support@lumicorepro.com').length).toBeGreaterThanOrEqual(1);
  });

  it('navigates home from the back button', () => {
    renderPage(<RefundPolicyPage />, '/refund');

    fireEvent.click(screen.getByRole('button', { name: /back to home/i }));

    expect(screen.getByText('home-page')).toBeTruthy();
  });
});
