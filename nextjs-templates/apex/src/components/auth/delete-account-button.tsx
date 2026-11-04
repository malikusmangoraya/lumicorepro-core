'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function DeleteAccountButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div>
      <button
        type="button"
        disabled={pending}
        onClick={async () => {
          const confirmed = window.confirm(
            'Delete your account and personal data? This cannot be undone.',
          );
          if (!confirmed) return;
          setPending(true);
          setError(null);
          try {
            const response = await fetch('/api/auth/account', { method: 'DELETE' });
            if (!response.ok) {
              const body = (await response.json().catch(() => ({}))) as { message?: string };
              setError(body.message ?? 'Could not delete the account.');
              setPending(false);
              return;
            }
            router.replace('/');
            router.refresh();
          } catch {
            setError('Network error. Please try again.');
            setPending(false);
          }
        }}
        className="inline-flex h-9 items-center rounded-control border border-red-500/40 px-3.5 text-sm font-semibold text-red-300 transition-colors hover:bg-red-500/10 disabled:opacity-60"
      >
        {pending ? 'Deleting…' : 'Delete account'}
      </button>
      {error && (
        <p role="alert" className="mt-2 text-xs font-medium text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
