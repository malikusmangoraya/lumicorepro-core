/**
 * Card — LUMI_UI_V8
 *
 * Surface container. `as` keeps the semantics the caller needs (article for a
 * listing, li inside a list) instead of forcing a div, and `interactive` only
 * adds the lift when the card really is clickable.
 */
import React from 'react';
import { cn } from '../../utils.js';

const Card = ({ as: Tag = 'div', interactive = false, className, children, ...rest }) => (
  <Tag
    className={cn(
      'rounded-[var(--t-radius-card,var(--t-radius-lg,1rem))] border border-[var(--t-border)]',
      'bg-[var(--t-surface)] p-6 shadow-[var(--t-shadow-md)]',
      'dark:border-[color-mix(in_srgb,var(--t-border)_75%,transparent)]',
      interactive && 'card-lift cursor-pointer',
      className
    )}
    {...rest}
  >
    {children}
  </Tag>
);

export default Card;
