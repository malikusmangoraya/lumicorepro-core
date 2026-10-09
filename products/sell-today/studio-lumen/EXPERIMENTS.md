# A/B Testing & Feature Flags — Saas Website

## Experiments

| ID                      | Name                   | Priority | Min Sample | Expected Lift |
| ----------------------- | ---------------------- | -------- | ---------- | ------------- |
| `pricing_page_layout`   | Pricing Page Highlight | critical | 300        | 18-30%        |
| `cta_trial_copy`        | Free Trial CTA Copy    | high     | 500        | 8-20%         |
| `social_proof_position` | Social Proof Placement | medium   | 400        | 10-15%        |

### Experiment Details

#### Pricing Page Highlight (`pricing_page_layout`)

**Hypothesis:** Highlighting 'Pro' plan increases Pro signups by 25%
**Success Metric:** `plan_selection_rate`
**Variants:**

- `control`: All plans equal (50% traffic)
- `variant_a`: Pro plan highlighted (50% traffic)

#### Free Trial CTA Copy (`cta_trial_copy`)

**Hypothesis:** 'Start free trial' vs 'Get started free' — testing urgency
**Success Metric:** `signup_rate`
**Variants:**

- `control`: Start free trial (33% traffic)
- `variant_a`: Get started free (33% traffic)
- `variant_b`: Try free for 14 days (34% traffic)

#### Social Proof Placement (`social_proof_position`)

**Hypothesis:** Testimonials above fold vs below — above increases signups
**Success Metric:** `signup_rate`
**Variants:**

- `control`: Below hero (50% traffic)
- `variant_a`: In hero section (50% traffic)

## Feature Flags

| Key                   | Description                       | Default | Rollout % |
| --------------------- | --------------------------------- | ------- | --------- |
| `new_onboarding_flow` | Redesigned onboarding wizard      | False   | 25%       |
| `ai_assistant`        | In-app AI assistant               | False   | 5%        |
| `advanced_analytics`  | Advanced analytics dashboard beta | False   | 15%       |

## Implementation Guide

1. Install PostHog: `npm install posthog-js`
2. Add `VITE_POSTHOG_KEY=phc_xxx` to `.env`
3. Call `initPostHog()` in `main.jsx`
4. Use `useExperiment('hero_cta_text', variants)` hook in components
5. Monitor results in PostHog Experiments dashboard

> Run each experiment for minimum 2 weeks for statistical significance.
