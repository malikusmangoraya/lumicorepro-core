export default function VehicleLoading() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
      <div className="h-3 w-32 animate-pulse rounded bg-white/10" />
      <div className="mt-6 grid gap-8 lg:grid-cols-[1.4fr_0.6fr]">
        <div>
          <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
          <div className="mt-4 h-10 w-3/4 animate-pulse rounded bg-white/10" />
          <div className="mt-6 aspect-[16/10] animate-pulse rounded-panel border border-line bg-white/5" />
          <div className="mt-8 h-64 animate-pulse rounded-panel border border-line bg-surface/40" />
        </div>
        <div className="space-y-5">
          <div className="h-32 animate-pulse rounded-panel border border-line bg-surface/40" />
          <div className="h-80 animate-pulse rounded-panel border border-line bg-surface/40" />
        </div>
      </div>
      <p className="sr-only">Loading vehicle</p>
    </div>
  );
}
