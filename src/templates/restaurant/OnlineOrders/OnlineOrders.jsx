import { useState } from 'react';
import { Check, ChefHat, Bike, Box, Package, RefreshCw, ShieldCheck } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { orderSteps, orders, deliveryPromise } from './data/mockData';

const STEP_ICONS = [ChefHat, Package, Bike, Box];

export default function OnlineOrders() {
  const [activeOrder, setActiveOrder] = useState(orders[0].id);
  const order = orders.find((o) => o.id === activeOrder);

  return (
    <TemplateShell
      title="Online Orders & Delivery"
      description="Track your food live — from the kitchen to your doorstep."
      category="Restaurant"
      actions={
        <Button size="sm">
          <Bike className="h-4 w-4 mr-1" />
          Order Delivery
        </Button>
      }
    >
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border h-44 mb-6">
        <img
          src={img.restaurant.hero}
          alt="Restaurant"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex items-end p-8">
          <div>
            <Badge className="mb-2 w-fit bg-emerald-500/90">Live order tracking</Badge>
            <h2 className="font-display text-2xl font-bold text-white">
              From Wok to Doorstep in 45 Minutes
            </h2>
          </div>
        </div>
      </div>

      {/* Order selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {orders.map((o) => (
          <button
            key={o.id}
            onClick={() => setActiveOrder(o.id)}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-bold transition-all border',
              activeOrder === o.id
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {o.id}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Progress tracker */}
        <Card animate="fade-up" className="lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-display font-bold">Order {order.id}</h3>
              <p className="text-xs text-muted-foreground">{order.items}</p>
            </div>
            <div className="text-right">
              <p className="font-display font-bold text-primary">{order.total}</p>
              <p className="text-xs text-muted-foreground">{order.payment}</p>
            </div>
          </div>

          {/* Stepper */}
          <div className="flex items-center">
            {orderSteps.map((step, i) => {
              const Icon = STEP_ICONS[i];
              const done = i <= order.step;
              const current = i === order.step;
              return (
                <div
                  key={step}
                  className={cn('flex items-center', i < orderSteps.length - 1 && 'flex-1')}
                >
                  <div className="flex flex-col items-center gap-1.5">
                    <div
                      className={cn(
                        'h-11 w-11 rounded-full flex items-center justify-center transition-all',
                        done
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-muted text-muted-foreground',
                        current && 'ring-2 ring-emerald-400/60 shadow-glow-sm'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <span
                      className={cn(
                        'text-[11px] font-medium',
                        done ? 'text-emerald-400' : 'text-muted-foreground'
                      )}
                    >
                      {step}
                    </span>
                  </div>
                  {i < orderSteps.length - 1 && (
                    <div
                      className={cn(
                        'flex-1 h-0.5 mx-2 mb-6',
                        done ? 'bg-emerald-400/60' : 'bg-muted'
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
              ETA: <span className="font-bold text-foreground">{order.eta}</span>
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" className="h-8 text-xs">
                Contact Rider
              </Button>
              <Button size="sm" className="h-8 text-xs">
                Reorder
              </Button>
            </div>
          </div>
        </Card>

        {/* Delivery promise */}
        <Card animate="fade-up" animationDelay={100}>
          <h3 className="font-display font-bold mb-4 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            Our Delivery Promise
          </h3>
          <div className="space-y-4">
            {deliveryPromise.map((p, i) => (
              <div key={i} className="flex gap-3">
                <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <Check className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{p.label}</p>
                  <p className="text-xs text-muted-foreground">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <Progress value={72} className="h-1.5 mt-5" />
          <p className="text-xs text-muted-foreground mt-2">
            72% of orders arrive within 40 minutes
          </p>
        </Card>
      </div>
    </TemplateShell>
  );
}
