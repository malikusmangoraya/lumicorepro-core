/**
 * AdminDashboard — restaurant admin: manage menu items, orders & stats.
 * Requires admin role (enforced by backend).
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Edit2, Trash2, Clock, CreditCard, Users, Settings, Loader,
  CheckCircle2, ChevronRight,
} from 'lucide-react';
import { useCart } from '@/store/cartStore';
import { useAuth } from '@/context/AuthContext';
import { useSocket } from '@/hooks/useSocket';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/services/api';
import { IMAGES } from './images';

const STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Preparing',
  shipped: 'Out for Delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};
const STATUS_COLORS = {
  pending: 'warning',
  processing: 'info',
  shipped: 'info',
  delivered: 'success',
  cancelled: 'destructive',
};

export default function AdminDashboard() {
  const { t } = useTranslation();
  const { count } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({});
  const [menuItems, setMenuItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openItem, setOpenItem] = useState(null); // {item, mode:'add'|'edit'}
  const [saving, setSaving] = useState(false);
  const [itemForm, setItemForm] = useState({
    title: '', description: '', price: '', category: '', tags: '', isFeatured: 'false', isActive: 'true',
  });

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sRes, mRes, oRes] = await Promise.all([
        api.get('/restaurant/admin/stats'),
        api.get('/restaurant/menu?limit=50'),
        api.get('/restaurant/orders?limit=50'),
      ]);
      setStats(sRes.data.data || {});
      setMenuItems(mRes.data.data || []);
      setOrders(oRes.data.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Silent refresh for realtime pushes (no full-page spinner per event).
  const refreshAll = useCallback(async () => {
    try {
      const [sRes, mRes, oRes] = await Promise.all([
        api.get('/restaurant/admin/stats'),
        api.get('/restaurant/menu?limit=50'),
        api.get('/restaurant/orders?limit=50'),
      ]);
      setStats(sRes.data.data || {});
      setMenuItems(mRes.data.data || []);
      setOrders(oRes.data.data || []);
      setError(null);
    } catch {
      // Keep the last known snapshot; explicit actions still surface errors.
    }
  }, []);

  // The socket is force-joined to the verified identity rooms (`user:<id>` and,
  // when present, `org:<id>`), so handlers fire for this tenant's pushes without
  // the client having to know or request a room name.
  const { connected: live } = useSocket(user?.id ? `user:${user.id}` : null, {
    'order:new': refreshAll,
    'order:updated': refreshAll,
    'reservation:created': refreshAll,
  });

  const handleOpen = (mode, item = null) => {
    setOpenItem({ mode, item });
    setItemForm({
      title: item?.title || '',
      description: item?.description || '',
      price: item?.price?.toString() || '',
      category: item?.category || '',
      tags: (item?.tags || []).join(', '),
      isFeatured: (item?.isFeatured ? 'true' : 'false'),
      isActive: (item?.isActive ? 'true' : 'false'),
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        title: itemForm.title,
        description: itemForm.description,
        price: parseFloat(itemForm.price),
        category: itemForm.category,
        tags: itemForm.tags.split(',').map((t) => t.trim()).filter(Boolean),
        isFeatured: itemForm.isFeatured === 'true',
        isActive: itemForm.isActive === 'true',
      };
      if (openItem.mode === 'add') {
        await api.post('/restaurant/admin/menu', payload);
      } else {
        await api.patch(`/restaurant/admin/menu/${openItem.item.id}`, payload);
      }
      setOpenItem(null);
      await fetchAll();
    } catch (err) {
      setError(err.message || 'Failed to save menu item.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('restaurant.admin.confirmDelete', 'Delete this menu item?'))) return;
    try {
      await api.delete(`/restaurant/admin/menu/${id}`);
      await fetchAll();
    } catch (err) {
      setError(err.message || 'Failed to delete item.');
    }
  };

  const handleStatus = async (id, status) => {
    try {
      await api.patch(`/restaurant/admin/orders/${id}/status`, { status });
      await fetchAll();
    } catch (err) {
      setError(err.message || 'Failed to update order status.');
    }
  };

  if (loading) {
    return (
      <section className="min-h-screen bg-background flex items-center justify-center">
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
        <div className="flex items-center gap-3 mb-6">
          <h1 className="text-2xl font-display font-bold">
            {t('restaurant.admin.title', 'Restaurant Admin')}
          </h1>
          {live && (
            <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              {t('common.live', 'Live')}
            </span>
          )}
        </div>
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {[{
            label: t('restaurant.admin.menuItems', 'Menu Items'),
            value: stats.totalMenuItems ?? 0,
            icon: <Users className="h-5 w-5" />,
          }, {
            label: t('restaurant.admin.totalOrders', 'Total Orders'),
            value: stats.totalOrders ?? 0,
            icon: <CreditCard className="h-5 w-5" />,
          }, {
            label: t('restaurant.admin.revenue', 'Revenue'),
            value: `$${(stats.totalRevenue ?? 0).toFixed(2)}`,
            icon: <CreditCard className="h-5 w-5" />,
          }, {
            label: t('restaurant.admin.pendingOrders', 'Pending Orders'),
            value: stats.pendingOrders ?? 0,
            icon: <Clock className="h-5 w-5" />,
          }].map((stat, i) => (
            <Card key={i} className="p-5">
              <div className="flex justify-between items-start mb-2">
                <span className="text-muted-foreground text-sm">{stat.label}</span>
                <div className="p-2 rounded-lg bg-primary/10 text-primary">{stat.icon}</div>
              </div>
              <p className="text-2xl font-display font-bold">{stat.value}</p>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Menu management */}
          <div className="lg:col-span-2">
            <div className="flex justify-between items-baseline mb-6">
              <h2 className="text-xl font-display font-bold">{t('restaurant.admin.manageMenu', 'Manage Menu')}</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpen('add')}
                leftIcon={Plus}
              >
                {t('restaurant.admin.addItem', 'Add Item')}
              </Button>
            </div>
            <div className="space-y-4">
              {menuItems.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  {t('restaurant.admin.noItems', 'No menu items yet')}
                </div>
              )}
              {menuItems.map((item) => (
                <Card key={item.id} className="p-4 flex flex-col md:flex-row gap-4 items-start">
                  <div className="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden">
                    <img
                      src={(item.images && item.images[0]) || IMAGES.fallback}
                      alt={item.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline mb-1">
                      <h3 className="font-semibold truncate">{item.title}</h3>
                      <span className="text-xs font-bold text-primary">${Number(item.price).toFixed(2)}</span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate md:max-w-[300px]">
                      {item.description || t('restaurant.admin.noDesc', 'No description')}
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {(item.tags || []).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      <Badge
                        variant={item.isActive ? 'success' : 'destructive'}
                        className="text-xs"
                      >
                        {item.isActive ? t('restaurant.admin.active', 'Active') : t('restaurant.admin.inactive', 'Inactive')}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleOpen('edit', item)} leftIcon={Edit2}>
                      {t('common.edit', 'Edit')}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(item.id)} leftIcon={Trash2} />
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Orders */}
          <div className="lg:col-span-1">
            <div className="flex justify-between items-baseline mb-6">
              <h2 className="text-xl font-display font-bold">{t('restaurant.admin.orders', 'Orders')}</h2>
            </div>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
              {orders.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">{t('restaurant.admin.noOrders', 'No orders yet')}</div>
              )}
              {orders.slice(0, 10).map((order) => (
                <Card key={order.id} className="p-4 border border-border">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium truncate">#{order.orderNumber}</span>
                    <Badge variant={STATUS_COLORS[order.status] || 'secondary'} className="text-xs">
                      {STATUS_LABELS[order.status] || order.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">
                    {new Date(order.createdAt).toLocaleDateString()} • ${Number(order.totalPrice || 0).toFixed(2)}
                  </p>
                  <div className="space-y-2">
                    {(['pending', 'processing', 'shipped', 'delivered']).map((status) => (
                      <Button
                        key={status}
                        variant={order.status === status ? 'primary' : 'outline'}
                        size="xs"
                        onClick={() => handleStatus(order.id, status)}
                        className="w-full text-xs px-2 py-1.5 justify-start"
                      >
                        {STATUS_LABELS[status]}
                      </Button>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>

        {/* Add/Edit modal */}
        {openItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpenItem(null)} />
            <Card className="relative mx-4 max-w-md p-6 bg-background shadow-2xl">
              <h3 className="font-display font-bold mb-6">
                {openItem.mode === 'add' ? t('restaurant.admin.addItem', 'Add Menu Item') : t('restaurant.admin.editItem', 'Edit Menu Item')}
              </h3>
              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('restaurant.admin.name', 'Name')}</label>
                  <input
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    value={itemForm.title}
                    onChange={(e) => setItemForm({ ...itemForm, title: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('restaurant.admin.category', 'Category')}</label>
                  <input
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    value={itemForm.category}
                    onChange={(e) => setItemForm({ ...itemForm, category: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('restaurant.admin.price', 'Price')}</label>
                  <input
                    type="number"
                    step="0.01"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    value={itemForm.price}
                    onChange={(e) => setItemForm({ ...itemForm, price: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('restaurant.admin.tags', 'Tags (comma-separated)')}</label>
                  <input
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="vegetarian, spicy"
                    value={itemForm.tags}
                    onChange={(e) => setItemForm({ ...itemForm, tags: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={itemForm.isFeatured === 'true'}
                    onChange={(e) => setItemForm({ ...itemForm, isFeatured: e.target.checked ? 'true' : 'false' })}
                    className="rounded border-border text-primary focus:ring-primary"
                  />
                  <label className="text-sm">{t('restaurant.admin.featured', 'Featured')}</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={itemForm.isActive === 'true'}
                    onChange={(e) => setItemForm({ ...itemForm, isActive: e.target.checked ? 'true' : 'false' })}
                    className="rounded border-border text-primary focus:ring-primary"
                  />
                  <label className="text-sm">{t('restaurant.admin.active', 'Active')}</label>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" size="sm" onClick={() => setOpenItem(null)}>
                    {t('common.cancel', 'Cancel')}
                  </Button>
                  <Button type="submit" variant="primary" size="sm" loading={saving}>
                    {t('common.save', 'Save')}
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}
      </div>
    </section>
  );
}
