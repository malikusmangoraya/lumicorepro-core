/**
 * LazyLayouts — React.lazy() registry for alternative layout templates.
 * Platform TRD: strict dynamic lazy loading for alternative layouts;
 * each template ships its own Suspense boundary with a CLS-safe skeleton.
 */
import React, { Suspense } from 'react';
import LayoutSkeleton from '../components/common/LayoutSkeleton';

export const LandingLayout = React.lazy(() => import('../layouts/LandingLayout'));
export const AppLayout = React.lazy(() => import('../layouts/AppLayout'));

export function withLayout(Layout) {
  return function LazyLayout(props) {
    return (
      <Suspense fallback={<LayoutSkeleton />}>
        <Layout {...props} />
      </Suspense>
    );
  };
}

export default { LandingLayout, AppLayout, withLayout };
