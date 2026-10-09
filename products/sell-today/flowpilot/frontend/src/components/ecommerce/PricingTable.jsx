import React, { useState } from 'react';
import { Check, Zap, ShieldCheck } from 'lucide-react';
import { openLemonSqueezyCheckout } from '../../services/lemonSqueezy';

export default function PricingTable({
  title = 'Flexible, Transparent Pricing',
  subtitle = 'Choose the perfect tier for your project. Upgrade, downgrade, or cancel anytime with zero lock-in.',
}) {
  const [annual, setAnnual] = useState(false);

  const plans = [
    {
      name: 'Starter',
      desc: 'Ideal for indie hackers and early prototypes.',
      priceMonthly: 29,
      priceAnnual: 24,
      popular: false,
      features: [
        'Single Commercial Project License',
        'Complete React 19 + Vite Source Code',
        'Tailwind CSS UI Component Library',
        'Standard Lemon Squeezy Integration',
        'Community Discord Support',
        'Free Updates for 6 Months',
      ],
    },
    {
      name: 'Pro',
      desc: 'Most popular for growing startups and agencies.',
      priceMonthly: 79,
      priceAnnual: 64,
      popular: true,
      badge: 'Most Popular',
      features: [
        'Unlimited Commercial Client Projects',
        'All Starter Features Included',
        'Full Express Backend & Auth Pipelines',
        'Multi-Currency Localization Suite',
        'Interactive Theme Customizer Drawer',
        'Priority 24/7 Technical SLA Support',
        'Lifetime Feature Updates',
      ],
    },
    {
      name: 'Enterprise',
      desc: 'Dedicated scalability for large engineering teams.',
      priceMonthly: 199,
      priceAnnual: 159,
      popular: false,
      features: [
        'Everything in Pro Suite',
        'Full Source Whitelabel Rights',
        'Custom Lemon Squeezy & Stripe Webhooks',
        '1-on-1 Architecture Consultation Call',
        'Custom Component Engineering Support',
        'Dedicated Enterprise Slack Channel',
      ],
    },
  ];

  const handleCheckout = (plan) => {
    const price = annual ? plan.priceAnnual * 12 : plan.priceMonthly;
    openLemonSqueezyCheckout({
      customData: {
        planName: plan.name,
        billingCycle: annual ? 'annual' : 'monthly',
        amount: price,
      },
      onSuccess: () => {
        alert(`Thank you for purchasing ${plan.name} plan!`);
      },
    });
  };

  return (
    <section className="py-20 px-6 max-w-6xl mx-auto w-full">
      <div className="text-center mb-12 space-y-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          Commercial Licensing
        </span>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">{title}</h2>
        {subtitle && (
          <p className="text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">{subtitle}</p>
        )}

        <div className="pt-4 flex items-center justify-center gap-3">
          <span className={`text-xs font-semibold ${!annual ? 'text-white' : 'text-slate-400'}`}>
            Monthly Billing
          </span>
          <button
            type="button"
            onClick={() => setAnnual(!annual)}
            className="relative h-6 w-11 rounded-full bg-slate-800 p-0.5 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
            role="switch"
            aria-checked={annual}
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-cyan-400 transition-transform ${
                annual ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
          <span
            className={`text-xs font-semibold flex items-center gap-1.5 ${annual ? 'text-white' : 'text-slate-400'}`}
          >
            Annual Billing
            <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
              Save 20%
            </span>
          </span>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3 items-stretch">
        {plans.map((plan) => {
          const price = annual ? plan.priceAnnual : plan.priceMonthly;
          return (
            <div
              key={plan.name}
              className={`relative flex flex-col justify-between rounded-3xl p-8 backdrop-blur-md transition-all duration-200 ${
                plan.popular
                  ? 'border-2 border-cyan-500 bg-slate-900/80 shadow-2xl shadow-cyan-500/10 scale-105 z-10'
                  : 'border border-slate-800 bg-slate-900/40 hover:border-slate-700'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-3.5 py-1 text-[11px] font-bold tracking-wide text-white uppercase shadow-md">
                  {plan.badge || 'Popular'}
                </div>
              )}

              <div>
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-xs text-slate-400 mb-6 min-h-[36px] leading-relaxed">
                  {plan.desc}
                </p>

                <div className="mb-6 flex items-baseline gap-1">
                  <span className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
                    ${price}
                  </span>
                  <span className="text-xs text-slate-400">
                    / {annual ? 'mo, billed annually' : 'month'}
                  </span>
                </div>

                <div className="space-y-3 mb-8 border-t border-slate-800/80 pt-6">
                  <p className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                    Included Features:
                  </p>
                  <ul className="space-y-2.5 text-xs text-slate-300">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-2.5">
                        <Check className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleCheckout(plan)}
                className={`w-full py-3 px-4 rounded-xl text-xs font-bold transition-all shadow-lg active:scale-95 flex items-center justify-center gap-2 ${
                  plan.popular
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-400 hover:to-blue-500 shadow-cyan-500/25'
                    : 'border border-slate-700 bg-slate-800 hover:bg-slate-700 text-white'
                }`}
              >
                <Zap className="h-3.5 w-3.5" /> Buy on Lemon Squeezy
              </button>
            </div>
          );
        })}
      </div>

      <div className="mt-16 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-4 py-2 text-xs text-slate-400">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>30-Day Money-Back Guarantee &bull; Instant Digital Delivery via Lemon Squeezy</span>
        </div>
      </div>
    </section>
  );
}
