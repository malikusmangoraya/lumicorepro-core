import { FileSearch } from 'lucide-react';
import { Panel } from '@/components/ui/card';
import { lookupVin, vinProviderConfigured } from '@/lib/vin';

/**
 * Renders only when a VIN provider is configured. With no provider the section
 * is absent rather than empty — a buyer must never see "history unavailable"
 * on a car the dealer simply has not paid to check.
 */
export async function VehicleHistory({ vin }: { vin: string | null }) {
  if (!vin || !vinProviderConfigured()) return null;

  const report = await lookupVin(vin);
  if (!report) return null;

  return (
    <Panel className="mt-6 p-6">
      <div className="flex items-center gap-2">
        <FileSearch className="size-4 text-accent" aria-hidden="true" />
        <h2 className="font-display text-lg font-600 text-heading">Vehicle history</h2>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-body/85">{report.summary}</p>
      <p className="mt-2 text-xs text-muted">VIN {report.vin}</p>
      {report.reportUrl && (
        <a
          href={report.reportUrl}
          target="_blank"
          rel="noreferrer noopener"
          className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-accent hover:underline"
        >
          Open the full report
        </a>
      )}
    </Panel>
  );
}
