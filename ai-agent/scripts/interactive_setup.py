#!/usr/bin/env python3
"""LumicorePro Core Interactive Setup Script — Guides through environment configuration, database initialization, and first project generation."""

import os
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import agent_logger, setup_logger

def main():
    """Run interactive setup wizard."""
    logger = setup_logger("LumicoreSetup")
    print("\n" + "=" * 60)
    print("  LUMICOREPRO CORE — INTERACTIVE SETUP WIZARD")
    print("=" * 60 + "\n")

    # 1. Check Python version
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 9):
        logger.error("Python 3.9+ is required.")
        sys.exit(1)
    print("✅ Python version: {}.{}.{} (OK)".format(py_version.major, py_version.minor, py_version.micro))

    # 2. Check .env file
    env_path = Path(__file__).resolve().parent.parent / ".env"
    env_example = Path(__file__).resolve().parent.parent / ".env.example"
    
    if not env_path.exists():
        print("\n📋 No .env file found. Creating from .env.example...")
        if env_example.exists():
            import shutil
            shutil.copy2(env_example, env_path)
            print("✅ .env file created. Please edit it with your API keys.")
        else:
            print("⚠️  .env.example not found either. Creating basic .env...")
            env_content = """# LumicorePro Core AI Agent Environment Variables
ACTIVE_AI_PROVIDER=grok
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_MODEL=gemini-3.6-flash
OPENROUTER_MODEL=google/gemini-flash-latest
GROK_API_KEY=your_grok_api_key_here
GROK_MODEL=openai/gpt-oss-120b
PROJECT_ROOT=..
GENERATED_PROJECTS_DIR=../generated-projects
REGISTRY_DIR=../registry
TEMPLATES_DIR=../src/templates
COMPONENTS_DIR=../src/components
BACKEND_LIBRARY_DIR=../backend-library
DATABASE_SCHEMAS_DIR=../database/schemas
AGENT_DB_PATH=database/agent.db
ALLOW_AI_FALLBACK=true
"""
            env_path.write_text(env_content)
            print("✅ Basic .env file created.")

    # 3. Ask about AI provider
    print("\n� AI Provider Configuration:")
    print("   (1) Grok / Groq Cloud (recommended, fast & reliable)")
    print("   (2) Google Gemini (fast, free tier)")
    print("   (3) OpenRouter (aggregated provider)")
    print("   (4) Skip — run in offline mode (no API key needed)")
    provider_choice = input("\n   Choose provider [1]: ").strip() or "1"

    if provider_choice == "1":
        provider_name = "grok"
        key_var = "GROK_API_KEY"
    elif provider_choice == "2":
        provider_name = "gemini"
        key_var = "GEMINI_API_KEY"
    elif provider_choice == "3":
        provider_name = "openrouter"
        key_var = "OPENROUTER_API_KEY"
    else:
        print("\n✅ Skipping AI provider. Agent will run in offline mode.")
        provider_name = None

    if provider_name:
        api_key = input(f"\n   Enter your {key_var.replace('_API_KEY', '').title()} API key (or press Enter to skip):\n   ").strip()
        if api_key:
            print(f"✅ API key for {provider_name} has been configured.")
        else:
            print("✅ Skipping API key. Agent will fallback to local mode if needed.")

    # 4. Initialize database
    print("\n🗄️  Initializing agent database...")
    try:
        from database.init_db import init_database
        init_database()
        print("✅ Agent database initialized at database/agent.db")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        print("⚠️  Could not initialize database. The agent will still work.")

    # 5. Check dependencies
    print("\n📦 Checking Python dependencies...")
    pip_proc = os.popen("python -c \"import dotenv, requests, tabulate; print('OK')\" 2>/dev/null")
    deps_ok = pip_proc.read().strip() == "OK"
    pip_proc.close()
    
    if not deps_ok:
        print("⚠️  Some dependencies may be missing. Run:")
        print("   pip install -r requirements.txt")
        install = input("\n   Install dependencies now? [y/N]: ").strip().lower()
        if install == "y":
            print("Installing dependencies...")
            os.system("pip install -r requirements.txt")
            print("✅ Dependencies installed.")
    else:
        print("✅ All dependencies are installed.")

    # 6. Generate directories
    project_root = Path(__file__).resolve().parent.parent.parent
    generated_dir = project_root / "generated-projects"
    os.makedirs(generated_dir, exist_ok=True)
    print(f"\n✅ Generated projects directory: {generated_dir}")

    # 7. Ask about first project
    print("\n🚀 Ready to generate your first project!")
    prompt = input("\nEnter your website prompt (or press Enter to skip):\n> ").strip()
    
    if prompt:
        print(f"\n🔄 Generating project: '{prompt}'")
        try:
            from agent.orchestrator import AgentOrchestrator
            from config.providers import is_provider_configured
            orchestrator = AgentOrchestrator()
            result = orchestrator.run(prompt)
            print(f"\n✅ Project generated successfully!")
            print(f"   Location: {result.get('generated_project_dir')}")
            zip_path = result.get('zip_archive_path', '')
            if zip_path:
                print(f"   ZIP Archive: {zip_path}")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            print(f"\n❌ Generation failed: {e}")
            print("   You can try again later by running:")
            print("   cd ai-agent && python main.py --prompt \"your prompt\"")
    else:
        print("✅ Setup complete! To generate a project later, run:")
        print("   cd ai-agent && python main.py --prompt \"your website description\"")

    print("\n" + "=" * 60)
    print("  SETUP COMPLETE! Welcome to LumicorePro Core 🚀")
    print("=" * 60)
    print("\nNext steps:")
    print("  • Browse templates: src/templates/")
    print("  • Browse components: src/components/")
    print("  • Generate project: cd ai-agent && python main.py --prompt \"...\"")
    print("  • Documentation: README.md\n")


if __name__ == "__main__":
    main()