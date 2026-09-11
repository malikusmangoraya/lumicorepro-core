import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { PricingGrid, FAQItem } from '@/components/business';
import { Button } from '@/components/ui';
import { plans, faqs } from './data/mockData';

export default function PricingPage() {
  const [yearly, setYearly] = useState(false);
  const mapped = plans.map((p) => ({
    ...p,
    price: yearly ? p.yearly : p.monthly,
    period: yearly ? '/yr' : '/mo',
  }));
  return (
    <TemplateShell
      title="Pricing"
      description="Simple tiers with monthly/yearly toggle."
      category="Business"
      actions={
        <div className="inline-flex rounded-lg border border-border p-1">
          <Button
            size="sm"
            variant={!yearly ? 'primary' : 'ghost'}
            onClick={() => setYearly(false)}
          >
            Monthly
          </Button>
          <Button size="sm" variant={yearly ? 'primary' : 'ghost'} onClick={() => setYearly(true)}>
            Yearly
          </Button>
        </div>
      }
    >
      <PricingGrid plans={mapped} />
      <div className="mt-12 max-w-2xl mx-auto">
        {faqs.map((f) => (
          <FAQItem key={f.q} question={f.q} answer={f.a} />
        ))}
      </div>
    </TemplateShell>
  );
}
