import ButtonMotion from '@/components/ui/ButtonMotion';
import React, { useEffect, useRef, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { cn } from '../../utils';
import Spinner from '../ui/Spinner';

const LENGTH = 6;

const OTPInput = ({
  onSubmit,
  onResend,
  title = 'Verify your email',
  subtitle = 'We sent a 6-digit code to your inbox',
  className = '',
  error = '',
  loading = false,
}) => {
  const [digits, setDigits] = useState(Array(LENGTH).fill(''));
  const [resendCountdown, setResendCountdown] = useState(30);
  const inputsRef = useRef([]);

  useEffect(() => {
    if (!onResend && resendCountdown > 0) {
      const t = setTimeout(() => setResendCountdown((c) => c - 1), 1000);
      return () => clearTimeout(t);
    }
    return undefined;
  }, [resendCountdown, onResend]);

  const focusIndex = (index) => {
    const el = inputsRef.current[index];
    if (el) el.focus();
  };

  const handleChange = (index, value) => {
    const clean = value.replace(/\D/g, '');
    if (!clean && value !== '') return;
    const next = [...digits];
    next[index] = clean.slice(-1);
    setDigits(next);
    if (clean && index < LENGTH - 1) focusIndex(index + 1);
    const full = next.join('');
    if (full.length === LENGTH && typeof onSubmit === 'function') {
      onSubmit(full);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) focusIndex(index - 1);
    if (e.key === 'ArrowLeft' && index > 0) focusIndex(index - 1);
    if (e.key === 'ArrowRight' && index < LENGTH - 1) focusIndex(index + 1);
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, LENGTH);
    if (!text) return;
    const next = Array(LENGTH).fill('');
    text.split('').forEach((ch, i) => {
      next[i] = ch;
    });
    setDigits(next);
    focusIndex(Math.min(text.length, LENGTH - 1));
    if (text.length === LENGTH && typeof onSubmit === 'function') {
      onSubmit(text);
    }
  };

  const handleResend = () => {
    if (typeof onResend === 'function') onResend();
    setResendCountdown(30);
    setDigits(Array(LENGTH).fill(''));
    focusIndex(0);
  };

  const canResend = !onResend || resendCountdown <= 0;

  return (
    <div className={cn('w-full max-w-md space-y-6 text-center', className)}>
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
        <ShieldCheck className="h-6 w-6 text-primary" aria-hidden="true" />
      </div>
      <div className="space-y-1.5">
        <h2 className="text-2xl font-bold tracking-tight text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>

      <div
        className="flex justify-center gap-2"
        role="group"
        aria-label="One-time passcode"
        onPaste={handlePaste}
      >
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(el) => {
              inputsRef.current[index] = el;
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            aria-label={`Digit ${index + 1}`}
            disabled={loading}
            className="h-14 w-11 rounded-lg border bg-background text-center text-xl font-semibold text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/30 disabled:opacity-60"
          />
        ))}
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {loading && (
        <div className="flex justify-center">
          <Spinner size="md" />
        </div>
      )}

      <p className="text-sm text-muted-foreground">
        Didn&apos;t receive the code?{' '}
        <ButtonMotion
          type="button"
          onClick={handleResend}
          disabled={!canResend}
          className="font-medium text-primary hover:underline disabled:cursor-not-allowed disabled:opacity-50"
        >
          {canResend ? 'Resend code' : `Resend in ${resendCountdown}s`}
        </ButtonMotion>
      </p>
    </div>
  );
};

export default OTPInput;
