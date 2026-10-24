# n8n Automation for LumicorePro Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide importable n8n examples to trigger and monitor LumicorePro agent runs through the existing authenticated API.

**Architecture:** Keep the integration as data/documentation under `ai-agent/integrations/n8n/`, using built-in HTTP Request/flow nodes only. Before creating templates, verify auth, request, response, and terminal run-state contracts from actual FastAPI code/tests; do not change server routes unless separately approved.

**Tech Stack:** Existing FastAPI server; n8n native workflow JSON; Node/Python standard test tooling already in the repository.

**Spec:** [2026-10-22-n8n-agent-automation-design.md](../specs/2026-10-22-n8n-agent-automation-design.md)

## Global Constraints

- Use existing authenticated LumicorePro endpoints only; no new public unauthenticated generation endpoint.
- Workflow JSON contains no credentials, private URLs, or real tokens.
- Polling has a finite attempt/time limit and covers success, error, cancellation, unexpected state, and HTTP errors.
- Prompts and generated artifacts are not sent to notifications by default.
- Use n8n built-in nodes only; do not claim live n8n import/runtime validation without testing in an n8n instance.

## Review Focus

- Missing/invalid auth credential: endpoint must reject safely and the workflow must stop/report failure.
- Generation request returns malformed or missing run ID: workflow must not poll an undefined identifier.
- Run stays queued/running forever: polling must terminate within its configured bound.
- Run reaches error/cancelled/unknown lifecycle state: workflow must take the correct non-success path.
- n8n base URL cannot reach a host-loopback LumicorePro service: setup guide must explain container networking and the workflow must expose configuration rather than hardcode localhost.

---

### Task 1: Verify existing API/auth contract and codify it in tests

**Files:**
- Test: `ai-agent/tests/test_n8n_workflow_templates.py`
- Read-only source references to verify: `ai-agent/server.py`, its relevant API tests, and `ai-agent/agent/extensions/notify.py`

**Interfaces:**
- Existing API contract must identify exact generation request fields, auth header/credential mechanism, run ID response shape, run status route and lifecycle terminal states.

- [ ] Add tests that currently fail because templates are not present: `test_templates_are_valid_json_without_embedded_credentials`, `test_http_nodes_use_existing_routes_and_auth_placeholders`, and `test_polling_is_bounded_and_handles_terminal_states`.
- [ ] Inspect and cite exact route definitions, Pydantic request models, auth dependency, response shape, and run-state transitions; do not infer contracts from route names.
- [ ] Run `pytest ai-agent/tests/test_n8n_workflow_templates.py -q` and confirm the missing-artifact failures.

### Task 2: Add importable native-node workflow templates

**Files:**
- Create: `ai-agent/integrations/n8n/generate-and-monitor.json`
- Create: `ai-agent/integrations/n8n/README.md`
- Test: `ai-agent/tests/test_n8n_workflow_templates.py`

**Interfaces:**
- Workflow inputs: operator-configured `LUMICORE_API_BASE_URL`, n8n credential, and explicit project prompt.
- Workflow outputs: run start result, bounded status result, and success/failure notification metadata without prompt or generated output unless explicitly opted in.

- [ ] Implement a valid native-node workflow with request generation, validated run-id extraction, bounded poll loop, explicit terminal-state branches, and credential references only.
- [ ] Add setup instructions for n8n credentials/environment variables, secure LumicorePro binding, container networking, import, test run, and data minimization.
- [ ] Run template JSON/contract tests; expected: all tests pass.

### Task 3: Validate workflow contracts and operational boundaries

**Files:**
- Modify: `ai-agent/tests/test_n8n_workflow_templates.py`
- Modify: `ai-agent/integrations/n8n/README.md`

- [ ] Add tests for missing run ID, bounded retry count, success/error/cancelled/unexpected terminal values, and notification payload exclusion of prompt/output.
- [ ] Run `pytest ai-agent/tests/test_n8n_workflow_templates.py -q` and relevant server auth/run-status tests.
- [ ] Validate the workflow import against an actual n8n instance only if one is available; otherwise report import-level schema checking as partial verification and do not claim n8n runtime success.
- [ ] Verify no server route or authentication behavior changed and report limitations clearly.

---
