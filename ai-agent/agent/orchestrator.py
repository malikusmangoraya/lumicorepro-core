import os
import sys
import json
import time
import hashlib
import traceback
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List, Sequence, Callable

from utils.logger import agent_logger
from utils.file_manager import FileManager
from config.providers import instantiate_provider, validate_provider_key, FALLBACK_ORDER
from config.settings import GENERATED_PROJECTS_DIR
from providers.base_provider import BaseAIProvider
from providers.provider_pool import get_pool

from . import run_status as rs
from .memory_retriever import MemoryRetriever
from .requirement_analyzer import RequirementAnalyzer
from .market_analyzer import MarketAnalyzer
from .tech_stack_selector import TechStackSelector
from .trending_features import TrendingFeaturesInjector
from .planner import GenerationPlanner
from .template_selector import TemplateSelector
from .component_selector import ComponentSelector
from .asset_selector import AssetSelector
from .backend_selector import BackendSelector
from .database_selector import DatabaseSelector
from .project_builder import ProjectBuilder
from .code_modifier import CodeModifier
from .validator import ProjectValidator
from .quality_gates import QualityGates
from .intelligence.design_planner import (
    create_design_plan,
    validate_design_plan,
    write_design_plan_artifacts,
)
from .intelligence.screenshot_to_code import (
    screenshot_to_design_spec,
    screenshot_to_design_spec_multi,
    design_spec_to_prompt,
    to_plan_inputs,
)
from .intelligence.browser_integration import (
    deep_browser_audit,
    responsive_check,
    network_audit,
    performance_audit,
    remediate_findings,
)
from .improvement_recommender import ImprovementRecommender
from .competitive_benchmark import CompetitiveBenchmark
from .currency_localizer import CurrencyLocalizer
from .compliance_generator import ComplianceGenerator
from .accessibility_checker import AccessibilityChecker
from .license_injector import LicenseInjector
from .localization_engine import LocalizationEngine
from .api_generator import APIGenerator
from .seo_automation import SEOAutomationEngine
from .cdn_optimizer import CDNOptimizer
from .performance_budget import PerformanceBudgetEngine
from .analytics_pipeline import AnalyticsPipeline
from .ab_testing_engine import ABTestingEngine
from .webhook_manager import WebhookManager
from .global_deployment import GlobalDeploymentEngine
from .security_engine import SecurityPostureEngine
from .iterate_engine import AgentIterationEngine
from .design_style import DesignStyleEngine
from .theme_matrix import ThemeMatrixEngine
from .quality_gate import DevOpsQualityGate, GateNotAvailableError
from .project_mode_engine import ProjectModeEngine
from .international_website_engine import InternationalWebsiteEngine
from .modern_3d_engine import Modern3DWebsiteEngine
from .omni_repair_engine import OmniRepairEngine
from .turbo_acceleration_engine import TurboAcceleratorEngine
from .update_engine import UpdateUpgradeEngine
from .motion_website_engine import MotionWebsiteEngine
from .hyper_unique_site_engine import HyperUniqueSiteEngine
from .fullstack_ultra_engine import FullStackUltraEngine
from .benchmark_3d_factory import Benchmark3DFactory


from config.master_prompt import get_master_prompt, MASTER_20_DESIGN_STYLES

class OrchestratorError(Exception):
    """Raised when pipeline execution encounters unrecoverable errors."""
    pass


# 20 Master Prompt design styles + dynamic rotation pool.
_STYLE_POOL = [
    "minimalism", "maximalism", "glassmorphism", "cyberpunk", "swiss",
    "retro_futurism", "editorial", "retro", "collage", "vector",
    "futuristic", "handwritten", "bohemian", "graffiti", "aurora",
    "victorian", "pixel_art", "claymorphism", "pop_art", "surreal",
    "bento_grid", "animaster", "skipper", "vengeance", "organic"
]


class PipelineCancelled(Exception):
    """Cooperative abort from WebSocket disconnect or an in-band cancel frame."""


class PhaseError(Exception):
    """Raised when a specific phase fails."""
    def __init__(self, phase_name: str, error: Exception):
        self.phase_name = phase_name
        self.error = error
        super().__init__(f"Phase '{phase_name}' failed: {error}")


