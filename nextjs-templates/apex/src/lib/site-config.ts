/**
 * One place for the facts that appear in the footer, the JSON-LD and the
 * floating contact buttons. A dealership that shows a different phone number in
 * two places loses trust, so nothing duplicates these strings.
 */

export const site = {
  name: 'Apex Motor Collective',
  legalName: 'Apex Digital',
  tagline: 'Your next car, found faster.',
  url: process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000',
  email: 'hello@apex.com',
  phone: '+1 (555) 019-2834',
  phoneHref: 'tel:+15550192834',
  whatsapp: process.env.NEXT_PUBLIC_WHATSAPP ?? '',
  address: {
    street: '750 Innovation Way, Suite 400',
    city: 'Los Angeles',
    region: 'CA',
    postalCode: '90012',
    country: 'US',
  },
  geo: { latitude: 34.0522, longitude: -118.2437 },
  hours: [
    { days: 'Monday – Friday', time: '09:00 – 18:00' },
    { days: 'Saturday', time: 'By appointment' },
    { days: 'Sunday', time: 'Closed' },
  ],
  /** Optional promo strip. Empty means no banner at all — never invent an offer. */
  promo: process.env.NEXT_PUBLIC_PROMO ?? '',
} as const;
