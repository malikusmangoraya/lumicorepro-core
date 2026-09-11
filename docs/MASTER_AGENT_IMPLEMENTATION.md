# Master Agent Implementation Guide

**Version:** 1.0  
**Audience:** Developers integrating the 9-phase system

---

## Architecture

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────┐
│           AgentOrchestrator (orchestrator.py)    │
│                                                  │
│  Phase 1: MarketAnalyzer                        │
│  Phase 2: RequirementAnalyzer                   │
│  Phase 3: TechStackSelector                     │
│  Phase 4: TrendingFeaturesInjector              │
│  Phase 5: Planner + Selectors                   │
│  Phase 6: ProjectBuilder + CodeModifier         │
│  Phase 7: ProjectValidator + QualityGates       │
│  Phase 8: ImprovementRecommender                │
│  Phase 9: CompetitiveBenchmark                  │
└─────────────────────────────────────────────────┘
    │
    ▼
generated-projects/{name}/
├── frontend/
├── backend/
├── database/schema.sql
├── INSTRUCTIONS.md
└── generation-report.json
```

## File Map

| File | Phase | Role |
|------|-------|------|
| `ai-agent/agent/orchestrator.py` | All | Master pipeline controller |
| `ai-agent/agent/market_analyzer.py` | 1 | Market research |
| `ai-agent/agent/requirement_analyzer.py` | 2 | Prompt → spec |
| `ai-agent/agent/tech_stack_selector.py` | 3 | Stack selection |
| `ai-agent/agent/trending_features.py` | 4 | Feature injection |
| `ai-agent/agent/planner.py` | 5 | Assembly plan |
| `ai-agent/agent/template_selector.py` | 5 | Template matching |
| `ai-agent/agent/component_selector.py` | 5 | Component matching |
| `ai-agent/agent/asset_selector.py` | 5 | Asset matching |
| `ai-agent/agent/backend_selector.py` | 5 | Backend matching |
| `ai-agent/agent/database_selector.py` | 5 | Schema matching |
| `ai-agent/agent/project_builder.py` | 6 | File assembly |
| `ai-agent/agent/code_modifier.py` | 6 | AI patches |
| `ai-agent/agent/validator.py` | 7 | Structural validation |
| `ai-agent/agent/quality_gates.py` | 7 | Enterprise gates |
| `ai-agent/agent/improvement_recommender.py` | 8 | ROI recommendations |
| `ai-agent/agent/competitive_benchmark.py` | 9 | Benchmark report |

## Integration Steps

### Step 1: Initialize Memory

```bash
cd lumicorepro-core
python ai-agent/database/init_db.py
```

This indexes:
- `registry/templates.json`
- `registry/components.json`
- `registry/images.json`, `icons.json`, `animations.json`
- `registry/backend-modules.json`
- `registry/trending-features.json`
- `database/schemas/*.sql`

### Step 2: Configure Environment

Copy `.env.example` to `.env` and set optional AI provider:

```env
ACTIVE_AI_PROVIDER=gemini
GEMINI_API_KEY=your_key
```

### Step 3: Run Generation

```python
from agent.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
report = orchestrator.run("Build a premium electronics e-commerce store")

print(report["enterprise_ready"])       # True/False
print(report["quality_gates"]["overall_score"])  # e.g. 83.3
print(report["competitive_benchmark"]["launch_ready"])
```

### Step 4: Read Report

`generation-report.json` contains:

```json
{
  "pipeline_version": "9-phase-enterprise-v1.0",
  "phases_completed": ["market_analysis", "..."],
  "phase_results": { "phase_1_market_analysis": {}, "..." },
  "quality_gates": { "overall_score": 83.3, "enterprise_ready": true },
  "improvement_recommendations": { "recommendations": [] },
  "competitive_benchmark": { "launch_ready": true }
}
```

## Production Components Integration

Copy these into generated projects or use from core library:

| Component | Path | Used In |
|-----------|------|---------|
| Icon | `src/components/common/Icon.jsx` | All UI |
| Image Validator | `src/utils/imageValidator.js` | Upload forms |
| Schema Validator | `src/utils/schemaValidator.js` | DB setup |
| Security Middleware | `backend-library/shared/middleware/security.js` | All backends |
| Error Handler | `backend-library/shared/middleware/errorHandler.js` | All backends |

### Apply Security to Backend

```javascript
const { applySecurityMiddleware } = require('../shared/middleware/security');
const errorHandler = require('../shared/middleware/errorHandler');

const app = express();
app.use(express.json());
applySecurityMiddleware(app, {
  corsOrigins: ['http://localhost:5173', process.env.FRONTEND_URL],
});
// ... routes ...
app.use(errorHandler);
```

## Extending the System

### Add a Trending Feature

Edit `registry/trending-features.json`:

```json
{
  "id": "live_inventory",
  "name": "Live Inventory Counter",
  "tags": ["ecommerce"],
  "components": ["ProductCard"],
  "roi_score": 86,
  "priority": "high"
}
```

Re-run `python ai-agent/database/init_db.py`.

### Add a Quality Gate

Extend `QualityGates.evaluate()` in `quality_gates.py` with a new check method.

### Add an Industry Benchmark

Extend `MarketAnalyzer.INDUSTRY_BENCHMARKS` in `market_analyzer.py`.

## Testing

```bash
cd ai-agent
python -m pytest tests/ -v
```

Key test: `test_e2e_electronics_generation` validates full pipeline output.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty component selection | Re-index DB: option 3 in CLI menu |
| Validation warnings | Check missing deps in package.json |
| Quality gate fails security | Ensure backend has helmet + rate-limit |
| No trending features | Verify `registry/trending-features.json` exists |
