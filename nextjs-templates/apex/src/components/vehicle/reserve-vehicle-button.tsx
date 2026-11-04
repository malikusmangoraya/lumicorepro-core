'use client';

import { useRouter } from 'next/navigation';
import { ShoppingBag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSite } from '@/components/providers/site-provider';

export function ReserveVehicleButton({
  slug,
  title,
  price,
  currency,
  image,
}: {
  slug: string;
  title: string;
  price: number;
  currency: string;
  image: string | null;
}) {
  const router = useRouter();
  const { addToCart, notify } = useSite();

  return (
    <Button
      fullWidth
      onClick={() => {
        addToCart({ kind: 'vehicle', slug, title, price, currency, image });
        notify(`${title} added to your bag`);
        router.push('/checkout');
      }}
    >
      <ShoppingBag className="size-4" aria-hidden="true" />
      Reserve this car
    </Button>
  );
}
