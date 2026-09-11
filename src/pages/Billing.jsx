import { useState, useEffect, useCallback } from 'react';
import {
  CreditCard,
  Settings2,
  Loader2,
  CheckCircle2,
  ExternalLink,
  Sparkles,
  Coins,
} from 'lucide-react';
import { Card, Badge, Button, Spinner } from '@/components/ui';
import { subscriptionsAPI, paymentsAPI } from '@/services/api';
import { useCurrency } from '@/hooks/useCurrency';
import { formatDate } from '@/utils/helpers';

export default function Billing() {
  const { formatPrice } = useCurrency();
  const [subs, setSubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await subscriptionsAPI.list();
      setSubs(res?.data?.data || []);
    } catch {
      setSubs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success')) {
      setMessage('Payment succeeded — thank you!');
    }
    load();
  }, [load]);

  const openPortal = useCallback(async () => {
    setBusy(true);
    setMessage('');
    try {
      const res = await paymentsAPI.portal();
      const url = res?.data?.url;
      if (url) window.location.href = url;
      else setMessage('Billing portal unavailable — is Stripe configured?');
    } catch (err) {
      setMessage(err?.response?.data?.error || err?.message || 'Portal failed');
    } finally {
      setBusy(false);
    }
  }, []);

  const cancelSub = useCallback(
    async (id) => {
      setBusy(true);
      setMessage('');
      try {
        await subscriptionsAPI.cancel(id);
        setMessage('Subscription cancelled — access continues until period end.');
        load();
      } catch (err) {
        setMessage(err?.response?.data?.error || err?.message || 'Cancel failed');
      } finally {
        setBusy(false);
      }
    },
    [load]
  );

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 text-primary">
          <CreditCard className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-bold text-foreground">Billing &amp; Subscriptions</h1>
          <p className="text-sm text-muted-foreground">Manage your plans, credits and invoices.</p>
        </div>
      </div>

      {message && (
        <div className="mb-6 rounded-xl border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary">
          {message}
        </div>
      )}

      <Card className="mb-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2 font-display text-lg font-bold text-foreground">
              <Settings2 className="h-4 w-4 text-primary" />
              Payment methods &amp; invoices
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Update cards, view invoices, and manage renewal settings.
            </p>
          </div>
          <Button onClick={openPortal} disabled={busy}>
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {busy ? 'Opening…' : 'Open billing portal'}
          </Button>
        </div>
      </Card>

      <h2 className="mb-4 flex items-center gap-2 font-display text-lg font-bold text-foreground">
        <Sparkles className="h-4 w-4 text-primary" />
        Active subscriptions
      </h2>

      {subs.length === 0 ? (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          No active subscriptions.{' '}
          <a href="/pricing" className="text-primary underline-offset-4 hover:underline">
            Browse plans
          </a>
        </Card>
      ) : (
        <div className="space-y-3">
          {subs.map((sub) => (
            <Card key={sub.id} className="flex flex-wrap items-center justify-between gap-4 p-5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-foreground">{sub.planName}</span>
                  <Badge
                    variant={
                      sub.status === 'active' || sub.status === 'trialing' ? 'success' : 'secondary'
                    }
                  >
                    {sub.status}
                  </Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Period: {formatDate(sub.currentPeriodStart)} →{' '}
                  {formatDate(sub.currentPeriodEnd)}
                </p>
                {sub.plan?.amount && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Coins className="h-3 w-3" /> {formatPrice(parseFloat(sub.plan.amount))}/
                    {sub.plan.interval === 'year' ? 'yr' : 'mo'}
                  </p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => cancelSub(sub.id)}
                disabled={busy || sub.status === 'canceled' || sub.status === 'cancelled'}
              >
                Cancel plan
              </Button>
            </Card>
          ))}
        </div>
      )}

      <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        Payments secured by Stripe — your card details are never stored locally.
      </div>
    </div>
  );
}