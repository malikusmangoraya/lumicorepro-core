# Analytics Setup Guide — Saas

## Recommended Provider Stack

- **Primary:** ga4 (region-optimised for SA)
- **Secondary:** PostHog (session recording + feature flags)

## Environment Variables

```bash
VITE_GA4_ID=G-XXXXXXXXXX
VITE_POSTHOG_KEY=phc_xxxxx
VITE_POSTHOG_HOST=https://app.posthog.com
VITE_PLAUSIBLE_DOMAIN=yourdomain.com
VITE_MIXPANEL_TOKEN=xxxxxxxxx
VITE_FATHOM_SITE_ID=XXXXXXX
```

## Conversion Goals

The following events are tracked as conversions:

- `subscription_created`
- `trial_started`
- `sign_up`
- `trial_converted`

## Event Taxonomy

| Event                    | Trigger                   | Key Parameters                 |
| ------------------------ | ------------------------- | ------------------------------ |
| `sign_up`                | Account created           | method, plan                   |
| `login`                  | User logged in            | method                         |
| `trial_started`          | Free trial started        | plan, trial_days               |
| `trial_converted`        | Trial → paid conversion   | plan, value, currency          |
| `plan_selected`          | Pricing page plan click   | plan_id, plan_name, value      |
| `subscription_created`   | Subscription confirmed    | plan_id, value, currency       |
| `subscription_cancelled` | Cancellation confirmed    | plan_id, reason                |
| `feature_used`           | Key feature interaction   | feature_name, feature_category |
| `onboarding_step`        | Onboarding step completed | step, step_name                |
| `onboarding_completed`   | Full onboarding done      | duration_seconds               |
| `invite_sent`            | Team member invited       | invitee_role                   |
| `search`                 | In-app search             | search_term, results_count     |

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
