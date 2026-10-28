import { Link } from 'react-router-dom';

const FEATURES = [
  {
    number: '01',
    title: 'Plans with perspective',
    text: 'Bring upcoming work into one view, without pretending every date is certain.',
    detail: 'A flexible view across the next few horizons.',
  },
  {
    number: '02',
    title: 'Context beside the work',
    text: 'Keep the goal and the conversation close to the initiative they inform.',
    detail: 'An idea for keeping intent in sight.',
  },
  {
    number: '03',
    title: 'A shared language',
    text: 'Give product, design, engineering, and operations a common place to orient.',
    detail: 'Different teams, one readable direction.',
  },
];

function ServicesPage() {
  return (
    <div className="content-page page-width">
      <header className="page-intro">
        <p className="eyebrow"><span className="eyebrow-line" /> Features · a product concept</p>
        <h1>Useful structure.<br /><em>Room to move.</em></h1>
        <p>
          Orbitboard explores a simple idea: make product direction easier to share,
          while leaving space for the plan to change.
        </p>
      </header>
      <section className="feature-list" aria-label="Product concepts">
        {FEATURES.map((feature) => (
          <article className="feature-row" key={feature.number}>
            <span className="feature-number">{feature.number}</span>
            <h2>{feature.title}</h2>
            <div>
              <p>{feature.text}</p>
              <span className="feature-detail">{feature.detail}</span>
            </div>
          </article>
        ))}
      </section>
      <div className="page-callout">
        <div>
          <p className="eyebrow">Take a look</p>
          <h2>Explore the sample roadmap.</h2>
        </div>
        <Link className="button button-dark" to="/#preview">
          Open the sample <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}

export default ServicesPage;
