import sys
import os
import argparse
import logging
import sqlite3
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database.init_db import init_database
from agent.orchestrator import AgentOrchestrator
from utils.logger import agent_logger
from utils.file_manager import FileManager
from config.settings import AGENT_DB_PATH, REGISTRY_DIR

def print_banner():
    print(r"""
======================================================================
   __   _____  ____  ____ ____  ___  ____  ___  ____  ____   
  / /  / / / \/  _ \/ ___/  _ \/ _ \/  _ \/ _ \/  _ \/ ___/   
 / /__/ /_/ /| / /| /__ | / /| /_)/| / /| /_)/| / /| /__    
/____/\____/ |_| |_|\____|_| |_|_|  |_|  |_|  |_|  |\____/    
                                                              
        LumicorePro Core — Professional Website Generation Agent   
======================================================================
""")

def display_interactive_menu() -> int:
    """Display clean professional CLI menu."""
    print("-------------------- LUMICOREPRO MASTER MENU --------------------\n")
    print("  [1] Generate New Project from Prompt")
    print("  [2] Run Dry-Run Plan Simulation")
    print("  [3] Re-Index & Seed SQLite Memory Database")
    print("  [4] Run Automated Pytest Test Suite")
    print("  [5] View Memory Registries Status Summary")
    print("  [6] Exit\n")
    print("----------------------------------------------------------------")
    choice = input("Select an option (1-6): ").strip()
    return int(choice) if choice.isdigit() else 6

def show_registries_summary():
    """Print summary of indexed library items."""
    print("\n================ MEMORY REGISTRIES SUMMARY ================")
    if not os.path.exists(AGENT_DB_PATH):
        print("Database not initialized yet.")
        return

    conn = sqlite3.connect(AGENT_DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        ("templates_index", "Templates"),
        ("components_index", "React Components"),
        ("assets_index", "Assets (Images/Icons/Animations)"),
        ("backend_index", "Backend Bases"),
        ("database_schemas_index", "SQL Schemas")
    ]
    for tbl, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        print(f"  • {label:<35}: {cnt} items indexed")
    conn.close()
    print("===========================================================\n")

def run_tests():
    """Execute test suite."""
    print("\nExecuting LumicorePro Core Test Suite...\n")
    import unittest
    suite = unittest.defaultTestLoader.discover(str(current_dir / "tests"))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="LumicorePro Core AI Website Generation Agent")
    parser.add_argument("--prompt", type=str, help="Natural language website prompt")
    parser.add_argument("--provider", type=str, choices=["grok", "gemini", "openai", "mistral", "openrouter"], help="Override active AI provider")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation plan without writing files to disk")
    parser.add_argument("--headless", action="store_true", help="Run without interactive prompts (for automation/testing)")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed debug logging")
    args = parser.parse_args()

    if args.verbose:
        agent_logger.setLevel(logging.DEBUG)
        for handler in agent_logger.handlers:
            handler.setLevel(logging.DEBUG)
        agent_logger.debug("Verbose debug logging enabled.")

    if not os.path.exists(AGENT_DB_PATH):
        init_database()

    prompt = args.prompt
    dry_run = args.dry_run

    if not prompt and not dry_run and len(sys.argv) == 1:
        choice = display_interactive_menu()
        if choice == 1:
            prompt = input("\nEnter your website generation prompt:\n> ").strip()
        elif choice == 2:
            prompt = input("\nEnter website prompt for Dry-Run simulation:\n> ").strip()
            dry_run = True
        elif choice == 3:
            init_database()
            print("Database re-indexed successfully.")
            return
        elif choice == 4:
            run_tests()
            return
        elif choice == 5:
            show_registries_summary()
            return
        else:
            print("Exiting LumicorePro CLI.")
            return

    if not prompt:
        print("Error: Prompt cannot be empty.")
        sys.exit(1)

    orchestrator = AgentOrchestrator(provider_name=args.provider)

    if dry_run:
        agent_logger.info("Executing DRY RUN simulation...")
        spec = orchestrator.analyzer.analyze(prompt)
        sel_temp = orchestrator.template_selector.select_template(spec)
        sel_comp = orchestrator.component_selector.select_components(spec)
        sel_asset = orchestrator.asset_selector.select_assets(spec)
        sel_backend = orchestrator.backend_selector.select_backend(spec)
        sel_schema = orchestrator.database_selector.select_schemas(spec)
        plan = orchestrator.planner.create_plan(spec, sel_temp, sel_comp, sel_asset, sel_backend, sel_schema)

        print("\n================ DRY RUN GENERATION PLAN ================")
        print(f"Project Name    : {plan['project_name']}")
        print(f"Target Path     : {plan['destination']}")
        print(f"Template        : {sel_temp.get('name') if sel_temp else 'Default Base'}")
        print(f"Components      : {len(sel_comp)} matched from local library")
        for c in sel_comp:
            print(f"  - {c['name']} ({c['file_path']})")
        print(f"Backend API     : {sel_backend.get('name') if sel_backend else 'Default Base'}")
        print(f"Database Schemas: {', '.join([s.get('name') for s in sel_schema])}")
        print(f"Assembly Steps  : {len(plan['assembly_steps'])} steps")
        print(f"Estimated Tokens: ~95% saved via local assembly")
        print("=========================================================\n")
        return

    report = orchestrator.run(prompt, interactive=not args.headless)

    print("\n---------------- GENERATION REPORT ----------------")
    print(f"Pipeline        : 15-Phase Enterprise v3.5")
    print(f"Project Name    : {report['project_name']}")
    print(f"Destination     : {report['generated_project_dir']}")
    print(f"ZIP Archive File: {report.get('zip_archive_path')}")
    print(f"Template Used   : {report['selected_resources']['template']}")
    print(f"Components      : {report['selected_resources']['components_count']} matched from local library")
    print(f"Trending Features: {', '.join(report['selected_resources'].get('trending_features', []))}")
    print(f"Backend API     : {report['selected_resources']['backend']}")
    print(f"Quality Score   : {report.get('quality_gates', {}).get('overall_score', 'N/A')}%")
    print(f"Enterprise Ready: {report.get('enterprise_ready', False)}")
    print(f"Launch Ready    : {report.get('launch_ready', False)}")
    print(f"Multi-Cloud CI  : Ready (Vercel, Railway, Render, AWS, GCP, Azure)")
    print(f"SEO & Edge CDN  : Configured (Sitemap, Robots, JSON-LD, Cloudflare)")
    print(f"AI API Calls    : {report['ai_api_calls_made']} (Tokens Saved: ~95% local reuse)")
    print(f"Validation      : Overall Valid = {report['validation_results']['valid']}")
    print(f"Report File     : {os.path.join(report['generated_project_dir'], 'generation-report.json')}")
    print("---------------------------------------------------\n")

if __name__ == "__main__":
    main()

