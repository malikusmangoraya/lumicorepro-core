import React, { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check, Languages } from 'lucide-react';
import ButtonMotion from '../ui/ButtonMotion';
import { cn } from '../../utils';

const languages = [
  { code: 'en', name: 'English', native: 'English', flag: '🇺🇸', dir: 'ltr' },
  { code: 'es', name: 'Spanish', native: 'Español', flag: '🇪🇸', dir: 'ltr' },
  { code: 'fr', name: 'French', native: 'Français', flag: '🇫🇷', dir: 'ltr' },
  { code: 'de', name: 'German', native: 'Deutsch', flag: '🇩🇪', dir: 'ltr' },
  { code: 'it', name: 'Italian', native: 'Italiano', flag: '🇮🇹', dir: 'ltr' },
  { code: 'pt', name: 'Portuguese', native: 'Português', flag: '🇧🇷', dir: 'ltr' },
  { code: 'ar', name: 'Arabic', native: 'العربية', flag: '🇸🇦', dir: 'rtl' },
  { code: 'ur', name: 'Urdu', native: 'اردو', flag: '🇵🇰', dir: 'rtl' },
  { code: 'zh', name: 'Chinese', native: '中文', flag: '🇨🇳', dir: 'ltr' },
  { code: 'ja', name: 'Japanese', native: '日本語', flag: '🇯🇵', dir: 'ltr' },
  { code: 'ko', name: 'Korean', native: '한국어', flag: '🇰🇷', dir: 'ltr' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳', dir: 'ltr' },
  { code: 'tr', name: 'Turkish', native: 'Türkçe', flag: '🇹🇷', dir: 'ltr' },
];

export default function Language({ currentLang = 'en', onLanguageChange, className }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const menuRef = useRef(null);

  const selected = languages.find((l) => l.code === currentLang) || languages[0];

  const filtered = query.trim()
    ? languages.filter(
        (l) =>
          l.code.includes(query.trim().toLowerCase()) ||
          l.name.toLowerCase().includes(query.trim().toLowerCase()) ||
          l.native.toLowerCase().includes(query.trim().toLowerCase())
      )
    : languages;

  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setIsOpen(false);
    };
    const handleKey = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [isOpen]);

  return (
    <div ref={menuRef} className={`relative inline-block text-left ${className || ''}`}>
      <ButtonMotion
        variant="ghost"
        size="sm"
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="gap-2 border border-border bg-background px-3 text-xs text-foreground"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Change language, current: ${selected.name}`}
      >
        <Globe className="w-3.5 h-3.5 text-primary" aria-hidden="true" />
        <span className="text-base leading-none">{selected.flag}</span>
        <span className="hidden sm:inline">{selected.code.toUpperCase()}</span>
        <ChevronDown
          className={cn(
            'w-3 h-3 text-muted-foreground transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </ButtonMotion>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-xl shadow-lg z-50 py-1">
          <div className="px-3 py-2 border-b border-border flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Languages className="w-3.5 h-3.5" aria-hidden="true" />
            Language
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search language..."
            className="w-full px-3 py-2 border-b border-border text-sm bg-transparent focus:outline-none focus:ring-0"
            aria-label="Search languages"
          />
          <ul role="listbox" className="max-h-72 overflow-y-auto">
            {filtered.map((lang) => (
              <li key={lang.code} role="option" aria-selected={lang.code === currentLang}>
                <ButtonMotion
                  variant="ghost"
                  size="xs"
                  type="button"
                  fullWidth
                  className={`justify-start text-left ${
                    lang.code === currentLang
                      ? 'text-primary font-bold bg-primary/5'
                      : 'text-foreground'
                  }`}
                  onClick={() => {
                    onLanguageChange?.(lang.code);
                    setIsOpen(false);
                    setQuery('');
                  }}
                  dir={lang.dir}
                >
                  <span className="text-base leading-none">{lang.flag}</span>
                  <span className="font-medium" dir={lang.dir}>
                    {lang.native}
                  </span>
                  <span className="text-muted-foreground ml-auto text-[10px] uppercase">
                    {lang.code}
                  </span>
                  {lang.code === currentLang && (
                    <Check className="w-3 h-3 text-primary shrink-0" aria-hidden="true" />
                  )}
                </ButtonMotion>
              </li>
            ))}
            {filtered.length === 0 && (
              <li className="px-3 py-3 text-xs text-muted-foreground text-center">
                No languages found
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
