import React from 'react';
import { useTranslation } from 'react-i18next';
import CheckoutFlow from '@/components/checkout/CheckoutFlow';
import { useCurrency } from '@/context/CurrencyContext';

export default function Checkout() {
  const { t } = useTranslation();
  const { currency } = useCurrency();
  return (
    <div className="min-h-screen bg-[var(--t-canvas)] text-[var(--t-text)] py-12 px-4">
      <h1 className="text-3xl font-bold mb-8">{t('Checkout.checkout', t('Checkout.checkout', 'Checkout'))}</h1>
      <CheckoutFlow currency={{currency}} submitEndpoint="/api/orders" />
    </div>
  );
}
