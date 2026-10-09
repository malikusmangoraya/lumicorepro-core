import React, { useState } from 'react';
import { ShoppingBag, X, Zap } from 'lucide-react';
import { openLemonSqueezyCheckout } from '../../services/lemonSqueezy';

export default function BuyTemplateBanner({
  templateName = 'apex',
  price = '$49',
  checkoutUrl = '',
}) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const handleBuy = () => {
    openLemonSqueezyCheckout({
      checkoutUrl,
      customData: { product: templateName, price },
      onSuccess: () => alert(`Thank you for purchasing ${templateName}!`),
    });
  };

  return (
    <div className="fixed top-0 inset-x-0 z-[60] bg-gradient-to-r from-cyan-600 via-indigo-600 to-violet-600 px-4 py-2 text-white shadow-xl">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs sm:text-sm font-medium">
        <div className="flex items-center gap-2 truncate">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/20">
            <Zap className="h-3.5 w-3.5" />
          </span>
          <span className="truncate">
            Previewing <strong>{templateName}</strong> &bull; Commercial License &amp; Full Code
            Access
          </span>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={handleBuy}
            className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1 text-xs font-bold text-slate-950 shadow hover:bg-slate-100 active:scale-95 transition-all"
          >
            <ShoppingBag className="h-3.5 w-3.5 text-cyan-600" />
            <span>Buy Template &bull; {price}</span>
          </button>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            className="p-1 text-white/80 hover:text-white rounded"
            aria-label="Dismiss banner"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
