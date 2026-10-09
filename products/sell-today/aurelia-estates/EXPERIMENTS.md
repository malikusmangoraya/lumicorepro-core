# A/B Testing & Feature Flags — Realestate Website

## Experiments

| ID                 | Name               | Priority | Min Sample | Expected Lift |
| ------------------ | ------------------ | -------- | ---------- | ------------- |
| `hero_headline`    | Hero Headline Copy | high     | 500        | 10-20%        |
| `contact_form_cta` | Contact Form CTA   | high     | 200        | 15-30%        |

### Experiment Details

#### Hero Headline Copy (`hero_headline`)

**Hypothesis:** Benefit-focused headline outperforms feature-focused
**Success Metric:** `scroll_depth`
**Variants:**

- `control`: Feature-focused (50% traffic)
- `variant_a`: Benefit-focused (50% traffic)

#### Contact Form CTA (`contact_form_cta`)

**Hypothesis:** 'Send Message' vs 'Get Free Consultation' increases submissions
**Success Metric:** `form_submission_rate`
**Variants:**

- `control`: Send Message (50% traffic)
- `variant_a`: Get Free Consultation (50% traffic)

## Feature Flags

| Key                | Description             | Default | Rollout % |
| ------------------ | ----------------------- | ------- | --------- |
| `dark_mode`        | Dark mode toggle        | False   | 100%      |
| `newsletter_popup` | Newsletter signup popup | True    | 80%       |
| `chat_widget`      | Live chat widget        | False   | 50%       |

## Implementation Guide

1. Install PostHog: `npm install posthog-js`
2. Add `VITE_POSTHOG_KEY=phc_xxx` to `.env`
3. Call `initPostHog()` in `main.jsx`
4. Use `useExperiment('hero_cta_text', variants)` hook in components
5. Monitor results in PostHog Experiments dashboard

> Run each experiment for minimum 2 weeks for statistical significance.
