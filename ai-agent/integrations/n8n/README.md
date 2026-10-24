# LumicorePro n8n integration

This directory contains a native-node n8n workflow for starting an authenticated LumicorePro generation run and polling its lifecycle until a terminal state.

## API contract

- `POST /api/generate` accepts a JSON body with `prompt` (5–2000 characters), and optional `provider` and `dry_run`. It returns `run_id` and lifecycle status `queued`.
- `GET /api/runs/{run_id}` returns lifecycle status: `queued`, `running`, `done`, `error`, or `cancelled`, plus result/error fields when available.
- Both endpoints use the existing `X-API-KEY` contract. The workflow references an n8n Header Auth credential named `LumicorePro API Key`; it contains no key value.

## Setup

1. Set the n8n environment variable `LUMICORE_API_BASE_URL` to the reachable LumicorePro origin, without a trailing slash.
2. Import `generate-and-monitor.json` in n8n.
3. Create a Header Auth credential named `LumicorePro API Key` with header name `X-API-KEY`; enter the value in n8n's credential store, not in this repository.
4. Open the `Start generation` node and provide the input item containing `prompt`; optionally provide `provider` and `dry_run`. The included Manual Trigger is for import/smoke testing; use a Webhook, Schedule, or external trigger in production.
5. Connect the final `Build notification metadata` node to an operator-owned notification node if desired. Its payload intentionally contains only `run_id`, lifecycle `status`, and a safe `reason`.

The workflow polls at most 30 times with a five-second delay. It treats `done`, `error`, and `cancelled` as terminal; unknown states become `unexpected_status`, HTTP/request failures become `request_failed`, and an unfinished run becomes `poll_timeout`. A response without a string `run_id` becomes `missing_run_id` and is not polled.

## Networking and data minimization

If LumicorePro runs on the host and n8n runs in Docker, `localhost` inside n8n refers to the container. Use a host gateway name or a routable internal address appropriate to your deployment, and restrict the agent's bind host/CORS/API key configuration for that network. Do not expose the agent without `AGENT_API_KEY`.

The template does not send prompts, generated project content, provider credentials, or run results to notification nodes by default. Review n8n execution retention and any downstream notification payload before enabling external integrations.

## Verification limits

The JSON is covered by `ai-agent/tests/test_n8n_workflow_templates.py`, which checks the routes, credential references, lifecycle handling, bounded polling, and notification data minimization. It has not been imported or executed in a live n8n instance in this repository, so runtime compatibility with a particular n8n release remains to be verified by the operator.
