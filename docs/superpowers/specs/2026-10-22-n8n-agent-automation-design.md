# n8n Automation for LumicorePro Agent — Design Specification

**Status:** Draft for review  
**Date:** 2026-10-22

## Goal

Let operators orchestrate LumicorePro generation and QA workflows from their own n8n instance by using existing authenticated agent APIs, without embedding n8n or exposing a new unauthenticated trigger surface.

## Current context

LumicorePro has a FastAPI generation server with run creation, run status, cancellation, dry-run and event-streaming surfaces. The repository also has outbound notification helpers for arbitrary webhooks and an n8n entry in a generated project's webhook integration registry; neither is a reviewed end-to-end n8n operator workflow for the agent itself. Existing auth/bind behavior and exact request schemas need verification during implementation. The current environment cannot use web search, so official n8n import/schema guidance must be checked when network access is available; templates should use conservative native HTTP Request nodes and avoid community nodes.

## Design

- Ship version-controlled, importable n8n workflow JSON templates and a concise operator setup guide under `ai-agent/integrations/n8n/`.
- Workflows call existing LumicorePro endpoints only. Do not add a new endpoint unless an existing API proves insufficient and the user separately approves that API surface change.
- Configure the LumicorePro base URL and authentication using n8n credentials or instance variables; never include real tokens, API keys, webhook secrets, or private URLs in templates.
- Provide a bounded example flow: start generation; poll the run-status endpoint with a finite retry/timeout budget; branch on terminal success/failure; then notify through operator-configured channels. Include dry-run as a safe option if the existing request contract supports it.
- Do not put project prompts or generated output into external notification services by default. The guide must make data flow explicit and instruct operators to minimize sensitive data.
- Verify importability/JSON structure, endpoint/auth contracts against source and tests, bounded polling, terminal-state handling, and failure handling. Do not claim live n8n compatibility without importing/running in an n8n instance.

## Acceptance criteria

1. Each workflow template is valid JSON and imports without credentials embedded.
2. Every HTTP node targets an existing LumicorePro endpoint with request/response shapes verified against the actual FastAPI implementation.
3. Authentication relies only on the existing supported auth contract; no public unauthenticated generation endpoint is introduced.
4. Polling is bounded and handles success, failure, cancellation, unexpected status, and request errors without infinite loops.
5. Notification nodes do not transmit prompts/output unless an operator explicitly configures that data.
6. Setup docs describe required variables/credentials, local networking considerations, setup, test execution, and limitations.
7. Existing agent generation and current webhook functionality remain unchanged.

## Out of scope

- Embedding, hosting, or provisioning n8n.
- Automatically creating n8n accounts, workflows, credentials, or hosted services.
- Adding generated-project event callbacks (the user selected agent automation, not website event delivery).
- Supporting arbitrary community nodes or unverified n8n APIs.
