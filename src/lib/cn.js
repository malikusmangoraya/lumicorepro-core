import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge conditional class names and de-duplicate conflicting Tailwind utilities.
 * shadcn/ui's standard `cn` helper — kept here so shadcn components and any
 * consumer can compose classes without fighting the existing design-system tokens.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export default cn;
