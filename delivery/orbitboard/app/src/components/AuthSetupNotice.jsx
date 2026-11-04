function AuthSetupNotice({ reason }) {
  const isUnsafeKey = reason === 'invalid-key';

  return (
    <div className="auth-setup-notice" role="status">
      <p className="eyebrow">Account setup required</p>
      <h1>Authentication is not configured.</h1>
      <p>
        {isUnsafeKey
          ? 'A server-only Supabase key was rejected. Replace it with the public anonymous or publishable key.'
          : 'Sign-in is paused until this deployment is connected to its Supabase project.'}
        {' '}No account details have been sent or saved.
      </p>
      <p className="auth-setup-code">
        Configure <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code>
        {' '}with a public anonymous/publishable key for the site build, then rebuild and deploy.
      </p>
    </div>
  );
}

export default AuthSetupNotice;
