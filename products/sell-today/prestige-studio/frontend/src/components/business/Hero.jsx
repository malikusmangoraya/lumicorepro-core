/**
 * Hero — the page-opening composition for this product.
 *
 * Variant: editorial. Copy comes from the caller or from i18n, and every colour is a
 * --t-* token, so the same primitive renders differently for each brand rather than being one
 * hard-coded dark template shared by every product.
 *
 * The artwork is a real asset that ships with this product and is imported so the bundler
 * fingerprints it. (The previous version imported `img` from utils.js, which never exported
 * it — a latent build failure for anything that wired this component up.)
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, PlayCircle, Sparkles } from 'lucide-react';
import LazyImage from '../common/LazyImage';
import defaultImage from '../../assets/images/corporate-space.jpg';
import { cn } from '../../utils';
import { BRAND } from '../brand/BRAND';

const Hero = ({
  badge,
  title,
  highlight,
  subtitle,
  primaryLabel,
  secondaryLabel,
  onPrimary,
  onSecondary,
  image = defaultImage,
  imageAlt = 'A studio space',
  metrics = [],
  className = '',
}) => {
  const { t } = useTranslation();
  const resolvedTitle = title || t('hero.title', 'Work that speaks for itself');
  const resolvedHighlight = highlight || t('hero.highlight', BRAND.name);
  const resolvedSubtitle =
    subtitle || t('hero.subtitle', 'A complete platform for teams who care about craft, speed and detail.');
  const resolvedMetrics = metrics.length
    ? metrics
    : [
        { label: t('hero.metric_1', 'Projects delivered'), value: '1,200+' },
        { label: t('hero.metric_2', 'Client retention'), value: '98%' },
        { label: t('hero.metric_3', 'Avg. response'), value: '< 4h' },
      ];

  const renderBadge = () =>
    badge === null ? null : (
      <span
        className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium"
        style={{ borderColor: 'var(--t-border)', color: 'var(--t-primary)' }}
      >
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {badge || t('hero.badge', 'Design studio')}
      </span>
    );

  const renderActions = () => (
    <div className="mt-8 flex flex-col gap-3 sm:flex-row">
      <button type="button" onClick={onPrimary} className="btn-primary justify-center">
        {primaryLabel || t('hero.primary', 'View work')}
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </button>
      <button type="button" onClick={onSecondary} className="btn-outline justify-center">
        <PlayCircle className="h-4 w-4" aria-hidden="true" />
        {secondaryLabel || t('hero.secondary', 'See it in action')}
      </button>
    </div>
  );

  return (
    <section className={cn('relative overflow-hidden px-6 py-16 sm:py-24', className)}>
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        style={{ background: 'radial-gradient(60% 50% at 50% 0%, color-mix(in srgb, var(--t-primary) 12%, transparent), transparent 70%)' }}
      />
      <div className="relative mx-auto max-w-7xl">
        <div>
          <div className="flex flex-wrap items-baseline justify-between gap-4">
            {renderBadge()}
            <span className="text-xs uppercase tracking-[0.3em]" style={{ color: 'var(--t-muted)' }}>{BRAND.initials}</span>
          </div>
          <h1 className="mt-6 max-w-4xl text-5xl font-bold leading-[1.02] sm:text-7xl">{title} <em className="not-italic" style={{ color: 'var(--t-primary)' }}>{highlight}</em></h1>
          <p className="mt-7 max-w-2xl text-base leading-relaxed sm:text-lg" style={{ color: 'var(--t-muted)' }}>{subtitle}</p>
          {renderActions()}
          <div className="mt-14 grid gap-3 sm:grid-cols-3">
            <LazyImage src={image} alt={imageAlt} className="h-56 w-full rounded object-cover sm:col-span-2" />
            <div className="card-panel p-6">
              <ul className="space-y-3 text-sm">
                {metrics.map((metric) => (
                  <li key={metric.label} className="flex justify-between gap-3">
                    <span style={{ color: 'var(--t-muted)' }}>{metric.label}</span>
                    <strong>{metric.value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
