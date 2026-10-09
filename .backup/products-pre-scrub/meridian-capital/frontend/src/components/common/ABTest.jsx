/**
 * ABTest — Declarative A/B Test Wrapper Component
 * Auto-generated for A/B testing & feature flagging
 *
 * Usage:
 *   <ABTest
 *     experimentId="hero_cta_text"
 *     variants={[
 *       { id: 'control',   weight: 0.5, children: <Button>Shop Now</Button> },
 *       { id: 'variant_a', weight: 0.5, children: <Button>Explore</Button> },
 *     ]}
 *   />
 */

import { useExperiment } from '@/hooks/useExperiment';

export default function ABTest({ experimentId, variants = [], fallback = null }) {
  const assignedVariant = useExperiment(
    experimentId,
    variants.map(({ id, weight }) => ({ id, weight }))
  );

  const match = variants.find((v) => v.id === assignedVariant);
  return match?.children ?? fallback ?? null;
}

/**
 * FeatureFlag — Conditional render based on feature flag
 *
 * Usage:
 *   <FeatureFlag flag="show_ai_recommendations">
 *     <AIRecommendations />
 *   </FeatureFlag>
 */
export function FeatureFlag({ flag, defaultValue = false, children, fallback = null }) {
  const { useFeatureFlag } = require('@/hooks/useExperiment');
  const enabled = useFeatureFlag(flag, defaultValue);
  return enabled ? children : fallback;
}
