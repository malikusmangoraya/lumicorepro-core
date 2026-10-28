import { Link } from 'react-router-dom';

const ROUTES = {
  login: {
    title: 'Sign-in is unavailable.',
    explanation: 'This preview has no authentication service or user accounts.',
  },
  register: {
    title: 'Account creation is unavailable.',
    explanation: 'This preview does not store account details or create users.',
  },
  admin: {
    title: 'Admin tools are unavailable.',
    explanation: 'There is no backend, admin workspace, or private product data here.',
  },
  checkout: {
    title: 'Checkout is unavailable.',
    explanation: 'There is no billing provider, published price, or payment flow in this demo.',
  },
};

function UnavailablePage({ route }) {
  const content = ROUTES[route];

  return (
    <section className="state-page page-width">
      <span className="state-mark" aria-hidden="true">—</span>
      <p className="eyebrow">Static showcase · unavailable</p>
      <h1>{content.title}</h1>
      <p>{content.explanation}</p>
      <Link className="button button-dark" to="/#preview">
        Return to product preview <span aria-hidden="true">↗</span>
      </Link>
    </section>
  );
}

export default UnavailablePage;
