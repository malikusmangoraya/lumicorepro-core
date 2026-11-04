'use client';

import { useState } from 'react';
import { Check, ShoppingBag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSite } from '@/components/providers/site-provider';

export function AddToCartButton({
  kind,
  slug,
  title,
  price,
  currency,
  image,
  disabled,
}: {
  kind: 'product' | 'vehicle';
  slug: string;
  title: string;
  price: number;
  currency: string;
  image: string | null;
  disabled?: boolean;
}) {
  const { addToCart, notify, t } = useSite();
  const [added, setAdded] = useState(false);

  return (
    <Button
      variant={added ? 'outline' : 'primary'}
      fullWidth
      disabled={disabled}
      onClick={() => {
        addToCart({ kind, slug, title, price, currency, image });
        notify(`${title} added to your bag`);
        setAdded(true);
        window.setTimeout(() => setAdded(false), 2000);
      }}
    >
      {added ? (
        <>
          <Check className="size-4" aria-hidden="true" />
          {t('common.added')}
        </>
      ) : (
        <>
          <ShoppingBag className="size-4" aria-hidden="true" />
          {disabled ? t('common.outOfStock') : kind === 'vehicle' ? t('common.reserve') : t('common.addToBag')}
        </>
      )}
    </Button>
  );
}
