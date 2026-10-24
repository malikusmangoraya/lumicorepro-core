import { describe, expect, it } from 'vitest';
import {
  getEvidenceState,
  getNextAction,
  getPhaseGroups,
  normalizePhaseState,
  normalizeRunState,
} from '../utils/agentControlCenter';

describe('Agent Control Center view-model utilities', () => {
  it('normalizes known and unknown run states without false success', () => {
    expect(normalizeRunState('queued')).toBe('queued');
    expect(normalizeRunState('running')).toBe('running');
    expect(normalizeRunState('done')).toBe('completed');
    expect(normalizeRunState('error')).toBe('failed');
    expect(normalizeRunState('cancelled')).toBe('cancelled');
    expect(normalizeRunState('mystery')).toBe('unknown');
    expect(normalizeRunState(null)).toBe('unavailable');
  });

  it('normalizes phase states and groups phases in pipeline order', () => {
    expect(normalizePhaseState('complete')).toBe('completed');
    expect(normalizePhaseState('skipped')).toBe('skipped');
    expect(normalizePhaseState('not-measured')).toBe('unknown');

    const groups = getPhaseGroups([
      { name: 'Verify', state: 'running' },
      { name: 'Discover brief', state: 'completed' },
      { name: 'Unknown future phase', state: 'queued' },
    ]);

    expect(groups.map((group) => group.id)).toEqual(['discover', 'verify', 'unknown']);
    expect(groups[0].phases[0].name).toBe('Discover brief');
    expect(groups[2].phases[0].state).toBe('unknown');
  });

  it('maps evidence values to honest display states', () => {
    expect(getEvidenceState({ status: 'passed' })).toBe('passed');
    expect(getEvidenceState({ status: 'failed' })).toBe('failed');
    expect(getEvidenceState({ status: 'not_measured' })).toBe('not_measured');
    expect(getEvidenceState({ available: false })).toBe('unavailable');
    expect(getEvidenceState({ status: 'unexpected' })).toBe('unknown');
    expect(getEvidenceState(null)).toBe('unavailable');
  });

  it('selects a recoverable next action from run provenance', () => {
    expect(getNextAction({ status: 'failed' })).toBe('retry');
    expect(getNextAction({ status: 'cancelled' })).toBe('revise');
    expect(getNextAction({ status: 'completed', quality_score: 92 })).toBe('review');
    expect(getNextAction({ status: 'completed', quality_score: 40 })).toBe('improve');
    expect(getNextAction({ status: 'running' })).toBe('monitor');
    expect(getNextAction({})).toBe('refresh');
  });
});