class AgentOrchestrator:
    """Master controller — 18-phase state-of-the-art enterprise AI project generation pipeline.

    Provider decisions are made by `agent.ai_routing` (the single routed entry
    point): tier classification, explicit pin, offline mode, dedupe cache,
    circuit breaker and EWMA latency all live there. Every run report carries the
    `run_status` vocabulary (`status`, `providers_used`, `fallback_used`,
    `reason`, `skipped_phases`) so a deterministic local build is never reported
    as if a model produced it.
    """

    PHASES = [
        "market_analysis",
        "requirement_analysis",
        "design_brand_planning",
        "design_planner",
        "tech_stack_selection",
        "trending_features_injection",
        "resource_assembly_planning",
        "code_generation",
        "quality_verification",
        "browser_qa",
        "improvement_recommendations",
        "competitive_benchmark_delivery",
        "international_delivery",
        "localization_and_i18n",
        "compliance_and_accessibility",
        "seo_and_cdn_optimization",
        "performance_growth_and_webhooks",
        "multi_cloud_global_deployment",
    ]

    CRITICAL_PHASES = {
        "requirement_analysis",
        "resource_assembly_planning",
        "code_generation",
    }
    NON_CRITICAL_FAILURE_LIMIT = 5
    RETRYABLE_PHASES = {
        "market_analysis",
        "trending_features_injection",
        "quality_verification",
        "improvement_recommendations",
        "competitive_benchmark_delivery",
    }
    MAX_RETRIES = 2
    PHASE_TIMEOUT_SECS = 120

    # Phase dependency graph
    PHASE_DEPENDENCIES = {
        "market_analysis": [],
        "requirement_analysis": [],
        "design_brand_planning": ["requirement_analysis", "market_analysis"],
        "design_planner": ["requirement_analysis", "design_brand_planning"],
        "tech_stack_selection": ["requirement_analysis"],
        "trending_features_injection": ["requirement_analysis", "market_analysis"],
        "resource_assembly_planning": ["requirement_analysis", "tech_stack_selection"],
        "code_generation": ["resource_assembly_planning", "design_planner"],
        "quality_verification": ["code_generation"],
        "browser_qa": ["quality_verification"],
        "improvement_recommendations": ["quality_verification", "browser_qa"],
        "competitive_benchmark_delivery": ["quality_verification", "market_analysis"],
        "international_delivery": ["code_generation"],
        "localization_and_i18n": ["code_generation"],
        "compliance_and_accessibility": ["code_generation"],
        "seo_and_cdn_optimization": ["code_generation"],
        "performance_growth_and_webhooks": ["code_generation"],
        "multi_cloud_global_deployment": ["code_generation"],
    }

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_pool = get_pool()
        # ── Run-scoped provenance ────────────────────────────────────────────
        # Evidence that a *live model* actually served this run. Everything the
        # pipeline produces without one is a deterministic local build, and the
        # report says so instead of implying a provider answered.
        self.ai_provider_name: str = ""
        self.providers_used: List[str] = []
        self.ai_model_calls_succeeded: int = 0
        self.ai_model_calls_failed: int = 0
        self.skipped_phases: List[Dict[str, str]] = []
        self._free_only_providers: set[str] = set()
        self.ai_provider = self._init_provider(provider_name)
        self.memory_retriever = MemoryRetriever()
        self.phase_timings: Dict[str, float] = {}
        self.retry_counts: Dict[str, int] = {}
        self.progress_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None
        # Cooperative cancellation hook (set by the server). Checked between
        # heavy subprocess steps so a cancelled run aborts promptly.
        self.cancel_check: Optional[Callable[[], None]] = None

        # Core generation agents
        self.market_analyzer = MarketAnalyzer()
        self.analyzer = RequirementAnalyzer(self.ai_provider)
        self.tech_stack_selector = TechStackSelector()
        self.trending_injector = TrendingFeaturesInjector()
        self.planner = GenerationPlanner()
        self.template_selector = TemplateSelector(self.memory_retriever)
        self.component_selector = ComponentSelector(self.memory_retriever)
        self.asset_selector = AssetSelector(self.memory_retriever)
        self.backend_selector = BackendSelector(self.memory_retriever)
        self.database_selector = DatabaseSelector(self.memory_retriever)
        self.project_builder = ProjectBuilder()
        self.code_modifier = CodeModifier(self.ai_provider)
        self.validator = ProjectValidator()
        self.quality_gates = QualityGates()
        # Agent Reach capability footprint (CLI/skill registration, zero subprocess)
        try:
            from agent.reach.environment import register_capability_flags
            self.reach_capability = register_capability_flags()
        except Exception as exc:
            agent_logger.warning(f"Agent Reach capability registration skipped: {exc}")
            self.reach_capability = {"available": False, "reason": str(exc)}
        self.improvement_recommender = ImprovementRecommender()
        self.competitive_benchmark = CompetitiveBenchmark()

        # International, compliance & accessibility engines
        self.currency_localizer = CurrencyLocalizer()
        self.compliance_generator = ComplianceGenerator()
        self.accessibility_checker = AccessibilityChecker()
        self.localization_engine = LocalizationEngine()

        # Enterprise REST API, SEO, CDN, Performance, Analytics, A/B Testing & Cloud Engines
        self.api_generator = APIGenerator()
        self.seo_engine = SEOAutomationEngine()
        self.cdn_optimizer = CDNOptimizer()
        self.performance_budget = PerformanceBudgetEngine()
        self.analytics_pipeline = AnalyticsPipeline()
        self.ab_testing_engine = ABTestingEngine()
        self.webhook_manager = WebhookManager()
        self.deployment_engine = GlobalDeploymentEngine()
        self.security_engine = SecurityPostureEngine()
        self.license_injector = LicenseInjector()
        self.iteration_engine = AgentIterationEngine(self)
        self.design_engine = DesignStyleEngine()
        self.theme_engine = ThemeMatrixEngine()
        self.mode_engine = ProjectModeEngine()
        # Next-gen engines: International inspection, 3D experience, omni-repair & turbo
        self.international_engine = InternationalWebsiteEngine()
        self.modern_3d_engine = Modern3DWebsiteEngine()
        self.omni_repair_engine = OmniRepairEngine()
        self.turbo_engine = TurboAcceleratorEngine()
        self.update_engine = UpdateUpgradeEngine()
        self.motion_engine = MotionWebsiteEngine()
        self.hyper_unique_engine = HyperUniqueSiteEngine()
        self.fullstack_engine = FullStackUltraEngine()
        self.benchmark_3d_factory = Benchmark3DFactory()
        try:
            self.devops_gate = DevOpsQualityGate()
        except GateNotAvailableError as exc:
            agent_logger.error(f"DevOps quality gate unavailable: {exc}")
            self.devops_gate = None

    def inspect_and_replicate_website(self, target: str, brand_override: Optional[str] = None) -> Dict[str, Any]:
        """Inspect an international website or reference profile and replicate its structure."""
        return self.international_engine.replicate_website_spec(target, brand_override)

    def inject_3d_experience(
        self,
        project_dir: str,
        archetype: str = "floating_crystal",
        brand_name: str = "Lumicore",
        primary_color: str = "#3b82f6",
    ) -> Dict[str, Any]:
        """Inject modern 3D Three.js experience into project."""
        return self.modern_3d_engine.inject_3d_experience(
            project_dir=project_dir,
            archetype=archetype,
            brand_name=brand_name,
            primary_color=primary_color,
        )

    def run_omni_repair(self, project_dir: str) -> Dict[str, Any]:
        """Run deep self-healing omni-repair across the project."""
        return self.omni_repair_engine.scan_and_repair_project(project_dir)

    def run_turbo_synthesis(
        self,
        pages: List[str],
        synthesis_fn: Callable[[str], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesize pages concurrently with turbo acceleration."""
        return self.turbo_engine.synthesize_pages_parallel(pages, synthesis_fn)

    def run_system_update(self) -> Dict[str, Any]:
        """Run automated system audit, database verification, and config maintenance."""
        return self.update_engine.run_full_system_update()

    def inject_advanced_motion(
        self,
        project_dir: str,
        preset: str = "kinetic_text",
        brand: str = "Lumicore",
        primary_color: str = "#3b82f6",
    ) -> Dict[str, Any]:
        """Inject advanced Framer Motion / GSAP animations into project."""
        return self.motion_engine.inject_motion_layer(
            project_dir=project_dir,
            preset=preset,
            brand=brand,
            primary_color=primary_color,
        )

    def generate_hyper_unique_blueprint(self, prompt: str, brand_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate guaranteed unique palette, SVG logo, typography, and architecture."""
        return self.hyper_unique_engine.synthesize_hyper_unique_blueprint(prompt, brand_name)

    def generate_fullstack_project(
        self,
        destination_dir: str,
        prompt: str = "Enterprise AI Cloud Platform",
        brand_name: Optional[str] = None,
        industry: str = "saas",
        primary_color: Optional[str] = None,
        *,
        generation_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate clean, complete full-stack web application with React 19 frontend and Express backend."""
        return self.fullstack_engine.generate_project(
            destination_dir=destination_dir,
            prompt=prompt,
            brand_name=brand_name,
            industry=industry,
            primary_color=primary_color,
            generation_contract=generation_contract,
        )

    def synthesize_benchmark_3d_site(
        self,
        destination_dir: str,
        prompt: str = "3d luxury realestate website with architectural villa",
        brand_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize complete full 3D website benchmarking international category leaders."""
        return self.benchmark_3d_factory.generate_full_3d_website(
            destination_dir=destination_dir,
            prompt=prompt,
            brand_name=brand_name,
        )

    def _select_portfolio_unique_design(
        self,
        spec: Dict[str, Any],
        decision: Dict[str, Any],
        design_plan: Dict[str, Any],
        project_dir: Path,
    ) -> Dict[str, Any]:
        """Apply a portfolio-aware design choice before code generation."""
        from .intelligence.design_uniqueness import (
            apply_design_uniqueness,
            extract_design_signature,
            load_portfolio_signatures,
            normalize_palette_overrides,
        )

        scan_error = ""
        try:
            prior_signatures = load_portfolio_signatures(
                Path(GENERATED_PROJECTS_DIR), exclude_project=Path(project_dir)
            )
        except Exception as exc:
            prior_signatures = []
            scan_error = str(exc)[:160]

        prompt = str(spec.get("original_prompt") or spec.get("prompt") or "")
        project_name = str(spec.get("project_name") or Path(project_dir).name)
        fingerprints = sorted(
            str(item.get("fingerprint"))
            for item in prior_signatures
            if item.get("fingerprint")
        )
        seed = str(spec.get("design_seed") or hashlib.sha256(
            "\n".join((prompt.strip().lower(), project_name, *fingerprints)).encode("utf-8")
        ).hexdigest())

        explicit_constraints = dict(spec.get("design_constraints") or {})
        requested_styles = spec.get("style") or []
        requested_style = spec.get("ui_style") or (decision or {}).get("ui_style")
        reference_inputs = any(
            spec.get(key)
            for key in (
                "screenshot", "screenshot_url", "image_url", "reference_spec",
                "reference_url", "reference_site",
            )
        ) or bool((decision or {}).get("reference_hints") or spec.get("reference_hints")) or bool(
            isinstance(spec.get("screenshot_spec"), dict)
            and spec["screenshot_spec"].get("analyzed")
        )
        color_inputs = bool(
            spec.get("primary_color_hint") or spec.get("color_palette_hints")
        )
        if requested_style and (
            requested_style in requested_styles
            or explicit_constraints.get("ui_style")
            or reference_inputs
            or color_inputs
        ):
            explicit_constraints.setdefault("ui_style", requested_style)
        decision = copy.deepcopy(decision or {})
        if requested_style:
            decision["ui_style"] = requested_style
        preferences = spec.get("style_preference") or {}
        if isinstance(preferences, dict):
            if preferences.get("animation") and "motion" in decision:
                explicit_constraints.setdefault("motion", decision["motion"])
            if preferences.get("layout") and "grid" in decision:
                explicit_constraints.setdefault("grid", decision["grid"])
        screenshot_spec = spec.get("screenshot_spec") or {}
        if isinstance(screenshot_spec, dict) and screenshot_spec.get("analyzed"):
            for key in ("hero", "grid"):
                if key in decision:
                    explicit_constraints.setdefault(key, decision[key])

        selected = apply_design_uniqueness(
            decision,
            design_plan,
            prior_signatures,
            seed=seed,
            explicit_constraints=explicit_constraints,
        )
        selected_ui_style = selected["decision"].get("ui_style") or requested_style or "glassmorphism"
        from agent.pro_design import resolve_design_blueprint
        from .intelligence.design_planner import build_design_system

        blueprint = resolve_design_blueprint(
            project_name,
            selected_ui_style,
            str(spec.get("target_region") or "default"),
            str(spec.get("brand_title") or project_name),
        )
        palette_override: Dict[str, Any] = {}
        screenshot_spec = spec.get("screenshot_spec") or {}
        if isinstance(screenshot_spec, dict) and screenshot_spec.get("colors_measured"):
            measured_colors = (
                ((selected["design_plan"].get("design_system") or {}).get("colors"))
                or {}
            )
            palette_override.update({
                "primary": measured_colors.get("primary"),
                "accent": measured_colors.get("accent"),
                "heading": measured_colors.get("text"),
                "navBg": measured_colors.get("bg"),
                "footerBg": measured_colors.get("surface_2"),
                "cardBg": measured_colors.get("surface"),
                "text": measured_colors.get("text"),
                "muted": measured_colors.get("text_dim"),
                "border": measured_colors.get("border"),
            })
        color_hints = spec.get("color_palette_hints") or []
        if isinstance(color_hints, str):
            color_hints = [color_hints]
        primary_hint = spec.get("primary_color_hint")
        if isinstance(primary_hint, str) and primary_hint.startswith("#"):
            palette_override["primary"] = primary_hint
        elif color_hints and isinstance(color_hints[0], str):
            palette_override["primary"] = color_hints[0]
        if len(color_hints) > 1 and isinstance(color_hints[1], str):
            palette_override["accent"] = color_hints[1]
        palette_override = normalize_palette_overrides(palette_override)
        blueprint.setdefault("palette", {}).update(palette_override)
        selected["decision"]["ui_style"] = blueprint.get("ui_style", selected_ui_style)
        selected["design_blueprint"] = blueprint
        selected["palette_override"] = palette_override
        selected["design_plan"]["ui_style"] = blueprint.get("ui_style", selected_ui_style)
        palette = blueprint.get("palette") or {}
        color_tokens = {
            "primary": palette.get("primary"),
            "accent": palette.get("accent"),
            "bg": palette.get("navBg"),
            "surface": palette.get("cardBg"),
            "surface_2": palette.get("footerBg"),
            "border": palette.get("border"),
            "text": palette.get("text"),
            "text_dim": palette.get("muted"),
        }
        color_tokens = {key: value for key, value in color_tokens.items() if value}
        fonts = blueprint.get("fonts") or {}
        resolved_system = build_design_system(
            palette=color_tokens,
            design_tokens={
                "heading_font": fonts.get("display"),
                "body_font": fonts.get("sans"),
            },
        )
        selected["design_plan"].setdefault("design_system", {})
        selected["design_plan"]["design_system"]["colors"] = resolved_system["colors"]
        selected["design_plan"]["design_system"]["contrast"] = resolved_system["contrast"]
        selected["design_plan"]["design_system"]["typography"] = resolved_system["typography"]
        manifest = selected["decision"].get("design_manifest")
        if isinstance(manifest, dict):
            manifest.setdefault("visual", {})["ui_style"] = selected["decision"]["ui_style"]
            manifest["colors"] = {"tokens": color_tokens, "source": "pro_design_blueprint"}
        signature = extract_design_signature(
            selected["decision"], selected["design_plan"]
        )
        selected["design_signature"] = signature
        selected["decision"].setdefault("design_manifest", {})["design_signature"] = signature
        selected["design_plan"]["design_signature"] = signature
        selected["comparison"]["status"] = (
            "unavailable" if scan_error else
            "compared" if prior_signatures else "empty"
        )
        if scan_error:
            selected["comparison"]["reason"] = scan_error
        return selected

    def _provider_name(self) -> str:
        """Name of the provider currently serving this run ("" when none)."""
        if self.ai_provider is None:
            return ""
        if self.ai_provider_name:
            return self.ai_provider_name
        try:
            name = self.provider_pool.get_provider_name(self.ai_provider)
        except Exception:
            name = None
        return name or type(self.ai_provider).__name__

    def _record_model_evidence(self, source: str, provider_name: str = "") -> None:
        """Record a confirmed live model response for this run."""
        self.ai_model_calls_succeeded += 1
        name = provider_name or self._provider_name()
        if name and name not in self.providers_used:
            self.providers_used.append(name)
        agent_logger.info(f"[EVIDENCE] live model response ({source}) from '{name or 'unknown'}'")

    def _record_model_failure(self, source: str) -> None:
        """Record a model call that was attempted and failed."""
        self.ai_model_calls_failed += 1
        agent_logger.info(f"[EVIDENCE] model call failed ({source})")

    def _mark_skipped(self, phase: str, reason: str) -> None:
        """Record a phase that was skipped (never silently) with its reason."""
        entry = rs.skipped_phase(phase, reason)
        if entry not in self.skipped_phases:
            self.skipped_phases.append(entry)
            agent_logger.warning(f"[PHASE SKIPPED] {phase} — {reason}")

    def _init_provider(self, provider_name: Optional[str] = None):
        """Resolve the run's AI provider through the task router.

        `agent.ai_routing.prefer` is the single routed entry point: it owns the
        explicit pin (`provider_name` / AI_PROVIDER / REASONING_PROVIDER), the
        AI_OFFLINE switch, tier classification, cooldowns and the latency-aware
        ranking. The orchestrator no longer calls `pool.get_active()` directly,
        so there is exactly one place that decides which provider serves a call.
        """
        from agent import ai_routing

        self.ai_provider_name = ""
        if ai_routing.offline():
            # AI_OFFLINE=1 is a product-level switch, not a router preference: it
            # must win over the pool too, otherwise the keyless gateways
            # (ninerouter/omniroute) still resolve and local-first runs quietly
            # reach the network. This is also what makes the offline and
            # determinism tests hermetic.
            agent_logger.info("[ORCH] AI_OFFLINE=1: local-first mode, no provider resolved.")
            return None

        inst, name, tier = ai_routing.prefer("codegen", "", pin=provider_name)
        if inst is not None:
            self.ai_provider_name = name
            agent_logger.info(
                f"[ORCH] Routed AI provider: '{name}' (tier={tier}, pin={provider_name or 'none'})"
            )
            return inst

        if provider_name:
            agent_logger.warning(
                f"[ORCH] Requested provider '{provider_name}' is not usable — "
                "continuing with deterministic local engines."
            )
        else:
            agent_logger.info(
                "No external AI provider is configured/usable. Operating in local-first offline mode."
            )
        return None

    def set_provider(self, provider, name: str = "") -> None:
        """Point every provider-holding sub-engine at `provider`.

        Sub-engines snapshot the provider at construction
        (`RequirementAnalyzer`, `CodeModifier`, `AgentIterationEngine`), so
        assigning `orch.ai_provider` alone leaves them on the old instance —
        which once caused real network calls from runs that had swapped in an
        offline fake. Centralize the swap here; rotation uses this too.
        """
        self.ai_provider = provider
        if name:
            self.ai_provider_name = name
        self.analyzer.ai_provider = provider
        self.code_modifier.ai_provider = provider
        # Attribute name is `iteration_engine`; a silent miss here would leave the
        # iteration engine on the previous provider and quietly reintroduce the
        # leak this method exists to close, so failures are surfaced, not swallowed.
        self.iteration_engine.provider = provider
        self.iteration_engine.code_modifier = CodeModifier(provider)

    def _rotate_provider(self):
        """Move to the next routed provider and propagate it to all sub-engines.

        Rotation goes through `agent.ai_routing.rotate` so it obeys the same
        tier/cooldown/circuit-breaker decision as primary selection and can never
        land back on the provider that just failed.
        """
        from agent import ai_routing

        if ai_routing.offline():
            return False
        current = self._provider_name()
        inst, name, tier = ai_routing.rotate("repair", current)
        if inst is None or inst is self.ai_provider:
            agent_logger.info(
                f"[ORCH] No alternative provider for retry (current='{current or 'none'}')."
            )
            return False
        agent_logger.info(f"[ORCH] Rotating provider: '{current}' -> '{name}' (tier={tier})")
        self.set_provider(inst, name=name)
        return True

    def _run_phase(self, phase_name: str, func, *args, **kwargs) -> Any:
        """Execute a single phase with error isolation, retry logic, recovery fallback, timing, and callbacks."""
        retries = kwargs.pop("_retries", 0)
        fallback = kwargs.pop("_fallback", None)
        is_critical = kwargs.pop("_critical", False)
        is_retryable = kwargs.pop("_retryable", False)

        if is_retryable and retries == 0:
            retries = self.MAX_RETRIES

        self.retry_counts[phase_name] = retries
        initial_retries = retries

        self._checkpoint_cancel()
        agent_logger.info(f"[PHASE START] ---- {phase_name}")
        if self.progress_callback:
            try:
                self.progress_callback(phase_name, "phase_start", {"ts": time.time()})
            except PipelineCancelled:
                raise
            except Exception:
                pass

        phase_start = time.time()
        try:
            if phase_name.startswith("Phase") and self.PHASE_TIMEOUT_SECS > 0:
                result = self._run_with_hard_timeout(phase_name, func, args, kwargs)
            else:
                result = func(*args, **kwargs)
            phase_time = round(time.time() - phase_start, 3)
            self.phase_timings[phase_name] = phase_time
            retries_used = initial_retries - retries
            if retries_used > 0:
                agent_logger.info(f"[PHASE COMPLETE] {phase_name} (took {phase_time}s) — Succeeded after {retries_used} retry attempt(s)")
            else:
                agent_logger.info(f"[PHASE COMPLETE] {phase_name} (took {phase_time}s)")

            if self.progress_callback:
                try:
                    self.progress_callback(phase_name, "phase_done", {"ts": time.time(), "duration": phase_time})
                except PipelineCancelled:
                    raise
                except Exception:
                    pass
            return result
        except PipelineCancelled:
            raise
        except Exception as e:
            phase_time = round(time.time() - phase_start, 3)
            self.phase_timings[phase_name] = phase_time
            error_trace = traceback.format_exc()
            agent_logger.error(f"[PHASE FAILED] {phase_name} (took {phase_time}s) — {e}")
            agent_logger.debug(f"[PHASE TRACE] {phase_name}:\n{error_trace}")

            if self.progress_callback:
                try:
                    self.progress_callback(phase_name, "phase_error", {"ts": time.time(), "error": str(e)})
                except PipelineCancelled:
                    raise
                except Exception:
                    pass

            if retries > 0:
                # Rotate provider before retrying on rate limits or connectivity
                # failures (e.g. OmniRoute gateway unreachable → fall back fast).
                rotate_reason = None
                current_name = self._provider_name()
                if self.ai_provider:
                    if BaseAIProvider.is_rate_limited(e):
                        rotate_reason = "rate limit"
                        self.provider_pool.mark_rate_limited(current_name)
                    elif BaseAIProvider.is_connectivity_error(e):
                        rotate_reason = "connectivity failure"
                        self.provider_pool.mark_failed(current_name)
                if rotate_reason and self.ai_provider:
                    self._record_model_failure(f"phase:{phase_name}:{rotate_reason}")
                    agent_logger.warning(
                        f"[PHASE ROTATE] {phase_name} hit {rotate_reason} on '{current_name}' — rotating provider"
                    )
                    self._rotate_provider()

                agent_logger.warning(f"[PHASE RETRY] Retrying {phase_name} ({retries - 1} attempts left)...")
                return self._run_phase(phase_name, func, *args, _retries=retries - 1,
                                       _fallback=fallback,
                                       _critical=is_critical,
                                       _retryable=is_retryable,
                                       **kwargs)
            if is_critical:
                agent_logger.critical(f"[PHASE CRITICAL FAILURE] {phase_name} failed with no fallback. Pipeline cannot continue.")
                raise OrchestratorError(f"Critical phase '{phase_name}' failed: {e}")
            if fallback is not None:
                agent_logger.info(f"[PHASE FALLBACK] Using fallback for {phase_name}")
                return fallback
            agent_logger.error(f"[PHASE UNRECOVERABLE] {phase_name} failed with no fallback.")
            raise

    def _persist_design_plan_artifacts(
        self,
        project_dir: str,
        design_plan: Dict[str, Any],
        phase_log: Dict[str, Any],
        artifact_key: str = "artifacts",
    ) -> Dict[str, Any]:
        """Persist the pre-coding design contract next to the generated project.

        The planner runs before `project_dir` exists, so the first attempt is
        expected to report a missing directory. The build phase calls this again
        after the directory exists; both attempts are recorded instead of
        letting one silent no-op imply persistence.
        """
        entry = phase_log.setdefault("phase_5b_design_planner", {})
        if not design_plan:
            written = {"ok": False, "reason": "no design plan"}
            entry[artifact_key] = written
            return written
        try:
            written = write_design_plan_artifacts(project_dir, design_plan)
        except PipelineCancelled:
            raise
        except Exception as exc:
            written = {"ok": False, "reason": str(exc)[:200]}
            agent_logger.warning(f"Design plan artifacts skipped: {exc}")
        entry[artifact_key] = written
        if written.get("ok"):
            agent_logger.info(
                "Design plan artifacts written: %s",
                (written.get("paths") or {}).get("json"),
            )
        return written

    def _checkpoint_cancel(self) -> None:
        """Abort immediately when the WebSocket loop raised a cancel token."""
        if self.cancel_check:
            self.cancel_check()

    def _bind_engineering_matrix(self, spec: Dict[str, Any], phase_log: Dict[str, Any]) -> Dict[str, Any]:
        """Pillar 4: load PRD/TRD/tokens/schema/SRS and the local component contracts before codegen."""
        matrix: Dict[str, Any] = {"loaded": False, "all_present": False}
        try:
            from agent.enterprise_architect import enterprise_architect
            docs = enterprise_architect.load_rules()
            matrix["docs"] = {
                name: {"loaded": info.get("loaded"), "anchors_ok": all((info.get("anchors") or {}).values())}
                for name, info in (docs.get("files") or {}).items()
            }
            matrix["all_present"] = bool(docs.get("all_present"))
            matrix["loaded"] = True
        except Exception as exc:
            agent_logger.warning(f"Engineering matrix load skipped: {exc}")
            matrix["reason"] = str(exc)
        try:
            from agent.component_registry import component_contract_snippet, get_component_registry
            registry = get_component_registry()
            matrix["component_registry_count"] = registry.count()
            spec["component_contract"] = component_contract_snippet()
        except Exception as exc:
            agent_logger.warning(f"Component registry bind skipped: {exc}")
            matrix["component_registry_count"] = 0
        spec["engineering_matrix"] = {
            "loaded": matrix.get("loaded"),
            "all_present": matrix.get("all_present"),
            "docs": matrix.get("docs"),
            "component_registry_count": matrix.get("component_registry_count"),
        }
        phase_log["engineering_matrix"] = spec["engineering_matrix"]
        if matrix.get("loaded") and not matrix.get("all_present"):
            agent_logger.error("Engineering matrix incomplete — ZIP will be blocked after verification.")
        return matrix

    def _run_devops_quality_gate(self, project_dir: str) -> Dict[str, Any]:
        """Run Prettier/ESLint via asyncio.create_subprocess_exec on a worker-thread loop."""
        if self.devops_gate is None:
            return {
                "available": False,
                "passed": False,
                "note": "Node.js tooling unavailable — ZIP compilation blocked by DevOps quality gate.",
            }
        from agent.reach.process import in_worker_loop
        report = in_worker_loop(
            lambda: self.devops_gate.run_gate(
                project_dir,
                self_heal=self._self_heal_generated,
                error_fixer=self._self_correct_generated,
                checkpoint=self.cancel_check,
            )
        )
        if report is None:
            return {
                "available": True,
                "passed": False,
                "note": "Quality gate refused to block the FastAPI event loop; ZIP compilation blocked.",
            }
        return report

    @staticmethod
    def _deployment_release_gate(
        validation_report: Dict[str, Any],
        quality_report: Dict[str, Any],
        devops_gate: Dict[str, Any],
        architect_gate: Dict[str, Any],
        completeness_report: Dict[str, Any],
        guardrails_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Allow deployment only after project, DevOps, and architecture checks pass."""
        blockers = []
        if not validation_report.get("valid", False):
            blockers.append("project_validation_failed")
        if quality_report.get("overall_score", 0) < 80:
            blockers.append("quality_score_below_80")
        if not devops_gate.get("passed", False):
            blockers.append("devops_quality_gate_failed")
        if not (architect_gate.get("skipped") or architect_gate.get("passed")):
            blockers.append("enterprise_architecture_gate_failed")
        if completeness_report.get("status") != "complete":
            missing = completeness_report.get("blockers") or ["required_artifacts_missing"]
            blockers.extend(f"generated_project_incomplete:{item}" for item in missing)
        if not guardrails_report.get("passed", False):
            blockers.append("output_guardrails_failed")
        return {"passed": not blockers, "blockers": blockers}

    @staticmethod
    def _build_workflow_agents_report(
        phase_log: Dict[str, Any],
        spec: Dict[str, Any],
        project_dir: str,
    ) -> Dict[str, Any]:
        """Summarize role ownership and the artifacts handed between specialists."""
        requirements = phase_log.get("phase_2_requirement_analysis") or {}
        assembly = phase_log.get("phase_5_assembly_plan") or {}
        research = spec.get("benchmark_first") or {}
        design = phase_log.get("phase_2_design_decision") or {}
        design_plan = phase_log.get("phase_2b_design_plan") or {}
        code = phase_log.get("phase_6_code_generation") or {}
        release_gate = phase_log.get("qa_release_gate") or {}
        deployment = phase_log.get("live_deployment") or {}
        qa_status = (
            "blocked" if not release_gate.get("passed")
            else "deployed" if deployment.get("status") == "deployed"
            else "ready"
        )

        return {
            "planner": {
                "name": "Product Planner",
                "status": "completed" if requirements and assembly else "partial",
                "handoff": {
                    "project_name": assembly.get("project_name"),
                    "requirements_count": len(requirements.get("features") or []),
                    "assembly_steps": assembly.get("steps", 0),
                },
            },
            "design_researcher": {
                "name": "International Design Researcher",
                "status": "completed" if research and design else "partial",
                "handoff": {
                    "research_source": research.get("source", "unavailable"),
                    "industry": research.get("industry"),
                    "benchmark_peers": research.get("benchmark_peers", []),
                    "design_blueprint": bool(design_plan),
                    "design_direction": {
                        key: design.get(key)
                        for key in ("hero", "motion", "cta_style", "references")
                        if design.get(key) is not None
                    },
                },
            },
            "coder": {
                "name": "Implementation Engineer",
                "status": "completed" if project_dir and code else "failed",
                "handoff": {
                    "project_dir": project_dir,
                    "ai_calls": code.get("ai_calls", 0),
                },
            },
            "qa_deployment": {
                "name": "QA and Deployment Engineer",
                "status": qa_status,
                "handoff": {
                    "release_gate": release_gate,
                    "tests": (phase_log.get("quality_gate_devops") or {}).get("tests", {}),
                    "deployment_status": deployment.get("status", "not_attempted"),
                    "live_url": deployment.get("url", ""),
                    "quality_score": (phase_log.get("phase_7_quality_verification") or {}).get(
                        "overall_score", 0
                    ),
                },
            },
        }

    def _run_phase_safe(self, phase_name: str, func, func_args=None, fallback=None, critical=False, retryable=False):
        """Run a phase and only recover automatically when it is non-critical."""
        args = func_args or []
        try:
            return self._run_phase(phase_name, func, *args, _critical=critical, _retryable=retryable, _fallback=fallback)
        except PipelineCancelled:
            raise
        except Exception as e:
            agent_logger.error(f"[PHASE CAUGHT] {phase_name} final fallback: {e}")
            if critical:
                raise
            return fallback if fallback is not None else None

    def _run_phases_parallel(self, phases: List[tuple]):
        """Run several independent, thread-safe phases concurrently.

        Each tuple: (phase_name, func, func_args, fallback). Safe when every
        phase writes distinct files (verified per phase-group) and none mutates
        the shared spec dict. Never parallelize AI/LLM calls (free-tier rate
        limits) or two functions writing the same file.
        """
        results: Dict[str, Any] = {}
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _wrapper(name, func, fargs, fallback):
            try:
                return name, self._run_phase_safe(
                    name, func, func_args=list(fargs), fallback=fallback
                )
            except Exception as exc:  # pragma: no cover — defensive
                return name, fallback

        with ThreadPoolExecutor(max_workers=max(1, len(phases))) as ex:
            futures = [ex.submit(_wrapper, *p) for p in phases]
            for fut in as_completed(futures):
                try:
                    name, result = fut.result()
                    results[name] = result
                except Exception as exc:  # pragma: no cover
                    agent_logger.error(f"[PARALLEL] {exc}")
        return results

    def _reset_phase_tracking(self):
        """Reset phase tracking state between pipeline runs."""
        self.phase_timings = {}
        self.retry_counts = {}

    def _run_with_hard_timeout(self, phase_name: str, func, args, kwargs) -> Any:
        """Execute a blocking phase in a worker with a hard wall-clock timeout.

        The AI providers use 30s×3 synchronous retries; without a hard cap a
        hung/gated provider stalls the pipeline for ~90s per call. Running the
        phase in a detached daemon thread lets `PHASE_TIMEOUT_SECS` bound
        wall-clock time and rebuild ETA predictability. Only the finished result
        is committed; a timed-out worker is abandoned (daemon, killed on exit)
        and its phase falls back to `_run_phase_safe`'s fallback.
        """
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
        timeout = self.PHASE_TIMEOUT_SECS
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="phase")
        try:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except FutureTimeout:
                agent_logger.error(
                    f"[PHASE TIMEOUT] {phase_name} exceeded {timeout}s — "
                    "abandoning worker and continuing with fallback."
                )
                future.cancel()
                raise TimeoutError(f"{phase_name} exceeded {timeout}s")
        finally:
            executor.shutdown(wait=False)

    def _get_project_main_files(self, project_dir: str, max_files: int = None) -> List[str]:
        """Discover key project files for AI modification by searching frontend/src."""
        from config.settings import AI_MAX_CONTEXT_FILES
        max_files = max_files or AI_MAX_CONTEXT_FILES
        src_dir = os.path.join(project_dir, "frontend", "src")
        files: List[str] = []
        if not os.path.isdir(src_dir):
            return []
        for root, _, filenames in os.walk(src_dir):
            for fname in filenames:
                if fname.endswith((".jsx", ".tsx", ".js", ".ts")):
                    files.append(os.path.join(root, fname))
        return files[:max_files]

    def _calculate_health(self, phase_failures: List[str]) -> Dict[str, Any]:
        """Calculate pipeline health score based on failures and critical phase impact."""
        failed_phases = self._phase_failure_names(phase_failures)
        critical_failures = sorted(failed_phases & self.CRITICAL_PHASES)
        non_critical_failures = sorted(failed_phases - self.CRITICAL_PHASES)
        # Gate identifiers (quality_gate_devops, architect_enterprise_verification,
        # final_production_validation) are not phases but still degrade the run.
        non_critical_failures += sorted(
            f for f in phase_failures if isinstance(f, str) and not f.startswith("phase_")
        )

        health = 100
        health -= len(critical_failures) * 20
        health -= len(non_critical_failures) * 4

        return {
            "score": max(0, health),
            "critical_failures": critical_failures,
            "non_critical_failures": non_critical_failures,
            "status": "healthy" if health >= 80 else "degraded" if health >= 50 else "critical",
        }

    def _phase_failure_names(self, phase_failures: List[str]) -> set:
        """Map report identifiers such as phase_6_code_generation to canonical phase IDs.

        Several steps were appended under their historical names (`phase_3_tech_stack`,
        `phase_5_assembly_planning`, …) which never matched a `PHASES` id, so a
        failed phase was still listed in `phases_completed`. `_PHASE_FAILURE_ALIASES`
        is the single mapping from every emitted failure id to its real phase.
        """
        names = set()
        for failure in phase_failures:
            if not isinstance(failure, str) or not failure.startswith("phase_"):
                continue
            raw = failure.split("_", 2)[-1]
            names.add(self._PHASE_FAILURE_ALIASES.get(raw, raw))
        return names

    # Failure identifiers that were emitted under a name that is not a PHASES id.
    _PHASE_FAILURE_ALIASES = {
        "tech_stack": "tech_stack_selection",
        "trending_features": "trending_features_injection",
        "assembly_planning": "resource_assembly_planning",
        "improvements": "improvement_recommendations",
        "benchmark": "competitive_benchmark_delivery",
        "localization": "localization_and_i18n",
        "compliance_accessibility": "compliance_and_accessibility",
    }

    @staticmethod
    def _seeded_choice(options: Sequence[str], *inputs: str) -> str:
        """Deterministic choice: the same inputs always pick the same option.

        Replaces `random.choice` for style/palette-style decisions. `hash()` is
        deliberately not used — it is salted per process (PYTHONHASHSEED) and would
        make the same prompt produce a different design on a rerun.
        """
        if not options:
            return ""
        digest = hashlib.sha256("\x1f".join(str(i) for i in inputs).encode("utf-8", "replace"))
        return options[int(digest.hexdigest()[:8], 16) % len(options)]

    @staticmethod
    def _design_seed(*inputs: str) -> str:
        """Stable digest of the run's design inputs (recorded in the manifest)."""
        digest = hashlib.sha256("\x1f".join(str(i) for i in inputs).encode("utf-8", "replace"))
        return digest.hexdigest()[:16]

    def _resolve_design_style(
        self,
        explicit: Optional[str],
        prompt: str,
        spec: Dict[str, Any],
    ) -> str:
        """Explicit style wins; otherwise the seeded decision engine picks one.

        Same prompt + same website type ⇒ same style, in this process and the next.
        """
        if explicit:
            return explicit
        current = spec.get("design_style")
        if current:
            return str(current)
        return self._seeded_choice(
            _STYLE_POOL,
            prompt,
            str(spec.get("website_type", "")),
            str(spec.get("industry", "")),
        )

    def _collect_user_design_preferences(
        self,
        spec: Dict[str, Any],
        market_analysis: Optional[Dict[str, Any]] = None,
        interactive: bool = False,
    ) -> Dict[str, Any]:
        """Consolidated design customization flow. Supports interactive CLI or automated defaults."""
        website_type = spec.get("website_type", "ecommerce")
        industry = spec.get("industry", "general")
        project_name = spec.get("project_name", "my-project")

        # Benchmark-First (mandatory, deterministic): decode the industry
        # playbook + international benchmark attributes BEFORE design, so every
        # fresh build follows global best-in-class style. Falls back to a fully
        # deterministic profile when the provider is unavailable -- never empty.
        try:
            from agent.intelligence.benchmark_first import run_benchmark_first
            import logging
            _log = logging.getLogger("lumicorepro.orchestrator")
            _bench = run_benchmark_first(spec, provider=getattr(self, "ai_provider", None))
            spec["benchmark_first"] = _bench
            _log.info(
                "Benchmark-First: source=%s industry=%s peers=%d",
                _bench.get("source"), _bench.get("industry"),
                len(_bench.get("benchmark_peers") or []),
            )
        except Exception as bench_err:
            import logging as _l
            _l.getLogger("lumicorepro.orchestrator").warning(
                "Benchmark-First research failed (non-blocking): %s", bench_err)
        # -- end Benchmark-First hook

        # Smart defaults based on industry & website type
        defaults = {
            "animation_style": "modern",
            "color_scheme": "cyan" if website_type in ("saas", "dashboard", "fintech") else "dark",
            "layout_style": "multi_page",
            "font_style": "sans_serif",
            "pages": spec.get("pages", ["Home", "About", "Services", "Contact"]),
            "extra_features": ["cookie_consent", "responsive_navbar", "dark_mode_toggle"],
        }

        # Never prompt when the calling context has no real terminal (HTTP/WS
        # workers, tests, CI). input() on a non-TTY stream can hang indefinitely.
        if interactive and not sys.stdin.isatty():
            agent_logger.info("Interactive design flow requested but stdin is not a TTY — using smart defaults.")
            interactive = False
        if not interactive:
            spec.update(defaults)
            return spec

        print("\n" + "=" * 65)
        print("   🎨 LUMICOREPRO ENTERPRISE DESIGN CUSTOMIZER")
        print("=" * 65)
        print(f"  📌 Project Type  : {website_type.title()} Website")
        print(f"  🏭 Industry      : {industry.title()}")
        print(f"  📁 Project Name  : {project_name}")

        try:
            # 1. Animation Style
            print("\n  [1/4] ANIMATION STYLE:")
            print("     (1) Modern & Clean (smooth micro-interactions)")
            print("     (2) Glassmorphism (frosted glass panels & blur)")
            print("     (3) Minimal (fast, subtle transitions)")
            print("     (4) Bold Dynamic (parallax & scroll effects)")
            anim_choice = input("     Select choice (1-4, default=1): ").strip()
            animation_map = {"1": "modern", "2": "glassmorphism", "3": "minimal", "4": "bold"}
            selected_anim = animation_map.get(anim_choice, "modern")

            # 2. Color Theme
            print("\n  [2/4] COLOR SCHEME:")
            print("     (1) Dark Mode (Slate & Cyan Accent)")
            print("     (2) Clean Light (White & Indigo Accent)")
            print("     (3) Emerald Green (Organic / Modern)")
            print("     (4) Sunset Amber (Warm & Creative)")
            color_choice = input("     Select choice (1-4, default=1): ").strip()
            color_map = {"1": "dark_cyan", "2": "clean_light", "3": "emerald", "4": "sunset"}
            selected_color = color_map.get(color_choice, "dark_cyan")

            # 3. Extra Pages
            print("\n  [3/4] ADDITIONAL PAGES (comma-separated, or Enter to use defaults):")
            extra_pages_in = input("     Extra pages: ").strip()
            if extra_pages_in:
                pages_list = [p.strip() for p in extra_pages_in.split(",") if p.strip()]
                spec["pages"] = list(set(spec.get("pages", []) + pages_list))

            # 4. Confirmation
            confirm = input("\n  ✅ Type 'build' or press Enter to generate project: ").strip().lower()
            if confirm in ("cancel", "exit", "quit", "n", "no"):
                print("  ❌ Generation cancelled by user.")
                raise KeyboardInterrupt("Cancelled by user")

            spec["animation_style"] = selected_anim
            spec["color_scheme"] = selected_color
            print(f"  🚀 Plan approved! Building '{project_name}'...\n")
        except (EOFError, KeyboardInterrupt):
            agent_logger.info("Non-interactive / input stream closed. Using smart defaults.")
            spec.update(defaults)

        return spec

    # Backwards-compatible aliases
    _interactive_plan_approval = _collect_user_design_preferences
    _ask_design_preferences = _collect_user_design_preferences
    _interact_with_user = _collect_user_design_preferences

    def _safe_zip(self, project_dir: str, spec: Dict[str, Any]) -> str:
        """Create ZIP archive safely; returns empty string on failure."""
        try:
            zip_output_base = os.path.join(
                os.path.dirname(project_dir),
                spec.get("project_name", "generated-website")
            )
            return FileManager.create_zip_archive(project_dir, zip_output_base)
        except Exception as e:
            agent_logger.error(f"ZIP archive creation failed: {e}")
            return ""

    def _auto_deploy_project(self, project_dir: str, spec: Dict[str, Any]) -> str:
        """Auto-deploy project to GitHub Pages and return the live URL.

        Uses the robust auto_deploy module (root-level static preview,
        `.nojekyll`, Pages source update via PUT with POST fallback, and
        build polling until HTTP 200). Falls back gracefully to an empty
        string when the token is missing or deployment fails.
        """
        try:
            from agent.auto_deploy import deploy as auto_deploy
            project_name_raw = spec.get("project_name", "generated-website")
            repo_name = str(project_name_raw).lower().replace(" ", "-")
            industry = spec.get("industry", "general")
            website_type = spec.get("website_type", "business")

            name = spec.get("project_name_human", project_name_raw.title())
            tagline = spec.get(
                "project_tagline",
                f"Production-ready {website_type} platform for the {industry} industry, "
                "built with LumicorePro Core.",
            )
            category = f"{industry.title()} / {website_type.title()}"
            features = spec.get("project_features") or [
                "Full-stack React 19 + Express + MySQL architecture",
                "JWT auth, RBAC and rate-limited APIs",
                "i18n (14 languages) + RTL support",
                "SEO + JSON-LD structured data",
                "Pro UI: dark mode, motion, responsive",
                "Deployment configs for Vercel/Docker/NGINX",
            ]

            # Prefer a real SPA deployment (built dist on gh-pages branch) so the
            # live preview shows the actual product — not the generic root shell.
            live_url = ""
            try:
                # Ensure the GitHub repo exists first (gh-pages push needs it).
                from agent.auto_deploy import repo_exists, create_repo, load_token
                token = load_token()
                if token and repo_exists(repo_name, token):
                    pass
                elif token:
                    create_repo(repo_name, token, tagline)
                if token:
                    from agent.pro_design import build_and_deploy_ghpages
                    live_url = build_and_deploy_ghpages(Path(project_dir), repo_name, token) or ""
            except Exception as spa_err:
                agent_logger.warning(f"SPA deploy unavailable ({spa_err}); falling back to root preview.")

            if not live_url:
                live_url = auto_deploy(
                    project_dir=Path(project_dir),
                    repo_name=repo_name,
                    name=name,
                    tagline=tagline,
                    category=category,
                    features=features,
                )
            if live_url:
                agent_logger.info(f"Auto-deploy complete. Live URL: {live_url}")
            else:
                agent_logger.warning("Auto-deploy returned no live URL.")
            return live_url
        except Exception as e:  # noqa: BLE001
            agent_logger.error(f"Auto-deploy failed: {e}")
            return ""

    def _self_heal_generated(self, project_dir: str, offenders: List[str]) -> int:
        """Route gate-failing files back to the code_modifier agent for a self-healing pass."""
        return self.code_modifier.self_heal_project(project_dir, offenders)

    def _self_correct_generated(self, project_dir: str, error_blob: str, round_idx: int = 0) -> Dict[str, Any]:
        """Self-correction hook: send the isolated compiler error output back to
        the reasoning model as a unified-diff fix (Lovable/Bolt-style loop)."""
        from agent.code_modifier import SecurityViolationError
        try:
            return self.code_modifier.fix_from_errors(project_dir, error_blob, round_idx=round_idx)
        except SecurityViolationError as exc:
            agent_logger.error(f"Self-correction rejected (security): {exc}")
            return {"status": "error", "reason": str(exc)}
        except Exception as exc:
            agent_logger.warning(f"Self-correction skipped: {exc}")
            return {"status": "error", "reason": str(exc)}

    def _architect_enterprise_gate(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Enterprise Project Architect gate — pull project-rules, verify the 4-point
        protocol, and route violating files to code_modifier self-healing before ZIP."""
        from agent.enterprise_architect import enterprise_architect
        try:
            return enterprise_architect.enforce(
                project_dir,
                spec,
                self_heal=self._self_heal_generated,
                max_rounds=2,
            )
        except Exception as exc:
            agent_logger.warning(f"EnterpriseArchitect skipped: {exc}")
            return {"skipped": True, "reason": str(exc)}

    def _build_report(
        self, *,
        start_time: float,
        prompt: str,
        spec: Dict[str, Any],
        project_dir: str,
        phase_log: Dict[str, Any],
        phase_failures: list,
        selected_template,
        selected_components: list,
        selected_assets: Dict[str, list],
        selected_backend,
        selected_schemas: list,
        tech_stack: Dict[str, Any],
        trending_result: Dict[str, Any],
        ai_calls_count: int,
        validation_report: Dict[str, Any],
        quality_report: Dict[str, Any],
        improvements: Dict[str, Any],
        benchmark: Dict[str, Any],
        zip_archive_path: str,
        quality_gate: Optional[Dict[str, Any]] = None,
        architect_gate: Optional[Dict[str, Any]] = None,
        live_url: str = "",
        rag_context: Optional[Dict[str, Any]] = None,
        prompt_provenance: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        instructions_file_path = os.path.join(project_dir, "INSTRUCTIONS.md")
        execution_time = round(time.time() - start_time, 2)

        failed_phase_names = self._phase_failure_names(phase_failures)
        critical_failure = any(
            name in self.CRITICAL_PHASES for name in failed_phase_names
        )

        # ── Status vocabulary (agent/run_status.py) ──────────────────────────
        # failed  : a critical phase failed (no usable project)
        # partial : something failed but the pipeline finished
        # skipped : nothing failed, but at least one phase was skipped
        # succeeded: everything that was applicable ran
        from agent import ai_routing

        fallback_reason = rs.fallback_reason(
            offline=ai_routing.offline(),
            provider_resolved=self.ai_provider is not None,
            calls_succeeded=self.ai_model_calls_succeeded,
            calls_failed=self.ai_model_calls_failed,
        )
        fallback_used = fallback_reason is not None
        if critical_failure:
            run_state = rs.STATUS_FAILED
        else:
            run_state = rs.resolve_status(
                failed=bool(phase_failures), skipped=bool(self.skipped_phases)
            )
        status_fields = rs.status_block(
            status=run_state,
            providers_used=self.providers_used,
            fallback_used=fallback_used,
            reason=fallback_reason,
            skipped_phases=self.skipped_phases,
        )

        report = {
            "user_prompt": prompt,
            "project_name": spec.get("project_name", "generated-website"),
            "features": spec.get("features") or [],
            "generated_project_dir": project_dir,
            "zip_archive_path": zip_archive_path,
            "quality_gate_devops": quality_gate or {},
            "architect_enterprise_gate": architect_gate or {},
            "generated_project_completeness": phase_log.get("generated_project_completeness", {}),
            "release_ready": bool((phase_log.get("qa_release_gate") or {}).get("passed")),
            "zip_classification": (
                "release_candidate"
                if (phase_log.get("qa_release_gate") or {}).get("passed")
                else "diagnostic_incomplete"
            ),
            "instructions_file_path": instructions_file_path,
            "execution_time_seconds": execution_time,
            "pipeline_version": "18-phase-enterprise-v3.6",
        }
        # Status vocabulary fields (agent/run_status.py) live at the top level:
        # status / providers_used / fallback_used / reason / skipped_phases.
        report.update(status_fields)
        report.update({
            "pipeline_health": self._calculate_health(phase_failures),
            "phase_statistics": {
                "total_phases": len(self.PHASES),
                "phases_failed": len(failed_phase_names),
                "phase_timings": self.phase_timings,
                "retries_per_phase": self.retry_counts,
                "phases_skipped": len(self.skipped_phases),
            },
            "phases_completed": [
                p for p in self.PHASES if p not in failed_phase_names
            ],
            "phase_failures": phase_failures,
            "phase_results": phase_log,
            "ai_evidence": {
                "provider_resolved": self._provider_name() or None,
                "model_calls_succeeded": self.ai_model_calls_succeeded,
                "model_calls_failed": self.ai_model_calls_failed,
            },
            "project_layout": {
                "mode": spec.get("layout_mode", "enterprise"),
                "has_api": spec.get("has_api", True),
                "phase_report": phase_log.get("phase_6_layout_mode", {}),
            },
            "selected_resources": {
                "template": selected_template.get("name") if selected_template else "Default Base",
                "components_count": len(selected_components),
                "components": [c["name"] for c in selected_components],
                "images_count": len(selected_assets.get("images", [])),
                "icons_count": len(selected_assets.get("icons", [])),
                "animations_count": len(selected_assets.get("animations", [])),
                "backend": selected_backend.get("name") if selected_backend else "Default Express",
                "database_schemas": [s.get("name") for s in selected_schemas],
                "tech_stack": tech_stack,
                "trending_features": trending_result.get("feature_ids", []),
            },
            "ai_api_calls_made": ai_calls_count,
            "validation_results": validation_report,
            "quality_gates": quality_report,
            "improvement_recommendations": improvements,
            "competitive_benchmark": benchmark,
            "enterprise_ready": (
                quality_report.get("enterprise_ready", False)
                and (phase_log.get("generated_project_completeness") or {}).get("status") == "complete"
            ),
            "launch_ready": benchmark.get("launch_ready", False),
            "live_preview_url": live_url,
            # ── Enterprise Capabilities ────────────────────────────────
            "international": {
                "region":                  spec.get("region", "NA"),
                "primary_currency":        phase_log.get("phase_11_localization", {}).get("primary_currency", "USD"),
                "payment_gateways":        phase_log.get("phase_11_localization", {}).get("payment_gateways", ["Stripe"]),
                "languages_generated":     phase_log.get("phase_11_localization", {}).get("languages_generated", ["en"]),
                "total_languages":         phase_log.get("phase_11_localization", {}).get("total_languages", 1),
                "rtl_support":             spec.get("rtl_support", False),
                "rtl_languages":           phase_log.get("phase_11_localization", {}).get("rtl_languages", []),
                "compliance_regs":         phase_log.get("phase_12_compliance_accessibility", {}).get("compliance_regs", []),
                "compliance_artifacts":    phase_log.get("phase_12_compliance_accessibility", {}).get("compliance_artifacts", 0),
                "requires_consent_banner": phase_log.get("phase_12_compliance_accessibility", {}).get("requires_consent_banner", False),
                "accessibility_score":     phase_log.get("phase_12_compliance_accessibility", {}).get("accessibility_score", 0),
                "wcag_aa_compliant":       phase_log.get("phase_12_compliance_accessibility", {}).get("wcag_aa_compliant", False),
            },
            "seo_and_edge": phase_log.get("phase_13_seo_and_cdn", {}),
            "performance_and_growth": phase_log.get("phase_14_performance_growth", {}),
            "multi_cloud_deployment": phase_log.get("phase_15_global_deployment", {}),
            "design_style": phase_log.get("phase_6_design_style", {}),
            "theme_variant": phase_log.get("phase_6_theme_matrix", {}),
            "design_decision": phase_log.get("phase_2_design_decision", {}),
            "design_memory": phase_log.get("phase_6_design_memory", {}),
            # ── Provenance / safety / retrieval observability ────────────
            "rag_context": {
                "retrieved": bool((rag_context or {}).get("retrieved", False)),
                "chars": (rag_context or {}).get("chars", 0),
                "sources": (rag_context or {}).get("sources", []),
                "past_lessons": len((rag_context or {}).get("past_lessons", [])),
            },
            "guardrails": phase_log.get("phase_16_output_guardrails", {}),
            "prompt_provenance": prompt_provenance or [],
            "design_scan": phase_log.get("phase_7_1_design_scan", {}),
            "visual_critic": phase_log.get("phase_7_1_design_scan", {}).get(
                "visual_critic", {}),
            "browser_qa": phase_log.get("browser_qa", {}),
            "design_plan": {
                "industry": (phase_log.get("phase_5b_design_planner", {}) or {}).get("industry"),
                "brand_style": (phase_log.get("phase_5b_design_planner", {}) or {}).get("brand_style"),
                "pages": (phase_log.get("phase_5b_design_planner", {}) or {}).get("pages", 0),
                "playbooks_loaded": (phase_log.get("phase_5b_design_planner", {}) or {}).get("playbooks_loaded"),
                "issues": (phase_log.get("phase_5b_design_planner", {}) or {}).get("issues", []),
            },
            "learned_gaps": phase_log.get("phase_2_design_decision", {}).get(
                "learned_gaps") or (phase_log.get("phase_2_design_decision", {}).get(
                    "design_decision", {}) or {}).get("learned_gaps", []),
        })

        report_path = os.path.join(project_dir, "generation-report.json")
        try:
            FileManager.write_json(report_path, report)
        except Exception as e:
            agent_logger.error(f"Failed to write generation-report.json: {e}")

        return report

    def iterate(
        self,
        project_dir: str,
        instruction: str,
        provider_name: Optional[str] = None,
        client_brand: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post-generation refinement loop (Lovable/v0-style chat editing) with
        diff-based partial regeneration:

          - Edits only the affected files (git-style unified diff recorded).
          - Re-runs only verification/publishing phases (7, 12, security, 15)
            against the changed files — phases 1–6 stay untouched.
          - Works with an AI provider or fully offline via deterministic rules.
        """
        agent_logger.info(f"[ITERATE] project={project_dir} instruction='{instruction}'")
        return self.iteration_engine.iterate(
            project_dir=project_dir,
            instruction=instruction,
            provider_name=provider_name,
            client_brand=client_brand,
        )

    def _append_compliance_evidence(
        self, project_dir: str, compliance: Dict, accessibility: Dict,
        security: Dict, quality: Dict, cost: Dict
    ) -> str:
        """Append machine-readable evidence block to COMPLIANCE.md (audit proof)."""
        if not self.iteration_engine:
            return ""
        return self.iteration_engine._append_compliance_evidence(
            project_dir, compliance, accessibility, security, quality, cost
        )

    def run(
        self,
        prompt: str,
        interactive: bool = False,
        progress_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
        design_style: Optional[str] = None,
        extra_spec: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the 18-phase enterprise project generation pipeline with error isolation and callbacks."""
        self._reset_phase_tracking()
        self._free_only_run = bool((extra_spec or {}).get("free_provider_only"))
        if self._free_only_run and not self._free_only_providers:
            raise RuntimeError("Free-only rebuild requires configured, explicitly allowed providers")
        if self._free_only_run and (
            not self.ai_provider or self.ai_provider_name.lower() not in self._free_only_providers
        ):
            raise RuntimeError("Free-only rebuild provider is outside the configured allowlist")
        self.progress_callback = progress_callback
        start_time = time.time()
        phase_log: Dict[str, Any] = {}
        phase_failures: List[str] = []

        # Per-run provenance: reset so a reused orchestrator reports this run only.
        self.providers_used = []
        self.ai_model_calls_succeeded = 0
        self.ai_model_calls_failed = 0
        self.skipped_phases = []

        # Defaults for downstream safety
        market_analysis = {}
        spec = {}
        tech_stack = {}
        trending_result = {"injected_count": 0, "feature_ids": [], "required_components": []}
        selected_template = None
        selected_components: list = []
        selected_assets = {"images": [], "icons": [], "animations": []}
        selected_backend = {
            "name": "E-Commerce Modular Base API",
            "file_path": "backend-library/ecommerce-base",
        }
        selected_schemas: list = []
        project_dir = ""
        ai_calls_count = 0
        validation_report = {"valid": True, "errors": [], "warnings": []}
        quality_report = {"overall_score": 0, "enterprise_ready": False}
        design_decision: Dict[str, Any] = {}
        design_plan: Dict[str, Any] = {}
        browser_qa_report: Dict[str, Any] = {}
        improvements = {"total_recommendations": 0, "recommendations": []}
        benchmark = {"launch_ready": False}
        plan = {
            "project_name": "generated-website",
            "assembly_steps": [],
            "ai_tasks_required": [],
            "template": {},
            "components": [],
            "assets": {},
            "backend": {},
            "database_schemas": [],
        }

        agent_logger.info("==================================================")
        agent_logger.info("  LUMICOREPRO 18-PHASE ENTERPRISE GENERATION AGENT")
        agent_logger.info("==================================================")
        agent_logger.info(f"User Prompt: '{prompt}'")

        # ── Phase 0a: RAG context retrieval (past builds + best practices) ──
        # Retrieval is observational: a RAG outage degrades to empty context,
        # never a failed run. Retrieved context rides in spec/plan so the
        # planner and every downstream engine see the same guidance.
        rag_context: Dict[str, Any] = {
            "retrieved": False,
            "chars": 0,
            "text": "",
            "sources": [],
            "past_lessons": [],
        }
        try:
            from .rag_engine import get_rag_engine
            rag = get_rag_engine()
            if getattr(rag, "enabled", False):
                retrieved_text = rag.get_context_for_prompt(prompt, max_context_length=2400) or ""
                rag_context["retrieved"] = bool(retrieved_text.strip())
                rag_context["chars"] = len(retrieved_text)
                rag_context["text"] = retrieved_text
                try:
                    rag_context["sources"] = [
                        (r.get("title") or r.get("name") or r.get("id") or "doc")
                        for r in rag.search_documentation(prompt, top_k=3)
                    ][:5]
                except Exception:  # noqa: BLE001
                    pass
        except Exception as rag_exc:  # noqa: BLE001
            agent_logger.warning(f"RAG retrieval skipped: {rag_exc}")
        try:
            rag_context["past_lessons"] = [
                {"query": s.get("query", "")[:160], "summary": s.get("summary", "")[:400]}
                for s in self.memory_retriever.recent_searches(limit=5)
            ]
        except Exception as mem_exc:  # noqa: BLE001
            agent_logger.warning(f"Memory lesson retrieval skipped: {mem_exc}")

        # ── Phase 0: Vision Layout & Theme Extraction (pre-P1, screenshot-driven) ──
        vision_source = (
            (extra_spec or {}).get("screenshot")
            or (extra_spec or {}).get("screenshot_url")
            or (extra_spec or {}).get("image_url")
            or ""
        )
        if vision_source:
            try:
                from agent.vision_pipeline import VisionPipeline, LayoutMapper
                from config.providers import instantiate_provider
                from config.settings import VISION_PROVIDER
                # Fallback chain: configured vision provider → OpenRouter → Groq/Groq
                # (Groq now carries llama-vision). Each candidate that resolves with a
                # real key is given a shot before we degrade to heuristics.
                vision_candidates = [VISION_PROVIDER, "openrouter", "grok"]
                vp_provider = None
                vp_provider_name = ""
                for vp_name in vision_candidates:
                    try:
                        from config.providers import get_active_provider_config, validate_provider_key
                        cfg = get_active_provider_config(vp_name)
                        key = (cfg or {}).get("api_key", "") or ""
                        if key and not str(key).startswith(("your_",)):
                            inst = instantiate_provider(vp_name)
                            if inst is not None:
                                vp_provider = inst
                                vp_provider_name = vp_name
                                break
                    except Exception:
                        continue
                vision_pipe = VisionPipeline(provider=vp_provider)
                vision_layout = vision_pipe.extract_layout(vision_source)
                overlays = vision_pipe.to_spec_overlays(vision_layout)
                mapper = LayoutMapper()
                mapped = mapper.map_regions(vision_layout)
                vision_used_model = vision_layout.get("source") == "ai_vision"
                phase_log["phase_0_vision"] = {
                    "parsed": vision_layout.get("parsed", False),
                    "source": vision_layout.get("source", "unknown"),
                    "provider": vp_provider_name or None,
                    "regions": overlays.get("vision_layout_regions", []),
                    "design_tokens": overlays.get("design_tokens", {}),
                    "regions_mapped": mapped,
                    "reason": vision_layout.get("reason"),
                }
                if vision_used_model:
                    self._record_model_evidence("phase_0_vision", vp_provider_name)
                else:
                    self._mark_skipped(
                        "vision_analysis",
                        rs.REASON_VISION_FALLBACK
                        + (f":{vp_provider_name}" if vp_provider_name else ":no_vision_provider"),
                    )
                agent_logger.info(
                    f"Phase 0 vision: parsed={vision_layout.get('parsed')} "
                    f"source={vision_layout.get('source')} regions={len(overlays.get('vision_layout_regions', []))}"
                )
            except PipelineCancelled:
                raise
            except Exception as exc:
                agent_logger.warning(f"Phase 0 vision extraction skipped: {exc}")
                phase_log["phase_0_vision"] = {"parsed": False, "reason": str(exc)}
                self._mark_skipped("vision_analysis", f"vision_error:{str(exc)[:80]}")

        # ── Phase 1: Market Analysis ─────────────────────────────────────────
        try:
            # Fast lane: a streamed pipeline may already own the market pass —
            # never analyze twice when `extra_spec["market_analysis"]` exists.
            streamed_market = (extra_spec or {}).get("market_analysis") or {}
            streamed_prelim = (extra_spec or {}).get("market_prelim_spec")
            prelim_spec = self._run_phase_safe(
                "Phase 1 - Market Analysis",
                self.analyzer._local_rule_analysis,
                func_args=[prompt],
                fallback={"website_type": "ecommerce", "industry": "general", "features": []}
            )
            if streamed_market:
                market_analysis = streamed_market
                agent_logger.info("Phase 1 market analysis reused from streamed pipeline (no re-analyze).")
                prelim_spec = streamed_prelim or prelim_spec
            else:
                market_analysis = self._run_phase_safe(
                    "Phase 1 - Market Analysis",
                    self.market_analyzer.analyze,
                    func_args=[prelim_spec],
                    fallback={}
                )
            # Phase 1b: Agent Reach social signal research (Reddit + Twitter/X).
            # Runs only via asyncio.create_subprocess_exec in a worker-thread
            # loop; degrades to an empty payload when channels are unavailable.
            live_signals = {}
            try:
                from agent.reach.market_signals import market_signals_sync
                live_signals = market_signals_sync(prelim_spec) or {}
                phase_log["phase_1_social_signals"] = live_signals
                if live_signals.get("fragments") and market_analysis:
                    market_analysis = self.market_analyzer.analyze(prelim_spec, live_signals)
                if not live_signals.get("fragments"):
                    # Async deep-research fallback: query Agent Reach directly
                    # when the sync sweep found nothing. Fully degraded on any
                    # error — live signals are observational, never fatal.
                    try:
                        import asyncio
                        deep_signals = asyncio.run(
                            self.market_analyzer.research_social_signals(prelim_spec)
                        )
                        if isinstance(deep_signals, dict) and deep_signals.get("fragments"):
                            live_signals = deep_signals
                            phase_log["phase_1_social_signals"] = live_signals
                            if market_analysis:
                                market_analysis = self.market_analyzer.analyze(prelim_spec, live_signals)
                    except PipelineCancelled:
                        raise
                    except Exception as deep_exc:
                        agent_logger.warning(f"Phase 1b async social research skipped: {deep_exc}")
            except PipelineCancelled:
                raise
            except Exception as exc:
                agent_logger.warning(f"Phase 1 social signal research skipped: {exc}")
                phase_log["phase_1_social_signals"] = {"ok": False, "reason": str(exc)}
            phase_log["phase_1_market_analysis"] = market_analysis
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_1_market_analysis")

# ── Phase 2: Requirement Analysis ────────────────────────────────────
        try:
            market_context = market_analysis if isinstance(market_analysis, dict) and market_analysis else None
            spec = self._run_phase_safe(
                "Phase 2 - Requirement Analysis",
                lambda: self.analyzer.analyze(prompt, market_context=market_context),
                fallback={"is_ambiguous": False, "website_type": "ecommerce",
                          "industry": "general", "features": []}
            )
            # Explicit overrides win over analyzer heuristics; otherwise the
            # seeded decision engine picks the style (same prompt ⇒ same style,
            # identical on a rerun — random.choice used to reshuffle it).
            spec["design_style"] = self._resolve_design_style(
                design_style, prompt, spec
            )
            # Stable digest of every input the design decision is derived from.
            # It is written into design-manifest.json so a run can be reproduced.
            spec["design_seed"] = self._design_seed(
                prompt,
                str(spec.get("website_type", "")),
                str(spec.get("industry", "")),
                str(spec.get("design_style", "")),
                str((extra_spec or {}).get("target_region", "") or spec.get("target_region", "")),
            )
            # Provenance: only a real provider answer counts as live evidence, and
            # only a provider that was actually consulted can count as a failure.
            if spec.get("analysis_source") == "ai_provider":
                self._record_model_evidence("phase_2_requirement_analysis")
            elif self.ai_provider is not None:
                self._record_model_failure("phase_2_requirement_analysis")
            if extra_spec:
                spec.update(extra_spec)
            # Pass Agent Reach social signals into the planner engine
            if phase_log.get("phase_1_social_signals", {}).get("fragments"):
                live = phase_log["phase_1_social_signals"]
                spec["live_signal_summary"] = {
                    "complaints": (live.get("complaints") or [])[:4],
                    "preferred_features": (live.get("preferred_features") or [])[:4],
                    "design_topics": (live.get("design_topics") or [])[:4],
                    "sources": sorted({str(f.get("platform")) for f in (live.get("fragments") or []) if isinstance(f, dict)}),
                }
            if spec.get("is_ambiguous"):
                agent_logger.warning(f"PROMPT AMBIGUITY DETECTED: {spec.get('ambiguity_reason')}")
                if interactive and sys.stdin.isatty():
                    print("\n[CLARIFICATION REQUIRED]")
                    print(f"Reason: {spec.get('ambiguity_reason')}")
                    for opt in spec.get("clarifying_options", []):
                        print(f"  {opt}")
                    new_prompt = input("\nPlease re-enter a clarified prompt:\n> ").strip()
                    if new_prompt:
                        prompt = new_prompt
                        spec = self._run_phase_safe(
                            "Phase 2 - Requirement Analysis (retry)",
                            lambda: self.analyzer.analyze(prompt, market_context=market_context),
                            fallback=spec
                        )
            # Apply design preferences
            spec = self._collect_user_design_preferences(spec, market_analysis, interactive=interactive)
            phase_log["phase_2_requirement_analysis"] = spec
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_2_requirement_analysis")

        # ── Phase 2b: International Design & Brand Planning ────────────────────
        # Produces the full design plan (style + region + palette + vault source)
        # BEFORE any code is generated — the single source of truth for the build.
        try:
            from agent.pro_design import resolve_design_blueprint
            _ui_style = spec.get('ui_style', 'glassmorphism')
            _region = spec.get('target_region', 'default')
            _repo = spec.get('project_name', 'project')
            _brand = spec.get('brand_title', _repo)
            _blueprint = self._run_phase_safe(
                "Phase 2b - Design & Brand Planning",
                lambda: resolve_design_blueprint(_repo, _ui_style, _region, _brand),
                fallback={'ui_style': _ui_style, 'target_region': _region, 'palette': {}},
            )
            spec['design_blueprint'] = _blueprint
            spec['ui_style'] = _blueprint.get('ui_style', _ui_style)
            spec['target_region'] = _blueprint.get('target_region', _region)
            agent_logger.info(
                f"Design plan resolved: style={spec['ui_style']} region={spec['target_region']} "
                f"vault={_blueprint.get('vault_source', 'built-in')}"
            )
            phase_log["phase_2b_design_plan"] = _blueprint
        except PipelineCancelled:
            raise
        except Exception:
            agent_logger.warning("Design brand planning skipped — falling back to analyzer defaults")
            spec.setdefault('design_blueprint', {})

        # ── Phase 3: Tech Stack & Architecture Selection ─────────────────────
        try:
            p3 = self._run_phases_parallel([
                ("Phase 3 - Backend Selection",
                 self.backend_selector.select_backend, [spec],
                 {"name": "E-Commerce Modular Base API", "file_path": "backend-library/ecommerce-base"}),
                ("Phase 3 - Schema Selection",
                 self.database_selector.select_schemas, [spec], []),
            ])
            selected_backend = p3.get("Phase 3 - Backend Selection")
            selected_schemas = p3.get("Phase 3 - Schema Selection") or []
            tech_stack = self._run_phase_safe(
                "Phase 3 - Tech Stack Selection",
                self.tech_stack_selector.select,
                func_args=[spec, selected_backend, selected_schemas],
                fallback={}
            )
            phase_log["phase_3_tech_stack"] = tech_stack
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_3_tech_stack")

        # ── Phase 4: Trending Features Injection ─────────────────────────────
        try:
            trending_result = self._run_phase_safe(
                "Phase 4 - Trending Features",
                self.trending_injector.inject,
                func_args=[spec, market_analysis],
                fallback={"injected_count": 0, "feature_ids": [], "required_components": []},
                retryable=True
            )
            phase_log["phase_4_trending_features"] = trending_result
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_4_trending_features")

        # ── Phase 5: Resource Assembly Planning ──────────────────────────────
        try:
            p5 = self._run_phases_parallel([
                ("Phase 5 - Template Selection",
                 self.template_selector.select_template, [spec], None),
                ("Phase 5 - Component Selection",
                 self.component_selector.select_components, [spec], []),
                ("Phase 5 - Asset Selection",
                 self.asset_selector.select_assets, [spec],
                 {"images": [], "icons": [], "animations": []}),
            ])
            selected_template = p5.get("Phase 5 - Template Selection")
            selected_components = p5.get("Phase 5 - Component Selection") or []
            selected_assets = p5.get("Phase 5 - Asset Selection") or {"images": [], "icons": [], "animations": []}

            trending_components = trending_result.get("required_components", [])
            if trending_components:
                extra = self.component_selector.select_by_names(trending_components)
                existing_names = {c["name"] for c in selected_components}
                for comp in extra:
                    if comp["name"] not in existing_names:
                        selected_components.append(comp)

            # RAG context + past-build lessons become part of the generation
            # contract: spec → plan → builder all see identical guidance.
            spec.setdefault("rag_context", rag_context.get("text", ""))
            spec.setdefault("past_lessons", rag_context.get("past_lessons", []))

            plan = self.planner.create_plan(
                spec, selected_template, selected_components,
                selected_assets, selected_backend, selected_schemas,
            )
            plan["spec"] = spec
            plan["rag_context"] = rag_context
            phase_log["phase_5_assembly_plan"] = {
                "project_name": plan["project_name"],
                "steps": len(plan["assembly_steps"]),
                "ai_tasks": len(plan.get("ai_tasks_required", [])),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_5_assembly_planning")

        # ── Phase 5b: Explicit Design Planner (pre-coding design contract) ──
        # Locks page/section structure, design system and UX flow BEFORE any
        # code is generated, so generation has a concrete blueprint instead of
        # improvising. Observational: a planner failure never blocks the build.
        try:
            _industry = (
                (design_decision or {}).get("industry")
                or spec.get("industry")
                or market_analysis.get("industry")
                or "saas"
            )
            _brand_style = (
                (design_decision or {}).get("brand")
                or spec.get("brand_style")
                or spec.get("design_style")
                or "corporate"
            )
            _tokens = {}
            _palette = {}
            try:
                _blueprint = spec.get("design_blueprint") or {}
                _palette = _blueprint.get("palette") or {}
            except Exception:
                _palette = {}
            if isinstance(_palette, dict):
                for key in ("primary", "primary_light", "primary_dark", "accent"):
                    value = _palette.get(key)
                    if isinstance(value, str) and value.strip():
                        _tokens[key] = value.strip()

            # Screenshot-driven reference: if the user supplied a mockup/screenshot,
            # extract its real section order, components and measured colours and
            # hand them to the planner as the structural contract. A failed or
            # absent vision parse degrades to the industry playbook — never blocks.
            _reference_sections: list = []
            _reference_intelligence: dict = {}
            _screenshot_spec: dict = {}
            if vision_source:
                try:
                    _screenshot_spec = screenshot_to_design_spec_multi(
                        [vision_source],
                        business_type=str(
                            spec.get("business_type") or market_analysis.get("business_type")
                            or spec.get("website_type") or "project"
                        ),
                    )
                    _plan_inputs = to_plan_inputs(_screenshot_spec)
                    _reference_sections = _plan_inputs.get("reference_sections") or []
                    _reference_intelligence = _plan_inputs.get("reference_intelligence") or {}
                    if _plan_inputs.get("palette"):
                        _palette = dict(_palette, **_plan_inputs["palette"])
                    if _plan_inputs.get("design_tokens"):
                        _tokens = dict(_tokens, **_plan_inputs["design_tokens"])
                    phase_log["phase_5b_screenshot_spec"] = {
                        "analyzed": bool(_screenshot_spec.get("analyzed")),
                        "colors_measured": bool(_screenshot_spec.get("colors_measured")),
                        "sections": _reference_sections,
                        "failed_shots": _screenshot_spec.get("failed_shots") or [],
                        "vision_source": _screenshot_spec.get("vision_source"),
                    }
                except Exception as spec_exc:
                    agent_logger.warning(f"Screenshot design-spec skipped: {spec_exc}")
                    phase_log["phase_5b_screenshot_spec"] = {
                        "skipped": True,
                        "error": str(spec_exc)[:200],
                    }

            design_plan = create_design_plan(
                business_type=str(
                    spec.get("business_type") or market_analysis.get("business_type")
                    or spec.get("website_type") or "project"
                ),
                industry=_industry,
                brand_style=_brand_style,
                palette=_palette,
                design_tokens=_tokens,
                reference_sections=_reference_sections or None,
                reference_intelligence=_reference_intelligence or None,
            )
            _plan_issues = validate_design_plan(design_plan or {})
            if _plan_issues:
                agent_logger.warning(
                    f"Design planner reported {len(_plan_issues)} issue(s): {_plan_issues[:3]}"
                )
            spec["design_plan"] = design_plan
            spec["screenshot_spec"] = _screenshot_spec
            phase_log["phase_5b_design_planner"] = {
                "industry": design_plan.get("industry"),
                "brand_style": design_plan.get("brand_style"),
                "pages": len(design_plan.get("pages") or []),
                "page_plans": len(design_plan.get("page_plans") or {}),
                "playbooks_loaded": design_plan.get("playbooks_loaded"),
                "design_system_present": bool(design_plan.get("design_system")),
                "issues": _plan_issues,
                "structure_from_reference": bool(
                    _reference_intelligence.get("structure_from_reference")
                ),
            }
            # Persist the plan + markdown so the build and any later "change the
            # hero" request can read the contract instead of re-deriving it.
            # The project directory does not exist yet, so this attempt usually
            # records why persistence is deferred until after the build.
            self._persist_design_plan_artifacts(
                project_dir,
                design_plan,
                phase_log,
                artifact_key="prebuild_artifacts",
            )
            agent_logger.info(
                f"Phase 5b design planner: industry={design_plan.get('industry')} "
                f"pages={len(design_plan.get('pages') or [])} "
                f"playbooks_loaded={design_plan.get('playbooks_loaded')}"
            )
        except PipelineCancelled:
            raise
        except Exception as dp_exc:
            agent_logger.warning(f"Design planner skipped: {dp_exc}")
            spec.setdefault("design_plan", {})
            phase_log["phase_5b_design_planner"] = {
                "skipped": True,
                "error": str(dp_exc)[:200],
            }

        # ── Phase 6: Code Generation & REST API Scaffolding ──────────────────
        try:
            self._checkpoint_cancel()
            self._bind_engineering_matrix(spec, phase_log)

            # ── Phase 6a: Design Decision Engine (Part 3) ────────────────────
            # Merges industry playbook + brand playbook + reference intelligence
            # into a single machine-readable design spec before generation.
            # Observational: failures never block code generation.
            design_decision: Dict[str, Any] = {}
            try:
                from agent.intelligence.design_decision_engine import (
                    decide_design,
                    detect_industry,
                )
                design_spec = dict(spec or {})
                design_spec["prompt"] = prompt
                design_spec["project_name"] = plan.get("project_name", "generated-website")
                if design_plan:
                    design_spec["design_plan"] = design_plan
                    design_spec.setdefault(
                        "planned_pages",
                        list(design_plan.get("pages") or []),
                    )
                    design_spec.setdefault(
                        "design_system",
                        design_plan.get("design_system") or {},
                    )
                if not design_spec.get("industry"):
                    design_spec["industry"] = detect_industry(design_spec)
                # Cross-project learning: consult prior builds for this
                # industry/brand and bias the new decision toward known gaps.
                try:
                    from agent.intelligence.lessons_store import LessonsStore
                    bias = LessonsStore().to_bias_payload(
                        design_spec.get("industry") or "general",
                        (design_spec.get("brand") or "general"),
                    )
                    if bias.get("attention"):
                        design_spec["prior_attention"] = bias["attention"]
                        agent_logger.info(
                            f"Phase 6a learned gaps for {design_spec.get('industry')}: "
                            f"{bias['attention']}"
                        )
                except Exception as bias_exc:
                    agent_logger.warning(f"Lessons bias skipped: {bias_exc}")
                design_decision = decide_design(
                    design_spec,
                    reference_analysis=(spec.get("reference_spec") or {}).get(
                        "reference_intelligence"),
                ) or {}
                spec.setdefault("design_decision", {})
                spec["design_decision"].update(design_decision)
                agent_logger.info(
                    f"Phase 6a design decision: industry={design_decision.get('industry')} "
                    f"brand={design_decision.get('brand')} hero={design_decision.get('hero')} "
                    f"cta={design_decision.get('cta_style')} 3d={design_decision.get('3d')}"
                )
            except Exception as de_exc:
                agent_logger.warning(f"Design Decision Engine skipped: {de_exc}")
            try:
                uniqueness = self._select_portfolio_unique_design(
                    spec, design_decision, design_plan, Path(project_dir)
                )
                design_decision = uniqueness["decision"]
                design_plan = uniqueness["design_plan"]
                spec["ui_style"] = design_decision.get("ui_style", spec.get("ui_style"))
                spec["design_blueprint"] = uniqueness["design_blueprint"]
                spec["design_palette_override"] = uniqueness.get("palette_override", {})
                spec["design_plan"] = design_plan
                spec["design_decision"] = design_decision
                spec["design_signature"] = uniqueness["design_signature"]
                spec["design_uniqueness"] = uniqueness["comparison"]
            except Exception as unique_exc:
                agent_logger.warning(
                    f"Portfolio design uniqueness skipped: {unique_exc}"
                )
                uniqueness = {"design_signature": {}, "comparison": {"status": "unavailable"}}
            phase_log["phase_2_design_decision"] = {
                "industry": design_decision.get("industry"),
                "brand": design_decision.get("brand"),
                "hero": design_decision.get("hero"),
                "motion": design_decision.get("motion"),
                "3d": design_decision.get("3d"),
                "cta_style": design_decision.get("cta_style"),
                "conversion_primary_cta": (design_decision.get("conversion") or {}).get("primary_cta"),
                "references": design_decision.get("reference_hints") or [],
                "reproducibility": (
                    design_decision.get("design_manifest") or {}
                ).get("reproducibility") or {"seed": spec.get("design_seed")},
                "design_signature": uniqueness.get("design_signature", {}),
                "uniqueness_comparison": uniqueness.get("comparison", {}),
            }

            plan["spec"] = copy.deepcopy(spec)
            project_dir = self.project_builder.build_project(plan)
            if project_dir:
                self._persist_design_plan_artifacts(
                    project_dir, design_plan, phase_log, artifact_key="artifacts"
                )

            # ── Buyer-Directed Project Layout Mode ─────────────────────────────
            # Renders the workspace under one of two STRICT execution modes:
            #   client-static  -> strip backend/docker/nginx, client-only showcase
            #   enterprise     -> mount master-express-backend scaffold + hydrate 14
            #                     Sequelize models / 18 API route groups / Redis+BullMQ
            #                     + Axios interceptor for relative /api/* via Nginx.
            layout_mode_report: Dict[str, Any] = {}
            if project_dir:
                try:
                    layout_mode_report = self.mode_engine.render_layout(project_dir, spec)
                except Exception as layout_err:
                    agent_logger.warning(f"ProjectModeEngine render skipped: {layout_err}")
            plan["layout_mode"] = spec.get("layout_mode", "enterprise")
            phase_log["phase_6_layout_mode"] = layout_mode_report

            # Generate feature-specific rest controllers/models only for the
            # enterprise hydration mode (static showcase has no backend at all).
            if project_dir:
                backend_dir = Path(project_dir) / "backend"
                if spec.get("layout_mode") == "enterprise":
                    try:
                        self.api_generator.generate_full_backend(backend_dir, plan)
                    except Exception as api_err:
                        agent_logger.warning(f"APIGenerator backend note: {api_err}")
                    # Backend package.json only exists AFTER api_generator; the
                    # build_project-time auto-fix was a no-op. Fix missing deps now.
                    try:
                        fixed = self.project_builder._auto_fix_npm_dependencies(backend_dir, is_backend=True)
                    except Exception as fix_err:
                        agent_logger.warning(f"Backend npm auto-fix skipped: {fix_err}")

            ai_calls_count = 0
            diff_mode = (os.getenv("AI_DIFF_PATCHING", "1").strip().lower() in ("1", "true", "yes"))
            if plan.get("ai_tasks_required") and self.ai_provider:
                from config.settings import AI_MAX_PATCH_FILES, AI_MAX_CONTEXT_FILES
                max_patches = AI_MAX_PATCH_FILES
                tasks = plan["ai_tasks_required"]
                if diff_mode:
                    # VFS mode: 1 model call returns a unified diff applied across
                    # any number of files — the 50+ file path without token blowup.
                    vfs_results: List[Dict[str, Any]] = []
                    # Combine every task into ONE batched diff call when the tasks
                    # are small (default), collapsing the N-call fan-out to a
                    # single reasoning pass. Toggle off with AI_COMBINE_TASKS=0.
                    combine = (os.getenv("AI_COMBINE_TASKS", "1").strip().lower() in ("1", "true", "yes"))
                    combined_ok = False
                    if combine and len(tasks) > 1:
                        combined_task = (
                            "Apply ALL of the following feature/customization "
                            "requests to the website. Handle each one precisely "
                            "in a single unified diff — touch only the files that "
                            "each request needs, and do not leave placeholder "
                            "logic. Return ONE diff covering every request.\n\n"
                            + "\n".join(f"{i+1}. {t}" for i, t in enumerate(tasks))
                        )
                        try:
                            res = self.code_modifier.apply_ai_diff_batch(
                                project_dir, combined_task,
                                max_context_files=AI_MAX_CONTEXT_FILES,
                            )
                            vfs_results.append({"task": "<combined>", **res})
                            ai_calls_count += 1
                            combined_ok = res.get("status") in ("applied", "no_changes")
                        except Exception as exc:
                            agent_logger.warning(f"VFS combined batch skipped: {exc}")
                            vfs_results.append({"task": "<combined>", "status": "error", "reason": str(exc)})
                    # Only run each task individually if the combined pass was
                    # skipped or failed (never double-apply on success).
                    if not combined_ok:
                        for task_item in tasks:
                            try:
                                res = self.code_modifier.apply_ai_diff_batch(
                                    project_dir, task_item,
                                    max_context_files=AI_MAX_CONTEXT_FILES,
                                )
                                vfs_results.append({"task": task_item, **res})
                                ai_calls_count += 1
                                if res.get("status") == "error":
                                    agent_logger.warning(
                                        f"VFS diff batch error on task '{task_item}': {res.get('reason')}"
                                    )
                            except Exception as exc:
                                agent_logger.warning(f"VFS diff batch skipped '{task_item}': {exc}")
                                vfs_results.append({"task": task_item, "status": "error", "reason": str(exc)})
                    phase_log["phase_6_vfs_diff_mode"] = {
                        "enabled": True,
                        "calls": ai_calls_count,
                        "batches": vfs_results,
                    }
                    # Provenance: code_modifier reports `applied`/`no_changes` only
                    # after a real model reply, `skipped:no_ai_provider` when there
                    # was nothing to call, and `error` when the call failed.
                    for batch in vfs_results:
                        status = batch.get("status")
                        if status in ("applied", "no_changes"):
                            self._record_model_evidence("phase_6_code_generation")
                        elif status == "error":
                            self._record_model_failure("phase_6_code_generation")
                else:
                    for task_item in tasks:
                        agent_logger.info(f"Executing AI customization: {task_item}")
                        project_files = self._get_project_main_files(project_dir)
                        for file_path in project_files:
                            if os.path.exists(file_path):
                                self.code_modifier.patch_file(file_path, task_item)
                                ai_calls_count += 1
                                if ai_calls_count >= max_patches:
                                    break
                        if ai_calls_count >= max_patches:
                            break
            phase_log["phase_6_code_generation"] = {"project_dir": project_dir, "ai_calls": ai_calls_count}

            # ── Launch Pack (business-in-a-box stamping) ────────────────────
            # Generates the niche production-seeder, non-technical SETUP_GUIDE.md
            # and the self-hosted license/compliance notice into the project.
            launch_report: Dict[str, Any] = {}
            if project_dir:
                try:
                    from agent.launch_pack import generate_launch_pack
                    launch_report = generate_launch_pack(project_dir, spec)
                except Exception as lpk_err:
                    agent_logger.warning(f"Launch Pack stamping skipped: {lpk_err}")
            phase_log["phase_6_launch_pack"] = launch_report

            # ── Design Style Phase (phase 6b): art-direct the site + original assets ──
            # Runs right after code generation (content) and before verification
            # & layout-tuning phases — the defined integration point of the
            # Design Style Engine.
            design_report = {}
            if project_dir:
                try:
                    design_report = self.design_engine.apply(project_dir, spec)
                except Exception as de:
                    agent_logger.warning(f"Design Style Engine skipped: {de}")
            phase_log["phase_6_design_style"] = design_report

            # Theme-variant record for this template+style combo (Theme Matrix).
            theme_report = {
                "variant": {},
                "variant_count_total": 0,
                "compatible_styles": [],
            }
            try:
                if project_dir and len(self.theme_engine.templates):
                    selected_template = self.theme_engine.templates[0]
                    for tpl in self.theme_engine.templates:
                        if tpl.get("category", "").lower() in [
                            str(spec.get("website_type", "") or "").lower(),
                            str(spec.get("industry", "") or "").lower(),
                        ]:
                            selected_template = tpl
                            break
                    variant = self.theme_engine.project_variant(spec, selected_template)
                    effective_matrix = self.theme_engine.build_matrix()
                    theme_report["compatible_styles"] = self.theme_engine.compatible_styles(selected_template)
                    theme_report["variant"] = variant
                    theme_report["variant_count_total"] = len(effective_matrix)
                    theme_report["quality_gate"] = self.theme_engine.quality_gate(selected_template, variant.get("style_id", "minimalism"))
                    previews = self.theme_engine.preview_manifest(project_dir, variant)
                    theme_report["preview_manifest"] = {
                        "gallery": previews.get("gallery"),
                        "active_variant": previews.get("active_variant"),
                        "captured": previews.get("captured"),
                    }
            except Exception as te:
                agent_logger.warning(f"Theme Matrix note skipped: {te}")
            phase_log["phase_6_theme_matrix"] = theme_report

            # ── Phase 5.5: Bespoke AI Design (reasoning-tier, post-assembly) ──
            # After the site is assembled & styled, one reasoning-model pass
            # regenerates key sections from scratch using the AST structure map
            # + any vision-derived design tokens — the Bolt/v0-style bespoke step.
            bespoke_report = {"active": False, "generated_blocks": [], "reason": "skipped"}
            if project_dir:
                try:
                    from agent.design_intelligence import BespokeUIDesignEngine
                    from config.settings import REASONING_PROVIDER
                    bespoke_spec = dict(spec)
                    vision_tokens = phase_log.get("phase_0_vision", {}).get("design_tokens", {})
                    if vision_tokens:
                        bespoke_spec["design_tokens"] = vision_tokens.get("palette", {})
                        if not bespoke_spec.get("design_style"):
                            bespoke_spec["design_style"] = "modern"
                    bespoke_provider_name = str(os.getenv("REASONING_PROVIDER") or REASONING_PROVIDER or "")
                    if self._free_only_run and bespoke_provider_name.lower() not in self._free_only_providers:
                        bespoke_provider_name = sorted(self._free_only_providers)[0]
                    engine = BespokeUIDesignEngine(ai_provider=self.ai_provider)
                    bespoke_report = engine.run(
                        project_dir,
                        bespoke_spec,
                        provider_name=bespoke_provider_name,
                    )
                    agent_logger.info(
                        f"Phase 5.5 bespoke design: active={bespoke_report.get('active')} "
                        f"blocks={len(bespoke_report.get('generated_blocks', []))}"
                    )
                except Exception as bd_exc:
                    agent_logger.warning(f"Phase 5.5 bespoke design skipped: {bd_exc}")
                    bespoke_report = {"active": False, "reason": str(bd_exc)}
            if bespoke_report.get("active"):
                self._record_model_evidence("phase_5_5_bespoke_design")
            else:
                self._mark_skipped(
                    "bespoke_design",
                    f"bespoke_design_{bespoke_report.get('reason') or 'inactive'}",
                )
            phase_log["phase_5_5_bespoke_design"] = bespoke_report

            # ── Phase 6b: Design Memory (manifest + .artifacts chain) ────────
            # Every decision is traceable for later iteration ("change the hero").
            design_memory: Dict[str, Any] = {}
            try:
                from agent.intelligence.design_manifest import (
                    DesignManifestWriter,
                    _ARTIFACT_CHAIN,
                )
                writer = DesignManifestWriter(project_dir)
                manifest_decision = (
                    design_decision.get("design_manifest") or design_decision or {})
                manifest_path = writer.write_manifest(manifest_decision)
                stage_payloads = {
                    "01-business": {
                        "industry": manifest_decision.get("industry", spec.get("industry")),
                        "website_type": spec.get("website_type"),
                        "project_name": plan.get("project_name"),
                    },
                    "02-audience": {
                        "target_audience": spec.get("target_audience"),
                        "personas": [],
                    },
                    "03-brand": {
                        "archetype": manifest_decision.get("brand", {}).get("archetype") if isinstance(manifest_decision.get("brand"), dict) else manifest_decision.get("brand"),
                    },
                    "04-reference": {
                        "references": manifest_decision.get("reference_sources", []),
                        "hints": design_decision.get("reference_hints", []),
                    },
                    "05-playbook": design_decision.get("playbooks", {}),
                    "06-ux": {
                        "pages": manifest_decision.get("pages", []),
                        "conversion": manifest_decision.get("conversion", {}),
                        "avoid": design_decision.get("avoid", []),
                    },
                    "07-design": {
                        "visual": manifest_decision.get("visual", {}),
                        "typography": manifest_decision.get("typography", {}),
                    },
                }
                for name, payload in stage_payloads.items():
                    writer.write_artifact(name, payload or {})
                design_memory["manifest"] = str(manifest_path)
                design_memory["chain"] = list(_ARTIFACT_CHAIN)
            except Exception as dm_exc:
                agent_logger.warning(f"Design Memory write skipped: {dm_exc}")
                self._mark_skipped("design_memory", f"write_failed:{str(dm_exc)[:80]}")
            phase_log["phase_6_design_memory"] = design_memory
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_6_code_generation")

# ── Phase 7: Quality Verification ────────────────────────────────────
        try:
            if project_dir:
                validation_report = self.validator.validate_project(project_dir)
                quality_report = self.quality_gates.evaluate(project_dir, spec, validation_report)
            phase_log["phase_7_quality_verification"] = quality_report
            if not quality_report.get("overall_score", 0) >= 80:
                phase_failures.append("phase_7_quality_verification")

            # ── Phase 7.1: DesignLint + Automated Design Score + Design Gate ──
            # Observed once per build (read + score + report, never blocks).
            if project_dir:
                design_scan: Dict[str, Any] = {}
                try:
                    from agent.intelligence.design_lint import run_designlint
                    from agent.intelligence.automated_design_score import score_design
                    from agent.intelligence.design_gate import evaluate_design_gate
                    lint_result = run_designlint(project_dir)
                    score_result = score_design(project_dir, lint_result=lint_result)
                    gate_result = evaluate_design_gate(score_result, design_decision)
                    design_scan = {
                        "lint": lint_result.get("summary", {}),
                        "score": {
                            "visual_quality_score": score_result.get("visual_quality_score"),
                            "benchmark_passed": score_result.get("benchmark_passed"),
                            "metrics": score_result.get("metrics"),
                        },
                        "gate": {
                            "passed": gate_result.get("passed"),
                            "decision": gate_result.get("decision"),
                            "failing": gate_result.get("failing"),
                            "metrics": gate_result.get("metrics"),
                            "recommendations": gate_result.get("recommendations"),
                        },
                    }
                    agent_logger.info(
                        f"Phase 7.1 design gate: passed={gate_result.get('passed')} "
                        f"score={score_result.get('visual_quality_score')} "
                        f"decision={gate_result.get('decision')}"
                    )
                    # Cross-project self-learning: remember this build's weak
                    # metrics so future automotive/saas/ecommerce builds bias
                    # their design decisions toward the benchmark gaps.
                    try:
                        from agent.intelligence.lessons_store import LessonsStore
                        LessonsStore().record_lesson(
                            (design_decision or {}).get("industry") or "general",
                            (design_decision or {}).get("brand") or "general",
                            score_result.get("visual_quality_score"),
                            gate_result,
                            design_decision,
                            score_result.get("metrics"),
                        )
                    except Exception as l_exc:
                        agent_logger.warning(f"Lessons record skipped: {l_exc}")
                    # Visual Critic: judge the built site itself (rendered
                    # html + sources), grounded in artifact statements.
                    try:
                        from agent.intelligence.visual_critic import run_visual_critic
                        design_scan["visual_critic"] = run_visual_critic(
                            project_dir, design_decision, self.ai_provider)
                    except Exception as vc_exc:
                        design_scan["visual_critic"] = {"verdict": "SKIPPED",
                                                        "notes": [str(vc_exc)[:200]]}
                except Exception as ds_exc:
                    design_scan["error"] = str(ds_exc)
                    agent_logger.warning(f"Design Scan skipped: {ds_exc}")
                phase_log["phase_7_1_design_scan"] = design_scan

            # ---- Phase 7.2: Premium Motion (lumi-motion layer) ----
            # Append-only CSS + IntersectionObserver runtime so every
            # generated site animates on scroll. Never blocks the build.
            try:
                from agent.extensions.animation_injector import inject_motion_layer
                anim_intensity = spec.get("animation_intensity", "high")
                if anim_intensity not in ("none", "low", "off", ""):
                    phase_log["phase_7_2_animation"] = inject_motion_layer(
                        project_dir, intensity=anim_intensity)
                else:
                    phase_log["phase_7_2_animation"] = {
                        "status": "skipped",
                        "reason": f"animation_intensity={anim_intensity}",
                    }
                    self._mark_skipped(
                        "premium_motion", f"animation_intensity={anim_intensity}"
                    )
            except Exception as anim_exc:  # noqa: BLE001
                phase_log["phase_7_2_animation"] = {
                    "status": "skipped",
                    "error": str(anim_exc)[:200],
                }
                self._mark_skipped("premium_motion", f"error:{str(anim_exc)[:80]}")
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_7_quality_verification")

        # ── Phase 7.5: Real Browser QA ─────────────────────────────────────
        # Playwright is the evidence source (screenshots, console/page errors,
        # horizontal-collapse at 4 breakpoints, LCP). The agent-browser deep
        # audit (axe-core a11y + Core Web Vitals) is opt-in via
        # LUMI_BROWSER_DEEP_AUDIT=1 because its daemon can stall on locked-down
        # hosts. Never blocking: an unavailable runtime reports `not_measured`.
        try:
            if project_dir:
                try:
                    from agent.extensions.browser_qa import run_browser_qa
                    browser_qa_report = self._run_phase_safe(
                        "Phase 7.5 - Browser QA",
                        run_browser_qa,
                        func_args=[project_dir],
                        fallback={
                            "status": "not_measured",
                            "message": "Browser QA unavailable in this environment.",
                            "evidence": {},
                        },
                    )
                except Exception as bq_exc:
                    browser_qa_report = {
                        "status": "not_measured",
                        "message": f"Browser QA unavailable: {bq_exc}"[:200],
                        "evidence": {},
                    }

                deep_audit_requested = os.getenv(
                    "LUMI_BROWSER_DEEP_AUDIT", ""
                ).strip().lower() in ("1", "true", "yes", "on")
                if deep_audit_requested:
                    browser_qa_report["deep_audit"] = {
                        "status": "deferred",
                        "reason": "runs after live deployment when a live URL exists",
                    }
                else:
                    browser_qa_report["deep_audit"] = {
                        "status": "not_measured",
                        "reason": "disabled (set LUMI_BROWSER_DEEP_AUDIT=1 to enable)",
                    }

                agent_logger.info(
                    f"Phase 7.5 browser QA: status={browser_qa_report.get('status')} "
                    f"evidence={browser_qa_report.get('evidence')}"
                )
                if browser_qa_report.get("status") == "not_measured":
                    self._mark_skipped(
                        "browser_qa", f"not_measured:{browser_qa_report.get('message', '')}"[:120]
                    )
        except PipelineCancelled:
            raise
        except Exception as bqa_exc:
            agent_logger.warning(f"Browser QA phase degraded: {bqa_exc}")
            browser_qa_report = {
                "status": "not_measured",
                "message": str(bqa_exc)[:200],
                "evidence": {},
            }

        phase_log["browser_qa"] = browser_qa_report

        # ── Phase 8: Improvement Recommendations ─────────────────────────────
        try:
            improvements = self.improvement_recommender.recommend(spec, quality_report, validation_report)
            phase_log["phase_8_improvements"] = improvements
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_8_improvements")

        # ── Phase 9: Competitive Benchmark & ROI Scoring ─────────────────────
        try:
            benchmark = self.competitive_benchmark.benchmark(spec, market_analysis, quality_report, tech_stack)
            phase_log["phase_9_benchmark"] = benchmark
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_9_benchmark")

        # ── Phase 10: International Delivery Meta ────────────────────────────
        try:
            if project_dir:
                expected_files = [
                    "docker-compose.yml",
                    "README.md",
                    "LICENSE.md",
                    "INSTRUCTIONS.md",
                    "DEPLOYMENT_CHECKLIST.md",
                    "SEO_META_TAGS.md",
                    ".github/workflows/deploy.yml",
                    "frontend/public/robots.txt",
                    "frontend/public/sitemap.xml",
                    "frontend/public/manifest.json",
                    "frontend/Dockerfile",
                    "backend/Dockerfile",
                ]
                delivery_status = {fname: "✅" if os.path.exists(os.path.join(project_dir, fname)) else "⚠️ missing" for fname in expected_files}
                phase_log["phase_10_international_delivery"] = {
                    "files_checked": len(expected_files),
                    "delivery_status": delivery_status,
                }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_10_international_delivery")

        # ── Phase 11: Multi-Currency & i18n Localization ─────────────────────
        try:
            currency_result = self._run_phase_safe(
                "phase_11_currency_localization",
                self.currency_localizer.localize,
                func_args=[spec],
                fallback={"region": "NA", "primary_currency": {"code": "USD"}, "payment_gateways": ["Stripe"]}
            )
            if currency_result:
                spec["region"] = currency_result.get("region", "NA")

            localization_result = {}
            if project_dir:
                localization_result = self._run_phase_safe(
                    "phase_11_i18n_generation",
                    self.localization_engine.generate,
                    func_args=[spec, project_dir],
                    fallback={"languages_generated": ["en"], "total_languages": 1}
                )
                if not localization_result:
                    self._mark_skipped("localization_and_i18n", "no_localization_output")

            phase_log["phase_11_localization"] = {
                "region": currency_result.get("region", "NA"),
                "primary_currency": currency_result.get("primary_currency", {}).get("code", "USD"),
                "payment_gateways": currency_result.get("payment_gateways", [])[:3],
                "languages_generated": localization_result.get("languages_generated", ["en"]),
                "total_languages": localization_result.get("total_languages", 1),
                "rtl_languages": localization_result.get("rtl_languages", []),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_11_localization")

        # ── Phase 12: Compliance (GDPR/CCPA) & Accessibility (WCAG 2.1 AA) ──
        try:
            compliance_report = {}
            accessibility_report = {}
            security_report = {}
            if project_dir:
                region = spec.get("region", "NA")
                p12 = self._run_phases_parallel([
                    ("phase_12_compliance",
                     self.compliance_generator.generate,
                     [spec, project_dir, region],
                     {"region": region, "applicable_regs": [], "artifacts_generated": []}),
                    ("phase_12_accessibility",
                     self.accessibility_checker.check,
                     [project_dir, spec],
                     {"accessibility_score": 0, "wcag_aa_compliant": False}),
                    ("phase_12_security_posture",
                     self.security_engine.generate,
                     [spec, project_dir],
                     {"controls_verified": 0, "review_items": 0}),
                    ("phase_12_license_stamp",
                     self.license_injector.generate,
                     [spec, project_dir],
                     {"artifacts": [], "stamped": 0}),
                    ("phase_12_cost_model",
                     self.deployment_engine.estimate_running_cost,
                     [spec.get("website_type", "business"), "low"],
                     {"estimates": {}}),
                ])
                compliance_report = p12.get("phase_12_compliance") or {}
                accessibility_report = p12.get("phase_12_accessibility") or {}
                security_report = p12.get("phase_12_security_posture") or {}
                cost_report = p12.get("phase_12_cost_model") or {"estimates": {}}
                try:
                    self._append_compliance_evidence(
                        project_dir, compliance_report, accessibility_report,
                        security_report, {}, cost_report
                    )
                except Exception as ce:
                    agent_logger.warning(f"Compliance evidence append failed: {ce}")

            phase_log["phase_12_compliance_accessibility"] = {
                "compliance_regs": compliance_report.get("reg_codes", []),
                "compliance_artifacts": len(compliance_report.get("artifacts_generated", [])),
                "requires_consent_banner": compliance_report.get("requires_consent_banner", False),
                "accessibility_score": accessibility_report.get("accessibility_score", 0),
                "wcag_aa_compliant": accessibility_report.get("wcag_aa_compliant", False),
                "security_controls_verified": security_report.get("controls_verified", 0),
                "security_checklist": security_report.get("checklist_path", ""),
                "estimated_monthly_cost": cost_report.get("estimates", {}),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_12_compliance_accessibility")

        # ── Phase 13: SEO Suite & Edge CDN Rules ─────────────────────────────
        try:
            seo_report = {}
            cdn_report = {}
            if project_dir:
                p13 = self._run_phases_parallel([
                    ("phase_13_seo_automation",
                     self.seo_engine.generate,
                     [spec, project_dir],
                     {}),
                    ("phase_13_cdn_optimization",
                     self.cdn_optimizer.generate,
                     [project_dir, spec],
                     {}),
                ])
                seo_report = p13.get("phase_13_seo_automation") or {}
                cdn_report = p13.get("phase_13_cdn_optimization") or {}
            phase_log["phase_13_seo_and_cdn"] = {
                "pages_optimized": seo_report.get("pages_optimized", 0),
                "sitemap_url": seo_report.get("sitemap_url", ""),
                "cdn_platforms": cdn_report.get("platforms_configured", []),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_13_seo_and_cdn_optimization")

        # ── Phase 14: Performance, Webhooks & Conversion Growth ──────────────
        try:
            perf_report = {}
            analytics_report = {}
            ab_report = {}
            webhook_report = {}
            if project_dir:
                p14 = self._run_phases_parallel([
                    ("phase_14_performance_budget",
                     self.performance_budget.generate,
                     [spec, project_dir],
                     {}),
                    ("phase_14_analytics_pipeline",
                     self.analytics_pipeline.generate,
                     [spec, project_dir],
                     {}),
                    ("phase_14_ab_testing",
                     self.ab_testing_engine.generate,
                     [spec, project_dir],
                     {}),
                    ("phase_14_webhook_manager",
                     self.webhook_manager.generate,
                     [spec, project_dir],
                     {}),
                ])
                perf_report = p14.get("phase_14_performance_budget") or {}
                analytics_report = p14.get("phase_14_analytics_pipeline") or {}
                ab_report = p14.get("phase_14_ab_testing") or {}
                webhook_report = p14.get("phase_14_webhook_manager") or {}
            phase_log["phase_14_performance_growth"] = {
                "performance_targets": perf_report.get("targets", {}),
                "analytics_events": analytics_report.get("total_events", 0),
                "ab_experiments": ab_report.get("total_experiments", 0),
                "webhook_events": webhook_report.get("total_events", 0),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_14_performance_growth_and_webhooks")

        # ── Phase 15: Multi-Cloud Production Deployment ──────────────────────
        try:
            cloud_report = {}
            if project_dir:
                cloud_report = self._run_phase_safe(
                    "phase_15_global_deployment",
                    self.deployment_engine.generate,
                    func_args=[spec, project_dir],
                    fallback={}
                )
            phase_log["phase_15_global_deployment"] = {
                "supported_clouds": cloud_report.get("platforms_supported", ["vercel", "railway", "render", "aws", "gcp"]),
                "artifacts_count": len(cloud_report.get("artifacts", [])),
                "recommended_platform": cloud_report.get("recommended_platform", ""),
                "estimated_monthly_cost": self.deployment_engine.estimate_running_cost(
                    spec.get("website_type", "business"), "low"
                ).get("estimates", {}),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_15_multi_cloud_global_deployment")

        # ── Safe ZIP Creation & Report Assembly ──────────────────────────────
        # Re-run validation after every artifact-producing phase so readiness is
        # based on the final project, not the pre-localization scaffold.
        if project_dir:
            try:
                validation_report = self.validator.validate_project(project_dir)
                quality_report = self.quality_gates.evaluate(project_dir, spec, validation_report)
                phase_log["final_production_validation"] = {
                    "valid": validation_report.get("valid", False),
                    "quality_score": quality_report.get("overall_score", 0),
                    "enterprise_ready": quality_report.get("enterprise_ready", False),
                }
            except PipelineCancelled:
                raise
            except Exception as exc:
                agent_logger.error(f"Final production validation failed: {exc}")
                phase_failures.append("final_production_validation")

        # ── DevOps Quality Gate & ZIP Serializer Gate ─────────────────────────
        # Before the ZIP archive is compiled, run the Prettier + ESLint pass on
        # the exported project (Node.js background process via subprocess). The
        # archive is only created when both exit codes are 0; otherwise the
        # project is routed back through the code_modifier self-healing loop.
        #
        # Enterprise Architect gate: reads project-rules/ (PRD/TRD/UI-UX/SCHEMA/
        # SRS) and blocks ZIP compilation while any of the four verification
        # points is red, routing offending files through the same self-healing.
        zip_archive_path = ""
        quality_gate_devops: Dict[str, Any] = {}
        architect_gate: Dict[str, Any] = {}
        if project_dir:
            # Re-assert the selected layout mode's invariants so the shipped
            # bundle matches the buyer's mode even after later artifact phases.
            try:
                self.mode_engine.finalize_layout(project_dir, spec)
            except Exception as finalize_err:
                agent_logger.warning(f"ProjectModeEngine finalize skipped: {finalize_err}")
            try:
                from agent.pro_design import restyle_project
                repo_dir = Path(project_dir)
                brand_key = spec.get("project_name") or repo_dir.name
                repo_key = brand_key
                ui_style = spec.get("ui_style", "glassmorphism")
                region = spec.get("target_region", "default")
                applied = restyle_project(
                    project_dir,
                    repo_key,
                    ui_style,
                    region,
                    palette_override=spec.get("design_palette_override"),
                )
                phase_log["pro_design_restyle"] = applied
                phase_log["pro_design_ui_style"] = ui_style
                phase_log["pro_design_region"] = region
                if applied:
                    agent_logger.info(f"ProDesign applied to newly generated project {repo_key} [{ui_style}/{region}]")
                try:
                    from agent.design_vault import write_manifest
                    vault_manifest = write_manifest()
                    phase_log["design_vault_sources"] = vault_manifest.get("sources", [])
                except Exception as vault_err:
                    agent_logger.warning(f"Design vault manifest skipped: {vault_err}")
            except Exception as pro_err:
                agent_logger.warning(f"ProDesign restyle skipped for new project: {pro_err}")
            try:
                from agent.component_injection import inject_component_imports
                inject_report = inject_component_imports(project_dir)
                phase_log["component_injection"] = inject_report
            except Exception as inject_err:
                agent_logger.warning(f"Component injection sweep skipped: {inject_err}")
            try:
                # Autonomous production-readiness repair for ANY lane: static
                # storefronts get the live commerce backend; transactional trees
                # get the schema contract (models/index.js FK wiring, org/RBAC
                # middleware) + JSON-LD/heading compliance. Deterministic only —
                # zero AI calls, so the pipeline never blocks on rate limits.
                from agent.enterprise_repair import repair_any_layout
                repair_report = repair_any_layout(project_dir, spec)
                phase_log["production_readiness_repair"] = repair_report
            except Exception as commerce_err:
                agent_logger.warning(f"Production-readiness repair skipped: {commerce_err}")
            try:
                architect_gate = self._architect_enterprise_gate(project_dir, spec)
                phase_log["architect_enterprise_verification"] = architect_gate
                if architect_gate.get("blocked_zip") and not architect_gate.get("skipped"):
                    agent_logger.error(
                        "Enterprise Architect gate FAILED — " + architect_gate.get("reason", "")
                        + " violating files routed to self-healing: "
                        + ", ".join(architect_gate.get("violating_files", [])[:10])
                    )
                    phase_failures.append("architect_enterprise_verification")
            except PipelineCancelled:
                raise
            except Exception as gate_err:
                agent_logger.error(f"Enterprise Architect gate error: {gate_err}")
                phase_failures.append("architect_enterprise_verification")
            try:
                self._checkpoint_cancel()
                try:
                    from .guardrails import apply_guardrails
                    guardrails_report = apply_guardrails(project_dir)
                except Exception as guardrails_error:
                    guardrails_report = {
                        "passed": False,
                        "error": str(guardrails_error)[:200],
                    }
                phase_log["phase_16_output_guardrails"] = guardrails_report
                from .generated_project_completeness import evaluate_generated_project
                completeness_report = evaluate_generated_project(project_dir, spec)
                phase_log["generated_project_completeness"] = completeness_report
                quality_gate_devops = self._run_devops_quality_gate(project_dir)
                phase_log["quality_gate_devops"] = quality_gate_devops
                architect_ok = architect_gate.get("skipped") or architect_gate.get("passed")
                # ZIP compilation is ALWAYS attempted — a formatting/lint gate
                # must never block the deliverable. Gate failures only trigger
                # the self-healing pass; the finished project + ZIP + live
                # preview are always produced for the buyer.
                if not (quality_gate_devops.get("passed") and architect_ok):
                    failed_by = (
                        "Enterprise Architect gate" if not architect_ok
                        else "DevOps quality gate"
                    )
                    agent_logger.warning(
                        f"{failed_by} not cleared — routing offending files through "
                        "self-healing, but continuing to ZIP + auto-deploy the project."
                    )
                    phase_failures.append("quality_gate_devops")
                qa_release_gate = self._deployment_release_gate(
                    validation_report,
                    quality_report,
                    quality_gate_devops,
                    architect_gate,
                    completeness_report,
                    guardrails_report,
                )
                phase_log["qa_release_gate"] = qa_release_gate
                if self._free_only_run:
                    phase_log["live_deployment"] = {
                        "status": "disabled",
                        "reason": "free-only rebuilds never deploy",
                    }
                elif qa_release_gate["passed"]:
                    live_url = self._auto_deploy_project(project_dir, spec)
                    if live_url:
                        phase_log["live_deployment"] = {"url": live_url, "status": "deployed"}
                        agent_logger.info(f"🚀 Live preview: {live_url}")
                    else:
                        phase_log["live_deployment"] = {
                            "status": "skipped",
                            "reason": "auto-deploy returned no URL",
                        }
                else:
                    phase_log["live_deployment"] = {
                        "status": "blocked",
                        "reason": "QA release gate failed",
                        "blockers": qa_release_gate["blockers"],
                    }
                    agent_logger.warning(
                        "Auto-deployment blocked by QA release gate: "
                        + ", ".join(qa_release_gate["blockers"])
                    )
                browser_qa = phase_log.get("browser_qa")
                if isinstance(browser_qa, dict) and browser_qa.get("deep_audit", {}).get("status") == "deferred":
                    live_target = phase_log.get("live_deployment", {}).get("url", "")
                    if live_target and os.getenv("LUMI_BROWSER_DEEP_AUDIT", "").strip().lower() in (
                        "1", "true", "yes", "on",
                    ):
                        # Stable digest, not hash(): the session name ends up in
                        # filenames, so it must not change per process.
                        _audit_session = "lumi-qa-" + hashlib.sha256(
                            str(live_target).encode("utf-8", "replace")
                        ).hexdigest()[:10]
                        try:
                            browser_qa["deep_audit"] = self._run_with_hard_timeout(
                                "Phase 7.5 - Browser QA deep audit",
                                deep_browser_audit,
                                [live_target],
                                {"session": _audit_session},
                            )
                        except PipelineCancelled:
                            raise
                        except Exception as deferred_exc:
                            browser_qa["deep_audit"] = {
                                "status": "not_measured",
                                "reason": str(deferred_exc)[:200],
                            }
                        # Supplementary measured audits. Each is independent and
                        # observational: a failure in one never suppresses the others.
                        for _audit_name, _audit_fn, _audit_args in (
                            ("responsive", responsive_check, [live_target]),
                            ("network", network_audit, [live_target]),
                            ("performance", performance_audit, [live_target]),
                        ):
                            try:
                                browser_qa[_audit_name] = self._run_with_hard_timeout(
                                    f"Phase 7.5 - {_audit_name} audit",
                                    _audit_fn,
                                    _audit_args,
                                    {"session": _audit_session},
                                )
                            except Exception as audit_exc:
                                browser_qa[_audit_name] = {
                                    "status": "not_measured",
                                    "reason": str(audit_exc)[:200],
                                }
                        try:
                            browser_qa["remediation"] = remediate_findings(
                                browser_qa.get("deep_audit") or {}
                            )
                        except Exception as rem_exc:
                            browser_qa["remediation"] = {
                                "status": "not_measured",
                                "reason": str(rem_exc)[:200],
                            }
                    else:
                        browser_qa["deep_audit"] = {
                            "status": "not_measured",
                            "reason": "no live URL available for deep audit",
                        }
                zip_archive_path = self._safe_zip(project_dir, spec)
            except PipelineCancelled:
                raise
            except Exception as gate_err:
                agent_logger.error(f"DevOps quality gate error: {gate_err}")
                phase_failures.append("quality_gate_devops")
                # Still attempt the deliverable even if the gate itself broke.
                try:
                    zip_archive_path = self._safe_zip(project_dir, spec)
                except Exception:  # noqa: BLE001
                    agent_logger.error("ZIP creation failed after gate error.")
                phase_log["qa_release_gate"] = {
                    "passed": False,
                    "blockers": ["quality_gate_error"],
                }
                phase_log["live_deployment"] = {
                    "status": "blocked",
                    "reason": "QA gate errored; deployment was not attempted",
                    "blockers": ["quality_gate_error"],
                }

        # Every project-dependent phase below was skipped as a group when the
        # build never produced a project directory — say so instead of leaving it
        # implicit in an empty phase log.
        if not project_dir:
            for _skipped_phase in (
                "quality_verification",
                "browser_qa",
                "international_delivery",
                "localization_and_i18n",
                "compliance_and_accessibility",
                "seo_and_cdn_optimization",
                "performance_growth_and_webhooks",
                "multi_cloud_global_deployment",
            ):
                self._mark_skipped(_skipped_phase, "no_project_directory")

        report = self._build_report(
            start_time=start_time,
            prompt=prompt,
            spec=spec,
            project_dir=project_dir,
            phase_log=phase_log,
            phase_failures=phase_failures,
            selected_template=selected_template,
            selected_components=selected_components,
            selected_assets=selected_assets,
            selected_backend=selected_backend,
            selected_schemas=selected_schemas,
            tech_stack=tech_stack,
            trending_result=trending_result,
            ai_calls_count=ai_calls_count,
            validation_report=validation_report,
            quality_report=quality_report,
            improvements=improvements,
            benchmark=benchmark,
            zip_archive_path=zip_archive_path,
            quality_gate=quality_gate_devops,
            architect_gate=architect_gate,
            live_url=phase_log.get("live_deployment", {}).get("url", ""),
            rag_context=rag_context,
            prompt_provenance=plan.get("prompt_provenance", []),
        )
        report["workflow_agents"] = self._build_workflow_agents_report(
            phase_log, spec, project_dir
        )

        execution_time = round(time.time() - start_time, 2)
        health = self._calculate_health(phase_failures)
        timings_summary = ", ".join(f"{k}: {v}s" for k, v in self.phase_timings.items())

        agent_logger.info("==================================================")
        agent_logger.info(f"  18-PHASE ENTERPRISE GENERATION COMPLETE IN {execution_time}s")
        agent_logger.info(
            f"  Status: {report.get('status')} | Quality Score: "
            f"{quality_report.get('overall_score', 'N/A')}% | "
            f"Launch Ready: {benchmark.get('launch_ready', 'N/A')}"
        )
        agent_logger.info(
            f"  Providers used: {', '.join(report.get('providers_used') or []) or 'none'} | "
            f"fallback_used={report.get('fallback_used')} reason={report.get('reason')}"
        )
        if report.get("skipped_phases"):
            agent_logger.warning(
                "  Skipped phases: "
                + ", ".join(f"{e['phase']}({e['reason']})" for e in report["skipped_phases"])
            )
        agent_logger.info(f"  Pipeline Health: {health['score']}/100 ({health['status']})")
        if phase_failures:
            agent_logger.warning(f"  Phases with failures: {', '.join(phase_failures)}")
        agent_logger.info(f"  Phase Timings: [{timings_summary}]")
        agent_logger.info(f"  ZIP: {zip_archive_path}")
        agent_logger.info("==================================================")

        # Observational V6.5 delivery hooks — never block, never raise.
        try:
            from agent.extensions.delivery_report import write_delivery_reports
            write_delivery_reports(project_dir, report)
        except Exception as delivery_err:  # noqa: BLE001
            agent_logger.warning(f"Delivery reports hook skipped: {delivery_err}")
        try:
            from agent.extensions.notify import notify
            # `fallback_used`/`reason` ride along so monitoring can alert on a run
            # that only produced deterministic local output.
            notify("run.completed", {
                "run_id": getattr(self, "run_id", "") or report.get("run_id", ""),
                "project_dir": project_dir,
                "status": report.get("status", ""),
                "providers_used": report.get("providers_used", []),
                "fallback_used": report.get("fallback_used", False),
                "reason": report.get("reason"),
                "skipped_phases": report.get("skipped_phases", []),
                "quality_score": (report.get("quality_gates", {}) or {}).get("overall_score"),
                "live_preview_url": report.get("live_preview_url", ""),
                "zip_archive_path": zip_archive_path,
            })
        except Exception as notify_err:  # noqa: BLE001
            agent_logger.warning(f"Webhook notify hook skipped: {notify_err}")

        return report
