/**
 * Order state machine and totals.
 *
 * Kept pure so the rules can be tested without a database, and so the UI and the
 * API agree on what is allowed. A status change that skips a step is how money
 * and goods get out of sync, so transitions are explicit rather than a free
 * text field.
 */

export const ORDER_STATUSES = [
  'pending',
  'paid',
  'processing',
  'shipped',
  'delivered',
  'cancelled',
  'refunded',
] as const;

export type OrderStatus = (typeof ORDER_STATUSES)[number];

const TRANSITIONS: Record<OrderStatus, readonly OrderStatus[]> = {
  pending: ['paid', 'cancelled'],
  paid: ['processing', 'refunded', 'cancelled'],
  processing: ['shipped', 'refunded', 'cancelled'],
  shipped: ['delivered', 'refunded'],
  delivered: ['refunded'],
  cancelled: [],
  refunded: [],
};

export const TERMINAL_STATUSES: readonly OrderStatus[] = ['delivered', 'cancelled', 'refunded'];

export function canTransition(from: string, to: string): boolean {
  if (from === to) return false;
  const allowed = TRANSITIONS[from as OrderStatus];
  if (!allowed) return false;
  return allowed.includes(to as OrderStatus);
}

export function nextStatuses(from: string): readonly OrderStatus[] {
  return TRANSITIONS[from as OrderStatus] ?? [];
}

export function isTerminal(status: string): boolean {
  return TERMINAL_STATUSES.includes(status as OrderStatus);
}

/** Shipping/delivery only make sense once money is in. */
export function requiresTracking(status: string): boolean {
  return status === 'shipped' || status === 'delivered';
}

export type OrderLine = { unitPrice: number; quantity: number };

export type OrderTotals = {
  subtotal: number;
  discount: number;
  tax: number;
  shipping: number;
  total: number;
};

const round = (value: number) => Math.round(value * 100) / 100;

export function calculateTotals(
  lines: OrderLine[],
  options: { discount?: number; taxRate?: number; shipping?: number } = {},
): OrderTotals {
  const subtotal = round(
    lines.reduce((sum, line) => sum + Math.max(0, line.unitPrice) * Math.max(0, line.quantity), 0),
  );
  const discount = round(Math.min(Math.max(0, options.discount ?? 0), subtotal));
  const taxable = subtotal - discount;
  const tax = round(taxable * Math.max(0, options.taxRate ?? 0));
  const shipping = round(Math.max(0, options.shipping ?? 0));
  return { subtotal, discount, tax, shipping, total: round(taxable + tax + shipping) };
}

/** Human-readable next action for the admin list. */
export function primaryAction(status: string): { to: OrderStatus; label: string } | null {
  switch (status) {
    case 'pending':
      return { to: 'paid', label: 'Mark paid' };
    case 'paid':
      return { to: 'processing', label: 'Start processing' };
    case 'processing':
      return { to: 'shipped', label: 'Mark shipped' };
    case 'shipped':
      return { to: 'delivered', label: 'Mark delivered' };
    default:
      return null;
  }
}
