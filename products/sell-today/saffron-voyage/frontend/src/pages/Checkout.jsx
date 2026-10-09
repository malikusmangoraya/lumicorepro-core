import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useTranslation } from 'react-i18next';
import CheckoutFlow from '@/components/checkout/CheckoutFlow';
import { useCurrency } from '@/context/CurrencyContext';

export default function Checkout() {
const { t } = useTranslation();
const { currency } = useCurrency();
  return (
    <div className="min-h-screen flex flex-col bg-[var(--t-canvas)] text-[var(--t-text)]">
      <Navbar />
      <main id="main-content" className="flex-1 py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">{t('Checkout.checkout', t('Checkout.checkout', 'Checkout'))}</h1>
          <CheckoutFlow currency={currency} submitEndpoint="/api/orders" />
        </div>
      </main>
      <Footer />
    </div>
  );
}
