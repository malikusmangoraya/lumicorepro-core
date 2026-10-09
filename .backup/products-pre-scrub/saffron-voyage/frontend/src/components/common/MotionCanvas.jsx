/**
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
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)
      return undefined;

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

    const n = Math.min(70, Math.max(18, Math.floor(canvas.width * canvas.height * density)));
    const dots = Array.from({ length: n }, () => ({
      x: Math.random(),
      y: Math.random(),
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
        d.x += d.vx;
        d.y += d.vy;
        if (d.x < 0) d.x += 1;
        else if (d.x > 1) d.x -= 1;
        if (d.y < 0) d.y += 1;
        else if (d.y > 1) d.y -= 1;
        ctx.beginPath();
        ctx.arc(d.x * w, d.y * h, d.r * dpr, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${200 + Math.sin(t / 9000 + d.x * 12) * 40}, 90%, 65%, ${d.a})`;
        ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    };

    const start = () => {
      if (!running && !document.hidden) {
        running = true;
        raf = requestAnimationFrame(tick);
      }
    };
    const stop = () => {
      running = false;
      cancelAnimationFrame(raf);
    };
    const onReduced = () => {
      if (reduced.matches) stop();
      else start();
    };
    reduced.addEventListener('change', onReduced);
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    start();

    return () => {
      stop();
      window.removeEventListener('resize', resize);
      reduced.removeEventListener('change', onReduced);
    };
  }, [density]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none fixed inset-0 -z-10 h-screen w-screen ${className}`}
    />
  );
}
