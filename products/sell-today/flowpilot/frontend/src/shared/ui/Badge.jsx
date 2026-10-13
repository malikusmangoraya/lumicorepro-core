/**
 * Badge — LUMI_UI_V8
 *
 * Status/category label. Tone colours are mixed toward --t-text so small text
 * keeps its contrast ratio against the tinted background instead of failing
 * 4.5:1 the way a raw status hue would.
 */
import React from 'react';
import { cn } from '../../utils.js';

const TONES = {
  neutral: 'bg-[color-mix(in_srgb,var(--t-muted)_12%,transparent)] text-[var(--t-heading)]',
  primary: 'bg-[color-mix(in_srgb,var(--t-primary)_14%,transparent)] text-[var(--t-primary)]',
  success:
    'bg-[color-mix(in_srgb,var(--t-success)_16%,transparent)] text-[color-mix(in_srgb,var(--t-success)_62%,var(--t-text))]',
  warning:
    'bg-[color-mix(in_srgb,var(--t-warn)_18%,transparent)] text-[color-mix(in_srgb,var(--t-warn)_55%,var(--t-text))]',
  danger:
    'bg-[color-mix(in_srgb,var(--t-error)_16%,transparent)] text-[color-mix(in_srgb,var(--t-error)_65%,var(--t-text))]',
};

const Badge = ({ tone = 'neutral', className, children, ...rest }) => (
  <span
    className={cn(
      'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold',
      TONES[tone] ?? TONES.neutral,
      className
    )}
    {...rest}
  >
    {children}
  </span>
);

export default Badge;
