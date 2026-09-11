# LumicorePro Quick Reference

> **Start here.** Everything you need to run the **BEST-OF-YEAR** enterprise AI generation system.

## System Overview

LumicorePro generates production-grade full-stack projects from a single natural language prompt using a **10-phase pipeline** (including international delivery):

| Phase | Module | Output |
|-------|--------|--------|
| 1 | `market_analyzer.py` | Competitors, trends, positioning |
| 2 | `requirement_analyzer.py` | Structured requirement spec |
| 3 | `tech_stack_selector.py` | Optimal React/Node/PostgreSQL stack |
| 4 | `trending_features.py` | 5-20 market-leading features injected |
| 5 | `planner.py` + selectors | Assembly plan from local library |
| 6 | `project_builder.py` | Generated project on disk + ZIP |
| 7 | `quality_gates.py` + `validator.py` | Enterprise quality verification |
| 8 | `improvement_recommender.py` | ROI-ranked next steps |
| 9 | `competitive_benchmark.py` | Competitive advantage report |
| 10 | **International Delivery** | Docker, SEO, CI/CD, PWA, i18n |

## Quick Start

```bash
# 1. Initialize memory database
python ai-agent/database/init_db.py

# 2. Generate a project
python ai-agent/main.py --prompt "Build me a premium electronics e-commerce store"

# 3. Dry-run (plan only, no files written)
python ai-agent/main.py --dry-run --prompt "Create a SaaS dashboard with analytics"
```

## Quality Standards

| Metric | Target |
|--------|--------|
| Lighthouse Performance | 95+ |
| Security | Helmet, rate limit, CORS, input sanitization |
| Features | 5-7 trending auto-injected |
| Assets | Real only (zero AI-generated) |
| Code Quality | Zero validation errors |

## Project Structure

```
lumicorepro-core/
├── ai-agent/           # 9-phase generation engine
├── registry/           # JSON catalogs (components, templates, trending-features)
├── src/                # Component library + templates
├── backend-library/    # Express backend bases + shared middleware
├── database/schemas/   # PostgreSQL schemas
├── generated-projects/ # Output directory
└── docs/               # This documentation set
```

## Week 1 Checklist

- [ ] Run `python ai-agent/database/init_db.py`
- [ ] Test generation with electronics prompt
- [ ] Verify `generation-report.json` includes all 9 phases
- [ ] Copy production components from `LUMICOREPRO_QUICK_IMPLEMENTATION.md`
- [ ] Apply security middleware to backend bases
- [ ] Fix any validation warnings in generated projects

## Document Index

| Document | Purpose |
|----------|---------|
| `LUMICOREPRO_QUICK_REFERENCE.md` | This file — start here |
| `MASTER_AGENT_PROMPT_v3.md` | 9-phase AI system prompt |
| `MASTER_AGENT_IMPLEMENTATION.md` | Integration architecture |
| `LUMICOREPRO_EXECUTIVE_SUMMARY.md` | 4-week launch timeline |
| `LUMICOREPRO_SYSTEM_PROMPT.md` | Quality standards reference |
| `LUMICOREPRO_IMPROVEMENTS_ROADMAP.md` | Feature prioritization |
| `LUMICOREPRO_QUICK_IMPLEMENTATION.md` | 6 production-ready components |

## CLI Menu

```
[1] Generate New Project from Prompt
[2] Run Dry-Run Plan Simulation
[3] Re-Index & Seed SQLite Memory Database
[4] Run Automated Pytest Test Suite
[5] View Memory Registries Status Summary
[6] Exit
```

## Environment Variables

```env
ACTIVE_AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
# Optional fallbacks: DEEPSEEK_API_KEY, OPENROUTER_API_KEY
```

The system works **offline** without API keys using local rule-based analysis and component library assembly (~95% token savings).
