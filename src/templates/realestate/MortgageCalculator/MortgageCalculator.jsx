import { useState } from 'react';
import { Calculator, Landmark, RefreshCw } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/utils';
import { defaults, rateTiers, monthlyPayment } from './data/mockData';

const fmt = (n) => Math.round(n).toLocaleString('en-PK');

export default function MortgageCalculator() {
  const [price, setPrice] = useState(defaults.price);
  const [downPct, setDownPct] = useState(defaults.downPct);
  const [years, setYears] = useState(defaults.years);
  const [ratePct, setRatePct] = useState(defaults.ratePct);

  const down = price * (downPct / 100);
  const principal = price - down;
  const monthly = monthlyPayment(principal, ratePct, years);
  const totalPayment = monthly * years * 12;
  const totalInterest = totalPayment - principal;

  const reset = () => {
    setPrice(defaults.price);
    setDownPct(defaults.downPct);
    setYears(defaults.years);
    setRatePct(defaults.ratePct);
  };

  return (
    <TemplateShell
      title="Mortgage Calculator"
      description="Estimate monthly installments and total cost with Pakistani bank home-loan rates."
      category="Real Estate"
      actions={
        <Button size="sm">
          <Landmark className="h-4 w-4 mr-1" />
          Talk to a Bank
        </Button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Inputs */}
        <Card animate="fade-up" className="lg:col-span-3">
          <h3 className="font-display font-bold mb-5 flex items-center gap-2">
            <Calculator className="h-5 w-5 text-primary" />
            Loan Details
          </h3>

          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
            Property Price — <span className="font-bold text-foreground">Rs {fmt(price)}</span>
          </label>
          <input
            type="range"
            min={10000000}
            max={200000000}
            step={500000}
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
            className="w-full accent-primary mb-4"
          />

          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
            Down Payment —{' '}
            <span className="font-bold text-foreground">
              {downPct}% (Rs {fmt(down)})
            </span>
          </label>
          <input
            type="range"
            min={10}
            max={50}
            step={5}
            value={downPct}
            onChange={(e) => setDownPct(Number(e.target.value))}
            className="w-full accent-primary mb-4"
          />

          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
            Loan Tenure — <span className="font-bold text-foreground">{years} years</span>
          </label>
          <input
            type="range"
            min={5}
            max={25}
            step={1}
            value={years}
            onChange={(e) => setYears(Number(e.target.value))}
            className="w-full accent-primary mb-4"
          />

          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
            Interest Rate — <span className="font-bold text-foreground">{ratePct}% / yr</span>
          </label>
          <input
            type="range"
            min={7}
            max={13}
            step={0.25}
            value={ratePct}
            onChange={(e) => setRatePct(Number(e.target.value))}
            className="w-full accent-primary mb-5"
          />

          {/* Bank tiers */}
          <p className="text-xs font-medium text-muted-foreground mb-2">
            Compare against current bank tiers
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
            {rateTiers.map((b) => (
              <button
                key={b.bank}
                onClick={() => setRatePct(b.rate)}
                className={cn(
                  'rounded-xl border px-3 py-2 text-left transition-all',
                  ratePct === b.rate
                    ? 'bg-primary/10 border-primary'
                    : 'border-border hover:border-primary/40'
                )}
              >
                <p className="text-[11px] font-semibold">{b.bank}</p>
                <p className="text-sm font-bold text-primary">{b.rate}%</p>
                {b.months && <p className="text-[10px] text-muted-foreground">{b.months}</p>}
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={reset}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Reset
          </Button>
        </Card>

        {/* Result */}
        <Card
          animate="fade-up"
          animationDelay={80}
          className="lg:col-span-2 bg-gradient-to-br from-primary/10 to-primary/5 border-primary/30"
        >
          <p className="text-sm font-medium text-muted-foreground mb-1">
            Estimated Monthly Installment
          </p>
          <p className="font-display text-4xl font-bold tracking-tight">Rs {fmt(monthly)}</p>
          <p className="text-xs text-muted-foreground mt-1 mb-5">
            Based on a {years}-year loan at {ratePct}% / yr
          </p>

          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Loan Amount</span>
              <span className="font-bold">Rs {fmt(principal)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Down Payment</span>
              <span className="font-bold">Rs {fmt(down)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Total Interest</span>
              <span className="font-bold text-amber-400">Rs {fmt(totalInterest)}</span>
            </div>
            <div className="flex justify-between text-sm pt-3 border-t border-border">
              <span className="text-muted-foreground">Total Payment</span>
              <span className="font-bold text-primary">Rs {fmt(totalPayment)}</span>
            </div>
          </div>

          <div className="mt-5 h-2 rounded-full bg-muted overflow-hidden flex">
            <div className="bg-primary" style={{ width: `${(principal / totalPayment) * 100}%` }} />
            <div
              className="bg-amber-400/70"
              style={{ width: `${(totalInterest / totalPayment) * 100}%` }}
            />
          </div>
          <p className="text-[11px] text-muted-foreground mt-2 flex justify-between">
            <span>■ Principal</span>
            <span>■ Interest</span>
          </p>
        </Card>
      </div>

      <div className="mt-6">
        <Badge variant="outline" className="text-[11px]">
          Estimates pre-approval. Actual rates depend on bank policy, salary & property valuation.
        </Badge>
      </div>
    </TemplateShell>
  );
}
