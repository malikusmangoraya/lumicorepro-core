/**
 * LayoutSkeleton — CLS-safe placeholder (reserved height, no layout shift).
 * Platform TRD: zero unhandled layout shifts, CLS budget < 0.1.
 */
export default function LayoutSkeleton({ minHeight = '70vh', shimmer = true }) {
  return (
    <div
      aria-hidden="true"
      className={shimmer ? 'skeleton-shimmer' : undefined}
      style={{ minHeight, width: '100%' }}
    />
  );
}
