from typing import Dict, Any, List
from utils.logger import agent_logger
from config.master_prompt import get_master_prompt, MASTER_20_DESIGN_STYLES

class GenerationPlanner:
    """Creates a step-by-step project assembly and generation plan with interactive style configuration."""

    ANIMATION_STYLES = [
        {"id": "smooth_fade", "name": "Smooth Fade In", "description": "Subtle, premium fade-entrance animations (Apple-like)"},
        {"id": "bounce_elastic", "name": "Bounce & Elastic", "description": "Playful, animated bounce effects (startup vibe)"},
        {"id": "neon_pulse", "name": "Neon Glow Pulse", "description": "Cyberpunk neon pulsing on hover & click (tech vibe)"},
        {"id": "slide_reveal", "name": "Slide & Reveal", "description": "Sections slide in from edges (modern corporate)"},
        {"id": "particle_float", "name": "Particle Float", "description": "Particles & floating elements in background (creative)"},
        {"id": "minimal_none", "name": "Minimal / No Animation", "description": "Clean, fast, no flashy animations (professional)"},
    ]

    COLOR_SCHEMES = [
        {"id": "midnight_cyan", "name": "Midnight Cyan", "colors": {
            "primary": "#06b6d4", "secondary": "#3b82f6", "bg": "#0a0e1a", "card": "#111827", "text": "#f1f5f9"}},
        {"id": "purple_dream", "name": "Purple Dream", "colors": {
            "primary": "#a855f7", "secondary": "#ec4899", "bg": "#0f0a1a", "card": "#1a1128", "text": "#f5f3ff"}},
        {"id": "emerald_dark", "name": "Emerald Dark", "colors": {
            "primary": "#10b981", "secondary": "#06b6d4", "bg": "#0a1a14", "card": "#132e22", "text": "#ecfdf5"}},
        {"id": "warm_orange", "name": "Warm Orange", "colors": {
            "primary": "#f97316", "secondary": "#ef4444", "bg": "#1a0f0a", "card": "#2a1a10", "text": "#fef3c7"}},
        {"id": "arctic_blue", "name": "Arctic Blue", "colors": {
            "primary": "#38bdf8", "secondary": "#818cf8", "bg": "#0c1929", "card": "#152032", "text": "#e0f2fe"}},
        {"id": "rose_golden", "name": "Rose Gold", "colors": {
            "primary": "#f472b6", "secondary": "#fbbf24", "bg": "#1a0f15", "card": "#2a1520", "text": "#fdf2f8"}},
    ]

    PAGE_LAYOUTS = [
        {"id": "single_page", "name": "Single Page", "description": "All content on one scrollable page"},
        {"id": "multi_page", "name": "Multi Page", "description": "Separate pages: Home, About, Products, Contact"},
        {"id": "dashboard_layout", "name": "Dashboard", "description": "Sidebar + content area dashboard layout"},
    ]

    def create_plan(
        self,
        spec: Dict[str, Any],
        selected_template: Dict[str, Any],
        selected_components: List[Dict[str, Any]],
        selected_assets: Dict[str, List[Dict[str, Any]]],
        selected_backend: Dict[str, Any],
        selected_schemas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Construct structured generation plan with style configuration."""
        agent_logger.info("Constructing assembly & generation plan aligned with Master Prompt...")

        project_name = spec.get("project_name", "generated-website")

        plan = {
            "project_name": project_name,
            "destination": f"generated-projects/{project_name}",
            "master_prompt": get_master_prompt(),
            "zero_budget_mode": True,
            "template": selected_template,
            "components": selected_components,
            "assets": selected_assets,
            "backend": selected_backend,
            "database_schemas": selected_schemas,
            "style_preference": spec.get("style_preference", {}),
            "assembly_steps": [
                f"1. Scaffold modular directory at generated-projects/{project_name} (frontend, backend, docs)",
                f"2. Copy base template from {selected_template.get('file_path') if selected_template else 'Vite React Base'}",
                f"3. Inject {len(selected_components)} matched reusable React components and 3D hero if applicable",
                f"4. Copy selected images, icons, and animation stylesheets",
                f"5. Configure Node.js/Express backend ({selected_backend.get('name') if selected_backend else 'Default Express Base'}) with Prisma/SQLite zero-budget setup",
                "6. Implement mock_response() and demo mode for AI and Payment handlers (Zero-Budget requirement)",
                f"7. Consolidate database schemas ({', '.join([s.get('name') for s in selected_schemas])})",
                "8. Generate complete docs/ suite (PRD, ARCHITECTURE, RULES, DESIGN, TASKS, MEMORY, SETUP, DEPLOYMENT, COMPLIANCE)",
                "9. Generate free hosting configs (Cloudflare Pages, Netlify, Render, Fly.io) and GitHub Actions",
                "10. Generate .vscode/extensions.json (25 extensions), CONTRIBUTING.md, and .env.example with client activation comments",
                "11. Run quality gates (dependencies, imports, env vars, WCAG a11y) and self-healing",
                "12. Finalize Lemon Squeezy ready README.md"
            ],
            "ai_tasks_required": []
        }

        # Agent Reach social signal payload (Phase 1b) → assembly plan
        live = spec.get("live_signal_summary") or {}
        if live:
            plan["market_signals"] = {
                "sources": live.get("sources", []),
                "complaints": live.get("complaints", []),
                "preferred_features": live.get("preferred_features", []),
                "design_topics": live.get("design_topics", []),
            }
            source_label = "community" if live.get("sources") else "market"
            for complaint in (live.get("complaints") or [])[:2]:
                plan["ai_tasks_required"].append(
                    f"Address live {source_label} signal in generated copy/UX: {complaint}"
                )

        # Check missing features to queue for AI generation
        req_features = set(spec.get("features", []))
        provided_features = set(selected_template.get("features", [])) if selected_template else set()
        for comp in selected_components:
            for f in comp.get("features", []):
                provided_features.add(f)

        missing = req_features - provided_features
        if missing:
            for m in missing:
                plan["ai_tasks_required"].append(f"Synthesize custom logic/component for missing feature: {m}")

        agent_logger.info(f"Plan created with {len(plan['assembly_steps'])} steps and {len(plan['ai_tasks_required'])} AI tasks.")
        return plan

    def ask_style_preferences(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive: Ask user about animation, color, and layout preferences."""
        print("\n" + "=" * 70)
        print("  STYLE & DESIGN CONFIGURATION")
        print("=" * 70)
        print(f"\nProject: {spec.get('project_name', 'N/A')}")
        print(f"Type: {spec.get('website_type', 'N/A')}")
        print(f"Industry: {spec.get('industry', 'N/A')}\n")

        # Ask Animation Style
        print(">>> ANIMATION STYLE")
        for i, anim in enumerate(self.ANIMATION_STYLES, 1):
            print(f"  [{i}] {anim['name']} - {anim['description']}")
        
        anim_choice = input("\nSelect animation style (1-6, default=1): ").strip()
        if anim_choice.isdigit() and 1 <= int(anim_choice) <= len(self.ANIMATION_STYLES):
            selected_anim = self.ANIMATION_STYLES[int(anim_choice) - 1]
        else:
            selected_anim = self.ANIMATION_STYLES[0]
        print(f"  Selected: {selected_anim['name']}")

        # Ask Color Scheme
        print("\n>>> COLOR SCHEME")
        for i, cs in enumerate(self.COLOR_SCHEMES, 1):
            colors_str = ", ".join([f"{k}: {v}" for k, v in cs['colors'].items()])
            print(f"  [{i}] {cs['name']} - {colors_str}")
        
        color_choice = input("\nSelect color scheme (1-6, default=1): ").strip()
        if color_choice.isdigit() and 1 <= int(color_choice) <= len(self.COLOR_SCHEMES):
            selected_color = self.COLOR_SCHEMES[int(color_choice) - 1]
        else:
            selected_color = self.COLOR_SCHEMES[0]
        print(f"  Selected: {selected_color['name']}")

        # Ask Page Layout
        print("\n>>> PAGE LAYOUT")
        for i, layout in enumerate(self.PAGE_LAYOUTS, 1):
            print(f"  [{i}] {layout['name']} - {layout['description']}")
        
        layout_choice = input("\nSelect page layout (1-3, default=1): ").strip()
        if layout_choice.isdigit() and 1 <= int(layout_choice) <= len(self.PAGE_LAYOUTS):
            selected_layout = self.PAGE_LAYOUTS[int(layout_choice) - 1]
        else:
            selected_layout = self.PAGE_LAYOUTS[0]
        print(f"  Selected: {selected_layout['name']}")

        # Ask Number of categories/pages
        print("\n>>> EXTRA OPTIONS")
        cats = input("Number of product categories (default=10): ").strip()
        product_categories_count = int(cats) if cats.isdigit() else 10

        # Ask for extra pages
        extra_pages = input("Extra pages? (e.g. 'Blog, FAQ, Team' or press Enter to skip): ").strip()
        extra_pages_list = [p.strip() for p in extra_pages.split(",")] if extra_pages else []

        style_preference = {
            "animation": selected_anim,
            "color_scheme": selected_color,
            "layout": selected_layout,
            "product_categories_count": product_categories_count,
            "extra_pages": extra_pages_list
        }
        return style_preference

    def display_plan_summary(self, spec: Dict[str, Any], tech_stack: Dict[str, Any],
                             selected_template: Dict[str, Any], selected_components: List[Dict[str, Any]],
                             selected_assets: Dict[str, Any], selected_backend: Dict[str, Any],
                             selected_schemas: List[Dict[str, Any]],
                             feature_list: List[str], trending_features: List[str]) -> bool:
        """Display the complete plan summary and ask for user approval."""
        print("\n" + "=" * 70)
        print("  PROJECT GENERATION PLAN")
        print("=" * 70)

        style = spec.get("style_preference", {})
        
        print(f"\n📋 Project Name: {spec.get('project_name', 'N/A')}")
        print(f"🌐 Website Type: {spec.get('website_type', 'N/A')}")
        print(f"🏭 Industry: {spec.get('industry', 'N/A')}")
        
        if style:
            anim = style.get("animation", {})
            color = style.get("color_scheme", {})
            layout = style.get("layout", {})
            print(f"🎨 Animation Style: {anim.get('name', 'Smooth Fade In')}")
            print(f"🎨 Color Scheme: {color.get('name', 'Midnight Cyan')}")
            print(f"� Page Layout: {layout.get('name', 'Single Page')}")
            cats = style.get("product_categories_count", 10)
            extras = style.get("extra_pages", [])
            print(f"📦 Product Categories: {cats}")
            if extras:
                print(f"📄 Extra Pages: {', '.join(extras)}")

        print(f"\n🖥️  Template: {selected_template.get('name', 'Default Base') if selected_template else 'Default Base'}")
        print(f"🧩 Components: {len(selected_components)} selected")
        for c in selected_components[:8]:
            print(f"    - {c.get('name', 'N/A')}")
        if len(selected_components) > 8:
            print(f"    ... and {len(selected_components) - 8} more")

        images = len(selected_assets.get("images", []))
        icons = len(selected_assets.get("icons", []))
        animations = len(selected_assets.get("animations", []))
        print(f"�️  Assets: {images} images, {icons} icons, {animations} animations")

        print(f"\n⚙️  Backend: {selected_backend.get('name', 'Express.js') if selected_backend else 'Express.js'}")
        print(f"🗄️  Database: {len(selected_schemas)} schema(s)")
        if tech_stack:
            print(f"🔧 Tech Stack: {tech_stack.get('frontend', 'React')} + {tech_stack.get('backend', 'Express')} + {tech_stack.get('database', 'PostgreSQL')}")

        if feature_list:
            print(f"\n🎯 Features ({len(feature_list)}):")
            print("  " + ", ".join(feature_list[:15]))
            if len(feature_list) > 15:
                print(f"  ... and {len(feature_list) - 15} more")

        if trending_features:
            print(f"\n🔥 Trending Features: {', '.join(trending_features)}")

        print("\n" + "=" * 70)
        choice = input("  ✅ Approve & Build? (y/n, type 'edit' to modify style): ").strip().lower()
        
        if choice in ('y', 'yes'):
            return True
        elif choice == 'edit':
            return 'edit'  # Signal to re-ask style preferences
        else:
            print("\n❌ Project generation cancelled.")
            return False
