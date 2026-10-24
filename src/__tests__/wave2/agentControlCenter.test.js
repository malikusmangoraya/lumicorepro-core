import { describe, expect, it } from 'vitest';
import {
  getEvidenceState,
  getNextAction,
  getPhaseGroups,
  normalizePhaseState,
  normalizeRunState,
} from '../../utils/agentControlCenter';

describe('agentControlCenter run/phase state normalization', () => {
  it('normalizes aliases case-insensitively and trims whitespace', () => {
    expect(normalizeRunState(' SUCCESS ')).toBe('completed');
    expect(normalizeRunState('Pending')).toBe('queued');
    expect(normalizeRunState('ACTIVE')).toBe('running');
    expect(normalizeRunState('Canceled')).toBe('cancelled');
    expect(normalizeRunState('unexpected')).toBe('unknown');
    expect(normalizeRunState('')).toBe('unavailable');
    expect(normalizeRunState(undefined)).toBe('unavailable');
  });

  it('supports the phase-only states in addition to run aliases', () => {
    expect(normalizePhaseState('current')).toBe('running');
    expect(normalizePhaseState('partial')).toBe('partial');
    expect(normalizePhaseState(' Skipped ')).toBe('skipped');
    expect(normalizePhaseState('active')).toBe('running');
    expect(normalizePhaseState('mystery')).toBe('unknown');
    expect(normalizePhaseState(null)).toBe('unavailable');
  });

  it('groups string and object phases, keeping extra properties', () => {
    const groups = getPhaseGroups([
      'Market research',
      { id: 'deploy-release', state: 'done', owner: 'ops' },
      { name: 'Some future phase' },
    ]);

    const discover = groups.find((group) => group.id === 'discover');
    expect(discover.phases[0]).toMatchObject({
      name: 'Market research',
      state: 'unavailable',
    });

    const deliver = groups.find((group) => group.id === 'deliver');
    expect(deliver.phases[0]).toMatchObject({
      name: 'deploy-release',
      state: 'completed',
      owner: 'ops',
    });

    const unknown = groups.find((group) => group.id === 'unknown');
    expect(unknown.phases[0]).toMatchObject({
      name: 'Some future phase',
      state: 'unknown',
    });
  });

  it('orders groups by pipeline stage and tolerates non-array input', () => {
    const groups = getPhaseGroups([
      { name: 'Deploy', state: 'running' },
      { name: 'Verify QA', state: 'running' },
      { name: 'Build', state: 'running' },
      { name: 'Design', state: 'running' },
      { name: 'Discover', state: 'running' },
    ]);

    expect(groups.map((group) => group.id)).toEqual([
      'discover',
      'design',
      'build',
      'verify',
      'deliver',
    ]);
    expect(getPhaseGroups(null)).toEqual([]);
    expect(getPhaseGroups(undefined)).toEqual([]);
  });
});

describe('agentControlCenter evidence and next-action helpers', () => {
  it('maps evidence fields to honest display states', () => {
    expect(getEvidenceState({ state: 'success' })).toBe('passed');
    expect(getEvidenceState({ result: 'FAIL' })).toBe('failed');
    expect(getEvidenceState({ status: 'not available' })).toBe('not_measured');
    expect(getEvidenceState({ status: 'SKIPPED' })).toBe('skipped');
    expect(getEvidenceState({ status: 'passed', available: false })).toBe('unavailable');
    expect(getEvidenceState(undefined)).toBe('unavailable');
    expect(getEvidenceState('passed')).toBe('unknown');
  });

  it('selects a next action across lifecycle aliases and quality thresholds', () => {
    expect(getNextAction({ lifecycle: 'pending' })).toBe('monitor');
    expect(getNextAction({ status: 'done', qualityScore: '95' })).toBe('review');
    expect(getNextAction({ status: 'completed', quality_score: 80 })).toBe('review');
    expect(getNextAction({ status: 'completed', quality_score: 79.9 })).toBe('improve');
    expect(getNextAction({ status: 'completed', qualityScore: 'great' })).toBe('review');
    expect(getNextAction({ status: 'failure' })).toBe('retry');
    expect(getNextAction(null)).toBe('refresh');
  });
});
