export const ROADMAP_ITEMS = [
  {
    id: 'voice-of-customer',
    title: 'Voice of the customer',
    description: 'Bring feedback themes into planning conversations.',
    team: 'Product',
    quarter: 'Q4 2026',
    status: 'In discovery',
    color: 'coral',
  },
  {
    id: 'shared-views',
    title: 'Shared roadmap views',
    description: 'Give every team a useful view of the same plan.',
    team: 'Platform',
    quarter: 'Q4 2026',
    status: 'In progress',
    color: 'ink',
  },
  {
    id: 'dependency-map',
    title: 'Dependency map',
    description: 'Make cross-team handoffs easier to spot.',
    team: 'Platform',
    quarter: 'Q4 2026',
    status: 'Planned',
    color: 'sand',
  },
  {
    id: 'release-notes',
    title: 'Release notes',
    description: 'Connect shipped work back to the original intent.',
    team: 'Product',
    quarter: 'Q1 2027',
    status: 'Planned',
    color: 'coral',
  },
  {
    id: 'capacity-signals',
    title: 'Capacity signals',
    description: 'See the shape of the work before dates get set.',
    team: 'Operations',
    quarter: 'Q1 2027',
    status: 'Exploring',
    color: 'ink',
  },
  {
    id: 'research-library',
    title: 'Research library',
    description: 'Keep decisions close to the evidence behind them.',
    team: 'Research',
    quarter: 'Q2 2027',
    status: 'Exploring',
    color: 'sand',
  },
];

export const DEFAULT_ROADMAP_FILTERS = {
  horizon: 'all',
  team: 'all',
};

const HORIZON_QUARTERS = {
  next: ['Q4 2026', 'Q1 2027'],
  'Q4 2026': ['Q4 2026'],
  'Q1 2027': ['Q1 2027'],
};

export function filterRoadmap(items, { horizon, team }) {
  return items.filter((item) => {
    const matchesHorizon =
      horizon === 'all' || HORIZON_QUARTERS[horizon]?.includes(item.quarter);
    const matchesTeam = team === 'all' || item.team === team;

    return matchesHorizon && matchesTeam;
  });
}
