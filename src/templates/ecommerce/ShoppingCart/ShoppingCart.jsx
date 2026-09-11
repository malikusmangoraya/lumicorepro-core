import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Empty } from '@/components/ui';
import { items as seed } from './data/mockData';

export default function ShoppingCart() {
  const [items, setItems] = useState(seed);
  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
  const update = (id, qty) =>
    setItems((prev) => prev.map((i) => (i.id === id ? { ...i, qty: Math.max(1, qty) } : i)));
  const remove = (id) => setItems((prev) => prev.filter((i) => i.id !== id));

  return (
    <TemplateShell
      title="Shopping Cart"
      description="Review items and totals before checkout."
      category="E-Commerce"
    >
      {items.length === 0 ? (
        <Empty
          title="Cart is empty"
          description="Add products to continue."
          action={<Button>Browse products</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-3">
            {items.map((item, i) => (
              <Card
                key={item.id}
                className="flex gap-4 items-center hover-lift"
                animate="fade-up"
                animationDelay={i * 60}
              >
                <div className="h-16 w-16 rounded-lg bg-muted shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{item.name}</p>
                  <p className="text-sm text-muted-foreground">${item.price}</p>
                </div>
                <div className="inline-flex items-center rounded-lg border border-border">
                  <Button variant="ghost" size="sm" onClick={() => update(item.id, item.qty - 1)}>
                    -
                  </Button>
                  <span className="w-8 text-center text-sm">{item.qty}</span>
                  <Button variant="ghost" size="sm" onClick={() => update(item.id, item.qty + 1)}>
                    +
                  </Button>
                </div>
                <Button variant="ghost" size="sm" onClick={() => remove(item.id)}>
                  Remove
                </Button>
              </Card>
            ))}
          </div>
          <Card className="h-fit space-y-4" animate="fade-up" animationDelay={150}>
            <h3 className="font-display font-semibold">Summary</h3>
            <Input placeholder="Coupon code" />
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Subtotal</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Shipping</span>
              <span>$8.00</span>
            </div>
            <div className="flex justify-between font-semibold text-lg border-t border-border pt-3">
              <span>Total</span>
              <span>${(subtotal + 8).toFixed(2)}</span>
            </div>
            <Button className="w-full">Checkout</Button>
          </Card>
        </div>
      )}
    </TemplateShell>
  );
}
