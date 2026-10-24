import { describe, expect, it } from 'vitest';
import { normalizeGenerationContext } from '../utils/generationContext';

describe('generation handoff context', () => {
  it('preserves live run provenance and quality evidence', () => {
    const context = normalizeGenerationContext({
      mode: 'live_agent',
      run_id: 'run-live-1',
      result: { project_name: 'Acme', quality_gates: { overall_score: 88 } },
    });

    expect(context.run_id).toBe('run-live-1');
    expect(context.project_name).toBe('Acme');
    expect(context.quality_score).toBe(88);
    expect(context.provenance).toBe('live_agent');
    expect(context.lifecycle).toBe('completed');
  });

  it('marks offline fallback as partial and never release-ready', () => {
    const context = normalizeGenerationContext({
      mode: 'offline_engine',
      run_id: 'run-fallback-1',
      fallback_data: { projectName: 'Fallback Site', qualityScore: 95 },
    });

    expect(context.project_name).toBe('Fallback Site');
    expect(context.provenance).toBe('offline_fallback');
    expect(context.lifecycle).toBe('partial');
    expect(context.release_ready).toBe(false);
    expect(context.skipped_phases.length).toBeGreaterThan(0);
  });

  it('does not invent success when report fields are absent', () => {
    const context = normalizeGenerationContext({ mode: 'live_agent', run_id: 'run-unknown' });

    expect(context.lifecycle).toBe('unknown');
    expect(context.quality_score).toBeNull();
    expect(context.release_ready).toBe(false);
  });
});
