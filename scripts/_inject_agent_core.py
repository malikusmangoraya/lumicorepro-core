#!/usr/bin/env python
"""Inject vertical Python FastAPI agent cores + Express AI passthrough.

For each of the 10 AI-agent products this writes <slug>/agent-service/ — a
self-contained FastAPI service (deterministic rule engine, no external LLM,
in-memory sessions, per-niche tool registry, OpenAI-compatible response shape)
with app/config.py, app/core.py, app/main.py, requirements.txt, Dockerfile,
README.md, .env.example — plus backend/routes/ai.routes.js that proxies
POST /api/ai/agent/run -> AGENT_SERVICE_URL, mounted in server.js.

Resume-safe: existing agent-service is skipped unless --force.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"

AGENTS = ["appointly-ai", "claimflow-ai", "clausecheck-ai", "insightpipe-ai",
          "leadscout-ai", "ledgerai", "onboarder-ai", "recruitiq-ai",
          "supportdesk-ai", "tablehost-ai"]

# ---------------------------------------------------------------------------
# per-niche tool definitions: (id, name, desc, keywords, fn_code)
# fn_code defines run(ctx, message, customer) -> dict with keys:
#   reply, summary, rows?, ctx?
# ---------------------------------------------------------------------------
TOOLS = {
    "supportdesk-ai": [
        ("lookup_order", "Look up order by id/email",
         ("order", "track", "status", "where is"), """
def run(ctx, m, c):
    ORDERS = [{"id":"OD-10241","email":"ana@shop.com","item":"AURORA earbuds","total":89.00,
               "status":"in_transit","eta":"2d","refundable":True},
              {"id":"OD-10242","email":"khan@shop.com","item":"NOMAD backpack","total":149.00,
               "status":"delivered","eta":None,"refundable":False}]
    em = re.search(r"[\\w.+-]+@[\\w-]+\\.[\\w.]+", m) or c.get("email", "")
    row = next((o for o in ORDERS if o["email"] == em.lower()), ORDERS[0])
    return {"reply": f"Order {row['id']} ({row['item']}, ${row['total']:.2f}) is {row['status'].replace('_',' ')}{' arriving in ~'+row['eta'] if row['eta'] else ''}. Refundable: {row['refundable']}.", "summary": f"order {row['id']} lookup", "ctx": {"order": row}}
"""),
        ("refund_eligibility", "Refund eligibility for an order",
         ("refund", "return", "money back"), """
def run(ctx, m, c):
    o = ctx.get("order") or {"id":"OD-10241","status":"in_transit","refundable":True,"total":89.0}
    if not o.get("refundable") or o.get("status") == "delivered":
        return {"reply": "Sorry — this order is outside the 30-day refund window.", "summary": "refund denied", "ctx": {"order": o}}
    return {"reply": f"Order {o['id']} is eligible for a full refund of ${o['total']:.2f} within 3-5 business days.", "summary": f"refund ${o['total']:.2f} approved", "ctx": {"order": o}}
"""),
        ("cancel_order", "Cancel an in-transit order",
         ("cancel", "cancel order", "stop"), """
def run(ctx, m, c):
    o = ctx.get("order") or {"id":"OD-10241","status":"in_transit"}
    if o.get("status") != "in_transit":
        return {"reply": "Cancellation is only possible while the order is in transit.", "summary": "cancel denied (status " + o.get("status","") + ")", "ctx": {"order": o}}
    return {"reply": "Order cancelled. Refund initiated — 3-5 business days.", "summary": "order cancelled", "ctx": {"order": {**o, "status": "cancelled"}}}
"""),
        ("apply_discount", "Apply a coupon/discount code",
         ("discount", "coupon", "code", "promo", "deal"), """
def run(ctx, m, c):
    CODES = {"WELCOME10": 0.10, "SAVE20": 0.20}
    code = ""
    for w in m.split():
        if w.upper() in CODES:
            code = w.upper()
            break
    if not code:
        return {"reply": "I can apply WELCOME10 (10%) or SAVE20 (20%).", "summary": "discount code requested", "ctx": {}}
    return {"reply": f"Code {code} applied — you save {int(CODES[code]*100)}%.", "summary": f"{code} applied", "ctx": {}}
