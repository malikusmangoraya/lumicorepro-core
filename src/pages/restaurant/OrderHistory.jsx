/**
 * OrderHistory — customer orders with status tracking.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Clock, Truck, CheckCircle2, XCircle, Loader, RefreshCw } from 'lucide-react';
import { useCart } from '@/store/cartStore';
import { useAuth } from '@/context/AuthContext';
import { useSocket } from '@/hooks/useSocket';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/services/api';

const STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Preparing',
  shipped: 'Out for Delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  refunded: 'Refunded',
};
const STATUS_COLORS = {
  pending: 'warning',
  processing: 'info',
  shipped: 'info',
  delivered: 'success',
  cancelled: 'destructive',
  refunded: 'destructive',
};

export default function OrderHistory() {
  const { t } = useTranslation();
  const { count } = useCart();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/restaurant/orders');
      setOrders(res.data.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Silent refresh: a status push must not flash the full-page spinner.
  const refreshOrders = useCallback(async () => {
    try {
      const res = await api.get('/restaurant/orders');
      setOrders(res.data.data || []);
      setError(null);
    } catch {
      // Keep the last known list; the manual retry path surfaces the error.
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const { connected: live } = useSocket(user?.id ? `user:${user.id}` : null, {
    'order:created': refreshOrders,
    'order:updated': refreshOrders,
  });

  const handleRetry = async () => {
    setRefreshing(true);
    await fetchOrders();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <section className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <Loader className="h-8 w-8 animate-spin" />
      </section>
    );
  }

  return (
    <section className="min-h-screen bg-background text-foreground">
      <nav className="container mx-auto px-4 py-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/restaurant/menu">
            <span>&larr;</span> {t('common.back', 'Back to menu')}
          </Link>
        </Button>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-baseline mb-8">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-display font-bold">{t('restaurant.orders.title', 'My Orders')}</h1>
            {live && (
              <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                {t('common.live', 'Live')}
              </span>
            )}
          </div>
          <Link to="/restaurant/cart" className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 004 0z" />
            </svg>
            {count} item{count !== 1 ? 's' : ''}
          </Link>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={handleRetry} loading={refreshing}>
              {t('common.retry', 'Retry')}
            </Button>
          </div>
        )}

        {!error && orders.length === 0 && (
          <div className="text-center py-20">
            <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-medium">{t('restaurant.orders.empty', 'No orders yet')}</h3>
            <p className="text-muted-foreground mt-2">{t('restaurant.orders.emptyDesc', 'Place your first order from the menu')}</p>
            <Button variant="primary" asChild>
              <Link to="/restaurant/menu">{t('restaurant.menu.viewMenu', 'Browse Menu')}</Link>
            </Button>
          </div>
        )}

        {!error && orders.length > 0 && (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} className="p-6 border border-border">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold">Order #{order.orderNumber}</h3>
                    <p className="text-sm text-muted-foreground">
                      {new Date(order.createdAt).toLocaleDateString()} • {order.paymentMethod}
                    </p>
                  </div>
                  <Badge variant={STATUS_COLORS[order.status] || 'secondary'}>
                    {STATUS_LABELS[order.status] || order.status}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                  <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">{t('restaurant.orders.total', 'Total')}</p>
                    <p className="font-semibold">${Number(order.totalPrice || 0).toFixed(2)}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/50 border border-border/50 flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${order.status === 'delivered' ? 'bg-green-500' : order.status === 'cancelled' ? 'bg-red-500' : 'bg-amber-500 animate-pulse'}`} />
                    <span className="text-sm">{t('restaurant.orders.status', 'Status')}: {STATUS_LABELS[order.status] || order.status}</span>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground text-right">
                  {order.status === 'delivered'
                    ? t('restaurant.orders.delivered', 'Delivered')
                    : order.status === 'cancelled'
                    ? t('restaurant.orders.cancelled', 'Cancelled')
                    : t('restaurant.orders.preparing', 'Your order is being prepared')}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
