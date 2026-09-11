import os
import sys
import json
import time
import traceback
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from utils.logger import agent_logger
from utils.file_manager import FileManager
from config.providers import instantiate_provider, validate_provider_key, FALLBACK_ORDER
from config.settings import GENERATED_PROJECTS_DIR
from providers.base_provider import BaseAIProvider
from providers.provider_pool import get_pool

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


class OrchestratorError(Exception):
    """Raised when pipeline execution encounters unrecoverable errors."""
    pass


class PipelineCancelled(Exception):
    """Cooperative abort from WebSocket disconnect or an in-band cancel frame."""


class PhaseError(Exception):
    """Raised when a specific phase fails."""
    def __init__(self, phase_name: str, error: Exception):
        self.phase_name = phase_name
        self.error = error
        super().__init__(f"Phase '{phase_name}' failed: {error}")


class AgentOrchestrator:
    """Master controller — 15-phase state-of-the-art enterprise AI project generation pipeline."""

    PHASES = [
        "market_analysis",
        "requirement_analysis",
        "tech_stack_selection",
        "trending_features_injection",
        "resource_assembly_planning",
        "code_generation",
        "quality_verification",
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
        "requirement_analysis": [],
        "tech_stack_selection": ["requirement_analysis"],
        "trending_features_injection": ["requirement_analysis", "market_analysis"],
        "resource_assembly_planning": ["requirement_analysis", "tech_stack_selection"],
        "code_generation": ["resource_assembly_planning"],
        "quality_verification": ["code_generation"],
        "improvement_recommendations": ["quality_verification"],
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
        try:
            self.devops_gate = DevOpsQualityGate()
        except GateNotAvailableError as exc:
            agent_logger.error(f"DevOps quality gate unavailable: {exc}")
            self.devops_gate = None

    def _init_provider(self, provider_name: Optional[str] = None):
        """Instantiate AI provider via the rotating provider pool (fallback chain + cycle-back)."""
        primary_name = (provider_name or os.getenv("ACTIVE_AI_PROVIDER", "gemini")).lower()

        # Position pool at primary provider first
        pool = self.provider_pool
        try:
            if primary_name in pool.available:
                idx = pool._order.index(primary_name)
                if pool._current_index != idx and primary_name in pool._providers:
                    pass  # pool handles ordering internally
        except Exception:
            pass

        provider_inst = pool.get_active()
        if provider_inst:
            agent_logger.info(f"[ORCH] Active AI Provider via pool: '{pool.get_current_name()}'")
            return provider_inst

        agent_logger.info("No external AI provider API keys configured. Operating in local-first offline mode.")
        return None

    def _rotate_provider(self):
        """Rotate to the next available provider and propagate to all sub-engines."""
        pool = self.provider_pool
        old_name = pool.get_current_name()
        provider_inst = pool.get_active()
        if provider_inst and provider_inst is not self.ai_provider:
            new_name = pool.get_provider_name(provider_inst)
            agent_logger.info(f"[ORCH] Rotating provider: '{old_name}' -> '{new_name}'")
            self.ai_provider = provider_inst
            self.analyzer.ai_provider = provider_inst
            self.code_modifier.ai_provider = provider_inst
            try:
                self.iterate_engine.provider = provider_inst
                self.iterate_engine.code_modifier = CodeModifier(provider_inst)
            except Exception:
                pass
            return True
        return False

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
                # If rate limited, rotate to next provider before retrying
                if self.ai_provider and BaseAIProvider.is_rate_limited(e):
                    current_name = (self.provider_pool.get_provider_name(self.ai_provider)
                                    or self.ai_provider.__class__.__name__)
                    self.provider_pool.mark_rate_limited(current_name)
                    agent_logger.warning(f"[PHASE ROTATE] {phase_name} hit rate limit on '{current_name}' — rotating provider")
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
        health = 100
        critical_failures = [f for f in phase_failures if f in {"phase_2_requirement_analysis",
                                                                 "phase_5_assembly_planning",
                                                                 "phase_6_code_generation"}]
        non_critical_failures = [f for f in phase_failures if f not in critical_failures]

        health -= len(critical_failures) * 20
        health -= len(non_critical_failures) * 4

        return {
            "score": max(0, health),
            "critical_failures": critical_failures,
            "non_critical_failures": non_critical_failures,
            "status": "healthy" if health >= 80 else "degraded" if health >= 50 else "critical",
        }

    def _phase_failure_names(self, phase_failures: List[str]) -> set:
        """Map report identifiers such as phase_6_code_generation to canonical phase IDs."""
        return {
            failure.split("_", 2)[-1]
            for failure in phase_failures
            if failure.startswith("phase_") and "_" in failure
        }

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
    ) -> Dict[str, Any]:
        instructions_file_path = os.path.join(project_dir, "INSTRUCTIONS.md")
        execution_time = round(time.time() - start_time, 2)

        failed_phase_names = self._phase_failure_names(phase_failures)
        critical_failure = any(
            name in self.CRITICAL_PHASES for name in failed_phase_names
        )
        report = {
            "user_prompt": prompt,
            "project_name": spec.get("project_name", "generated-website"),
            "generated_project_dir": project_dir,
            "zip_archive_path": zip_archive_path,
            "quality_gate_devops": quality_gate or {},
            "architect_enterprise_gate": architect_gate or {},
            "instructions_file_path": instructions_file_path,
            "execution_time_seconds": execution_time,
            "pipeline_version": "15-phase-enterprise-v3.5",
            "status": "failed" if critical_failure else "partial" if phase_failures else "succeeded",
            "pipeline_health": self._calculate_health(phase_failures),
            "phase_statistics": {
                "total_phases": len(self.PHASES),
                "phases_failed": len(phase_failures),
                "phase_timings": self.phase_timings,
                "retries_per_phase": self.retry_counts,
            },
            "phases_completed": [p for p in self.PHASES if p not in failed_phase_names],
            "phase_failures": phase_failures,
            "phase_results": phase_log,
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
            "enterprise_ready": quality_report.get("enterprise_ready", False),
            "launch_ready": benchmark.get("launch_ready", False),
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
        }

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
        """Execute 15-phase enterprise project generation pipeline with error isolation and callbacks."""
        self._reset_phase_tracking()
        self.progress_callback = progress_callback
        start_time = time.time()
        phase_log: Dict[str, Any] = {}
        phase_failures: List[str] = []

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
        agent_logger.info("  LUMICOREPRO 15-PHASE ENTERPRISE GENERATION AGENT")
        agent_logger.info("==================================================")
        agent_logger.info(f"User Prompt: '{prompt}'")

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
                for vp_name in vision_candidates:
                    try:
                        from config.providers import get_active_provider_config, validate_provider_key
                        cfg = get_active_provider_config(vp_name)
                        key = (cfg or {}).get("api_key", "") or ""
                        if key and not str(key).startswith(("your_",)):
                            inst = instantiate_provider(vp_name)
                            if inst is not None:
                                vp_provider = inst
                                break
                    except Exception:
                        continue
                vision_pipe = VisionPipeline(provider=vp_provider)
                vision_layout = vision_pipe.extract_layout(vision_source)
                overlays = vision_pipe.to_spec_overlays(vision_layout)
                mapper = LayoutMapper()
                mapped = mapper.map_regions(vision_layout)
                phase_log["phase_0_vision"] = {
                    "parsed": vision_layout.get("parsed", False),
                    "source": vision_layout.get("source", "unknown"),
                    "regions": overlays.get("vision_layout_regions", []),
                    "design_tokens": overlays.get("design_tokens", {}),
                    "regions_mapped": mapped,
                    "reason": vision_layout.get("reason"),
                }
                agent_logger.info(
                    f"Phase 0 vision: parsed={vision_layout.get('parsed')} "
                    f"source={vision_layout.get('source')} regions={len(overlays.get('vision_layout_regions', []))}"
                )
            except PipelineCancelled:
                raise
            except Exception as exc:
                agent_logger.warning(f"Phase 0 vision extraction skipped: {exc}")
                phase_log["phase_0_vision"] = {"parsed": False, "reason": str(exc)}

        # ── Phase 1: Market Analysis ─────────────────────────────────────────
        try:
            prelim_spec = self._run_phase_safe(
                "Phase 1 - Market Analysis",
                self.analyzer._local_rule_analysis,
                func_args=[prompt],
                fallback={"website_type": "ecommerce", "industry": "general", "features": []}
            )
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
            spec = self._run_phase_safe(
                "Phase 2 - Requirement Analysis",
                self.analyzer.analyze,
                func_args=[prompt],
                fallback={"is_ambiguous": False, "website_type": "ecommerce",
                          "industry": "general", "features": []}
            )
            # Explicit overrides win over analyzer heuristics
            if design_style:
                spec["design_style"] = design_style
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
                            self.analyzer.analyze,
                            func_args=[prompt],
                            fallback=spec
                        )
            # Apply design preferences
            spec = self._collect_user_design_preferences(spec, market_analysis, interactive=interactive)
            phase_log["phase_2_requirement_analysis"] = spec
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_2_requirement_analysis")

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

            plan = self.planner.create_plan(
                spec, selected_template, selected_components,
                selected_assets, selected_backend, selected_schemas,
            )
            plan["spec"] = spec
            phase_log["phase_5_assembly_plan"] = {
                "project_name": plan["project_name"],
                "steps": len(plan["assembly_steps"]),
                "ai_tasks": len(plan.get("ai_tasks_required", [])),
            }
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_5_assembly_planning")

        # ── Phase 6: Code Generation & REST API Scaffolding ──────────────────
        try:
            self._checkpoint_cancel()
            self._bind_engineering_matrix(spec, phase_log)
            plan["spec"] = copy.deepcopy(spec)
            project_dir = self.project_builder.build_project(plan)

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
                    engine = BespokeUIDesignEngine(ai_provider=self.ai_provider)
                    bespoke_report = engine.run(
                        project_dir,
                        bespoke_spec,
                        provider_name=str(os.getenv("REASONING_PROVIDER") or REASONING_PROVIDER or ""),
                    )
                    agent_logger.info(
                        f"Phase 5.5 bespoke design: active={bespoke_report.get('active')} "
                        f"blocks={len(bespoke_report.get('generated_blocks', []))}"
                    )
                except Exception as bd_exc:
                    agent_logger.warning(f"Phase 5.5 bespoke design skipped: {bd_exc}")
                    bespoke_report = {"active": False, "reason": str(bd_exc)}
            phase_log["phase_5_5_bespoke_design"] = bespoke_report
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
        except PipelineCancelled:
            raise
        except Exception:
            phase_failures.append("phase_7_quality_verification")

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
                from agent.component_injection import inject_component_imports
                inject_report = inject_component_imports(project_dir)
                phase_log["component_injection"] = inject_report
            except Exception as inject_err:
                agent_logger.warning(f"Component injection sweep skipped: {inject_err}")
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
                quality_gate_devops = self._run_devops_quality_gate(project_dir)
                phase_log["quality_gate_devops"] = quality_gate_devops
                architect_ok = architect_gate.get("skipped") or architect_gate.get("passed")
                if quality_gate_devops.get("passed") and architect_ok:
                    zip_archive_path = self._safe_zip(project_dir, spec)
                else:
                    failed_by = (
                        "Enterprise Architect gate" if not architect_ok
                        else "DevOps quality gate"
                    )
                    agent_logger.error(
                        f"{failed_by} NOT cleared — ZIP compilation blocked; "
                        "project routed to code_modifier self-healing (see phase_log)."
                    )
                    phase_failures.append("quality_gate_devops")
            except PipelineCancelled:
                raise
            except Exception as gate_err:
                agent_logger.error(f"DevOps quality gate error: {gate_err}")
                phase_failures.append("quality_gate_devops")

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
        )

        execution_time = round(time.time() - start_time, 2)
        health = self._calculate_health(phase_failures)
        timings_summary = ", ".join(f"{k}: {v}s" for k, v in self.phase_timings.items())

        agent_logger.info("==================================================")
        agent_logger.info(f"  15-PHASE ENTERPRISE GENERATION COMPLETE IN {execution_time}s")
        agent_logger.info(
            f"  Quality Score: {quality_report.get('overall_score', 'N/A')}% | "
            f"Launch Ready: {benchmark.get('launch_ready', 'N/A')}"
        )
        agent_logger.info(f"  Pipeline Health: {health['score']}/100 ({health['status']})")
        if phase_failures:
            agent_logger.warning(f"  Phases with failures: {', '.join(phase_failures)}")
        agent_logger.info(f"  Phase Timings: [{timings_summary}]")
        agent_logger.info(f"  ZIP: {zip_archive_path}")
        agent_logger.info("==================================================")
        return report
