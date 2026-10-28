import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <section className="state-page page-width">
      <span className="state-mark" aria-hidden="true">404</span>
      <p className="eyebrow">That route isn’t on this map</p>
      <h1>We can’t find that page.</h1>
      <p>The address may have changed, or this page may not be part of the showcase.</p>
      <Link className="button button-dark" to="/">
        Back to Orbitboard <span aria-hidden="true">↗</span>
      </Link>
    </section>
  );
}

export default NotFoundPage;
