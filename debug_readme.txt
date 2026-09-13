def _static_readme(self, spec: Dict[str, Any]) -> str:
        from .marketplace_readme import generate_marketplace_readme

        name = str(spec.get("project_name") or "Generated Project").replace("-", " ").title()
        wtype = str(spec.get("website_type") or "website").replace("_", " ").title()
        extra = (
            f"# {name}\n\n"
            f"Client-only static showcase (Mode 1) — `{wtype}` landing experience with "
            f"zero server hosting maintenance. The bundle is an API-less single-page "
            f"app ready for direct drop into **Vercel** or **Netlify**.\n\n"
            f"## What is included\n\n"
            f"- Frontend client layer only — all navigation, state and form interactions "
            f"run in the browser.\n"
            f"- Static API mock handlers: `frontend/src/services/mockApi.js`\n"
            f"- Cloud-edge contact forms via client actions: `frontend/src/services/staticForms.js` "
            f"(Formspree → Resend/generic webhook → dev mock).\n"
            f"- Edge deploy configs: `vercel.json`, `netlify.toml`, `frontend/public/_redirects`, "
            f"`frontend/public/_headers`.\n\n"
            f"## Quick start (local)\n\n"
            f"```bash\n"
            f"cd frontend\n"
            f"npm install\n"
            f"npm run dev        # http://localhost:5173\n"
            f"```\n\n"
            f"## Deploy to Vercel (copy-paste)\n\n"
            f"```bash\n"
            f"npm install -g vercel\n"
            f"vercel            # root of this bundle; rootDirectory: frontend is pre-set in vercel.json\n"
            f"vercel --prod\n"
            f"```\n\n"
            f"Or import the repo at https://vercel.com/new — Vercel auto-detects "
            f"`vercel.json` (Vite, rootDirectory `frontend`).\n\n"
            f"## Deploy to Netlify (copy-paste)\n\n"
            f"```bash\n"
            f"npm install -g netlify-cli\n"
            f"netlify deploy    # base \"frontend\", publish \"dist\" pre-set in netlify.toml\n"
            f"netlify deploy --prod\n"
            f"```\n\n"
            f"Or drag-and-drop the `frontend/dist` folder after `npm run build`.\n\n"
            f"## Contact forms — pick a provider\n\n"
            f"Create `.env` from `.env.example` and set one of:\n\n"
            f"1. **Formspree (zero server):** create a form at https://formspree.io and set\n"
            f"   `VITE_FORMSPREE_ENDPOINT=https://formspree.io/f/your-id`. Optional second form\n"
            f"   id for the newsletter: `VITE_FORMSPREE_NEWSLETTER_ID=your-newsletter-id`.\n"
            f"2. **Resend / webhook (client action):** set\n"
            f"   `VITE_CONTACT_WEBHOOK_URL=https://your-edge-function.example/resend` pointing\n"
            f"   at a Vercel/Netlify edge function (or Resend serverless hook).\n"
            f"3. **Mock (default):** with no vars set, forms resolve to a 450ms mock success "
            f"for demos.\n\n"
            f"Remember to re-run `npm run build` after changing env vars (Vite inlines them).\n\n"
            f"## Custom domain\n\n"
            f"- Vercel: Settings → Domains → add your domain + DNS A/CNAME records.\n"
            f"- Netlify: Domain settings → assign domain + update the registrar nameservers "
            f"to Netlify DNS (or add a CNAME to yoursite.netlify.app).\n\n"
        )
        return generate_marketplace_readme(spec, mode="static", extra_sections=extra)

    # ── Mode 2: Enterprise Full-Stack Hydration ─────────────────────────────
    def render_enterprise_layout(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        agent_logger.info(
            "Layout Mode 2 (enterprise): mounting master-express-backend scaffold + "
            "canonical hydration (14 Sequelize models / 18 route groups / Redis+BullMQ)..."
        )
        root = project_dir
        canonical = (PROJECT_ROOT / BACKEND_CANONICAL).resolve()

        # Re-seed backend/ with the ecommerce-base scaffold first.
        backend_dir = os.path.join(root, "backend")
        if os.path.isdir(backend_dir):
            shutil.rmtree(backend_dir, ignore_errors=True)
        FileManager.ensure_dir(backend_dir)
        ecommerce_base = (PROJECT_ROOT / "backend-library" / "ecommerce-base").resolve()
        if ecommerce_base.exists():
            agent_logger.info(f"Copying ecommerce-base scaffold from: {ecommerce_base}")
            FileManager.copy_directory(str(ecommerce_base), str(backend_dir), ignore_patterns=["node_modules", ".git"])

        # Overlay with canonical enterprise scaffold (no secrets).
        mounted = 0
        if canonical.exists():
            for sub in BACKEND_COPY_DIRS:
                src = canonical / sub
                if src.is_dir():
                    dst = os.path.join(backend_dir, sub)
                    FileManager.copy_directory(
                        str(src), dst,
                        ignore_patterns=list(BACKEND_EXCLUDE_DIRS),
                    )
                   