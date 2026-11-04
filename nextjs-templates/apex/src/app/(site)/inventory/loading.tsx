export default function InventoryLoading() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <div className="h-3 w-24 animate-pulse rounded bg-white/10" />
      <div className="mt-4 h-9 w-2/3 animate-pulse rounded bg-white/10" />
      <div className="mt-3 h-4 w-1/2 animate-pulse rounded bg-white/5" />

      <div className="mt-10 h-40 animate-pulse rounded-panel border border-line bg-surface/40" />

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="overflow-hidden rounded-panel border border-line bg-surface/40">
            <div className="aspect-[16/10] animate-pulse bg-white/5" />
            <div className="space-y-3 p-5">
              <div className="h-4 w-3/4 animate-pulse rounded bg-white/10" />
              <div className="h-3 w-1/2 animate-pulse rounded bg-white/5" />
              <div className="h-3 w-2/3 animate-pulse rounded bg-white/5" />
            </div>
          </div>
        ))}
      </div>
      <p className="sr-only">Loading inventory</p>
    </div>
  );
}
