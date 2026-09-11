export const defaults = {
  price: 85000000,
  downPct: 20,
  years: 15,
  ratePct: 9.5,
};

export const rateTiers = [
  { bank: 'HBL Bank', rate: 9.5, months: '3-yr felix' },
  { bank: 'Meezan Bank', rate: 9.25, months: '5-yr felix' },
  { bank: 'UBL', rate: 10.0, months: '' },
  { bank: 'Bank Alfalah', rate: 9.75, months: '2-yr felix' },
];

export function monthlyPayment(principal, annualRatePct, years) {
  const r = annualRatePct / 100 / 12;
  const n = years * 12;
  if (r === 0) return principal / n;
  return (principal * r) / (1 - Math.pow(1 + r, -n));
}
