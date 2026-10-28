import { Link } from 'react-router-dom';

function PrivacyContent() {
  return (
    <>
      <p>
        This product preview uses fictional roadmap content and does not include
        persistent roadmap or team data. If account access is enabled for this
        deployment, authentication is handled by its configured Supabase project.
        Email address and account/session data are processed by that provider to
        create and maintain sign-in access.
      </p>
      <h2>Information entered here</h2>
      <p>
        Authentication forms send account details to the configured identity provider
        over HTTPS. Passwords are handled by that provider and are not stored by the
        Orbitboard frontend. The hosting platform may process ordinary technical
        request information when serving the site. Review the provider and host
        privacy notices before using a production deployment.
      </p>
      <h2>Questions</h2>
      <p>
        No support inbox is connected to this preview. For its scope and limits, see
        the <Link to="/about">about page</Link> or return to the <Link to="/#preview">sample roadmap</Link>.
      </p>
    </>
  );
}

function TermsContent() {
  return (
    <>
      <p>
        Orbitboard is shown here as a product preview, not as a subscription or live
        planning service. Sample projects, teams, statuses, and dates are fictional
        and exist only to demonstrate the interface.
      </p>
      <h2>Accounts and transactions</h2>
      <p>
        Account registration and sign-in are available only when this deployment is
        connected to its identity provider. The preview does not save roadmap data,
        accept payment, offer administration, or provide contact submission.
      </p>
      <h2>Using the sample</h2>
      <p>
        You may change the sample roadmap filters while viewing this page. Reloading
        returns to the default sample. Read the <Link to="/privacy">privacy information</Link>
        or <Link to="/#preview">visit the product preview</Link>.
      </p>
    </>
  );
}

function PolicyPages({ page }) {
  const isPrivacy = page === 'privacy';
  return (
    <div className="content-page page-width">
      <header className="page-intro policy-intro">
        <p className="eyebrow"><span className="eyebrow-line" /> Information</p>
        <h1>{isPrivacy ? 'Privacy' : 'Terms'} <em>for this preview.</em></h1>
        <p>Last updated October 2026 · Applies to the static Orbitboard showcase.</p>
      </header>
      <article className="policy-copy">
        {isPrivacy ? <PrivacyContent /> : <TermsContent />}
      </article>
    </div>
  );
}

export default PolicyPages;
