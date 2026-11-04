/**
 * Finance maths for the payment estimator.
 *
 * A car listing that hides the monthly cost is a listing people bounce from,
 * but an estimate that quietly ignores interest is worse. This is the standard
 * amortisation formula, kept pure so it can be tested without a browser.
 */

export type FinanceInput = {
  price: number;
  deposit: number;
  aprPercent: number;
  termMonths: number;
};

export type FinanceResult = {
  financed: number;
  monthly: number;
  totalInterest: number;
  totalPayable: number;
};

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

export function calculateFinance(input: FinanceInput): FinanceResult {
  const price = Math.max(0, input.price);
  const deposit = clamp(input.deposit, 0, price);
  const term = clamp(Math.round(input.termMonths), 1, 360);
  const apr = Math.max(0, input.aprPercent);

  const financed = Math.round((price - deposit) * 100) / 100;

  // 0% APR is a real offer, and the amortisation formula divides by zero there.
  if (apr === 0) {
    const monthly = Math.round((financed / term) * 100) / 100;
    return { financed, monthly, totalInterest: 0, totalPayable: financed };
  }

  const monthlyRate = apr / 100 / 12;
  const factor = Math.pow(1 + monthlyRate, term);
  const monthly = (financed * monthlyRate * factor) / (factor - 1);
  const totalPayable = monthly * term;
  const roundedMonthly = Math.round(monthly * 100) / 100;

  return {
    financed,
    monthly: roundedMonthly,
    totalInterest: Math.round((totalPayable - financed) * 100) / 100,
    totalPayable: Math.round((totalPayable + deposit) * 100) / 100,
  };
}
