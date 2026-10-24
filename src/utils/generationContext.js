const valueOrNull = (value) => (value === undefined || value === null ? null : value);

export function normalizeGenerationContext(payload) {
  const data = payload && typeof payload === 'object' ? payload : {};
  const report = data.result || data.report || {};
  const fallback = data.fallback_data || {};
  const provenance = data.mode === 'live_agent' ? 'live_agent' : 'offline_fallback';
  const qualityScore = valueOrNull(report.quality_gates?.overall_score ?? fallback.qualityScore);
  const hasCompletionEvidence = data.mode === 'live_agent' && Boolean(data.result);
  const lifecycle = hasCompletionEvidence
    ? 'completed'
    : provenance === 'offline_fallback'
      ? 'partial'
      : 'unknown';

  return {
    run_id: valueOrNull(data.run_id),
    project_name: report.project_name || fallback.projectName || null,
    quality_score: qualityScore,
    lifecycle,
    provenance,
    release_ready: lifecycle === 'completed' && report.workflow_agents?.qa_deployment?.handoff?.release_gate?.passed === true,
    workflow_agents: report.workflow_agents || {},
    skipped_phases: provenance === 'offline_fallback' ? ['agent verification', 'deployment evidence'] : [],
    preview_url: report.preview_url || data.preview_url || null,
    deployment_url: report.deployment_url || data.deployment_url || null,
  };
}
