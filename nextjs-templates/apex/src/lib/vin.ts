/**
 * Vehicle history provider — an integration point, not an implementation.
 *
 * VIN decoding and history reports are paid data (Experian AutoCheck, Carfax,
 * or a local equivalent). This template deliberately ships no scraping and no
 * guessed data: the buyer would read a fabricated accident count as fact.
 *
 * To connect a provider:
 *   1. Set VIN_API_KEY (server side) and, if the provider gives you a public
 *      report URL, NEXT_PUBLIC_VIN_REPORT_BASE.
 *   2. Implement `lookupVin` with the provider's REST call and map the response
 *      into `VinReport`.
 *   3. The vehicle page already renders the report when `vinProviderConfigured()`
 *      is true — no UI work needed.
 */

export type VinReport = {
  vin: string;
  summary: string;
  reportUrl: string | null;
  checkedAt: string;
};

export function vinProviderConfigured(): boolean {
  return Boolean(process.env.VIN_API_KEY && process.env.NEXT_PUBLIC_VIN_REPORT_BASE);
}

export async function lookupVin(vin: string): Promise<VinReport | null> {
  if (!vinProviderConfigured()) return null;

  // Placeholder: wire the provider call here. Returning the raw object the
  // page expects is all the UI needs.
  const base = process.env.NEXT_PUBLIC_VIN_REPORT_BASE;
  return {
    vin,
    summary: 'Provider response not mapped yet',
    reportUrl: base ? `${base}/${encodeURIComponent(vin)}` : null,
    checkedAt: new Date().toISOString(),
  };
}
