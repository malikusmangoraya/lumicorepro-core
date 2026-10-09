/**
 * useExperiment — A/B Testing & Feature Flags Hook
 * Auto-generated for A/B testing & feature flagging
 *
 * Usage:
 *   const variant = useExperiment('hero_cta_text');
 *   const isEnabled = useFeatureFlag('show_ai_recommendations');
 */

import { useState, useEffect, useCallback } from 'react';

// Experiment IDs for this project
export const EXPERIMENT_IDS = ['hero_headline', 'contact_form_cta'];
export const FEATURE_FLAG_KEYS = ['dark_mode', 'newsletter_popup', 'chat_widget'];

// Storage key for consistent variant assignment
const STORAGE_KEY = 'lumicore_experiments';

function getStoredVariants() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  } catch {
    return {};
  }
}

function assignVariant(experimentId, variants) {
  const stored = getStoredVariants();
  if (stored[experimentId]) return stored[experimentId];

  // Weighted random assignment
  const rand = Math.random();
  let cumulative = 0;
  for (const v of variants) {
    cumulative += v.weight;
    if (rand < cumulative) {
      stored[experimentId] = v.id;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
      return v.id;
    }
  }
  return variants[0].id;
}

/**
 * Returns assigned variant id for an experiment
 * @param {string} experimentId
 * @param {Array} variants  — [{id, name, weight}]
 */
export function useExperiment(experimentId, variants = []) {
  const [variant, setVariant] = useState(() => {
    if (!variants.length) return 'control';
    return assignVariant(experimentId, variants);
  });

  useEffect(() => {
    // Track experiment exposure
    if (window.__posthog) {
      window.__posthog.capture('$experiment_started', {
        experiment: experimentId,
        variant,
      });
    }
    if (window.gtag) {
      window.gtag('event', 'experiment_impression', {
        experiment_id: experimentId,
        variant_id: variant,
      });
    }
  }, [experimentId, variant]);

  return variant;
}

/**
 * Returns boolean for a feature flag
 * @param {string} flagKey
 * @param {boolean} defaultValue
 */
export function useFeatureFlag(flagKey, defaultValue = false) {
  const [enabled, setEnabled] = useState(defaultValue);

  useEffect(() => {
    // Check PostHog feature flag
    if (window.__posthog?.isFeatureEnabled) {
      const isEnabled = window.__posthog.isFeatureEnabled(flagKey);
      if (isEnabled !== undefined) setEnabled(isEnabled);
    }
  }, [flagKey]);

  return enabled;
}

export default useExperiment;
