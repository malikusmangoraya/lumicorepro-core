import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import AuthSetupNotice from '../components/AuthSetupNotice.jsx';
import { useAuth } from '../context/AuthContext.jsx';

function getRedirectUrl(path) {
  return new URL(`${import.meta.env.BASE_URL}${path}`, window.location.origin).toString();
}

function AuthPage({ mode }) {
  const { authError, client, configError, isConfigured, isLoading, user } = useAuth();
  const [view, setView] = useState(mode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isConfigured) return <AuthSetupNotice reason={configError} />;
  if (isLoading) {
    return <p className="auth-loading" role="status">Checking your sign-in…</p>;
  }
  if (user && view !== 'reset') return <Navigate to="/account" replace />;

  const isRegister = view === 'register';
  const isRecovery = view === 'recovery';
  const isReset = view === 'reset';
  const title = isRegister
    ? 'Create your account'
    : isRecovery
      ? 'Reset your password'
      : isReset
        ? 'Choose a new password'
        : 'Welcome back';

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage('');
    setStatusMessage('');
    setIsSubmitting(true);

    try {
      if (isRegister) {
        const { data, error } = await client.auth.signUp({
          email: email.trim(),
          password,
          options: {
            data: { display_name: name.trim() },
            emailRedirectTo: getRedirectUrl('account'),
          },
        });
        if (error) throw error;
        if (data.session) {
          window.location.assign(getRedirectUrl('account'));
          return;
        }
        setStatusMessage('Account request received. Check your email to verify your account.');
      } else if (isRecovery) {
        const { error } = await client.auth.resetPasswordForEmail(email.trim(), {
          redirectTo: getRedirectUrl('reset-password'),
        });
        if (error) throw error;
        setStatusMessage('If an account exists for that email, a recovery link is on its way.');
      } else if (isReset) {
        const { error } = await client.auth.updateUser({ password });
        if (error) throw error;
        setStatusMessage('Your password has been updated. You can now sign in.');
        setView('login');
        setPassword('');
      } else {
        const { error } = await client.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (error) throw error;
        window.location.assign(getRedirectUrl('account'));
        return;
      }
    } catch (error) {
      setErrorMessage(
        isRecovery
          ? 'We could not send a recovery request. Please try again shortly.'
          : isRegister
            ? 'We could not create your account. Check your details and try again.'
            : isReset
              ? 'We could not update your password. Request a new recovery link and try again.'
              : 'We could not sign you in with those details.'
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="auth-page page-width">
      <div className="auth-panel">
        <p className="eyebrow"><span className="eyebrow-line" /> Your Orbitboard</p>
        <h1>{title}</h1>
        <p className="auth-intro">
          {isRegister
            ? 'Start with a secure account. Verify your email before signing in.'
            : isRecovery
              ? 'Enter the email address associated with your account.'
              : isReset
                ? 'Use a new password you have not used here before.'
                : 'Sign in to continue to your Orbitboard account.'}
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegister && (
            <label>
              Full name
              <input
                autoComplete="name"
                minLength={2}
                name="name"
                onChange={(event) => setName(event.target.value)}
                required
                value={name}
              />
            </label>
          )}
          <label>
            Email address
            <input
              autoComplete="email"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          {!isRecovery && (
            <label>
              {isReset ? 'New password' : 'Password'}
              <input
                autoComplete={isReset ? 'new-password' : isRegister ? 'new-password' : 'current-password'}
                minLength={8}
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </label>
          )}
          {view === 'login' && (
            <button
              className="auth-text-button"
              onClick={() => {
                setView('recovery');
                setErrorMessage('');
                setStatusMessage('');
              }}
              type="button"
            >
              Forgot password?
            </button>
          )}
          {authError && !client && (
            <p className="auth-message error" role="alert">
              Authentication could not be initialized. Refresh the page and try again.
            </p>
          )}
          {errorMessage && <p className="auth-message error" role="alert">{errorMessage}</p>}
          {statusMessage && <p className="auth-message success" role="status">{statusMessage}</p>}
          <button
            className="button button-dark auth-submit"
            disabled={!client || isSubmitting}
            type="submit"
          >
            {!client
              ? 'Service unavailable'
              : isSubmitting
              ? 'Please wait…'
              : isRegister
                ? 'Create account'
                : isRecovery
                  ? 'Send recovery link'
                  : isReset
                    ? 'Update password'
                    : 'Sign in'}
          </button>
        </form>

        {!isRecovery && !isReset && (
          <p className="auth-switch">
            {isRegister ? 'Already have an account?' : 'New to Orbitboard?'}{' '}
            <Link to={isRegister ? '/login' : '/register'}>
              {isRegister ? 'Sign in' : 'Create an account'}
            </Link>
          </p>
        )}
        {(isRecovery || isReset) && (
          <p className="auth-switch">
            <button
              className="auth-text-button"
              onClick={() => {
                setView('login');
                setErrorMessage('');
                setStatusMessage('');
              }}
              type="button"
            >
              Return to sign in
            </button>
          </p>
        )}
        <p className="auth-privacy">
          Authentication is handled by the configured identity provider. Review the
          <Link to="/privacy"> privacy information</Link>.
        </p>
      </div>
    </section>
  );
}

export default AuthPage;