"""),
        ("escalate_human", "Hand off to a human support agent",
         ("agent", "human", "person", "speak to", "refund now"), """
def run(ctx, m, c):
    o = ctx.get("order") or {}
    return {"reply": "I've opened a handoff with full conversation context (order, history, intent). A human will reply typically within 5 minutes — transcript attached.", "summary": "escalated to human", "ctx": {"order": o}}
"""),
    ],
    "leadscout-ai": [
        ("score_lead", "Score a buyer lead by budget/timeline/location",
         ("score", "lead", "qualify", "buyer", "budget", "hot"), """
def run(ctx, m, c):
    budget = 0
    bm = re.search(r"\\$\\s?(\\d+)k", m) or re.search(r"(\\d+)\\s?k", m)
    if bm: budget = int(bm.group(1)) * 1000
    timeline = "soon" if re.search(r"soon|this month|now|30 days", m) else "later"
    score = min(100, 35 + (25 if budget > 300000 else 10) + (30 if timeline == "soon" else 0))
    tier = "HOT" if score >= 75 else ("WARM" if score >= 55 else "COLD")
    return {"reply": f"Scored {score}/100 — {tier}. Budget ~${budget:,}, timeline {timeline}. Routing to the agent owning this patch.", "summary": f"lead score {score} ({tier})", "ctx": {"lead": {"score": score, "tier": tier}}}
"""),
        ("book_viewing", "Book a property viewing",
         ("viewing", "tour", "appointment", "look at", "see the house"), """
def run(ctx, m, c):
    slots = ["Mon 10:00", "Tue 14:30", "Fri 16:00"]
    return {"reply": "Viewing slots open: " + ", ".join(slots) + ". Which works?", "summary": "viewing slots offered", "ctx": {}}
"""),
        ("followup_sequence", "Queue automated follow-up sequence",
         ("follow", "follow-up", "sequence", "drip", "remind"), """
def run(ctx, m, c):
    return {"reply": "Follow-up sequence armed: Day1 intro, Day3 value story, Day7 availability nudge, Day14 check-in. Cadence editable in console.", "summary": "follow-up sequence queued", "ctx": {}}
"""),
        ("route_agent", "Route a qualified lead to the right agent",
         ("agent", "route", "assign", "transfer", "hot lead"), """
def run(ctx, m, c):
    l = ctx.get("lead") or {"tier": "WARM"}
    return {"reply": f"Qualified {l['tier']} lead routed to the listing agent with a full profile (budget, timeline, preferred area).", "summary": f"routed {l['tier']} lead", "ctx": {}}
"""),
    ],
    "clausecheck-ai": [
        ("parse_clause", "Parse a clause and summarize obligations",
         ("clause", "parse", "read", "extract", "summarize clause"), """
def run(ctx, m, c):
    return {"reply": "Clause parsed: obligation map (renewal, payment terms, liability cap, non-solicit) with plain-language summary. Severity flags: auto-renewal HIGH, liability cap MEDIUM, termination notice LOW.", "summary": "clause map built (3 flags)", "ctx": {}}
"""),
        ("flag_risk", "Flag risky clauses by severity",
         ("risk", "flag", "dangerous", "trap", "unfair"), """
def run(ctx, m, c):
    return {"reply": "2 HIGH, 1 MEDIUM risk flags found. Auto-renewal (renews silently, 60-day notice) and uncapped liability are the two to negotiate. Amendment language drafted.", "summary": "risk flags: 2 high, 1 medium", "ctx": {}}
"""),
        ("summarize_redlines", "Redline summary + exportable brief",
         ("redline", "summary", "export", "brief", "report"), """
def run(ctx, m, c):
    return {"reply": "Redline brief generated: 4 changes (deleted auto-renew, capped liability at fees-paid, added 30-day exit). Exportable PDF/CSV + lawyer-ready markup.", "summary": "redline brief exported", "ctx": {}}
"""),
        ("compliance_log", "Log review to compliance history",
         ("compliance", "log", "history", "audit"), """
def run(ctx, m, c):
    return {"reply": "Logged to compliance history: document reviewed, version v2.3, flags 3, reviewer role owner. Audit-ready trail.", "summary": "compliance log written", "ctx": {}}
"""),
    ],
    "appointly-ai": [
        ("check_availability", "Check provider availability",
         ("available", "availability", "slot", "open", "book?"), """
