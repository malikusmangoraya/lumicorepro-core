import { describe, expect, it } from 'vitest';
import { normalizeGenerationContext } from '../../utils/generationContext';

const liveAgentPayload = {
  mode: 'live_agent',
  run_id: 'run-42',
  result: {
    project_name: 'Acme Store',
    quality_gates: { overall_score: 91 },
    workflow_agents: { qa_deployment: { handoff: { release_gate: { passed: true } } } },
    preview_url: 'https://preview.test/acme',
    deployment_url: 'https://acme.test',
  },
};

describe('normalizeGenerationContext', () => {
  it('reports a live-agent run with evidence as completed and release ready', () => {
    const context = normalizeGenerationContext(liveAgentPayload);

    expect(context).toMatchObject({
      run_id: 'run-42',
      project_name: 'Acme Store',
      quality_score: 91,
      lifecycle: 'completed',
      provenance: 'live_agent',
      release_ready: true,
      preview_url: 'https://preview.test/acme',
      deployment_url: 'https://acme.test',
      skipped_phases: [],
    });
  });

  it('keeps a live run completed but not release ready when the gate failed', () => {
    const payload = {
      ...liveAgentPayload,
      result: {
        ...liveAgentPayload.result,
        workflow_agents: { qa_deployment: { handoff: { release_gate: { passed: false } } } },
      },
    };

    const context = normalizeGenerationContext(payload);
    expect(context.lifecycle).toBe('completed');
    expect(context.release_ready).toBe(false);
  });

  it('marks fallback payloads as partial and lists the skipped phases', () => {
    const context = normalizeGenerationContext({
      mode: 'fallback',
      fallback_data: { projectName: 'Fallback Site', qualityScore: 55 },
    });

    expect(context).toMatchObject({
      provenance: 'offline_fallback',
      lifecycle: 'partial',
      project_name: 'Fallback Site',
      quality_score: 55,
      release_ready: false,
      skipped_phases: ['agent verification', 'deployment evidence'],
    });
  });

  it('normalises junk payloads to nulls instead of throwing', () => {
    for (const payload of [null, undefined, 'text', 42, []]) {
      const context = normalizeGenerationContext(payload);
      expect(context.run_id).toBeNull();
      expect(context.project_name).toBeNull();
      expect(context.quality_score).toBeNull();
      expect(context.provenance).toBe('offline_fallback');
      expect(context.lifecycle).toBe('partial');
      expect(context.workflow_agents).toEqual({});
    }
  });

  it('falls back to top-level preview/deployment urls and ignores report overrides', () => {
    const context = normalizeGenerationContext({
      mode: 'live_agent',
      result: {},
      preview_url: 'https://top.test/preview',
      deployment_url: 'https://top.test/live',
    });

    expect(context.preview_url).toBe('https://top.test/preview');
    expect(context.deployment_url).toBe('https://top.test/live');
    expect(context.quality_score).toBeNull();
    expect(context.release_ready).toBe(false);
  });
});
