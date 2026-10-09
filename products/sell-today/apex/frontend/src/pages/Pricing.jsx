import React from 'react';
import { useTranslation } from 'react-i18next';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingTable from '../components/ecommerce/PricingTable';
import FAQAccordion from '../components/common/FAQAccordion';
import TestimonialGrid from '../components/common/TestimonialGrid';

export default function Pricing() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main id="main-content" className="flex-1">
        <PricingTable />
        <TestimonialGrid />
        <FAQAccordion />
      </main>

      <Footer />
    </div>
  );
}
