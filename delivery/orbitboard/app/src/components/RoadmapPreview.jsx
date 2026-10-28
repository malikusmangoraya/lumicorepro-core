import { useMemo, useState } from 'react';
import {
  DEFAULT_ROADMAP_FILTERS,
  filterRoadmap,
  ROADMAP_ITEMS,
} from '../data/roadmap.js';

const TEAMS = ['All teams', 'Product', 'Platform', 'Operations', 'Research'];

function RoadmapPreview() {
  const [filters, setFilters] = useState(DEFAULT_ROADMAP_FILTERS);
  const visibleItems = useMemo(
    () => filterRoadmap(ROADMAP_ITEMS, filters),
    [filters]
  );

  function resetSample() {
    setFilters(DEFAULT_ROADMAP_FILTERS);
  }

  return (
    <section className="preview-section page-width" id="preview" aria-labelledby="preview-title">
      <div className="section-heading preview-heading">
        <div>
          <p className="eyebrow">A small sample, not a live account</p>
          <h2 id="preview-title">A plan everyone can read.</h2>
        </div>
        <p className="section-aside">
          Move through a sample roadmap. Nothing here is saved or sent.
        </p>
      </div>

      <div className="roadmap-board">
        <div className="board-topline">
          <div className="board-title">
            <span className="board-indicator" aria-hidden="true" />
            <div>
              <span className="board-label">SAMPLE WORKSPACE</span>
              <h3>Northstar roadmap</h3>
            </div>
          </div>
          <button className="text-button" type="button" onClick={resetSample}>
            Reset sample
          </button>
        </div>

        <div className="board-toolbar">
          <label className="field-control">
            <span>Time horizon</span>
            <select
              aria-label="Time horizon"
              value={filters.horizon}
              onChange={(event) =>
                setFilters((current) => ({ ...current, horizon: event.target.value }))
              }
            >
              <option value="all">Full roadmap</option>
              <option value="next">Next two quarters</option>
              <option value="Q4 2026">Q4 2026</option>
              <option value="Q1 2027">Q1 2027</option>
            </select>
          </label>
          <fieldset className="team-filter">
            <legend>Filter by team</legend>
            <div className="filter-options">
              {TEAMS.map((team) => {
                const value = team === 'All teams' ? 'all' : team;

                return (
                  <button
                    className={`filter-chip${filters.team === value ? ' is-selected' : ''}`}
                    type="button"
                    aria-pressed={filters.team === value}
                    key={team}
                    onClick={() =>
                      setFilters((current) => ({ ...current, team: value }))
                    }
                  >
                    {team}
                  </button>
                );
              })}
            </div>
          </fieldset>
        </div>

        <div className="roadmap-list" aria-live="polite" aria-relevant="additions removals">
          {visibleItems.length > 0 ? (
            visibleItems.map((item) => (
              <article className="roadmap-item" key={item.id}>
                <span className={`item-marker marker-${item.color}`} aria-hidden="true" />
                <div className="item-copy">
                  <div className="item-heading">
                    <h4>{item.title}</h4>
                    <span className="item-team">{item.team}</span>
                  </div>
                  <p>{item.description}</p>
                </div>
                <div className="item-meta">
                  <span>{item.quarter}</span>
                  <span className="item-status">{item.status}</span>
                </div>
              </article>
            ))
          ) : (
            <p className="empty-state">No sample work matches these filters.</p>
          )}
        </div>
        <div className="board-footnote">
          <span>Example roadmap · fictional sample data</span>
          <span>{visibleItems.length} sample items</span>
        </div>
      </div>
    </section>
  );
}

export default RoadmapPreview;
