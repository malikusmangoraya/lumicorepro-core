import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastCtx = createContext({ toast: () => {} });
export const useToast = () => useContext(ToastCtx);

export default function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const toast = useCallback((message, kind = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((list) => [...list, { id, message, kind }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 3500);
  }, []);
  const ctx = useMemo(() => ({ toast }), [toast]);
  return (
    <ToastCtx.Provider value={ctx}>
      {children}
      <div className="fixed top-4 right-4 z-[90] flex flex-col gap-2 pointer-events-none" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto animate-toast-in flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg backdrop-blur text-sm font-medium border ${
              t.kind === 'error'
                ? 'bg-red-500/10 border-red-500/40 text-red-200'
                : 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
