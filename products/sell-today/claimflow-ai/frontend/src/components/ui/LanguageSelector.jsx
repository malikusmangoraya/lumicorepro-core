import React from 'react';
import { useTranslation } from 'react-i18next';
import { AVAILABLE_LANGUAGES } from '../../i18n';

export default function LanguageSelector({ className = '' }) {
  const { i18n } = useTranslation();
  return (
    <select
      value={i18n.resolvedLanguage || i18n.language || 'en'}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
      aria-label="Select language"
      className={'rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs transition-colors focus:outline-none ' + className}
    >
      {AVAILABLE_LANGUAGES.map((l) => (
        <option key={l} value={l}>{l.toUpperCase()}</option>
      ))}
    </select>
  );
}