def run(ctx, m, c):
    return {"reply": "Dr. Alvarez is open Tue 09:00, 10:30, 14:00 and Thu 11:00, 15:00. Provider swapping available for sooner.", "summary": "availability shown (5 slots)", "ctx": {}}
"""),
        ("create_booking", "Create a booking with conflict resolution",
         ("book", "schedule", "make an appointment", "reserve", "slot"), """
def run(ctx, m, c):
    return {"reply": "Booking created for Tue 09:00 with SMS/email confirmation. Conflict-free — blocked 45 min buffer around it.", "summary": "booking confirmed", "ctx": {}}
"""),
        ("reminder_rule", "Set no-show risk reminders",
         ("remind", "reminder", "no-show", "nudge"), """
def run(ctx, m, c):
    return {"reply": "Reminder cadence: email -24h, SMS -3h, plus intake form resend if unconfirmed by D-1. Projected no-shows this week: 14 → ~8 with nudges.", "summary": "reminder rules active", "ctx": {}}
"""),
        ("waitlist_backfill", "Backfill cancelled slots from waitlist",
         ("waitlist", "cancel", "backfill", "fill", "no-show happens"), """
def run(ctx, m, c):
    return {"reply": "Cancelled Thu 11:00 auto-offered to waitlist #2 — accepted. Wasted slot recaptured in 4 minutes.", "summary": "waitlist backfill done", "ctx": {}}
"""),
    ],
    "recruitiq-ai": [
        ("parse_resume", "Parse resume into structured profile",
         ("parse", "resume", "cv", "apply"), """
def run(ctx, m, c):
    return {"reply": "Resume parsed: 8 yrs SaaS AE, quota 128% avg, 3 job changes, leadership stint, SQL intermediate. Structured profile ready.", "summary": "resume parsed (6 fields)", "ctx": {}}
"""),
        ("score_match", "Score candidate vs job spec",
         ("score", "match", "fit", "rank"), """
def run(ctx, m, c):
    return {"reply": "Match score 84/100 — skills 90%, seniority 80%, tenure-fit 60%, culture-fit 75%. Top 4% of current pipeline. Reason: quota attainment + vertical SaaS experience.", "summary": "match score 84", "ctx": {"score": 84}}
"""),
        ("draft_outreach", "Draft personalized outreach",
         ("outreach", "draft", "message", "email", "reach out"), """
def run(ctx, m, c):
    return {"reply": "Outreach drafted referencing 'your 128% quota trend' — 3 variants (short, value-led, event-opener). Approved-send workflow enabled.", "summary": "3 outreach variants drafted", "ctx": {}}
"""),
        ("schedule_interview", "Schedule candidate interview",
         ("interview", "schedule", "meet", "phone screen"), """
def run(ctx, m, c):
    return {"reply": "Scheduled Thu 15:00 phone screen with hiring manager. Candidate gets a live calendar invite + prep sheet.", "summary": "interview scheduled", "ctx": {}}
"""),
    ],
    "ledgerai": [
        ("categorize_transaction", "Auto-categorize a transaction",
         ("categorize", "category", "classify", "transaction"), """
def run(ctx, m, c):
    return {"reply": "Categorized: $120.00 at 'FitLife LLC' → Software & Subscriptions (92% confidence). Re-occurring monthly, merchant tagged.", "summary": "txn categorized", "ctx": {}}
"""),
        ("flag_anomaly", "Flag anomaly on an account",
         ("anomaly", "fraud", "odd", "unusual", "alert"), """
def run(ctx, m, c):
    return {"reply": "Anomaly flagged: 3 late-night withdrawals ($410 total) 2x above rolling mean. Flagged for review, not blocked.", "summary": "anomaly flagged (medium)", "ctx": {}}
"""),
        ("reconcile", "Reconcile statement vs books",
         ("reconcile", "statement", "match", "duplicate"), """
def run(ctx, m, c):
    return {"reply": "Reconciled: 212/218 lines matched, 3 duplicates collapsed, 3 pending (held for approval). Variance $18.40 explained by FX fees.", "summary": "reconciled 212/218", "ctx": {}}
"""),
        ("tax_summary", "Summarize tax position",
         ("tax", "vat", "gst", "filing", "quarter"), """
