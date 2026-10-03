#!/usr/bin/env python
"""LumicorePro Build — 10 vertical AI Agent SaaS products (2026 market research).

Vertical agents win over horizontal platforms (Sierra, Harvey precedent). Each
product is a full-stack SaaS: React 19 + Vite + Tailwind frontend, Express +
MySQL backend, with an Agent Console (chat + tool calls + usage analytics)
built through the AI Website Factory pipeline. Python FastAPI agent cores are
injected in a later step (scripts/_inject_agent_core.py).

Resume-safe: completed projects are skipped via state file.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-agent"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ai-agents")

BRIEFS = [
    {
        "id": "agent-01",
        "slug": "supportdesk-ai",
        "brand": "SupportDesk AI",
        "market": "E-commerce customer support agent",
        "prompt": (
            "Build 'SupportDesk AI' — a vertical AI agent SaaS that automates e-commerce customer support: "
            "order tracking, returns and refunds, cancellation, discount codes, and human handoff with full "
            "context. Audience: Shopify/WooCommerce merchants drowning in tickets (human tickets cost $15-25, "
            "agent $0.50-2). Product: full-stack SaaS with auth (register/login/2FA, JWT+refresh), Stripe "
            "subscription billing with a 3-tier agents plan, landing page with ROI story and live agent demo "
            "chat, and an Agent Console dashboard: ticket queue, AI-handled vs escalated, resolution rate "
            "and savings metrics, usage/billing counters, conversation log with tool-call trail, integrations "
            "(Shopify/Woo/webhooks) with API keys, and team member roles. i18n (English, Spanish, French) with "
            "RTL, multi-currency (USD, EUR, GBP), privacy/terms, cookie consent, SEO + OG + JSON-LD + sitemap, "
            "modern clean SaaS theme. React 19 + Vite + Tailwind, Express + MySQL, structure identical to "
            "LumicorePro. Everything real, production-ready, no placeholders."
        ),
    },
    {
        "id": "agent-02",
        "slug": "leadscout-ai",
        "brand": "LeadScout AI",
        "market": "Real-estate lead qualification agent",
        "prompt": (
            "Build 'LeadScout AI' — a vertical AI agent SaaS that qualifies real-estate leads 24/7: pre-screens "
            "buyers on budget, timeline and location, scores them, books viewings, and routes hot leads to the "
            "right agent with a full profile. Audience: real-estate agents and brokerages (2M+ agents spend "
            "5-10 hrs/week qualifying leads). Product: full-stack SaaS with auth (register/login/2FA, JWT), "
            "Stripe subscription (brokerage seat pricing), landing page with the qualification workflow and "
            "'how a lead converts' narrative, and an Agent Console: lead inbox with AI scores and reasons, "
            "automated follow-up sequences, viewing calendar, MLS/CRM connector settings, usage metrics and "
            "billing. i18n (English, Arabic, Spanish) RTL, multi-currency (USD, EUR, AED), privacy/terms, "
            "cookie consent, SEO + OG + JSON-LD + sitemap, clean professional theme. React 19 + Vite + Tailwind, "
            "Express + MySQL, LumicorePro structure. Real and production-ready."
        ),
    },
    {
        "id": "agent-03",
        "slug": "clausecheck-ai",
        "brand": "ClauseCheck",
        "market": "Legal contract review agent",
        "prompt": (
            "Build 'ClauseCheck' — a vertical AI agent SaaS that reviews contracts and flags risky clauses, "
            "missing obligations, auto-renewals, liability caps and termination traps for SMBs (90% of small "
            "businesses need legal help, only 20% can afford it; Harvey serves big law, SMBs are underserved). "
            "Product: full-stack SaaS with auth (register/login/2FA, JWT), Stripe subscription with per-document "
            "packages ($50-200/review or $500-2000/mo unlimited), landing page showing the review pipeline "
            "(upload -> clause map -> risk flags -> redline summary), and an Agent Console: document upload "
            "with status, review results with severity-coded clause flags, exportable summary, lawyer handoff, "
            "compliance history and usage/billing. i18n (English, Spanish, French), multi-currency (USD, EUR, "
            "GBP), privacy/terms legal pages, cookie consent, SEO + OG + JSON-LD + sitemap, trustworthy "
            "institutional theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. Real."
        ),
    },
    {
        "id": "agent-04",
        "slug": "appointly-ai",
        "brand": "Appointly",
        "market": "Healthcare & salon appointment scheduling agent",
        "prompt": (
            "Build 'Appointly' — a vertical AI agent SaaS that owns the full booking lifecycle for service "
            "businesses: availability across providers, booking with conflict resolution, confirmation, "
            "no-show-risk reminders, rescheduling and waitlist backfill (no-shows cost healthcare $150B/yr and "
            "salons 20-30% of revenue). Audience: clinics, salons, consultancies. Product: full-stack SaaS with "
            "auth (register/login/2FA, JWT), Stripe subscription sessions + deposits, landing page with the "
            "booking lifecycle story and a scheduling demo, and an Agent Console: bookings calendar, provider "
            "roster, automated reminder rules, no-show analytics, intake forms, usage/billing and team roles. "
            "i18n (English, Spanish, Arabic) RTL, multi-currency (USD, EUR, AED), privacy/terms (health "
            "disclaimer), cookie consent, SEO + OG + JSON-LD, calm trust-worthy theme. React 19 + Vite + Tailwind, "
            "Express + MySQL, LumicorePro structure. Real and production-ready."
        ),
    },
    {
        "id": "agent-05",
        "slug": "recruitiq-ai",
        "brand": "RecruitIQ",
        "market": "Recruitment screening agent",
        "prompt": (
            "Build 'RecruitIQ' — a vertical AI agent SaaS for recruitment screening: parses and matches resumes "
            "to job specs, scores candidates, drafts personalized outreach and schedules interviews with "
            "hiring manager handoff. Audience: SMBs and staffing agencies hit by volume screening. Product: "
            "full-stack SaaS with auth (register/login/2FA, JWT), Stripe subscription (per-seat + candidate "
            "credits), landing page with the screen -> match -> schedule funnel, and an Agent Console: requisition "
            "board, candidate list with match scores and reasons, outreach drafts with approved-send workflow, "
            "interview calendar, pipeline analytics and usage/billing. i18n (English, Spanish, French), "
            "multi-currency (USD, EUR, GBP), privacy/terms, cookie consent, SEO + OG + JSON-LD + sitemap, "
            "modern HR-tech theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. Real."
        ),
    },
    {
        "id": "agent-06",
        "slug": "ledgerai",
        "brand": "LedgerAI",
        "market": "Bookkeeping & expense categorization agent",
        "prompt": (
            "Build 'LedgerAI' — a vertical AI agent SaaS for small-business bookkeeping: auto-categorizes "
            "expenses from receipts/bank feeds, reconciles records, flags anomalies and generates monthly "
            "reports accountants and owners can trust (72% of SMBs still run books on spreadsheets; data-entry "
            "errors cost businesses $3.1T/yr). Product: full-stack SaaS with auth (register/login/2FA, JWT), "
            "Stripe subscription tiers, landing page with the automated month-end close narrative and a live "
            "categorization demo, and an Agent Console: bank/receipt feed, categorized transactions with "
            "confidence and review queue, anomaly alerts, monthly close checklist, accountant access and "
            "read-only share, usage/billing. i18n (English, Spanish, German), multi-currency (USD, EUR, GBP, "
            "PKR), privacy/terms with accounting disclaimer, SEO + OG + JSON-LD + sitemap, trustworthy finance "
            "theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. Real."
        ),
    },
    {
        "id": "agent-07",
        "slug": "tablehost-ai",
        "brand": "TableHost AI",
        "market": "Restaurant host / reservation agent",
        "prompt": (
            "Build 'TableHost AI' — a vertical AI agent SaaS that answers calls and web inquiries, checks live "
            "table availability, books reservations, sends confirmations, manages waitlists and processes "
            "cancellations with automatic rebooking (restaurants pay $2-4k/mo for host labor). Audience: "
            "independent restaurants and groups. Product: full-stack SaaS with auth (register/login/2FA, JWT), "
            "Stripe subscription + reservation deposits, landing page with the 'host on autopilot' story and a "
            "live booking widget demo, and an Agent Console: live reservation board, waitlist management, "
            "SMS/email confirmation rules, peak-hour autopilot toggle, guest history and no-show stats, "
            "POS/OpenTable-style connector settings, usage/billing. i18n (English, Spanish, Arabic) RTL, "
            "multi-currency (USD, EUR, AED), privacy/terms, cookie consent, SEO + OG + JSON-LD + sitemap, "
            "warm hospitality theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. "
            "Real and production-ready."
        ),
    },
    {
        "id": "agent-08",
        "slug": "insightpipe-ai",
        "brand": "InsightPipe",
        "market": "Data pipeline / reporting agent",
        "prompt": (
            "Build 'InsightPipe' — a vertical AI agent SaaS that automates data pipeline work: ingests feeds "
            "from spreadsheets, legacy databases and SaaS tools, reconciles records across systems, runs "
            "scheduled reports and flags anomalies for human review (SMBs waste millions on disconnected data; "
            "spreadsheet-reliant businesses are the core market). Product: full-stack SaaS with auth "
            "(register/login/2FA, JWT), Stripe subscription (pipeline + report bundles), landing page with the "
            "extract -> reconcile -> report -> alert flow, and an Agent Console: connected data sources, pipeline "
            "run history with success/error states, scheduled report builder, reconciliation table with "
            "mismatch alerts, anomaly feed, usage/billing. i18n (English, Spanish, German), multi-currency "
            "(USD, EUR, GBP), privacy/terms, cookie consent, SEO + OG + JSON-LD + sitemap, technical modern "
            "theme. React 19 + Vite + Tailwind, Express + MySQL, LumicorePro structure. Real."
        ),
    },
    {
        "id": "agent-09",
        "slug": "claimflow-ai",
        "brand": "ClaimFlow",
        "market": "Insurance claims intake agent",
        "prompt": (
            "Build 'ClaimFlow' — a vertical AI agent SaaS for insurance claims intake: gathers documents, "
            "triage by policy coverage, validates completeness, drafts the claim summary and routes to an "
            "adjuster with GL codes and recommended next steps. Audience: P&C insurers and MGA/broker shops "
            "still running paper claims. Product: full-stack SaaS with auth (register/login/2FA, JWT), Stripe "
            "subscription (per-claim bundles), landing page with the intake -> validate -> route funnel and a "
            "claims demo, and an Agent Console: claims queue with triage status, document checklist, coverage "
            "match and fraud-flag hints, adjuster assignment, SLA timers, audit trail and usage/billing. i18n "
            "(English, Spanish, French), multi-currency (USD, EUR, GBP), privacy/terms with compliance "
            "disclaimer, cookie consent, SEO + OG + JSON-LD + sitemap, institutional trust theme. React 19 + "
            "Vite + Tailwind, Express + MySQL, LumicorePro structure. Real and production-ready."
        ),
    },
    {
        "id": "agent-10",
        "slug": "onboarder-ai",
        "brand": "Onboarder",
        "market": "B2B SaaS onboarding / churn-reduction agent",
        "prompt": (
            "Build 'Onboarder' — a vertical AI agent SaaS that runs personalized onboarding for B2B SaaS "
            "products: guides new users week-by-week, triggers product tours, answers product questions from "
            "docs, and alerts success teams to at-risk accounts to cut churn (personalized onboarding is the "
            "proven churn lever; agents plug into existing SaaS via API/snippet). Audience: SaaS founders and "
            "CS teams. Product: full-stack SaaS with auth (register/login/2FA, JWT), Stripe subscription "
            "(per active end-user), landing page with the 'first 30 days' onboarding story and a product-tour "
            "demo, and an Agent Console: accounts at risk, onboarding playbook editor with step triggers, "
            "in-app message preview, docs RAG source manager, CS alerts and team inbox, usage/billing. i18n "
            "(English, Spanish, French), multi-currency (USD, EUR, GBP), privacy/terms, cookie consent, SEO + "
            "OG + JSON-LD + sitemap, modern SaaS theme. React 19 + Vite + Tailwind, Express + MySQL, "
            "LumicorePro structure. Real."
        ),
    },
]

REQUIRED_FILES = [
    ("auth", ["login", "register"]),
    ("payment", ["stripe"]),
    ("agent_console", ["dashboard", "console", "agent"]),
    ("i18n", ["i18n"]),
    ("compliance", ["privacy", "terms"]),
    ("seo", ["sitemap", "og", "json-ld"]),
]


def verify_project(project_dir: Path) -> dict:
    report = {}
    files = [p.name.lower() for p in project_dir.rglob("*") if p.is_file()]

    def has_any(tokens):
        return any(any(t in n for t in tokens) for n in files)

    report["auth"] = has_any(["login", "register"])
    report["payment"] = any("stripe" in f for f in files) or has_any(["checkout"])
    report["agent_console"] = has_any(["dashboard", "console", "agent"])
    report["i18n"] = any("i18n" in f for f in files)
    report["compliance"] = has_any(["privacy"]) and has_any(["terms"])
    report["seo"] = has_any(["sitemap", "og", "json-ld", "seo"])
    report["package_json"] = (project_dir / "frontend" / "package.json").exists() or (project_dir / "package.json").exists()
    report["dist"] = (project_dir / "frontend" / "dist").exists() or (project_dir / "dist").exists()
    return report


def build_one(brief: dict, progress_log: Path):
    from agent.orchestrator import AgentOrchestrator

    def cb(phase, event, meta):
        with progress_log.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {brief['id']} | {phase} | {event}\n")
        log.info("%s | %s | %s", brief["id"], phase, event)

    orch = AgentOrchestrator()
    return orch.run(
        brief["prompt"],
        interactive=False,
        progress_callback=cb,
        extra_spec={
            "project_name": brief.get("slug", brief["id"]),
            "project_name_human": brief.get("brand", ""),
            "brand_name": brief.get("brand", ""),
            "company_name": brief.get("brand", ""),
            "agent_vertical": brief.get("market", ""),
        },
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="", help="comma-separated brief ids to build")
    args = ap.parse_args()

    out_root = ROOT / "generated-projects"
    out_root.mkdir(exist_ok=True)
    state_file = out_root / "ai-agents-results.json"
    log_file = out_root / "ai-agents-progress.log"

    briefs = BRIEFS
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
        briefs = [b for b in briefs if b["id"] in wanted]

    results = {}
    if state_file.exists():
        results = json.loads(state_file.read_text(encoding="utf-8"))

    log.info("AI-AGENTS START: %d brief(s)", len(briefs))
    for brief in briefs:
        if results.get(brief["id"], {}).get("status") == "complete":
            log.info("skip %s (already complete)", brief["id"])
            continue
        started = time.time()
        try:
            res = build_one(brief, log_file)
            name = res.get("project_name", brief["id"])
            pdir = out_root / name
            checks = verify_project(pdir)
            results[brief["id"]] = {
                "status": "complete",
                "project_name": name,
                "brand": brief["brand"],
                "market": brief["market"],
                "checks_passed": sum(1 for v in checks.values() if v),
                "checks_total": len(checks),
                "features": checks,
                "elapsed_s": round(time.time() - started),
                "score": res.get("score") or res.get("quality") or res.get("design_score"),
            }
            state_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("%s DONE in %ds | project=%s | checks %s/%s", brief["id"], results[brief["id"]]["elapsed_s"], name, results[brief["id"]]["checks_passed"], len(checks))
        except Exception as exc:  # noqa: BLE001 - keep the batch alive
            results[brief["id"]] = {"status": "error", "error": repr(exc), "elapsed_s": round(time.time() - started)}
            state_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log.error("%s FAILED: %s", brief["id"], exc)

    summary = {"total": len(results), "ok": sum(1 for r in results.values() if r.get("status") == "complete")}
    state_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("AI-AGENTS SUMMARY: %s", summary)
    print("AI-AGENTS RESULT:", json.dumps(summary))


if __name__ == "__main__":
    main()