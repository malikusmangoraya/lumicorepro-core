import React from 'react';
import { cn } from '../../utils';

const defaultFeatures = [
  {
    title: 'Lightning fast',
    body: 'Optimized builds and lazy-loaded routes deliver a sub-second start.',
    emoji: '⚡',
  },
  {
    title: 'Global ready',
    body: 'i18n, RTL, currencies and locales ship out of the box.',
    emoji: '🌍',
  },
  {
    title: 'Secure by design',
    body: 'JWT auth, input validation and privacy compliance built-in.',
    emoji: '🔒',
  },
  {
    title: 'Conversion focused',
    body: 'Persuasive layouts, social proof and frictionless checkout.',
    emoji: '📈',
  },
  {
    title: 'Fully responsive',
    body: 'Pixel-perfect from 320px phones to 4K desktops.',
    emoji: '📱',
  },
  {
    title: 'Accessible',
    body: 'WCAG 2.1 AA: keyboard nav, contrast and screen-reader support.',
    emoji: '♿',
  },
];

const FeatureGrid = ({
  features = defaultFeatures,
  title = 'Everything you need',
  subtitle = 'Powerful capabilities included with every project.',
  columns = 3,
  className = '',
}) => {
  const colClass =
    {
      2: 'sm:grid-cols-2',
      3: 'sm:grid-cols-2 lg:grid-cols-3',
      4: 'sm:grid-cols-2 lg:grid-cols-4',
    }[columns] || 'sm:grid-cols-2 lg:grid-cols-3';

  return (
    <section className={cn('w-full py-16', className)}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl space-y-3 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">{title}</h2>
          {subtitle && <p className="text-base text-muted-foreground">{subtitle}</p>}
        </div>
        <div className={cn('mt-12 grid grid-cols-1 gap-6', colClass)}>
          {features.map((feature, index) => (
            <article
              key={feature.title || index}
              className="group relative overflow-hidden rounded-2xl border bg-card p-6 text-card-foreground shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <span className="text-3xl" aria-hidden="true">
                {feature.emoji || '✦'}
              </span>
              <h3 className="mt-4 text-lg font-semibold text-foreground">{feature.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{feature.body}</p>
              <span
                className="pointer-events-none absolute inset-x-0 bottom-0 h-0.5 scale-x-0 bg-primary transition-transform duration-300 group-hover:scale-x-100"
                aria-hidden="true"
              />
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeatureGrid;
