/**
 * Cart — shopping cart with quantity adjust, remove, and checkout CTA.
 * Persisted via Zustand; empty/loading/error states included.
 */
import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import { Trash2, ChevronLeft, Plus, Minus, CreditCard } from 'lucide-react';
import { useCart, useCartTotals } from '@/store/cartStore';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import api from '@/services/api';
import { IMAGES } from './images';

export default function Cart() {
  const { t } = useTranslation();
  const { items, removeItem, updateQty, clear } = useCart();
  const { count, subtotal, shipping, total } = useCartTotals();
  const navigate = useNavigate();
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState(null);

  if (items.length === 0) {
    return (
      <section className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-4">
            <svg className="h-10 w-10 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 004 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-medium">{t('restaurant.cart.empty', 'Your cart is empty')}</h3>
          <p className="text-muted-foreground mt-2">{t('restaurant.cart.emptyDesc', 'Add some delicious items from the menu')}</p>
          <Button asChild variant="primary" size="lg" className="mt-6">
            <Link to="/restaurant/menu">{t('restaurant.menu.viewMenu', 'Browse Menu')}</Link>
          </Button>
        </div>
      </section>
    );
  }

  const handleCheckout = async (e) => {
    e.preventDefault();
    setPlacing(true);
    setError(null);
    try {
      const orderItems = items.map((i) => ({ productId: i.serverId || i.id, qty: i.qty }));
      await api.post('/restaurant/orders', { items: orderItems, notes: '' });
      clear();
      navigate('/restaurant/checkout/success');
    } catch (err) {
      setError(err.message || 'Failed to place order. Please try again.');
    } finally {
      setPlacing(false);
    }
  };

  return (
    <section className="min-h-screen bg-background text-foreground">
      <nav className="container mx-auto px-4 py-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/restaurant/menu">
            <ChevronLeft className="h-4 w-4 mr-2" /> {t('common.back', 'Back to menu')}
          </Link>
        </Button>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              {t('common.dismiss', 'Dismiss')}
            </Button>
          </div>
        )}

        <div className="grid lg:grid-cols-12 gap-8">
          {/* Cart items */}
          <div className="lg:col-span-8">
            <div className="flex justify-between items-baseline mb-6">
              <h2 className="text-2xl font-display font-bold">{t('restaurant.cart.heading', 'Your Cart')}</h2>
              <span className="text-primary font-semibold">{count} item{count !== 1 ? 's' : ''}</span>
            </div>
            <div className="space-y-4">
              {items.map((item) => (
                <Card key={item.id} className="p-4 flex flex-col md:flex-row gap-4 items-start">
                  <div className="flex-shrink-0 relative">
                    <img
                      src={item.image || IMAGES.fallback}
                      alt={item.name}
                      className="w-20 h-20 object-cover rounded-lg"
                      loading="lazy"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{item.name}</h3>
                    <p className="text-sm text-muted-foreground">${Number(item.price).toFixed(2)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => updateQty(item.id, Math.max(1, item.qty - 1))}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="w-8 text-center font-medium">{item.qty}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => updateQty(item.id, item.qty + 1)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                      onClick={() => removeItem(item.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => {
                clear();
                setError(null);
              }}
              className="mt-4 text-sm text-destructive"
            >
              {t('restaurant.cart.clear', 'Clear cart')}
            </Button>
          </div>

          {/* Order summary */}
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
                  <span className={items.length ? 'text-primary font-medium' : 'text-muted-foreground'}>
                    ${shipping.toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="border-t border-border pt-4 mb-6">
                <div className="flex justify-between text-lg font-bold">
                  <span>{t('restaurant.cart.total', 'Total')}</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>
              <form onSubmit={handleCheckout} className="space-y-3">
                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={placing}
                  disabled={placing}
                  className="text-lg"
                  leftIcon={CreditCard}
                >
                  {placing ? t('common.placing', 'Placing order…') : t('restaurant.cart.checkout', 'Proceed to Checkout')}
                </Button>
                <p className="text-xs text-center text-muted-foreground">
                  {t('restaurant.cart.note', 'Secure checkout. No card stored.')}
                </p>
              </form>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
