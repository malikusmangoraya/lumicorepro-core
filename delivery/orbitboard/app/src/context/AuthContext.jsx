import { createContext, useContext, useEffect, useState } from 'react';
import { authConfig } from '../services/authConfig.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [client, setClient] = useState(null);
  const [isLoading, setIsLoading] = useState(authConfig.configured);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    if (!authConfig.configured) return undefined;

    let active = true;
    let unsubscribe;

    import('../services/supabase.js').then(({ supabase: authClient }) => {
      if (!active) return;
      setClient(authClient);
      const { data: subscription } = authClient.auth.onAuthStateChange((_event, nextSession) => {
        if (!active) return;
        setSession(nextSession);
        setIsLoading(false);
        setAuthError('');
      });
      unsubscribe = () => subscription.subscription.unsubscribe();

      return authClient.auth.getSession().then(({ data, error }) => {
        if (!active) return;
        if (error) {
          setAuthError('We could not restore your sign-in. Please try again.');
        } else {
          setSession(data.session);
        }
        setIsLoading(false);
      });
    }).catch(() => {
      if (!active) return;
      setAuthError('We could not restore your sign-in. Please try again.');
      setIsLoading(false);
    });

    return () => {
      active = false;
      unsubscribe?.();
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user: session?.user ?? null,
        isLoading,
        authError,
        isConfigured: authConfig.configured,
        configError: authConfig.reason,
        client,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
