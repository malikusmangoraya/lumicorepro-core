/**
 * theme.js — dark-canvas default (TRD #3 canvas archetypes).
 * Applies `.dark` on <html> by default, honoring a saved preference, then the
 * operating-system scheme. Runs on import.
 */
(function applyTheme() {
  try {
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    const pref = saved
      ? saved === 'dark'
      : window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.classList.toggle('dark', pref === true || saved === 'dark');
    if (!saved) root.classList.add('dark'); // dark default per design tokens
  } catch (e) {
    void e;
  }
})();

export default function theme() {
  return document.documentElement.classList.contains('dark');
}
