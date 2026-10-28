import { Link } from 'react-router-dom';

function ContactPage() {
  return (
    <div className="content-page page-width">
      <header className="page-intro">
        <p className="eyebrow"><span className="eyebrow-line" /> Contact</p>
        <h1>No inbox here.<br /><em>Just a useful preview.</em></h1>
        <p>
          This static showcase has no support inbox or contact-submission service.
          We won’t ask you to enter information that has nowhere to go.
        </p>
      </header>
      <section className="contact-options">
        <article>
          <span className="contact-index">01 / PRODUCT</span>
          <h2>Explore the idea</h2>
          <p>Use the sample roadmap controls to explore a small, fictional planning board.</p>
          <Link className="quiet-link" to="/#preview">Open the sample <span aria-hidden="true">↗</span></Link>
        </article>
        <article>
          <span className="contact-index">02 / DETAILS</span>
          <h2>Understand the demo</h2>
          <p>Read what this preview does and does not store, and the limits of the sample.</p>
          <Link className="quiet-link" to="/privacy">Privacy information <span aria-hidden="true">↗</span></Link>
        </article>
      </section>
    </div>
  );
}

export default ContactPage;
