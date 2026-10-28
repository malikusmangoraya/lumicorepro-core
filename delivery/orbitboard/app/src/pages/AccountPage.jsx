import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

function AccountPage() {
  const { authError, client, isConfigured, isLoading, user } = useAuth();
  const [errorMessage, setErrorMessage] = useState('');
  const [isSigningOut, setIsSigningOut] = useState(false);
  const navigate = useNavigate();

  if (!isConfigured) return <Navigate to="/login" replace />;
  if (isLoading) return <p className="auth-loading" role="status">Checking your sign-in…</p>;
  if (!user) return <Navigate to="/login" replace />;

  async function handleSignOut() {
    setIsSigningOut(true);
    setErrorMessage('');
    try {
      const { error } = await client.auth.signOut();
      if (error) throw error;
      navigate('/login', { replace: true });
    } catch {
      setErrorMessage('We could not sign you out. Please try again.');
      setIsSigningOut(false);
    }
  }

  return (
    <section className="account-page page-width">
      <p className="eyebrow"><span className="eyebrow-line" /> Account</p>
      <h1>Your Orbitboard account is ready.</h1>
      <p className="account-email">Signed in as <strong>{user.email}</strong></p>
      <p className="account-note">
        This project preview does not yet save roadmaps or team data. Your account is
        used only for authentication until those product features are built.
      </p>
      {authError && <p className="auth-message error" role="alert">{authError}</p>}
      {errorMessage && <p className="auth-message error" role="alert">{errorMessage}</p>}
      <button
        className="button button-dark"
        disabled={isSigningOut}
        onClick={handleSignOut}
        type="button"
      >
        {isSigningOut ? 'Signing out…' : 'Sign out'}
      </button>
    </section>
  );
}

export default AccountPage;
