import { Link } from 'react-router-dom';
import RoadmapPreview from '../components/RoadmapPreview.jsx';

function HomePage() {
  return (
    <>
      <section className="hero page-width">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-line" /> A calmer way to see what’s next</p>
          <h1>Make room for <em>the next</em> good idea.</h1>
          <p className="hero-intro">
            Orbitboard is a product-planning concept for teams who want a shared view
            of the work, the why, and what might come next.
          </p>
          <div className="hero-actions">
            <a className="button button-dark" href="#preview">
              Explore the sample <span aria-hidden="true">↓</span>
            </a>
            <Link className="quiet-link" to="/services">
              See how it could work <span aria-hidden="true">↗</span>
            </Link>
          </div>
          <p className="hero-note">
            <span className="note-dot" aria-hidden="true" />
            A product preview · sample roadmap resets when you leave
          </p>
        </div>

        <div className="hero-art" role="img" aria-label="A sample roadmap with work planned across upcoming quarters">
          <div className="hero-board">
            <div className="hero-board-head">
              <span className="hero-board-mark" aria-hidden="true">O</span>
              <div><span>PRODUCT / SAMPLE</span><strong>Northstar roadmap</strong></div>
              <span className="hero-board-dots" aria-hidden="true">•••</span>
            </div>
            <div className="hero-board-track">
              <span className="track-quarter">Q4 <small>2026</small></span>
              <div className="track-item"><i className="track-dot dot-coral" />Feedback themes</div>
              <div className="track-item"><i className="track-dot dot-white" />Shared views</div>
              <div className="track-item"><i className="track-dot dot-sand" />Dependency map</div>
            </div>
            <div className="hero-board-track second-track">
              <span className="track-quarter">Q1 <small>2027</small></span>
              <div className="track-item"><i className="track-dot dot-coral" />Release notes</div>
              <div className="track-item"><i className="track-dot dot-white" />Capacity signals</div>
            </div>
            <div className="hero-board-foot">
              <span><i className="legend-dot" /> Fictional sample</span>
              <span>Direction, not a promise</span>
            </div>
          </div>
          <span className="hero-art-index">SAMPLE BOARD <i aria-hidden="true">↗</i></span>
          <div className="hero-orbit" aria-hidden="true"><span /></div>
        </div>
      </section>

      <div className="marquee-band" aria-label="Plan with a wider view">
        <div className="marquee-inner">
          <span>Make the work visible</span><i aria-hidden="true">✳</i>
          <span>Keep the why nearby</span><i aria-hidden="true">✳</i>
          <span>Plan with a wider view</span>
        </div>
      </div>

      <RoadmapPreview />

      <section className="closing-section page-width">
        <div className="closing-orbit" aria-hidden="true"><span /><i /></div>
        <div>
          <p className="eyebrow">A useful starting point</p>
          <h2>Better plans begin with a shared picture.</h2>
        </div>
        <Link className="button button-light" to="/about">
          About this showcase <span aria-hidden="true">↗</span>
        </Link>
      </section>
    </>
  );
}

export default HomePage;
