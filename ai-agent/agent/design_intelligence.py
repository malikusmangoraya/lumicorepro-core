"""
Bespoke Design Intelligence Engine — Phase 5.5
===============================================
Turns the agent from a template-remixer into a custom UI designer:

  1. Structure map builder — walks generated project files and produces a
     compact AST-ish structural map (imports, props, JSX tags, tailwind class
     blocks) that is injected as smart context into the reasoning model.
  2. Reasoning-tier generation — uses the top-reasoning provider (gpt-oss-120b
     via Groq, or Claude) with that structural map so it can write bespoke
     from-scratch components instead of remixing boilerplate.
  3. Atomic tweaks — applies dynamic Tailwind-utility adjustments against the
     local component registry so generated code stays contract-compatible.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import agent_logger
from utils.file_manager import FileManager
from config.settings import (
    AI_MAX_CONTEXT_FILES,
    AI_STRUCTURE_CONTEXT_CHARS,
    GENERATED_PROJECTS_DIR,
)


class StructureMapBuilder:
    """Lightweight structural map (AST-ish) of a generated frontend project."""

    _IMPORT_RE = re.compile(r"^\s*import\s+([^;]+);?", re.M)
    _EXPORT_RE = re.compile(r"^(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z][A-Za-z0-9_]*)\s*[=(]")
    _JSX_TAG_RE = re.compile(r"<([A-Z][A-Za-z0-9_]*)(?=[\s/>])")
    _CLASS_RE = re.compile(r'\b(?:className|class)=["\']([^"\']+)["\']')
    _PROPS_RE = re.compile(r"function\s+([A-Z][A-Za-z0-9_]*)\s*\(([^)]*)\)")

    def __init__(self, project_dir: str, max_files: int = None):
        self.project_dir = os.path.abspath(project_dir)
        self.max_files = max_files or AI_MAX_CONTEXT_FILES

    def discover_files(self) -> List[str]:
        src_dir = os.path.join(self.project_dir, "frontend", "src")
        files: List[str] = []
        if not os.path.isdir(src_dir):
            return files
        for root, _, filenames in os.walk(src_dir):
            for fname in filenames:
                if fname.endswith((".jsx", ".tsx", ".js", ".ts")):
                    files.append(os.path.join(root, fname))
        files.sort()
        return files[: self.max_files]

    def _map_file(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            return {}
        rel = os.path.relpath(path, self.project_dir).replace(os.sep, "/")
        imports = [
            m.strip().replace("\n", " ") for m in self._IMPORT_RE.findall(content)
        ]
        tags = sorted(set(self._JSX_TAG_RE.findall(content)))
        classes = [
            m for m in self._CLASS_RE.findall(content)
        ]
        props: Dict[str, List[str]] = {}
        for name, sig in self._PROPS_RE.findall(content):
            parts = [p.strip() for p in sig.split(",") if p.strip()]
            props[name] = parts[:8]
        return {
            "file": rel,
            "lines": content.count("\n") + 1,
            "imports": imports[:12],
            "jsx_tags": tags[:20],
            "tailwind_blocks": len(classes),
            "props": props,
        }

    def build(self) -> Dict[str, Any]:
        files = self.discover_files()
        mapped = [self._map_file(f) for f in files]
        mapped = [m for m in mapped if m.get("file")]
        return {
            "project": os.path.basename(self.project_dir),
            "scanned_files": len(mapped),
            "files": mapped,
        }

    def to_context(self, max_chars: int = None) -> str:
        """Render the structure map as compact injectable context."""
        limit = max_chars or AI_STRUCTURE_CONTEXT_CHARS
        lines = ["PROJECT STRUCTURE MAP (AST summary — use to write compatible code):"]
        for m in self.build().get("files", []):
            entry = [
                f"# {m['file']} ({m['lines']} lines)",
                f"  imports: {', '.join(m['imports'][:8])}",
            ]
            if m.get("props"):
                comps = "; ".join(f"{k}({', '.join(v)})" for k, v in list(m["props"].items())[:6])
                entry.append(f"  components: {comps}")
            if m.get("jsx_tags"):
                entry.append(f"  jsx: {', '.join(m['jsx_tags'][:14])}")
            lines.append("\n".join(entry))
        out = "\n".join(lines)
        return out[:limit]


class AtomicDesignEngine:
    """Applies dynamic Tailwind-utility tweaks against the local registry."""

    # Allows generated code to use the local UI tokens instead of raw hex.
    TOKEN_MAP = {
        "bg-primary": "bg-primary",
        "bg-primary/10": "bg-primary/10",
        "text-primary": "text-primary",
        "bg-card": "bg-card",
        "bg-muted": "bg-muted",
        "text-muted-foreground": "text-muted-foreground",
        "border-border": "border-border",
    }

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)

    def _registry_contract(self) -> str:
        try:
            from agent.component_registry import component_contract_snippet
            return component_contract_snippet()
        except Exception:
            return ""

    def build_bespoke_prompt(
        self, spec: Dict[str, Any], structure_context: str, task: str,
        block_name: str = "HeroSection",
    ) -> str:
        contract = self._registry_contract()
        style = spec.get("design_style") or "animaster"
        palette = spec.get("design_tokens", {}).get("palette", {})
        website_type = spec.get("website_type", "business")
        project_name = spec.get("project_name", "LumicorePlatform")
        return f"""
