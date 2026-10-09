import ButtonMotion from '@/components/ui/ButtonMotion';
import React from 'react';
import { ArrowRight, PlayCircle, Sparkles } from 'lucide-react';
import { cn, img } from '../../utils';
import LazyImage from '../common/LazyImage';

const Hero = ({
  badge = 'Trusted by 2,000+ teams',
  title = 'Build something extraordinary',
  highlight = 'today.',
  subtitle = 'A complete platform that turns ambitious ideas into polished, scalable products — fast, beautifully, and with everything you need to grow.',
  primaryLabel = 'Get started',
  secondaryLabel = 'Watch demo',
  onPrimary,
  onSecondary,
  image = img.business,
  imageAlt = 'Product preview',
  align = 'center',
  className = '',
}) => {
  return (
    <section className={cn('relative overflow-hidden py-20 sm:py-28', className)}>
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        style={{
          background:
            'radial-gradient(60% 50% at 50% 0%, hsl(var(--primary) / 0.12), transparent 70%)',
        }}
      />
      <div
        className={cn(
          'relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8',
          align === 'center' && 'flex flex-col items-center text-center'
        )}
      >
        <div className={cn('max-w-3xl', align === 'center' && 'mx-auto')}>
          {badge && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              {badge}
            </span>
          )}
          <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            {title} <span className="text-primary">{highlight}</span>
          </h1>
          <p className="mt-5 text-base text-muted-foreground sm:text-lg">{subtitle}</p>
          {(onPrimary || onSecondary) && (
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              {onPrimary && (
                <ButtonMotion
                  type="button"
                  onClick={onPrimary}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-all duration-200 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  {primaryLabel}
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </ButtonMotion>
              )}
              {onSecondary && (
                <ButtonMotion
                  type="button"
                  onClick={onSecondary}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border bg-background px-6 py-3 text-sm font-semibold text-foreground transition-all duration-200 hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/40"
                >
                  <PlayCircle className="h-4 w-4" aria-hidden="true" />
                  {secondaryLabel}
                </ButtonMotion>
              )}
            </div>
          )}
        </div>
        {image && (
          <div className="mt-12 overflow-hidden rounded-2xl border shadow-xl">
            <LazyImage
              src={image}
              alt={imageAlt}
              className="h-64 w-full object-cover sm:h-[26rem]"
            />
          </div>
        )}
      </div>
    </section>
  );
};

export default Hero;
