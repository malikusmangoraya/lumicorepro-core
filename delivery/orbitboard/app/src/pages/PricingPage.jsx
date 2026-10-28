import { Link } from 'react-router-dom';

const TIERS = [
  {
    name: 'Essentials',
    summary: 'A shared view for a small planning conversation.',
    features: ['One clear roadmap', 'A few planning horizons', 'Context alongside initiatives'],
  },
  {
    name: 'Team',
    summary: 'More ways for a cross-functional team to stay in sync.',
    features: ['Team-specific views', 'Shared initiative context', 'Room for changing priorities'],
    featured: true,
  },
  {
    name: 'Portfolio',
    summary: 'An expanded planning picture across multiple workstreams.',
    features: ['Multiple roadmap views', 'Cross-team visibility', 'Portfolio-level perspective'],
  },
];

function PricingPage() {
  return (
    <div className="content-page page-width">
      <header className="page-intro">
        <p className="eyebrow"><span className="eyebrow-line" /> Pricing · not yet published</p>
        <h1>Choose a view.<br /><em>Not a price tag.</em></h1>
        <p>
          These are illustrative feature groupings only. Final plans and pricing have
          not been published, and this showcase cannot start a subscription.
        </p>
      </header>
      <section className="tier-list" aria-label="Illustrative feature groupings">
        {TIERS.map((tier, index) => (
          <article className={`tier${tier.featured ? ' tier-featured' : ''}`} key={tier.name}>
            <div className="tier-heading">
              <span className="tier-number">0{index + 1}</span>
              {tier.featured && <span className="tier-note">Illustrative</span>}
            </div>
            <h2>{tier.name}</h2>
            <p>{tier.summary}</p>
            <ul>
              {tier.features.map((feature) => <li key={feature}>{feature}</li>)}
            </ul>
            <span className="tier-footer">No price published</span>
          </article>
        ))}
      </section>
      <p className="pricing-footnote">
        No monetary amounts are shown because no final pricing information is available.
      </p>
      <div className="page-callout">
        <div>
          <p className="eyebrow">See the concept</p>
          <h2>Explore the sample roadmap.</h2>
        </div>
        <Link className="button button-dark" to="/#preview">View sample <span aria-hidden="true">↗</span></Link>
      </div>
    </div>
  );
}

export default PricingPage;
