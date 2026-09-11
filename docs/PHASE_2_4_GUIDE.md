# Phase 2–4 Guide: Selectors, Assembly & Provider Fallback

## 1. Local Selection Pipeline
1. **Requirement Analyzer**: Parses prompt into structured specs (`website_type`, `industry`, `features`).
2. **Resource Selectors**: Queries SQLite memory to match best template, components, assets, Express backend, and PostgreSQL SQL schemas.
3. **Project Builder**: Assembles scaffold in `generated-projects/<project_name>/`.

## 2. Multi-Provider Fallback Chain
Configured via `AI_PROVIDER` in `ai-agent/.env`. If the primary provider fails after 3 exponential backoff retries, the agent automatically failovers down the chain:
`Gemini` ➔ `DeepSeek` ➔ `OpenRouter` ➔ `Local Offline Mode`.
