/**
 * CookieConsent — OPT-IN consent banner (project template).
 * Region: SA | Regulations: PECA_PK, GDPR
 * Mount once in App.jsx: <CookieConsent />
 * Reads the category model from ../../config/cookie-config.js.
 */

import { useEffect, useRef, useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { COOKIE_CONFIG, hasConsent, saveConsent } from '../../config/cookie-config';

const styles = {
  overlay: {
    position: 'fixed',
    insetInline: 0,
    bottom: 0,
    zIndex: 2147483000,
    padding: '1rem',
    display: 'flex',
    justifyContent: 'center',
  },
  card: {
    width: '100%',
    maxWidth: 640,
    background: 'rgb(var(--t-canvas))',
    color: 'rgb(var(--t-canvas-text))',
    border: '1px solid rgba(var(--t-glass-border), 0.6)',
    borderRadius: 12,
    boxShadow: '0 12px 32px rgba(2, 6, 23, 0.25)',
    padding: '1.25rem',
    fontFamily: 'system-ui, sans-serif',
    fontSize: 14,
    lineHeight: 1.55,
  },
  row: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginBlockStart: '0.5rem',
    alignItems: 'center',
  },
  toggle: { display: 'flex', alignItems: 'center', gap: '0.375rem' },
  button: {
    border: 'none',
    borderRadius: 8,
    padding: '0.5rem 0.875rem',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    marginInlineEnd: '0.5rem',
  },
  primary: { background: 'rgb(var(--t-primary))', color: 'rgb(var(--t-canvas))' },
  secondary: { background: 'rgba(var(--t-muted), 0.12)', color: 'rgb(var(--t-canvas-text))' },
  link: { color: 'rgb(var(--t-primary))' },
};

export default function CookieConsent() {
  const [stored] = useState(() => localStorage.getItem(COOKIE_CONFIG.consentCookieName));
  const [open, setOpen] = useState(() => COOKIE_CONFIG.showBanner && !stored);
  const [choices, setChoices] = useState(() => {
    const initial = {};
    Object.values(COOKIE_CONFIG.categories).forEach((cat) => {
      initial[cat.id] = cat.required ? true : hasConsent(cat.id);
    });
    return initial;
  });
  const acceptRef = useRef(null);

  useEffect(() => {
    if (open && acceptRef.current) acceptRef.current.focus();
  }, [open]);

  if (!open) return null;

  const categories = Object.values(COOKIE_CONFIG.categories);
  const set = (id, value) => setChoices((prev) => ({ ...prev, [id]: value }));
  const close = () => setOpen(false);
  const dismiss = () => setOpen(false);

  const finish = (finalChoices) => {
    saveConsent(finalChoices);
    close();
  };

  const onKeyDown = (event) => {
    if (event.key === 'Escape') dismiss();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-consent-title"
      onKeyDown={onKeyDown}
      style={styles.overlay}
    >
      <div style={styles.card}>
        <h2 id="cookie-consent-title" style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
          We value your privacy
        </h2>
        <p style={{ margin: '0.375rem 0 0' }}>
          We use cookies to make our site work and, where you agree, to analyse traffic and
          personalize content. Essential cookies are always active. For details see our{' '}
          <a href={COOKIE_CONFIG.privacyPolicyUrl} style={styles.link}>
            Privacy Policy
          </a>{' '}
          and{' '}
          <a href={COOKIE_CONFIG.termsOfServiceUrl} style={styles.link}>
            Terms of Service
          </a>
          .
        </p>

        {categories.map((cat) => (
          <label key={cat.id} style={{ ...styles.toggle, ...styles.row }}>
            <input
              type="checkbox"
              disabled={cat.required}
              checked={cat.required || choices[cat.id]}
              onChange={(e) => set(cat.id, e.target.checked)}
              aria-describedby={cat.required ? undefined : `cat-desc-${cat.id}`}
            />
            <span>{cat.name}</span>
            {cat.required ? null : <small style={{ opacity: 0.7 }}>({cat.description})</small>}
          </label>
        ))}

        <div style={styles.row}>
          <ButtonMotion
            ref={acceptRef}
            type="button"
            style={{ ...styles.button, ...styles.primary }}
            onClick={() => {
              const all = {};
              categories.forEach((cat) => {
                all[cat.id] = true;
              });
              finish(all);
            }}
          >
            Accept all
          </ButtonMotion>
          <ButtonMotion
            type="button"
            style={{ ...styles.button, ...styles.secondary }}
            onClick={() => {
              const minimal = {};
              categories.forEach((cat) => {
                minimal[cat.id] = cat.required;
              });
              finish(minimal);
            }}
          >
            Reject non-essential
          </ButtonMotion>
          <ButtonMotion type="button" style={styles.button} onClick={() => finish(choices)}>
            Save preferences
          </ButtonMotion>
        </div>
      </div>
    </div>
  );
}
