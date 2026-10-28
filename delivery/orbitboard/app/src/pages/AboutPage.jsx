import { Link } from 'react-router-dom';

function AboutPage() {
  return (
    <div className="content-page page-width">
      <header className="page-intro">
        <p className="eyebrow"><span className="eyebrow-line" /> About Orbitboard</p>
        <h1>Planning is a <em>conversation.</em></h1>
        <p>
          Orbitboard is presented here as a product idea for cross-functional teams:
          a clearer way to discuss direction without mistaking a roadmap for a promise.
        </p>
      </header>
      <section className="about-note">
        <span className="about-mark" aria-hidden="true">O</span>
        <div>
          <p className="eyebrow">What you’re looking at</p>
          <h2>A static product showcase.</h2>
          <p>
            This website is an interactive sample, not the Orbitboard service. It has
            no backend, account store, live workspace, or billing connection. The
            example roadmap uses fictional sample items and resets in your browser.
          </p>
          <Link className="quiet-link" to="/#preview">
            Try the sample roadmap <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </section>
      <section className="about-values">
        <h2>Three ideas behind the board.</h2>
        <div className="value-list">
          <p><span>01</span> Keep the direction visible.</p>
          <p><span>02</span> Make room for evidence and discussion.</p>
          <p><span>03</span> Treat plans as a guide, not a guarantee.</p>
        </div>
      </section>
    </div>
  );
}

export default AboutPage;
