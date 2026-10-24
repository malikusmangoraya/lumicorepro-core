/**
 * Checkout — order summary page with confirmation + success state.
 */
import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle2, CreditCard, Clock, MapPin, Phone } from 'lucide-react';
import { useCart, useCartTotals } from '@/store/cartStore';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/services/api';

export default function Checkout() {
  const { t } = useTranslation();
  const { items, clear } = useCart();
  const { count, subtotal, shipping, total } = useCartTotals();
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState('summary'); // summary | success

  useEffect(() => {
    if (location.pathname.includes('/success')) setStep('success');
  }, [location.pathname]);

  const handlePlaceOrder = useCallback(async () => {
    setStep('success');
    clear();
    navigate('/restaurant/checkout/success', { replace: true });
  }, [clearCart, navigate]);

  if (step === 'success') {
    return (
      <section className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center space-y-6">
          <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-2xl font-display font-bold">{t('restaurant.checkout.success', 'Order Placed!')}</h2>
          <p className="text-muted-foreground">
            {t('restaurant.checkout.successDesc', 'Your food is being prepared. You will receive a confirmation shortly.')}
          </p>
          <Card className="mt-8 p-6 max-w-md mx-auto border border-green-100 dark:border-green-900/30">
            <div className="flex items-start gap-3 mb-4">
              <CreditCard className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              <div>
                <p className="font-medium">Order Confirmed</p>
                <p className="text-sm text-muted-foreground">Thank you for your order!</p>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t('restaurant.checkout.items', 'Items')}</span>
                <span>{count}</span>
              </div>
              <div className="flex justify-between font-semibold">
                <span>{t('restaurant.cart.total', 'Total')}</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
            <div className="mt-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm flex items-start gap-3">
              <Clock className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">{t('restaurant.checkout.eta', 'Estimated time')}</p>
                <p className="font-semibold">30–45 minutes</p>
              </div>
            </div>
          </Card>
          <div className="mt-8 flex gap-3">
            <Button variant="outline" onClick={() => navigate('/restaurant/menu')}>
              {t('restaurant.checkout.orderMore', 'Order More')}
            </Button>
            <Button onClick={() => navigate('/restaurant/orders')}>
              {t('restaurant.checkout.trackOrder', 'Track Order')}
            </Button>
          </div>
        </div>
      </section>
    );
  }

  if (items.length === 0) {
    navigate('/restaurant/cart');
    return null;
  }

  return (
    <section className="min-h-screen bg-background text-foreground">
      <nav className="container mx-auto px-4 py-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/restaurant/cart">
            <span>&larr;</span> {t('common.back', 'Back to cart')}
          </Link>
        </Button>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-12 gap-8">
          {/* Summary */}
          <div className="lg:col-span-8">
            <h2 className="text-2xl font-display font-bold mb-8">{t('restaurant.checkout.review', 'Review Order')}</h2>
            <div className="space-y-4">
              {items.map((item) => (
                <Card key={item.id} className="p-4 flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{item.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {item.qty}x ${Number(item.price).toFixed(2)}
                    </p>
                  </div>
                  <span className="font-semibold">${(Number(item.price) * item.qty).toFixed(2)}</span>
                </Card>
              ))}
            </div>
          </div>

          {/* Totals + action */}
          <div className="lg:col-span-4">
            <Card className="p-6 sticky top-24">
              <h3 className="font-semibold mb-6">{t('restaurant.cart.summary', 'Order Summary')}</h3>
              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-sm">
                  <span>{t('restaurant.cart.subtotal', 'Subtotal')}</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>{t('restaurant.cart.delivery', 'Delivery')}</span>
                  <span className="text-primary font-medium">${shipping.toFixed(2)}</span>
                </div>
              </div>
              <div className="border-t border-border pt-4 mb-6">
                <div className="flex justify-between text-lg font-bold text-primary">
                  <span>{t('restaurant.cart.total', 'Total')}</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>
              <div className="space-y-3">
                <Badge variant="secondary" className="w-full">
                  {t('restaurant.checkout.paymentMethod', 'Payment on Delivery')}
                </Badge>
                <Button
                  onClick={handlePlaceOrder}
                  variant="primary"
                  fullWidth
                  className="text-lg"
                  leftIcon={CreditCard}
                >
                  {t('restaurant.checkout.confirm', 'Confirm & Place Order')}
                </Button>
              </div>
            </Card>
            <div className="mt-6 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm flex items-start gap-3">
              <MapPin className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">{t('restaurant.checkout.pickup', 'Pickup / Delivery')}</p>
                <p className="font-semibold">123 Taste Street, Flavor City</p>
              </div>
            </div>
            <div className="mt-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 text-sm flex items-start gap-3">
              <Phone className="h-4 w-4 mt-0.5" />
              <div>
                <p className="font-medium">{t('restaurant.checkout.contact', 'Contact')}</p>
                <p className="font-semibold">+1 (555) 123-4567</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
