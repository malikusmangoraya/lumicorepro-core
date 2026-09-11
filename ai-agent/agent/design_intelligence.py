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
        style = spec.get("design_style") or "modern"
        palette = spec.get("design_tokens", {}).get("palette", {})
        return f"""
You are a senior front-end designer. Generate a SINGLE self-contained React component
({block_name}.jsx) for a {spec.get('website_type', 'business')} site in the '{style}' style.

TASK: {task}

Design tokens available: {json.dumps(palette) if palette else 'use Tailwind semantic tokens (bg-primary, bg-card, text-muted-foreground). No hardcoded hex.'}

Follow the local component contract exactly:
{contract or "Use functional components, prop defaults, className passthrough."}

{structure_context[:6000]}

Rules:
- Tailwind utility classes only, no external CSS files.
- Use local UI tokens (bg-primary, bg-card, border-border) not raw colors.
- Accessible: aria-labels, semantic tags, no buttons without text.
- Dark mode: include dark: variants.
- Output ONLY the JSX component code.
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

        generated = []
        for block in targets:
            if not registry.has(block):
                try:
                    content = provider.generate_code(
                        self._prompt_for(AtomicDesignEngine(project_dir), spec, struct_ctx, block)
                    )
                    if content and len(content.strip()) > 50:
                        rel = self.atomic_reuse_or_create(project_dir, block, content, target_dir)
                        if rel:
                            generated.append({"block": block, "file": rel})
                except Exception as exc:
                    agent_logger.warning(f"Bespoke UI generation failed for {block}: {exc}")
        return {
            "active": bool(generated),
            "generated_blocks": generated,
            "target_dir": os.path.relpath(target_dir, project_dir).replace(os.sep, "/"),
            "structure_context_chars": len(struct_ctx),
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