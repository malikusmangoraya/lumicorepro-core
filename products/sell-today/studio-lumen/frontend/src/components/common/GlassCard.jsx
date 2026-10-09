/**
 * GlassCard — premium glassmorphism container (TRD #3 glass spec).
 * Exact spec: `backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border
 * border-white/10`. Use the token utility `.glass-md` for the same effect
 * through the design-token pipeline.
 */
export default function GlassCard({ className = '', children, ...props }) {
  return (
    <div
      {...props}
      className={`backdrop-blur-md bg-white/70 dark:bg-slate-900/70 border border-white/10 ${className}`}
    >
      {children}
    </div>
  );
}
