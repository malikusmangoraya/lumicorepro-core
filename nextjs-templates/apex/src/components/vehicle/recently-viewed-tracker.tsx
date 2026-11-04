'use client';

import { useEffect } from 'react';
import { useSite } from '@/components/providers/site-provider';

/** Records a vehicle view once per mount, for the "recently viewed" strip. */
export function RecentlyViewedTracker({ slug }: { slug: string }) {
  const { addRecent } = useSite();

  useEffect(() => {
    addRecent(slug);
  }, [slug, addRecent]);

  return null;
}