You are a world-class principal UI/UX designer and fullstack React 19 engineer.
Generate a high-converting, production-ready React component ({block_name}.jsx) for '{project_name}' ({website_type} site) in the '{style}' design style.

TASK: {task}

DESIGN SYSTEM TOKENS:
{json.dumps(palette, indent=2) if palette else 'Use semantic Tailwind classes (bg-primary, bg-card, border-border, text-foreground, text-muted-foreground).'}

LOCAL COMPONENT CONTRACT:
{contract or "Use functional components, prop defaults, className passthrough, dark mode support."}

STRUCTURE CONTEXT:
{structure_context[:6000]}

MANDATORY PRODUCTION & DESIGN STANDARDS:
1. ICONS: Use real icons from 'lucide-react' (e.g., Sparkles, ArrowRight, Shield, Zap, Check, Globe). Always pair icons with descriptive visible labels or aria-label for a11y.
2. IMAGES: Use real contextual high-resolution imagery (Unsplash or local asset paths), with LazyImage/img tags with proper alt text, object-cover, and rounded container styling.
3. MOTION & AESTHETICS (Animaster / Skipper UI / Vengeance UI):
   - Hero / Features: Use Bento Grid layouts, Spotlight hover radial glows, animated border beams, or 3D tilt perspective.
   - Micro-interactions: Smooth hover lifts (hover:-translate-y-1), active scale downs, transition-all duration-200.
   - Typography: Fluid bold font-display headings with dual-tone gradient accents (bg-gradient-to-r ... bg-clip-text text-transparent).
4. BRANDING & FOOTER:
   - Always use vector SVG logos (UniqueLogo or custom SVG geometric mark) instead of plain text.
   - If generating footer, create a 4-5 column professional footer with newsletter, status badge, categorized sitemap, and social icons. Never a single plain line!
5. SECURITY & RELIABILITY:
   - Parameterize and sanitize all inputs. No dangerouslySetInnerHTML without sanitization.
   - Zero hardcoded secrets or API keys.
6. REACT 19 + VITE:
   - Clean standard JSX hooks (useState, useEffect, useMemo, useCallback).
   - Export default function {block_name}(props) {{ ... }}.
   - Output ONLY the clean JSX component code without markdown backticks or commentary.
