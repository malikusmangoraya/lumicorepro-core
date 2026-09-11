import { useMemo, useState } from 'react';
import { Search, Star, ShoppingCart } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge, Input } from '@/components/ui';
import { products, categories } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';
import { img } from '@/utils/images';

const PRODUCT_IMGS = [
  img.ecommerce.product1,
  img.ecommerce.product2,
  img.ecommerce.product3,
  img.ecommerce.product4,
  img.ecommerce.product5,
  img.ecommerce.product6,
  img.ecommerce.product7,
  img.ecommerce.product8,
];

export default function ProductListing() {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState('all');
  const q = useDebounce(query);
  const list = useMemo(
    () =>
      products.filter(
        (p) =>
          (cat === 'all' || p.category === cat) && p.name.toLowerCase().includes(q.toLowerCase())
      ),
    [q, cat]
  );

  return (
    <TemplateShell
      title="Product Listing"
      description="Browse, filter, and sort products."
      category="E-Commerce"
    >
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="md:w-48 shrink-0 space-y-2">
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCat(c.id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                cat === c.id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              {c.label}
            </button>
          ))}
        </aside>
        <div className="flex-1 space-y-4">
          <Input
            leftIcon={Search}
            placeholder="Search products…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((p, i) => (
              <Card
                key={p.id}
                hoverable
                animate="fade-up"
                animationDelay={i * 50}
                className="overflow-hidden group"
                padding="none"
              >
                <div className="relative aspect-square overflow-hidden">
                  <img
                    src={PRODUCT_IMGS[i % PRODUCT_IMGS.length]}
                    alt={p.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="h-8 w-8 rounded-full bg-background/90 backdrop-blur flex items-center justify-center shadow-md hover:bg-primary hover:text-primary-foreground transition-colors">
                      <ShoppingCart className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold">{p.name}</h3>
                    <Badge size="sm" variant="secondary">
                      {p.category}
                    </Badge>
                  </div>
                  <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                    <Star className="h-3.5 w-3.5 fill-primary text-primary" />
                    {p.rating}
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="font-display text-lg font-bold">${p.price}</span>
                    <Button size="sm">Add</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </TemplateShell>
  );
}
