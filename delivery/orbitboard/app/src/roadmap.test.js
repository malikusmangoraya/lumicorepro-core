import { describe, expect, it } from 'vitest';
import {
  DEFAULT_ROADMAP_FILTERS,
  filterRoadmap,
  ROADMAP_ITEMS,
} from './data/roadmap.js';

describe('sample roadmap filters', () => {
  it('shows all fictional sample items by default', () => {
    expect(filterRoadmap(ROADMAP_ITEMS, DEFAULT_ROADMAP_FILTERS)).toHaveLength(6);
  });

  it('limits the selected horizon and team together', () => {
    const filtered = filterRoadmap(ROADMAP_ITEMS, {
      horizon: 'Q4 2026',
      team: 'Platform',
    });

    expect(filtered.map((item) => item.title)).toEqual([
      'Shared roadmap views',
      'Dependency map',
    ]);
  });

  it('returns an empty result for a horizon with no matching work', () => {
    expect(
      filterRoadmap(ROADMAP_ITEMS, { horizon: 'Q1 2027', team: 'Research' })
    ).toEqual([]);
  });
});