""".strip()

    def reuse_or_create(
        self,
        block_name: str,
        content: str,
        target_dir: str,
    ) -> str:
        """Write or overwrite a component file atomically."""
        safe_name = re.sub(r"[^A-Za-z0-9_]", "", block_name) or "BespokeBlock"
        path = os.path.join(target_dir, f"{safe_name}.jsx")
        path = FileManager.resolve_safe_path(path, self.project_dir)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        FileManager.write_file(path, content, self.project_dir)
        return os.path.relpath(path, self.project_dir).replace(os.sep, "/")


class BespokeUIDesignEngine:
    """Phase 5.5 driver — restructure selected sections with the reasoning model."""

    DEFAULT_BLOCKS = ["HeroSection", "FeaturesSection", "ProductGrid", "CTASection"]

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
        # Per-domain block set — bolted on the atomic mapper
        self.atomic = None

    def _reasoning_provider(self, provider_name: str = None):
        if provider_name:
            try:
                from config.providers import instantiate_provider
                inst = instantiate_provider(provider_name)
                if inst:
                    return inst
            except Exception:
                pass
        if self.ai_provider:
            return self.ai_provider
        try:
            from config.providers import get_reasoning_provider
            return get_reasoning_provider()
        except Exception:
            return None

    def run(
        self, project_dir: str, spec: Dict[str, Any],
        blocks: Optional[List[str]] = None,
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Regenerate selected section blocks with bespoke (from-scratch) UI code."""
        project_dir = os.path.abspath(project_dir)
        builder = StructureMapBuilder(project_dir)
        struct_ctx = builder.to_context()
        registry = ComponentRegistryAdapter(project_dir)
        targets = blocks or self.DEFAULT_BLOCKS
        src_pages = os.path.join(project_dir, "frontend", "src", "pages")
        target_dir = os.path.join(project_dir, "frontend", "src", "components", "atoms")
        os.makedirs(target_dir, exist_ok=True)

        provider = self._reasoning_provider(provider_name)
        if provider is None:
            agent_logger.warning("BespokeUIDesignEngine: no reasoning provider — skipping AI pass.")
            return {"active": False, "reason": "no_reasoning_provider"}

        # Bespoke section code is the highest-value generation step in the build
        # (Phase 5.5), so it routes to a reasoning-tier model. An explicit
        # provider_name / REASONING_PROVIDER still wins.
        from agent.ai_routing import prefer

        provider, provider_name_used, tier = prefer("design", struct_ctx) or (provider, "explicit", "pinned")
        agent_logger.info(
            f"[ROUTER] bespoke design -> tier={tier} provider={provider_name_used} blocks={len(targets)}"
        )

        # Section generation is independent per block, so the *model calls* run
        # concurrently while the file writes stay sequential and ordered. This is
        # the real wall-clock win: N blocks cost ~1 model call, not N.
        atomic = AtomicDesignEngine(project_dir)
        wanted = [b for b in targets if not registry.has(b)]
        jobs = [("design", "generate_code", (self._prompt_for(atomic, spec, struct_ctx, block),)) for block in wanted]

        from agent.ai_routing import get_router

        outputs = get_router().map_parallel(jobs) if jobs else []

        generated = []
        for block, (content, meta) in zip(wanted, outputs):
            provider_tag = f"{meta.get('provider', provider_name_used)}/{meta.get('tier', tier)}"
            if meta.get("error"):
                agent_logger.warning(f"Bespoke UI generation failed for {block}: {meta['error']}")
                continue
            if content and len(str(content).strip()) > 50:
                try:
                    rel = self.atomic_reuse_or_create(project_dir, block, content, target_dir)
                    if rel:
                        generated.append({"block": block, "file": rel, "via": provider_tag})
                except Exception as exc:
                    agent_logger.warning(f"Bespoke UI write failed for {block}: {exc}")
        return {
            "active": bool(generated),
            "generated_blocks": generated,
            "target_dir": os.path.relpath(target_dir, project_dir).replace(os.sep, "/"),
            "structure_context_chars": len(struct_ctx),
            "routing": {"tier": tier, "provider": provider_name_used, "blocks": len(wanted)},
        }

    def _prompt_for(self, atomic: AtomicDesignEngine, spec, struct_ctx, block: str) -> str:
        return atomic.build_bespoke_prompt(
            spec, struct_ctx, f"Build the '{block}' section from scratch, matching the project structure.", block
        )

    def atomic_reuse_or_create(self, project_dir, block, content, target_dir) -> Optional[str]:
        return AtomicDesignEngine(project_dir).reuse_or_create(block, content, target_dir)


class ComponentRegistryAdapter:
    """Checks whether a block already exists in the generated project.

    A bespoke pass skips blocks that already landed as files so working sections
    are never overwritten; missing sections are generated from scratch.
    """

    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)

    def has(self, name: str) -> bool:
        candidates = [
            os.path.join(self.project_dir, "frontend", "src", "components", "atoms", f"{name}.jsx"),
            os.path.join(self.project_dir, "frontend", "src", "components", f"{name}.jsx"),
            os.path.join(self.project_dir, "frontend", "src", "pages", f"{name}.jsx"),
        ]
        return any(os.path.isfile(c) for c in candidates)