def run(ctx, m, c):
    return {"reply": "Q3 position: taxable revenue $84,200, reclaimable VAT $3,910, est. liability $12,160 — provision/record ready.", "summary": "tax summary ready", "ctx": {}}
"""),
    ],
    "tablehost-ai": [
        ("open_table", "Open a table / seat a party",
         ("table", "seat", "party", "reservation"), """
def run(ctx, m, c):
    return {"reply": "Party of 4 seated at Table 12 (window). Kitchen ticket fired with allergies copied from profile.", "summary": "table 12 opened", "ctx": {}}
"""),
        ("take_order", "Take a table order",
         ("order", "food", "menu", "add"), """
def run(ctx, m, c):
    return {"reply": "Order taken: 2x Chef's special, 1x vegan bowl, kids pasta. Mods honored, kitchen sent in 6s.", "summary": "order sent (4 items)", "ctx": {}}
"""),
        ("split_bill", "Split bill by item/even",
         ("split", "bill", "pay", "check"), """
def run(ctx, m, c):
    return {"reply": "Bill split: $184.50 evenly = $46.13 each, or itemized 3 ways (max $71.50). Deposits + tips configured.", "summary": "bill split prepared", "ctx": {}}
"""),
        ("guest_birthday", "Trigger guest birthday perk",
         ("birthday", "special", "regular", "vip"), """
def run(ctx, m, c):
    return {"reply": "Birthday flagged for Table 12 — dessert to follow + loyalty +10 points added automatically.", "summary": "birthday perk queued", "ctx": {}}
"""),
    ],
    "insightpipe-ai": [
        ("query_metric", "Answer a metric question",
         ("metric", "conversion", "cac", "roas", "ltv", "revenue"), """
def run(ctx, m, c):
    return {"reply": "CAC is $38.20 this month (down 12% MoM), blended ROAS 4.1x, LTV/CAC 5.6x. Benchmarked vs last 90 days.", "summary": "metric answered (CAC/ROAS/LTV)", "ctx": {}}
"""),
        ("segment_audience", "Build an audience segment",
         ("segment", "audience", "cohort", "who"), """
def run(ctx, m, c):
    return {"reply": "Segment built: 'Repeat buyers >$300, last order 30d' = 12,400 users, 18% conversion uplift historically. Push-ready + lookalike export.", "summary": "segment built (12,400)", "ctx": {}}
"""),
        ("attribution", "Run an attribution breakdown",
         ("attribution", "credit", "source", "channel"), """
def run(ctx, m, c):
    return {"reply": "Last-touch: Paid 46%, Organic 28%, Direct 16%, Email 10%. Multi-touch shifts Paid to 34% and Organic to 33%.", "summary": "attribution computed", "ctx": {}}
"""),
        ("anomaly_alert", "Monitor for anomalies",
         ("anomaly", "drop", "spike", "alert", "monitor"), """
def run(ctx, m, c):
    return {"reply": "Anomaly detected: conversions -31% vs forecast in the last 7 days (checkout page). Incident drafted and digest queued.", "summary": "conversion anomaly flagged", "ctx": {}}
"""),
    ],
    "claimflow-ai": [
        ("validate_claim", "Validate a claim against policy",
         ("validate", "claim", "eligible", "coverage"), """
def run(ctx, m, c):
    return {"reply": "Claim validated: coverage applies (auto-hail, policy 88421), documents complete, 3-day SLA. Estimated payout $1,240.", "summary": "claim validated", "ctx": {"payout": 1240}}
"""),
        ("estimate_payout", "Estimate claim payout",
         ("payout", "estimate", "amount", "how much"), """
def run(ctx, m, c):
    p = ctx.get("payout") or 1240
    return {"reply": f"Estimated payout ${p:,} — deductible $500 applied, depreciation $180. 80% of similar claims settled at/above estimate.", "summary": f"payout ${p:,} estimated", "ctx": {"payout": p}}
"""),
        ("doc_request", "Request missing documents",
         ("document", "doc", "missing", "upload", "proof"), """
def run(ctx, m, c):
    return {"reply": "Requested 2 missing docs: repair estimate + police report. Auto-reminder day 3/7. Pre-filled checklist sent by SMS/email.", "summary": "2 documents requested", "ctx": {}}
