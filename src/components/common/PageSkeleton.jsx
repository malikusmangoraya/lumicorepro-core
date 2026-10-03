/**
 * PageSkeleton — shared loading placeholder.
 *
 * Used as the Suspense fallback for every lazy route in `routes/index.jsx`, and
 * as the "auth is resolving" state in the route guards.
 */
export default function PageSkeleton() {
  return (
    <div className="animate-pulse space-y-4 py-8" role="status" aria-live="polite">
      <span className="sr-only">Loading…</span>
      <div className="h-8 bg-muted rounded-xl w-1/3" />
      <div className="h-4 bg-muted rounded-lg w-2/3" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-48 bg-muted rounded-2xl" />
        ))}
      </div>
    </div>
  );
}
