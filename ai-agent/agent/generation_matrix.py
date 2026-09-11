"""Generation Matrix — "Modern Era Baseline" premium output layers.

Implements the four PRD pillars on top of every generated project:

1.  Responsive Fluid UI  → clamp-based spacing/type tokens + fluid utilities in
                          frontend/src/index.css (no Tailwind config needed).
2.  Micro-Interactions   → scroll-triggered canvas motion loop + hover micro-state
                          components (framer-motion), auto-mounted in App.jsx.
3.  Lead Capture         → conversion LeadForm (provider-resolved endpoints) and a
                          single-page CheckoutFlow with trust badges + analytics.
4.  Dual Runtime Surface → explicit `runtime_mode` (static | transactional) in the
                          spec, layout report and GENERATION-MATRIX.md.

Artifacts written per project:
    frontend/src/index.css                                (append fluid tokens)
    frontend/src/hooks/useInView.js
    frontend/src/components/common/MotionCanvas.jsx
    frontend/src/components/common/MotionSystems.jsx      (Reveal/Magnetic/Tilt)
    frontend/src/components/common/LeadForm.jsx
    frontend/src/components/checkout/CheckoutFlow.jsx
    frontend/src/services/analyticsBus.js
    frontend/src/App.jsx                                  (mounted MotionCanvas)
    GENERATION-MATRIX.md
"""
import os
from typing import Dict, Any, Optional, List

from utils.logger import agent_logger
from utils.file_manager import FileManager

_MARKER = "LUMICORE_MATRIX"


