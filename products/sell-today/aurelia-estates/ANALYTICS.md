# Analytics Setup Guide — Realestate

## Recommended Provider Stack

- **Primary:** ga4 (region-optimised for MENA)
- **Secondary:** PostHog (session recording + feature flags)

## Environment Variables

```bash
VITE_GA4_ID=G-XXXXXXXXXX
VITE_POSTHOG_KEY=phc_xxxxx
VITE_POSTHOG_HOST=https://malikusmangoraya.github.io/aurelia-estates
VITE_PLAUSIBLE_DOMAIN=yourdomain.com
VITE_MIXPANEL_TOKEN=xxxxxxxxx
VITE_FATHOM_SITE_ID=XXXXXXX
```

## Conversion Goals

The following events are tracked as conversions:

- `contact_submitted`
- `sign_up`

## Event Taxonomy

| Event               | Trigger                   | Key Parameters            |
| ------------------- | ------------------------- | ------------------------- |
| `page_view`         | Page load                 | page_title, page_location |
| `scroll`            | 25/50/75/90% scroll depth | percent_scrolled          |
| `click`             | Link/button click         | link_text, link_url       |
| `search`            | Site search               | search_term               |
| `contact_submitted` | Contact form submitted    | form_id                   |
| `sign_up`           | Newsletter/account signup | method                    |
| `share`             | Social share button click | method, content_type      |

## Quick Start

```jsx
import useAnalytics from '@/hooks/useAnalytics';

function CheckoutButton({ item }) {
  const { trackEvent } = useAnalytics();
  return (
    <button
      onClick={() =>
        trackEvent('add_to_cart', {
          currency: 'USD',
          value: item.price,
          items: [item],
        })
      }
    >
      Add to Cart
    </button>
  );
}
```