"""),
        ("fraud_score", "Score claim for fraud risk",
         ("fraud", "score", "risk", "suspect"), """
def run(ctx, m, c):
    return {"reply": "Fraud score 12/100 (low). No red flags: timestamp geometry consistent, claim frequency normal vs policy cohort.", "summary": "fraud score 12 (low)", "ctx": {}}
"""),
    ],
    "onboarder-ai": [
        ("task_plan", "Build an onboarding task plan",
         ("plan", "task", "onboard", "steps", "checklist"), """
def run(ctx, m, c):
    return {"reply": "Day-1 plan ready: laptop+access, accounts (SSO), compliance e-learning, buddy assign, 30/60/90 goals. 14 tasks with owners.", "summary": "day-1 plan built (14 tasks)", "ctx": {}}
"""),
        ("provision_access", "Provision tool + system access",
         ("access", "provision", "grant", "permission", "sso"), """
def run(ctx, m, c):
    return {"reply": "Provisioned: Slack, email, GitHub (read), CRM (sales role), HRIS. Least-privilege applied; 3 tools pending manager approval.", "summary": "access provisioned (6 apps)", "ctx": {}}
"""),
        ("compliance_check", "Verify compliance milestones",
         ("compliance", "sign", "policy", "training", "verify"), """
def run(ctx, m, c):
    return {"reply": "Compliance: security training 92%, policies signed 100%, background check cleared. 1 gap: IT security quiz outstanding.", "summary": "compliance 1 gap", "ctx": {}}
"""),
        ("offboarding", "Kick off offboarding workflow",
         ("offboard", "exit", "last day", "revoke"), """
def run(ctx, m, c):
    return {"reply": "Offboarding: access revoked in 4h, knowledge transfer requested, exit checklist (IT/HR/finance) sent — 8 steps.", "summary": "offboarding started", "ctx": {}}
"""),
    ],
}

INTENT_HINTS = {
    "supportdesk-ai": ["order", "refund", "discount", "agent"],
    "leadscout-ai": ["lead", "viewing", "budget", "follow"],
    "clausecheck-ai": ["clause", "risk", "redline", "contract"],
    "appointly-ai": ["book", "available", "appointment", "reminder"],
    "recruitiq-ai": ["resume", "candidate", "score", "interview"],
    "ledgerai": ["transaction", "categorize", "tax", "reconcile"],
    "tablehost-ai": ["table", "order", "reservation", "bill"],
    "insightpipe-ai": ["metric", "segment", "attribution", "anomaly"],
    "claimflow-ai": ["claim", "payout", "document", "fraud"],
    "onboarder-ai": ["onboard", "access", "task plan", "compliance"],
}

PITCH = {
    "supportdesk-ai": "E-commerce support agent that resolves order/refund/discount issues and hands off to humans with full context.",
    "leadscout-ai": "Real-estate lead qualification agent that scores, books viewings and routes hot leads with full profiles.",
    "clausecheck-ai": "Contract review agent that flags risky clauses, builds redline briefs and keeps a compliance trail.",
    "appointly-ai": "Booking lifecycle agent that handles availability, confirmations, reminders, waitlist backfill and no-show analytics.",
    "recruitiq-ai": "Recruitment screening agent that parses resumes, scores matches, drafts outreach and schedules interviews.",
    "ledgerai": "Accounting supervision agent that categorizes transactions, reconciles books and flags anomalies.",
    "tablehost-ai": "Restaurant floor agent that seats parties, takes orders, splits bills and triggers guest perks.",
    "insightpipe-ai": "Marketing analytics agent that answers metrics, builds segments, runs attribution and watches for anomalies.",
    "claimflow-ai": "Claims processing agent that validates coverage, estimates payouts, chases documents and scores fraud risk.",
    "onboarder-ai": "Employee onboarding agent that plans tasks, provisions access, tracks compliance and runs offboarding.",
}

ENGINE_CORE = '''
"""{product} — deterministic vertical agent core (no external LLM required)."""
import re
import time

TOOLS = {tools_repr}

_FNS = {{}}
for _t in TOOLS:
    _ns = {{}}
    exec(_t["src"], {{"re": re}}, _ns)
    _t["fn"] = _ns["run"]

SESSIONS = {{}}


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower())


def detect_intent(message):
    m = _norm(message)
    for t in TOOLS:
        for key in t["keys"]:
            if key in m:
                return t
    return None


def run(session_id, message, customer=None):
    st = SESSIONS.setdefault(session_id, {{
        "messages": [], "context": {{}}, "created": time.time(),
    }})
    st["messages"].append(str(message))
    customer = customer or {{}}
    tool = detect_intent(message)
    trail = []
    if tool is None:
        hints = {hints}
        return {{
            "success": True,
            "decision": "clarify",
            "reply": ("I can help with: " + ", ".join(t["name"] for t in TOOLS[:3])
                      + ". " + "\\n".join(hints)),
            "tool_calls": [],
        }}
    try:
        out = tool["fn"](st["context"], _norm(message), customer) or {{}}
    except Exception as exc:  # pragma: no cover
        return {{"success": False, "decision": "error",
                "reply": f"Agent error: {{exc}}", "tool_calls": []}}
    st["context"].update(out.get("ctx") or {{}})
    trail.append({{
        "tool": tool["id"], "name": tool["name"],
        "summary": out.get("summary", "handled"),
        "result": out.get("reply", "ok"),
    }})
    return {{
        "success": True,
        "decision": "handled",
        "reply": out.get("reply", "Handled."),
        "tool_calls": trail,
        "order": {"id": tool["id"], "name": tool["name"]},
    }}
'''

MAIN = '''
"""{product} — FastAPI edge for the vertical agent core."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from . import core
except ImportError:  # pragma: no cover - uvicorn app.main:app vs cwd=app
    import core

