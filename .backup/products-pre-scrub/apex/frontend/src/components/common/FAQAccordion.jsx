import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export default function FAQAccordion({
  items = [
    {
      q: 'What is included with this template?',
      a: 'You get full production source code (React 19, Vite, Tailwind CSS), backend API integrations, Lemon Squeezy checkout support, pre-built responsive pages, multi-currency localization, and commercial deployment configs.',
    },
    {
      q: 'Can I use this for commercial client projects?',
      a: 'Yes, 100%. Our commercial license permits you to build unlimited commercial client websites, client dashboards, or SaaS applications without recurring royalty fees.',
    },
    {
      q: 'How does the Lemon Squeezy integration work?',
      a: 'The template includes pre-configured Lemon Squeezy overlay triggers and webhook listeners. Simply add your Lemon Squeezy Store ID and Variant ID in the environment variables to start accepting payments immediately.',
    },
    {
      q: 'Is customer support and documentation included?',
      a: 'Yes! Every purchase comes with comprehensive setup documentation, step-by-step video walkthrough guides, and priority technical assistance.',
    },
    {
      q: 'Do you offer a money-back guarantee?',
      a: 'Yes, we offer a 30-day no-questions-asked refund guarantee if the template does not meet your project requirements.',
    },
  ],
  title = 'Frequently Asked Questions',
  subtitle = 'Everything you need to know about our platform, licensing, and payment integrations.',
}) {
  const [openIndex, setOpenIndex] = useState(0);

  const toggle = (idx) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section className="py-20 px-6 max-w-4xl mx-auto w-full">
      <div className="text-center mb-12 space-y-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          Got Questions?
        </span>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">{title}</h2>
        {subtitle && (
          <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">{subtitle}</p>
        )}
      </div>

      <div className="space-y-4">
        {items.map((item, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div
              key={item.q}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden transition-all duration-200"
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="w-full flex items-center justify-between p-5 text-left text-sm font-semibold text-white hover:text-cyan-400 transition-colors"
                aria-expanded={isOpen}
              >
                <span>{item.q}</span>
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200 ${
                    isOpen ? 'rotate-180 text-cyan-400' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-slate-400 leading-relaxed border-t border-slate-800/60">
                  {item.a}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
