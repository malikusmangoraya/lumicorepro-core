const RUN_STATE_ALIASES = {
  queued: 'queued',
  pending: 'queued',
  running: 'running',
  active: 'running',
  complete: 'completed',
  completed: 'completed',
  done: 'completed',
  success: 'completed',
  failed: 'failed',
  failure: 'failed',
  error: 'failed',
  cancelled: 'cancelled',
  canceled: 'cancelled',
};

const PHASE_STATE_ALIASES = {
  ...RUN_STATE_ALIASES,
  current: 'running',
  skipped: 'skipped',
  partial: 'partial',
};

const EVIDENCE_STATES = new Set(['passed', 'failed', 'not_measured', 'skipped', 'unavailable']);

const PHASE_GROUPS = [
  { id: 'discover', label: 'Discover', match: /discover|research|brief|audience|market/i },
  { id: 'design', label: 'Design', match: /brand|design|ux|visual|content|reference/i },
  { id: 'build', label: 'Build', match: /architect|build|implement|code|generate|scaffold/i },
  { id: 'verify', label: 'Verify', match: /verify|test|qa|audit|quality|accessib|performance|security|review/i },
  { id: 'deliver', label: 'Deliver', match: /deploy|delivery|package|export|release/i },
];

const asKey = (value) => (typeof value === 'string' ? value.trim().toLowerCase().replace(/[\s-]+/g, '_') : '');

export function normalizeRunState(value) {
  if (value === null || value === undefined || value === '') return 'unavailable';
  return RUN_STATE_ALIASES[asKey(value)] || 'unknown';
}

export function normalizePhaseState(value) {
  if (value === null || value === undefined || value === '') return 'unavailable';
  return PHASE_STATE_ALIASES[asKey(value)] || 'unknown';
}

function phaseGroupFor(name) {
  const group = PHASE_GROUPS.find((candidate) => candidate.match.test(String(name || '')));
  return group || { id: 'unknown', label: 'Unknown', match: null };
}

export function getPhaseGroups(phases) {
  const grouped = new Map();
  (Array.isArray(phases) ? phases : []).forEach((phase, index) => {
    const normalized = typeof phase === 'string' ? { name: phase } : { ...(phase || {}) };
    const group = phaseGroupFor(normalized.name || normalized.phase || normalized.id);
    const item = {
      ...normalized,
      name: normalized.name || normalized.phase || normalized.id || `Phase ${index + 1}`,
      state: group.id === 'unknown' ? 'unknown' : normalizePhaseState(normalized.state || normalized.status),
    };
    if (!grouped.has(group.id)) grouped.set(group.id, { id: group.id, label: group.label, phases: [] });
    grouped.get(group.id).phases.push(item);
  });

  return [...grouped.values()].sort(
    (a, b) =>
      (PHASE_GROUPS.findIndex((group) => group.id === a.id) + 1 || 99) -
      (PHASE_GROUPS.findIndex((group) => group.id === b.id) + 1 || 99)
  );
}

export function getEvidenceState(value) {
  if (value === null || value === undefined) return 'unavailable';
  if (value.available === false) return 'unavailable';
  const raw = asKey(value.status || value.state || value.result);
  if (raw === 'pass' || raw === 'success' || raw === 'complete' || raw === 'completed') return 'passed';
  if (raw === 'fail' || raw === 'failure' || raw === 'error') return 'failed';
  if (raw === 'not_measured' || raw === 'not_available' || raw === 'unmeasured') return 'not_measured';
  if (raw === 'skip' || raw === 'skipped') return 'skipped';
  return EVIDENCE_STATES.has(raw) ? raw : 'unknown';
}

export function getNextAction(run) {
  const data = run && typeof run === 'object' ? run : {};
  const state = normalizeRunState(data.status || data.lifecycle || data.state);
  if (state === 'failed') return 'retry';
  if (state === 'cancelled') return 'revise';
  if (state === 'running' || state === 'queued') return 'monitor';
  if (state === 'completed') {
    const score = Number(data.quality_score ?? data.qualityScore);
    return Number.isFinite(score) && score < 80 ? 'improve' : 'review';
  }
  return 'refresh';
}