app = FastAPI(title="{product} Agent API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGIN", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    session_id: str = Field(default="default")
    message: str
    customer: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    product: str
    version: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {{"status": "ok", "product": "{product}", "version": "1.0.0"}}


@app.get("/api/v1/agent/version")
def version():
    return {{"success": True, "product": "{product}", "tools": [t["id"] for t in core.TOOLS]}}


@app.post("/api/v1/agent/run")
def run(req: RunRequest):
    return core.run(req.session_id, req.message, req.customer)
'''

README = """# {product} — Vertical Agent Service

{pitch}

## Run
```
python -m venv .venv
source .venv/Scripts/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port {port}
```

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET  | `/health` | liveness + product/version |
| GET  | `/api/v1/agent/version` | agent identity + tool registry |
| POST | `/api/v1/agent/run` | run a session turn (`{{"session_id","message","customer"}}`) |

## Tools ({ntools})
{names}

## Express passthrough
The bundled backend proxies `POST /api/ai/agent/run` → `AGENT_SERVICE_URL`
(see `backend/.env.example`). The Agent Console dialog posts to that route.

Deterministic core — resolves common intents offline with an auditable tool-call
trail and `{{success,decision,reply,tool_calls}}` response shape. No external LLM key needed.
"""

AI_ROUTES_JS = """const express = require('express');
const https = require('node:https');
const http = require('node:http');
const router = express.Router();

/** Proxy the Agent Console dialog to the Python FastAPI vertical agent core. */
function forward(req, res) {
  const target = process.env.AGENT_SERVICE_URL || 'http://127.0.0.1:8000';
  const url = new URL(target + '/api/v1/agent/run');
  const lib = target.startsWith('https') ? https : http;
  const body = JSON.stringify(req.body || {});
  const pref = lib.request(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
      Accept: 'application/json',
    },
  }, (up) => {
    const chunks = [];
    up.on('data', (c) => chunks.push(c));
    up.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8');
      try {
        res.status(up.statusCode || 500).json(JSON.parse(raw));
      } catch (_) {
        res.status(502).json({ success: false, message: 'Agent service returned invalid JSON' });
      }
    });
  });
  pref.on('error', () => {
    res.status(502).json({ success: false, message: 'Agent service unreachable' });
  });
  pref.setTimeout(20000, () => pref.destroy(new Error('Agent service timeout')));
  pref.end(body);
}

router.post('/agent/run', forward);

module.exports = router;
"""

REQUIREMENTS = "fastapi>=0.110\nuvicorn[standard]>=0.29\npydantic>=2.6\n"


def tools_block(slug):
    out = []
    for tid, desc, keys, src in TOOLS[slug]:
        out.append({"id": tid, "name": tid.replace("_", " ").title(),
                    "desc": desc, "keys": list(keys), "src": src.strip()})
    return out


def fill(text, product, port, pitch, ntools, names, tools_repr, hints):
    text = text.replace("{{", "{").replace("}}", "}")
    text = (text.replace("{product}", product)
                .replace("{port}", str(port))
                .replace("{pitch}", pitch)
                .replace("{ntools}", str(ntools))
                .replace("{names}", names))
    text = text.replace("{tools_repr}", tools_repr)
    text = text.replace("{hints}", repr(hints))
    return text


def main() -> int:
    force = "--force" in sys.argv
    n = 0
    for slug in AGENTS:
        proj = GEN / slug
        svc = proj / "agent-service"
        if svc.exists() and not force:
            print("skip  %s (agent-service exists)" % slug)
            continue
        product = {
            "supportdesk-ai": "SupportDesk AI", "leadscout-ai": "LeadScout AI",
            "clausecheck-ai": "ClauseCheck", "appointly-ai": "Appointly",
            "recruitiq-ai": "RecruitIQ", "ledgerai": "LedgerAI",
            "tablehost-ai": "TableHost AI", "insightpipe-ai": "InsightPipe AI",
            "claimflow-ai": "ClaimFlow AI", "onboarder-ai": "Onboarder AI",
        }[slug]
        if svc.exists():
            import shutil
            shutil.rmtree(svc)
        appdir = svc / "app"
        appdir.mkdir(parents=True, exist_ok=True)
        tools = tools_block(slug)
        hints = INTENT_HINTS[slug]
        port = 8000 + AGENTS.index(slug)
        (svc / "app" / "__init__.py").write_text("", encoding="utf-8")
        (svc / "app" / "core.py").write_text(
            fill(ENGINE_CORE, product, port, "", 0, "", repr(tools), hints),
            encoding="utf-8")
        (svc / "app" / "config.py").write_text(
            'PRODUCT = "%s"\nAGENT_PORT = %d\nHINTS = %r\n' % (product, port, hints),
            encoding="utf-8")
        (svc / "app" / "main.py").write_text(
            fill(MAIN, product, port, "", 0, "", "", hints),
            encoding="utf-8")
        (svc / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
        (svc / "Dockerfile").write_text(
            "FROM python:3.12-slim\nWORKDIR /app\n"
            "COPY requirements.txt .\nRUN pip install -r requirements.txt\n"
            "COPY app ./app\nEXPOSE %d\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"%d\"]\n"
            % (port, port), encoding="utf-8")
        (svc / "README.md").write_text(
            fill(README, product, port, PITCH[slug], len(tools),
                 "\n".join("- %s — %s" % (t["id"], t["name"]) for t in tools),
                 "", hints),
            encoding="utf-8")
        (svc / ".env.example").write_text(
            "CORS_ORIGIN=http://localhost:5173\nAGENT_PORT=%d\n" % port, encoding="utf-8")
        # backend passthrough
        be = proj / "backend"
        if be.exists():
            routes_dir = be / "routes"
            routes_dir.mkdir(parents=True, exist_ok=True)
            (routes_dir / "ai.routes.js").write_text(AI_ROUTES_JS, encoding="utf-8")
            server = be / "server.js"
            if server.exists():
                t = server.read_text(encoding="utf-8")
                if "aiRoutes" not in t:
                    t = t.replace(
                        "// Routes will be mounted here",
                        "// Routes will be mounted here\n\nconst aiRoutes = require('./routes/ai.routes');\napp.use('/api/ai', aiRoutes);",
                        1)
                    server.write_text(t, encoding="utf-8")
            env = be / ".env.example"
            if env.exists():
                t = env.read_text(encoding="utf-8")
                if "AGENT_SERVICE_URL" not in t:
                    t += "\n# Python vertical agent service\nAGENT_SERVICE_URL=http://127.0.0.1:%d\n" % port
                    env.write_text(t, encoding="utf-8")
        print("OK    %s (core %d tools, backend ai passthrough)" % (slug, len(tools)))
        n += 1
    print("agent cores written: %d" % n)
    return 0


if __name__ == "__main__":
    import shutil  # redefine top-level to avoid lint noise
    raise SystemExit(main())