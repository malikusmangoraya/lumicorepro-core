'use client';

import { useMemo, useState } from 'react';
import { Calculator } from 'lucide-react';
import { calculateFinance } from '@/lib/finance';
import { formatCurrency } from '@/lib/utils';

const TERMS = [24, 36, 48, 60, 72];

export function FinanceCalculator({ price, currency }: { price: number; currency: string }) {
  const defaultDeposit = Math.round(price * 0.1);
  const [deposit, setDeposit] = useState(defaultDeposit);
  const [term, setTerm] = useState(48);
  const [apr, setApr] = useState(6.9);

  const result = useMemo(
    () => calculateFinance({ price, deposit, aprPercent: apr, termMonths: term }),
    [price, deposit, apr, term],
  );

  return (
    <div className="rounded-panel border border-line bg-surface/60 p-6">
      <div className="flex items-center gap-2">
        <Calculator className="size-4 text-accent" aria-hidden="true" />
        <h2 className="font-display text-lg font-600 text-heading">Estimate the monthly cost</h2>
      </div>
      <p className="mt-1 text-sm text-muted">
        Adjust the deposit, term and rate to see an indicative payment.
      </p>

      <div className="mt-5 space-y-4">
        <div>
          <div className="flex items-baseline justify-between">
            <label htmlFor="finance-deposit" className="text-sm font-medium text-heading">
              Deposit
            </label>
            <span className="text-sm text-muted">{formatCurrency(deposit, currency)}</span>
          </div>
          <input
            id="finance-deposit"
            type="range"
            min={0}
            max={Math.round(price * 0.6)}
            step={1000}
            value={deposit}
            onChange={(event) => setDeposit(Number(event.target.value))}
            className="mt-2 w-full accent-[var(--color-primary)]"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="finance-term" className="mb-1.5 block text-sm font-medium text-heading">
              Term
            </label>
            <select
              id="finance-term"
              value={term}
              onChange={(event) => setTerm(Number(event.target.value))}
              className="w-full rounded-control border border-line bg-canvas/70 px-3 py-2 text-sm text-heading focus:border-primary focus:outline-none"
            >
              {TERMS.map((months) => (
                <option key={months} value={months}>
                  {months} months
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="finance-apr" className="mb-1.5 block text-sm font-medium text-heading">
              Representative APR
            </label>
            <select
              id="finance-apr"
              value={apr}
              onChange={(event) => setApr(Number(event.target.value))}
              className="w-full rounded-control border border-line bg-canvas/70 px-3 py-2 text-sm text-heading focus:border-primary focus:outline-none"
            >
              {[0, 3.9, 6.9, 9.9, 12.9].map((rate) => (
                <option key={rate} value={rate}>
                  {rate}%
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <dl className="mt-6 grid gap-3 rounded-control border border-line/70 bg-canvas/50 p-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-[0.14em] text-muted">Monthly</dt>
          <dd className="mt-1 font-display text-2xl font-700 text-accent">
            {formatCurrency(result.monthly, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.14em] text-muted">Amount financed</dt>
          <dd className="mt-1 text-sm font-medium text-heading">
            {formatCurrency(result.financed, currency)}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-[0.14em] text-muted">Total interest</dt>
          <dd className="mt-1 text-sm font-medium text-heading">
            {formatCurrency(result.totalInterest, currency)}
          </dd>
        </div>
      </dl>

      <p className="mt-3 text-xs leading-relaxed text-muted">
        Indicative only. This is not a credit offer: the rate you are given depends on the lender
        and your circumstances. Nothing here is submitted anywhere.
      </p>
    </div>
  );
}
