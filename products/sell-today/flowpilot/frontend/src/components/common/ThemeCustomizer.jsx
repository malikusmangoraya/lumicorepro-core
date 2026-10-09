import React, { useState, useEffect } from 'react';
import { Palette, X, Sun, Moon, Check, Sparkles } from 'lucide-react';

const COLOR_THEMES = [
  { id: 'cyan', name: 'Electric Cyan', primary: 'rgb(6, 182, 212)', accent: 'rgb(14, 165, 233)' },
  { id: 'violet', name: 'Royal Violet', primary: 'rgb(139, 92, 246)', accent: 'rgb(168, 85, 247)' },
  {
    id: 'emerald',
    name: 'Emerald Fintech',
    primary: 'rgb(16, 185, 129)',
    accent: 'rgb(5, 150, 105)',
  },
  { id: 'amber', name: 'Sunset Amber', primary: 'rgb(245, 158, 11)', accent: 'rgb(217, 119, 6)' },
  { id: 'rose', name: 'Rose Quartz', primary: 'rgb(244, 63, 94)', accent: 'rgb(225, 29, 72)' },
];

export default function ThemeCustomizer() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTheme, setActiveTheme] = useState('cyan');
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('site_theme');
    if (saved && COLOR_THEMES.some((t) => t.id === saved)) {
      setActiveTheme(saved);
      applyTheme(saved);
    }
  }, []);

  const applyTheme = (themeId) => {
    const theme = COLOR_THEMES.find((t) => t.id === themeId);
    if (!theme) return;
    setActiveTheme(themeId);
    localStorage.setItem('site_theme', themeId);
    document.documentElement.style.setProperty('--color-primary', theme.primary);
    document.documentElement.style.setProperty('--color-accent', theme.accent);
  };

  const toggleDarkMode = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500 text-slate-950 shadow-2xl shadow-cyan-500/50 hover:bg-cyan-400 hover:scale-110 active:scale-95 transition-all"
        aria-label="Open theme customizer"
      >
        <Palette className="h-5 w-5" />
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      <div
        className={`fixed top-0 right-0 bottom-0 z-50 w-80 max-w-full bg-slate-950 border-l border-slate-800 p-6 shadow-2xl transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <h3 className="font-bold text-sm text-white">Live Theme Studio</h3>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="py-6 space-y-6">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 block">
              Color Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={toggleDarkMode}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                  isDark
                    ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                    : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                <Moon className="h-3.5 w-3.5" /> Dark Mode
              </button>
              <button
                type="button"
                onClick={toggleDarkMode}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                  !isDark
                    ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                    : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                <Sun className="h-3.5 w-3.5" /> Light Mode
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 block">
              Primary Accent Color
            </label>
            <div className="space-y-2">
              {COLOR_THEMES.map((thm) => {
                const isSelected = activeTheme === thm.id;
                return (
                  <button
                    key={thm.id}
                    type="button"
                    onClick={() => applyTheme(thm.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-xl border text-xs font-semibold transition-all ${
                      isSelected
                        ? 'border-cyan-500 bg-slate-900 text-white'
                        : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="h-4 w-4 rounded-full shadow-md"
                        style={{ backgroundColor: thm.primary }}
                      />
                      <span>{thm.name}</span>
                    </div>
                    {isSelected && <Check className="h-4 w-4 text-cyan-400" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Commercial Template Ready
            </span>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              This preview includes all commercial assets, Lemon Squeezy overlay triggers, and
              responsive pages.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
