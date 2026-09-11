import { useState, useEffect, useCallback } from 'react';
import { CreditCard, CheckCheck, Loader2, Sparkles, Bot } from 'lucide-react';
import { Card, Badge, Button, Spinner } from '@/components/ui';
import { plansAPI, paymentsAPI, subscriptionsAPI } from '@/services/api';
import { getApiKey } from '@/services/apiConfig';
import { useAppContext } from '@/context/AppContext';
import { useCurrency } from '@/hooks/useCurrency';
import PageSEO from '@/components/common/PageSEO';

export default function Pricing() {
  const { isAuthenticated } = useAppContext();
  const { formatPrice } = useCurrency();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectingId, setSelectingId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    plansAPI
      .list()
      .then((res) => {
        if (active) setPlans(res?.data?.data || []);
      })
      .catch(() => {
        if (active) setPlans([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleSelect = useCallback(
    async (plan) => {
      if (selectingId || !isAuthenticated) {
        setError(isAuthenticated ? '' : 'Please log in to subscribe.');
        return;
      }
      setSelectingId(plan.id);
      setError('');
      try {
        const agentKey = getApiKey('agent') || localStorage.getItem('agentApiKey') || '';
        if (plan.interval === 'one_time') {
          const res = await paymentsAPI.checkout({ planId: plan.id, agentApiKey: agentKey || undefined });
          const url = res?.data?.checkoutUrl;
          if (url) window.location.href = url;
          else setError('Checkout session unavailable — is Stripe configured?');
        } else {
          const res = await subscriptionsAPI.create(plan.id);
          const url = res?.data?.checkoutUrl;
          if (url) window.location.href = url;
          else setError('Checkout session unavailable — is Stripe configured?');
        }
      } catch (err) {
        setError(err?.response?.data?.error || err?.message || 'Checkout failed');
      } finally {
        setSelectingId(null);
      }
    },
    [isAuthenticated, selectingId]
  );

  const subscriptions = plans.filter((p) => p.interval !== 'one_time');
  const creditPacks = plans.filter((p) => p.interval === 'one_time');

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <PageSEO
        title="Pricing — LumicorePro"
        description="Simple pricing for AI-generated websites. Try the full 15-phase pipeline with per-plan AI credits — no card required to explore."
        keywords="lumicorepro, pricing, ai website generator, plans, credits"
      />
      <div className="mb-10 text-center">
        <h1 className="font-display text-3xl font-bold text-foreground">
          Simple pricing for AI-generated websites
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
          Every plan runs the full 15-phase international pipeline — market research, RTL/i18n,
          compliance, SEO, performance budget and multi-cloud deploy configs.
        </p>
        {!isAuthenticated && (
          <p className="mt-4 text-sm text-primary">
            Please log in before choosing a plan.
          </p>
        )}
      </div>

      {error && (
        <div className="mx-auto mb-6 max-w-md rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {subscriptions.map((plan) => (
          <Card key={plan.id} className="flex flex-col p-6">
            {plan.highlight && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most popular</Badge>
            )}
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h3 className="font-display text-lg font-bold text-foreground">{plan.name}</h3>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
            <div className="mt-4 flex items-baseline gap-1">
              <span className="font-display text-3xl font-extrabold text-foreground">
                {formatPrice(parseFloat(plan.amount))}
              </span>
              <span className="text-sm text-muted-foreground">
                /{plan.interval === 'year' ? 'year' : 'month'}
              </span>
            </div>
            <Badge variant="secondary" className="mt-2 w-fit">
              +{parseFloat(plan.creditsGrant || 0).toFixed(0)} AI credits / month
            </Badge>
            <ul className="mt-5 flex-1 space-y-2">
              {(plan.features || []).map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <CheckCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <Button
              onClick={() => handleSelect(plan)}
              disabled={selectingId || !isAuthenticated}
              variant={plan.highlight ? 'primary' : 'outline'}
              className="mt-6 w-full"
            >
              {selectingId === plan.id && <Loader2 className="h-4 w-4 animate-spin" />}
              {selectingId === plan.id ? 'Redirecting…' : 'Choose plan'}
            </Button>
          </Card>
        ))}
      </div>

      <div className="mt-14">
        <div className="mb-5 flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="font-display text-xl font-bold text-foreground">One-time credit packs</h2>
          <span className="text-sm text-muted-foreground">— extra generations without a plan</span>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {creditPacks.map((plan) => (
            <Card key={plan.id} className="flex flex-col p-6">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-primary" />
                <h3 className="font-display text-lg font-bold text-foreground">{plan.name}</h3>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="font-display text-3xl font-extrabold text-foreground">
                  {formatPrice(parseFloat(plan.amount))}
                </span>
                <span className="text-sm text-muted-foreground">one-time</span>
              </div>
              <Badge variant="secondary" className="mt-2 w-fit">
                {parseFloat(plan.creditsGrant || 0).toFixed(0)} credits
              </Badge>
              <ul className="mt-5 flex-1 space-y-2">
                {(plan.features || []).map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Button
                onClick={() => handleSelect(plan)}
                disabled={selectingId || !isAuthenticated}
                variant="outline"
                className="mt-6 w-full"
              >
                {selectingId === plan.id && <Loader2 className="h-4 w-4 animate-spin" />}
                {selectingId === plan.id ? 'Redirecting…' : 'Buy credits'}
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}