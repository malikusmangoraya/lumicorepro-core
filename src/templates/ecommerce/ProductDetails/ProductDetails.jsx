import { useState } from 'react';
import { Heart, Star } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge } from '@/components/ui';
import { product } from './data/mockData';

export default function ProductDetails() {
  const [qty, setQty] = useState(1);
  const [size, setSize] = useState(product.sizes[0]);
  return (
    <TemplateShell
      title="Product Details"
      description="Gallery, variants, and purchase actions."
      category="E-Commerce"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card padding="none" className="overflow-hidden animate-scale-in">
          <div className="aspect-square bg-gradient-to-br from-primary/20 via-muted to-primary/5" />
        </Card>
        <div className="space-y-5 animate-fade-in-up">
          <Badge variant="info">{product.category}</Badge>
          <h2 className="font-display text-3xl font-bold">{product.name}</h2>
          <div className="flex items-center gap-2 text-sm">
            <Star className="h-4 w-4 fill-primary text-primary" />
            {product.rating} · {product.reviews} reviews
          </div>
          <p className="font-display text-3xl font-bold text-primary">${product.price}</p>
          <p className="text-muted-foreground leading-relaxed">{product.description}</p>
          <div>
            <p className="text-sm font-medium mb-2">Size</p>
            <div className="flex gap-2">
              {product.sizes.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSize(s)}
                  className={`h-10 w-10 rounded-lg border text-sm transition-all ${
                    size === s
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="inline-flex items-center rounded-lg border border-border">
              <Button variant="ghost" size="sm" onClick={() => setQty(Math.max(1, qty - 1))}>
                -
              </Button>
              <span className="w-10 text-center text-sm">{qty}</span>
              <Button variant="ghost" size="sm" onClick={() => setQty(qty + 1)}>
                +
              </Button>
            </div>
            <Button className="flex-1">Add to cart</Button>
            <Button variant="outline" aria-label="Wishlist">
              <Heart className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </TemplateShell>
  );
}