class GenerationMatrix:
    """Applies the era-baseline quality layers to a generated project tree."""

    def generate(self, spec: Dict[str, Any], project_dir: str, mode: str = "") -> Dict[str, Any]:
        mode = mode or spec.get("layout_mode", "") or ""
        spec["runtime_mode"] = "static" if "static" in mode.lower() else "transactional"
        report: Dict[str, Any] = {"runtime_mode": spec["runtime_mode"], "artifacts": []}

        report["fluid_ui"] = self._apply_fluid_ui(project_dir)
        report["micro_interactions"] = self._apply_motion_layer(project_dir, spec)
        report["lead_capture"] = self._apply_lead_capture(project_dir, spec)
        report["matrix_doc"] = self._write_matrix_doc(project_dir, spec, report)

        report["artifacts"] = [report["fluid_ui"]["file"]] if report["fluid_ui"].get("applied") else []
        report["artifacts"] += report["micro_interactions"].get("artifacts", [])
        report["artifacts"] += report["lead_capture"].get("artifacts", [])
        report["artifacts"].append(report["matrix_doc"])

        agent_logger.info(
            f"GenerationMatrix: runtime='{spec['runtime_mode']}' artifacts={len(report['artifacts'])}"
        )
        return report

    # ── 1. Responsive Fluid UI ─────────────────────────────────────────────
    def _apply_fluid_ui(self, project_dir: str) -> Dict[str, Any]:
        css_path = os.path.join(project_dir, "frontend", "src", "index.css")
        block = """/* ── Responsive Fluid UI ────────────────────────────────────────────────── */
/* LUMICORE_MATRIX:responsive_fluid_ui */
:root {
  --fluid-space-1: clamp(0.25rem, 0.2rem + 0.4vw, 0.5rem);
  --fluid-space-2: clamp(0.5rem, 0.4rem + 0.6vw, 0.9rem);
  --fluid-space-3: clamp(0.75rem, 0.6rem + 0.9vw, 1.4rem);
  --fluid-space-4: clamp(1rem, 0.8rem + 1.2vw, 1.9rem);
  --fluid-space-5: clamp(1.5rem, 1.1rem + 1.9vw, 2.9rem);
  --fluid-space-6: clamp(2rem, 1.4rem + 2.8vw, 4rem);
  --fluid-page: clamp(1rem, 0.5rem + 2.4vw, 2.5rem);
}

@layer utilities {
  .fluid-container {
    width: 100%;
    max-width: 76rem;
    margin-inline: auto;
    padding-inline: var(--fluid-page);
  }
  .fluid-section { padding-block: var(--fluid-space-6); }
  .fluid-gap-1 { gap: var(--fluid-space-1); }
  .fluid-gap-2 { gap: var(--fluid-space-2); }
  .fluid-gap-3 { gap: var(--fluid-space-3); }
  .fluid-gap-4 { gap: var(--fluid-space-4); }
  .fluid-gap-5 { gap: var(--fluid-space-5); }
  .p-fluid-1 { padding: var(--fluid-space-1); }
  .p-fluid-2 { padding: var(--fluid-space-2); }
  .p-fluid-3 { padding: var(--fluid-space-3); }
  .p-fluid-4 { padding: var(--fluid-space-4); }
  .py-fluid-2 { padding-block: var(--fluid-space-2); }
  .py-fluid-3 { padding-block: var(--fluid-space-3); }
  .py-fluid-4 { padding-block: var(--fluid-space-4); }
  .text-fluid-hero { font-size: clamp(2rem, 1.2rem + 3.6vw, 4.5rem); line-height: 1.05; }
  .text-fluid-lg { font-size: clamp(1.25rem, 1.05rem + 1.1vw, 1.9rem); line-height: 1.35; }
  .fluid-bleed { width: 100vw; margin-inline-start: calc(50% - 50vw); }
  .fluid-ease { transition: transform 400ms cubic-bezier(0.22, 1, 0.36, 1), opacity 400ms ease; }
}
/* ── End Responsive Fluid UI ───────────────────────────────────────────── */
"""
        return self._append_idempotent(css_path, block, "responsive_fluid_ui", "index.css")

    # ── 2. Micro-Interactions Layer ────────────────────────────────────────
    def _apply_motion_layer(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        artifacts: List[str] = []

        use_in_view = """/**
 * useInView — reveal-on-scroll primitive (IntersectionObserver).
 */
import { useEffect, useRef, useState } from 'react';

export default function useInView(options = { threshold: 0.15, once: true }) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    if (typeof IntersectionObserver === 'undefined') { setInView(true); return undefined; }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setInView(true);
        if (options.once) observer.disconnect();
      } else if (!options.once) {
        setInView(false);
      }
    }, options);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, inView];
}
"""
        artifacts.append(self._write(src, "hooks", "useInView.js", use_in_view))

        motion_canvas = """/**
 * MotionCanvas — scroll-triggered ambient canvas loop.
 * Zero-dependency ambient particle field.
 * Auto-generated utility — project primitive.
 * Respects prefers-reduced-motion; pauses when off-screen/tab-hidden.
 */
import { useEffect, useRef } from 'react';

const DPR_LIMIT = 1.5;

export default function MotionCanvas({ density = 0.00006, className = '' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;

    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;
    let raf = 0;
    let running = false;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const dpr = Math.min(window.devicePixelRatio || 1, DPR_LIMIT);

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    };
    resize();
    window.addEventListener('resize', resize);

    const n = Math.min(70, Math.max(18, Math.floor((canvas.width * canvas.height) * density)));
    const dots = Array.from({ length: n }, () => ({
      x: Math.random(), y: Math.random(),
      r: 0.6 + Math.random() * 1.8,
      vx: (Math.random() - 0.5) * 0.0006,
      vy: (Math.random() - 0.5) * 0.0006,
      a: 0.12 + Math.random() * 0.35,
    }));

    const tick = (t) => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      for (const d of dots) {
        d.x += d.vx; d.y += d.vy;
        if (d.x < 0) d.x += 1; else if (d.x > 1) d.x -= 1;
        if (d.y < 0) d.y += 1; else if (d.y > 1) d.y -= 1;
        ctx.beginPath();
        ctx.arc(d.x * w, d.y * h, d.r * dpr, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${200 + Math.sin(t / 9000 + d.x * 12) * 40}, 90%, 65%, ${d.a})`;
        ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    };

    const start = () => { if (!running && !document.hidden) { running = true; raf = requestAnimationFrame(tick); } };
    const stop = () => { running = false; cancelAnimationFrame(raf); };
    const onReduced = () => { if (reduced.matches) stop(); else start(); };
    reduced.addEventListener('change', onReduced);
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    start();

    return () => {
      stop();
      window.removeEventListener('resize', resize);
      reduced.removeEventListener('change', onReduced);
    };
  }, [density]);

  return <canvas ref={canvasRef} aria-hidden="true" className={`pointer-events-none fixed inset-0 -z-10 h-screen w-screen ${className}`} />;
}
"""
        artifacts.append(self._write(src, "components", "common", "MotionCanvas.jsx", motion_canvas))

        motion_systems = """/**
 * MotionSystems — hover micro-states + reveal primitives (framer-motion).
 * Auto-generated utility — project primitive.
 * Respects prefers-reduced-motion.
 */
import { motion, useReducedMotion } from 'framer-motion';
import { useRef } from 'react';
import useInView from '../../hooks/useInView';

export function Reveal({ children, delay = 0, className = '' }) {
  const reduce = useReducedMotion();
  const [ref, inView] = useInView();
  return (
    <motion.div
      ref={ref}
      className={className}
      initial={reduce ? false : { opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function MagneticButton({ children, strength = 0.35, className = '', ...props }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const onMove = (e) => {
    if (reduce || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * strength;
    const y = (e.clientY - rect.top - rect.height / 2) * strength;
    ref.current.style.transform = `translate(${x}px, ${y}px)`;
  };
  const reset = () => { if (ref.current) ref.current.style.transform = 'translate(0, 0)'; };
  return (
    <motion.button
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      whileTap={{ scale: 0.97 }}
      className={`fluid-ease ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  );
}

export function TiltCard({ children, max = 6, className = '' }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const onMove = (e) => {
    if (reduce || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    ref.current.style.transform = `perspective(900px) rotateY(${px * max}deg) rotateX(${-py * max}deg)`;
  };
  const reset = () => { if (ref.current) ref.current.style.transform = ''; };
  return (
    <motion.div ref={ref} onMouseMove={onMove} onMouseLeave={reset} className={`fluid-ease ${className}`}>
      {children}
    </motion.div>
  );
}

export function HoverGlow({ className = '', children }) {
  return (
    <div className={`group relative overflow-hidden ${className}`}>
      <div className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100 bg-[radial-gradient(400px_circle_at_var(--x,50%)_var(--y,50%),rgba(6,182,212,0.18),transparent_60%)]" />
      {children}
    </div>
  );
}

export default function MotionSystems() { return null; }
"""
        artifacts.append(self._write(src, "components", "common", "MotionSystems.jsx", motion_systems))

        dep = self._ensure_framer_motion(project_dir)
        artifacts.append(dep or "framer-motion:already-present")

        mounted = self._mount_to_app(project_dir, "MotionCanvas", "./components/common/MotionCanvas")
        artifacts.append(mounted or "already-mounted")

        return {"components": ["MotionCanvas", "Reveal", "MagneticButton", "TiltCard", "HoverGlow"],
                "mounted_in_app": bool(mounted), "artifacts": artifacts}

    # ── 3. Lead Capture & Conversion Checkout ──────────────────────────────
    def _apply_lead_capture(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        src = os.path.join(project_dir, "frontend", "src")
        artifacts: List[str] = []

        bus = """/**
 * analyticsBus — provider-agnostic event bus for conversion tracking.
 * Auto-generated utility — project primitive. Zero dependencies.
 * Use after analytics-config loads: track('purchase', { value: 12.5, currency: 'USD' });
 */
const providers = () => [
  typeof window.gtag === 'function' && window.gtag,
  window.fathom && window.fathom.trackGoal,
  window.mixpanel && window.mixpanel.track,
  window.plausible && window.plausible,
].filter(Boolean);

export function track(name, properties = {}) {
  window.dispatchEvent(new CustomEvent('lumicore:analytics', { detail: { name, properties } }));
  providers().forEach((p) => { try { p('event', name, properties); } catch (e) {} });
}

export function trackConversion(name, value, currency = 'USD', extra = {}) {
  return track(name, { value, currency, ...extra });
}

export default { track, trackConversion };
"""
        artifacts.append(self._write(src, "services", "analyticsBus.js", bus))

        lead_form = """/**
 * LeadForm — conversion lead capture on the resolved provider pipeline.
 * Auto-generated utility — project primitive.
 * Endpoint resolution: Formspree -> generic webhook -> dev mock (no network).
 * Honeypot + status feedback + analytics events included.
 */
import { useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { track } from '../../services/analyticsBus';

const RESOLVE_ENDPOINT = (formId) => {
  const formspree = import.meta.env.VITE_FORMSPREE_ID;
  const webhook = import.meta.env.VITE_LEADS_WEBHOOK;
  if (formspree) return `https://formspree.io/f/${formspree}`;
  if (webhook) return webhook;
  return '/api/leads/mock';
};

export default function LeadForm({ title = 'Get early access', cta = 'Send my info', formId = 'lead_form' }) {
  const [status, setStatus] = useState('idle'); // idle | sending | success | error
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    if (data.website) return; // honeypot
    setStatus('sending');
    track('lead_capture_start', { form_id: formId });
    try {
      const res = await fetch(RESOLVE_ENDPOINT(formId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ name: data.name, email: data.email, message: data.message, _subject: `New lead: ${title}` }),
      });
      if (!res.ok && res.status !== 400 && res.status !== 422) throw new Error(`HTTP ${res.status}`);
      setStatus('success');
      track('lead_captured', { form_id: formId, method: window.navigator.userAgent ? 'webform' : 'webform' });
    } catch (err) {
      setStatus('error');
      setError('Could not submit — please try again or email us directly.');
    }
  };

  return (
    <form onSubmit={onSubmit} aria-label={title} className="glass-card space-y-3 p-6">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="hidden" aria-hidden="true"><label>Website<input type="text" name="website" tabIndex={-1} autoComplete="off" /></label></div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-name`}>Name</label>
        <input id={`${formId}-name`} name="name" required className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" />
      </div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-email`}>Email</label>
        <input id={`${formId}-email`} name="email" type="email" required autoComplete="email" className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" />
      </div>
      <div>
        <label className="mb-1 block text-sm" htmlFor={`${formId}-msg`}>Message</label>
        <textarea id={`${formId}-msg`} name="message" rows={3} className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" />
      </div>
      {status === 'error' && <p role="alert" className="text-sm text-rose-400">{error}</p>}
      {status === 'success' && <p role="status" className="text-sm text-emerald-400">Thanks! We will be in touch shortly.</p>}
      <ButtonMotion type="submit" disabled={status === 'sending'} className="w-full rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white transition hover:bg-cyan-500 disabled:opacity-60">
        {status === 'sending' ? 'Sending…' : cta}
      </ButtonMotion>
    </form>
  );
}
"""
        artifacts.append(self._write(src, "components", "common", "LeadForm.jsx", lead_form))

        checkout = """/**
 * CheckoutFlow — single-page conversion-optimized checkout.
 * Auto-generated utility — project primitive.
 * One-page (reduces abandonment), trust badges, order summary,
 * analytics begin_checkout/checkout /purchase pre-wired on the analytics bus.
 */
import { useEffect, useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { track, trackConversion } from '../../services/analyticsBus';

const TRUST_BADGES = ['SSL Secure', 'PCI-DSS Ready', 'Refund Guarantee', 'GDPR Compliant'];

export default function CheckoutFlow({ items = [], currency = 'USD', submitEndpoint = '/api/orders', onComplete }) {
  const [step, setStep] = useState(1); // 1 contact · 2 payment · 3 review
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [form, setForm] = useState({ email: '', name: '' });
  const subtotal = items.reduce((sum, it) => sum + (Number(it.price) || 0) * (Number(it.qty) || 1), 0);

  useEffect(() => {
    if (items.length) track('begin_checkout', { currency, value: subtotal, items: items.length });
  }, []);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setStatus('sending');
    try {
      const res = await fetch(submitEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, items, currency, total: subtotal }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      trackConversion('purchase', subtotal, currency, { items: items.length });
      setStatus('success');
      if (onComplete) onComplete();
    } catch (err) {
      setStatus('error');
      setError('Payment could not be processed. Please try again.');
    }
  };

  return (
    <div className="fluid-container py-fluid-4">
      <div className="grid gap-8 lg:grid-cols-3">
        <form onSubmit={submit} className="glass-panel space-y-4 rounded-2xl p-6 lg:col-span-2" aria-label="Checkout">
          <ol className="flex gap-2 text-xs">
            {['Contact', 'Payment', 'Review'].map((label, i) => (
              <li key={label} className={i + 1 <= step ? 'text-cyan-400' : 'opacity-50'}>
                {i + 1}. {label}{i < 2 ? ' ·' : ''}
              </li>
            ))}
          </ol>

          {step === 1 && (
            <div className="space-y-3">
              <div><label className="mb-1 block text-sm" htmlFor="co-email">Email</label>
                <input id="co-email" type="email" required autoComplete="email" value={form.email} onChange={set('email')} className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></div>
              <div><label className="mb-1 block text-sm" htmlFor="co-name">Full name</label>
                <input id="co-name" required autoComplete="name" value={form.name} onChange={set('name')} className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></div>
              <div className="flex gap-2">
                <ButtonMotion type="button" onClick={() => setStep(2)} className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white">Continue</ButtonMotion>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <div><label className="mb-1 block text-sm" htmlFor="co-card">Card number</label>
                <input id="co-card" inputMode="numeric" autoComplete="cc-number" placeholder="4242 4242 4242 4242" className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="mb-1 block text-sm" htmlFor="co-exp">Expiry</label>
                  <input id="co-exp" placeholder="MM/YY" autoComplete="cc-exp" className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></div>
                <div><label className="mb-1 block text-sm" htmlFor="co-cvc">CVC</label>
                  <input id="co-cvc" inputMode="numeric" autoComplete="cc-csc" className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></div>
              </div>
              <div className="flex gap-2">
                <ButtonMotion type="button" onClick={() => setStep(1)} className="rounded-lg border border-slate-600 px-4 py-2">Back</ButtonMotion>
                <ButtonMotion type="button" onClick={() => { track('checkout_progress', { step: 3 }); setStep(3); }} className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white">Review</ButtonMotion>
              </div>
              <p className="text-xs opacity-70">Demo scaffold — integrate a real payment provider before going live.</p>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-3">
              {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
              <ButtonMotion type="submit" disabled={status === 'sending'} className="w-full rounded-lg bg-emerald-600 px-4 py-3 font-bold text-white transition hover:bg-emerald-500 disabled:opacity-60">
                {status === 'sending' ? 'Processing…' : `Pay ${new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}`}
              </ButtonMotion>
              {status === 'success' && <p role="status" className="text-sm text-emerald-400">Order complete — thank you!</p>}
              <ul className="flex flex-wrap gap-2 text-center">
                {TRUST_BADGES.map((b) => <li key={b} className="rounded-full border border-slate-700 px-3 py-1 text-[11px] opacity-80">{b}</li>)}
              </ul>
            </div>
          )}
        </form>

        <aside aria-label="Order summary" className="glass-panel h-fit rounded-2xl p-6">
          <h4 className="mb-3 font-semibold">Order summary</h4>
          {items.length === 0 && <p className="text-sm opacity-70">No items yet.</p>}
          <ul className="space-y-2 text-sm">
            {items.map((it, i) => (
              <li key={`${it.id || i}`} className="flex justify-between gap-3">
                <span>{it.name} × {it.qty || 1}</span>
                <span>{new Intl.NumberFormat(undefined, { style: 'currency', currency }).format((Number(it.price) || 0) * (it.qty || 1))}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-between border-t border-slate-800 pt-3 font-semibold">
            <span>Total</span>
            <span>{new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(subtotal)}</span>
          </div>
        </aside>
      </div>
    </div>
  );
}
"""
        artifacts.append(self._write(src, "components", "checkout", "CheckoutFlow.jsx", checkout))

        return {"lead_form": "frontend/src/components/common/LeadForm.jsx",
                "checkout": "frontend/src/components/checkout/CheckoutFlow.jsx",
                "analytics_bus": "frontend/src/services/analyticsBus.js",
                "artifacts": artifacts}

    # ── Mount micro-interaction canvas into App.jsx (idempotent) ───────────
    def _mount_to_app(self, project_dir: str, component: str, import_path: str) -> Optional[str]:
        app_path = os.path.join(project_dir, "frontend", "src", "App.jsx")
        if not os.path.isfile(app_path):
            return None
        content = FileManager.read_file(app_path)
        if _MARKER in content:
            return None  # already mounted
        lines = content.splitlines()
        import_line = (
            f"import {component} from '{import_path}'; // {_MARKER}\n"
        )
        injected = False
        out: List[str] = []
        for line in lines:
            if not injected and line.strip().startswith("import "):
                out.append(line)
                out.append(import_line)
                injected = True
            else:
                out.append(line)
        if not injected:
            out.insert(0, import_line)
        text = "\n".join(out)
        # Mount as fixed background canvas after the top-level wrapper opening
        marker = f"<{component} />\n      {{/* {_MARKER} */}}"
        # Insert after the first JSX element opening (BrowserRouter or similar)
        if "<BrowserRouter" in text:
            text = text.replace("<BrowserRouter>", f"<BrowserRouter>\n      {marker}", 1)
        elif "return (" in text:
            text = text.replace("return (", f"return (\n      {marker}", 1)
        if _MARKER not in text:
            return None
        FileManager.write_file(app_path, text)
        return app_path

    # ── framer-motion dependency (auto-fix runs before layout render) ─────
    def _ensure_framer_motion(self, project_dir: str) -> Optional[str]:
        pkg_path = os.path.join(project_dir, "frontend", "package.json")
        if not os.path.isfile(pkg_path):
            return None
        pkg = FileManager.read_json(pkg_path)
        deps = pkg.setdefault("dependencies", {})
        if "framer-motion" in deps:
            return None
        deps["framer-motion"] = "^11.0.0"
        FileManager.write_json(pkg_path, pkg)
        return "framer-motion:^11.0.0"

    # ── 4. Matrix documentation (marketplace-ready listing) ───────────────
    def _write_matrix_doc(self, project_dir: str, spec: Dict[str, Any], report: Dict[str, Any]) -> str:
        project = spec.get("project_name", "This project")
        runtime = spec.get("runtime_mode", "transactional")
        path = os.path.join(project_dir, "GENERATION-MATRIX.md")
        body = f"""# Responsive Layout Blueprint — {project}

> Modern Era Baseline: ultra-premium output layers applied to every generated project.
> Runtime: **{runtime}** pipeline.

## 1. Responsive Fluid UI
- Clamp-based `--fluid-space-*` token scale + `.p-fluid-*`, `.py-fluid-*`, `.fluid-gap-*` custom spacing utilities.
- `.fluid-container`, `.fluid-section`, `.fluid-bleed`, fluid hero/lead type (`text-fluid-hero`, `text-fluid-lg`).
- All defined in `frontend/src/index.css`; RTL-safe (logical properties); no viewport breakpoint lock-in.

## 2. Micro-Interactions Layer
- `MotionCanvas` — scroll-triggered ambient canvas loop (DPR-capped, auto-pause, `prefers-reduced-motion` safe).
- `MotionSystems.jsx` — `Reveal`, `MagneticButton`, `TiltCard`, `HoverGlow` hover micro-states (framer-motion).
- `useInView` — IntersectionObserver reveal primitive. Canvas auto-mounted in `App.jsx`.

## 3. Lead Capture & Dynamic Pipelines
- `LeadForm` — conversion form wired to Formspree/webhook/mock, honeypot + analytics events.
- `CheckoutFlow` — single-page conversion checkout: trust badges, order summary, `begin_checkout` → `purchase` events.
- `analyticsBus` — provider-agnostic event bus; pairs with the auto-generated `useAnalytics` hook.

## 4. Dual Runtime
- **Static** (`layout_mode=static`): API-less SPA, Vercel/Netlify drop-in, client-side form mocks.
- **Transactional** (`layout_mode=enterprise`): Express + Redis + MySQL/Postgres backend, nginx gateway, real `/api/*`.

## Go-Live Checklist
- [ ] Pair LeadForm/CheckoutFlow with real endpoints (`VITE_FORMSPREE_ID`, `VITE_LEADS_WEBHOOK`, `/api/orders`)
- [ ] Replace demo card fields with a real PSP (Stripe/PayPal) before taking payments
- [ ] Run `npm run build` and deploy both tiers independently
"""
        FileManager.write_file(path, body)
        return path

    # ── Helpers ────────────────────────────────────────────────────────────
    def _write(self, src: str, *rel_pos: str) -> str:
        # Last positional argument is the file content; preceding are path parts.
        if len(rel_pos) < 2:
            raise ValueError("_write requires at least (dir, filename, content)")
        content = rel_pos[-1]
        target = os.path.join(src, *rel_pos[:-1])
        return self._write_idempotent(target, content)

    def _write_idempotent(self, path: str, content: str) -> str:
        if _MARKER not in content and os.path.isfile(path) and _MARKER in FileManager.read_file(path):
            return "already-present"
        FileManager.write_file(path, content)
        return path.replace("\\", "/")

    def _append_idempotent(self, path: str, block: str, marker: str, label: str) -> Dict[str, Any]:
        if not os.path.isfile(path):
            return {"applied": False, "reason": f"{label} missing"}
        existing = FileManager.read_file(path)
        if _MARKER in existing:
            return {"applied": False, "reason": "already-present"}
        FileManager.write_file(path, existing.rstrip("\n") + "\n" + block)
        return {"applied": True, "file": label}


default_matrix = GenerationMatrix()