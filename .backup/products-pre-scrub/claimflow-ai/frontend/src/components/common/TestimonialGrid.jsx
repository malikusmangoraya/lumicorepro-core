import React from 'react';
import { Star, CheckCircle2 } from 'lucide-react';

export default function TestimonialGrid({
  title = 'Trusted by 10,000+ Teams Worldwide',
  subtitle = 'See why founders, creators, and engineering leaders choose our templates to accelerate their digital products.',
  testimonials = [
    {
      name: 'Sarah Jenkins',
      role: 'Founder at CloudScale AI',
      avatar:
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
      rating: 5,
      content:
        'This template saved us at least 6 weeks of engineering. The Lemon Squeezy checkout integration worked out of the box and our launch did $18k in week one.',
    },
    {
      name: 'Marcus Vance',
      role: 'Principal Engineer at DevVenture',
      avatar:
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
      rating: 5,
      content:
        'The cleanest React 19 codebase I have purchased on any digital marketplace. Zero build warnings, flawless Tailwind styling, and rock-solid performance.',
    },
    {
      name: 'Elena Rostova',
      role: 'Head of Product at FinNext',
      avatar:
        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      rating: 5,
      content:
        'The multi-currency support and responsive design are simply unmatched. Easily worth 10x the price for any serious startup team.',
    },
  ],
}) {
  return (
    <section className="py-20 px-6 max-w-6xl mx-auto w-full">
      <div className="text-center mb-16 space-y-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          Wall of Love
        </span>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">{title}</h2>
        {subtitle && (
          <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">{subtitle}</p>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {testimonials.map((t) => (
          <div
            key={t.name}
            className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur-sm hover:border-cyan-500/40 transition-all hover:shadow-xl hover:shadow-cyan-500/5"
          >
            <div>
              <div className="flex items-center gap-1 mb-4 text-amber-400">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-amber-400" />
                ))}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed mb-6 italic">"{t.content}"</p>
            </div>

            <div className="flex items-center gap-3 pt-4 border-t border-slate-800/80">
              <img
                src={t.avatar}
                alt={t.name}
                loading="lazy"
                className="h-10 w-10 rounded-full object-cover ring-2 ring-cyan-500/20"
              />
              <div>
                <div className="flex items-center gap-1">
                  <h4 className="text-xs font-semibold text-white">{t.name}</h4>
                  <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
                </div>
                <p className="text-[11px] text-slate-400">{t.role}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
