import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger
from utils.file_manager import FileManager

class QualityGates:
    """Phase 7: Enterprise quality gates — performance, security, features, assets, animation, international compliance, accessibility, and deployment readiness."""

    PERFORMANCE_TARGETS = {
        "lighthouse_performance": 95,
        "lighthouse_accessibility": 90,
        "lighthouse_best_practices": 90,
        "lighthouse_seo": 90,
        "first_contentful_paint": 1.2,  # seconds
        "time_to_interactive": 2.5,  # seconds
        "animation_fps": 60,
    }

    SECURITY_CHECKS = [
        "helmet_middleware",
        "rate_limiting",
        "env_secrets_not_committed",
        "parameterized_queries",
        "cors_configured",
        "input_validation",
        "jwt_authentication",
        "bcrypt_password_hash",
        "xss_protection",
        "sql_injection_prevention",
        "content_security_policy",
        "hreflang_tags",  # International SEO
    ]

    REAL_ASSET_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif", ".avif"}
    
    # International compliance thresholds
    INTERNATIONAL_COMPLIANCE_THRESHOLD = 0.75  # 75% of checks must pass
    ACCESSIBILITY_THRESHOLD = 0.8  # 80% of accessibility checks must pass
    DEPLOYMENT_READINESS_THRESHOLD = 0.8  # 80% of deployment checks must pass

    def evaluate(self, project_path: str, spec: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Run enterprise quality gates against generated project — now includes accessibility & deployment checks."""
        agent_logger.info("Phase 7: Running enterprise quality gates...")
        p_dir = Path(project_path).resolve()

        gates = {
            "performance": self._check_performance(p_dir, spec),
            "security": self._check_security(p_dir),
            "features": self._check_features(spec),
            "assets": self._check_assets(p_dir),
            "code_quality": self._check_code_quality(validation_report),
            "differentiation": self._check_differentiation(spec),
            "international_compliance": self._check_international_compliance(p_dir, spec),
            "accessibility": self._check_accessibility(p_dir),
            "deployment_readiness": self._check_deployment_readiness(p_dir),
            "marketplace_docs": self._check_marketplace_docs(p_dir),
            "pro_ui": self._check_pro_ui(p_dir),
        }

        passed = sum(1 for g in gates.values() if g["passed"])
        total = len(gates)
        overall_score = round((passed / total) * 100, 1)

        enterprise_ready_threshold = 80
        marketplace_ok = gates["marketplace_docs"]["passed"]
        zero_errors = validation_report.get("valid", False) and not validation_report.get("errors")
        result = {
            "gates": gates,
            "passed_count": passed,
            "total_gates": total,
            "overall_score": overall_score,
            "marketplace_ready": marketplace_ok and gates["pro_ui"]["passed"] and zero_errors,
            "enterprise_ready": (
                overall_score >= enterprise_ready_threshold
                and marketplace_ok
                and zero_errors
            ),
            "targets": self.PERFORMANCE_TARGETS,
            "github_recovery_hint": self._github_recovery_hint(),
        }

        agent_logger.info(f"Quality gates: {passed}/{total} passed (score: {overall_score}%)")
        return result

    @staticmethod
    def _github_recovery_hint() -> Optional[Dict[str, Any]]:
        """Cache-only React 19 / Vite recovery hint bound to the GitHub channel.

        The actual server-side fetch lives in quality_gate.py (async subprocess);
        this evaluator only consumes the already-fetched bundle so it stays
        synchronous and never blocks the pipeline.
        """
        try:
            from agent.reach.github_recovery import cached_github_recovery
            hint = cached_github_recovery()
        except Exception:
            return None
        if hint and hint.get("applied"):
            return {
                "context": hint.get("context"),
                "patch_title": hint.get("patch_title"),
                "patch_url": hint.get("patch_url"),
                "patches": hint.get("patches", []),
            }
        return None

    def _check_performance(self, p_dir: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
        checks = []
        frontend = p_dir / "frontend"
        if frontend.exists():
            pkg = frontend / "package.json"
            if pkg.exists():
                checks.append({"check": "vite_bundler", "passed": True})
            tailwind = frontend / "tailwind.config.js"
            checks.append({"check": "tailwind_css", "passed": tailwind.exists() or (frontend / "postcss.config.js").exists()})
        passed = all(c["passed"] for c in checks) if checks else False
        return {"passed": passed, "checks": checks, "target_lighthouse": self.PERFORMANCE_TARGETS["lighthouse_performance"]}

    def _check_security(self, p_dir: Path) -> Dict[str, Any]:
        checks = []
        backend = p_dir / "backend"
        if backend.exists():
            from .intelligence.source_index import get_source_index
            index = get_source_index(str(p_dir.resolve()))
            server_files = [Path(p) for p in index.files(".js")]
            content = ""
            for sf in server_files[:5]:
                content += FileManager.read_file(str(sf))

            checks.append({"check": "helmet_middleware", "passed": "helmet" in content.lower()})
            checks.append({"check": "rate_limiting", "passed": "ratelimit" in content.lower() or "rate-limit" in content.lower()})
            checks.append({"check": "cors_configured", "passed": "cors" in content.lower()})
            checks.append({"check": "env_secrets_not_committed", "passed": not (backend / ".env").exists()})
        else:
            checks.append({"check": "backend_present", "passed": False})

        passed = sum(1 for c in checks if c["passed"]) >= len(checks) * 0.6 if checks else False
        return {"passed": passed, "checks": checks}

    def _check_features(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        features = spec.get("features", [])
        trending = spec.get("trending_features", [])
        count = len(set(features) | set(trending))
        passed = count >= 5
        return {"passed": passed, "feature_count": count, "minimum_required": 5, "trending_count": len(trending)}

    def _check_assets(self, p_dir: Path) -> Dict[str, Any]:
        assets_dir = p_dir / "frontend" / "src" / "assets"
        real_count = 0
        ai_generated = 0
        if assets_dir.exists():
            for root, _, files in os.walk(assets_dir):
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in self.REAL_ASSET_EXTENSIONS:
                        real_count += 1
                    if "generated" in f.lower() or "ai-" in f.lower():
                        ai_generated += 1
        passed = real_count > 0 and ai_generated == 0
        return {"passed": passed, "real_assets": real_count, "ai_generated_detected": ai_generated}

    def _check_code_quality(self, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        errors = len(validation_report.get("errors", []))
        warnings = len(validation_report.get("warnings", []))
        passed = validation_report.get("valid", False) and warnings < 10
        return {"passed": passed, "errors": errors, "warnings": warnings}

    def _check_differentiation(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        trending = spec.get("trending_features", [])
        count = len(trending)
        passed = count >= 3
        return {"passed": passed, "unique_features": count, "minimum_required": 3}

    def _check_international_compliance(self, p_dir: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check international market readiness (GDPR, i18n, PWA, accessibility, WhatsApp, Cookie Consent)."""
        checks = []
        frontend = p_dir / "frontend"
        
        if frontend.exists():
            # Check for i18n support
            i18n_config = frontend / "src" / "i18n"
            checks.append({
                "check": "i18n_support",
                "passed": i18n_config.exists() or any("i18n" in f.lower() for f in os.listdir(frontend / "src") if os.path.isdir(os.path.join(frontend / "src", f))),
                "weight": 1.0
            })
            
            # Check for cookie consent (GDPR/PECR)
            from .intelligence.source_index import get_source_index
            index = get_source_index(str(p_dir.resolve()))
            src_files = [Path(p) for p in
                         index.files(".jsx", ".tsx")]
            has_cookie_consent = False
            for sf in src_files[:50]:
                content = FileManager.read_file(str(sf))
                if "cookie" in content.lower() and ("consent" in content.lower() or "gdpr" in content.lower()):
                    has_cookie_consent = True
                    break
            checks.append({"check": "cookie_consent", "passed": has_cookie_consent, "weight": 1.5})
            
            # Check for PWA manifest
            manifest = frontend / "public" / "manifest.json"
            checks.append({"check": "pwa_manifest", "passed": manifest.exists(), "weight": 1.0})
            
            # Check for service worker
            sw_exists = (frontend / "public" / "sw.js").exists() or (frontend / "src" / "sw.js").exists()
            checks.append({"check": "service_worker", "passed": sw_exists, "weight": 1.0})
            
            # Check for robots.txt and sitemap.xml
            checks.append({"check": "robots_txt", "passed": (frontend / "public" / "robots.txt").exists(), "weight": 0.5})
            checks.append({"check": "sitemap_xml", "passed": (frontend / "public" / "sitemap.xml").exists(), "weight": 0.5})
            
            # Check for RTL support
            rtl_found = False
            for sf in src_files[:50]:
                content = FileManager.read_file(str(sf))
                if "rtl" in content.lower() or 'dir="rtl"' in content.lower():
                    rtl_found = True
                    break
            checks.append({"check": "rtl_support", "passed": rtl_found, "weight": 1.0})
            
            # Check for WhatsApp integration
            whatsapp_found = False
            for sf in src_files[:50]:
                content = FileManager.read_file(str(sf))
                if "whatsapp" in content.lower() or "wa.me" in content.lower():
                    whatsapp_found = True
                    break
            checks.append({"check": "whatsapp_integration", "passed": whatsapp_found, "weight": 1.0})
            
            # Enhanced: Check for accessibility (ARIA labels)
            aria_found = False
            for sf in src_files[:30]:
                content = FileManager.read_file(str(sf))
                if 'aria-' in content.lower() or 'role=' in content.lower():
                    aria_found = True
                    break
            checks.append({"check": "accessibility_aria", "passed": aria_found, "weight": 1.0})
            
            # Enhanced: Check for dark mode support
            dark_mode = False
            for sf in src_files[:20]:
                content = FileManager.read_file(str(sf))
                if "dark:" in content.lower() or "darkmode" in content.lower():
                    dark_mode = True
                    break
            checks.append({"check": "dark_mode_support", "passed": dark_mode, "weight": 0.5})
            
            # Enhanced: Check for mobile responsive (Tailwind responsive classes)
            responsive = False
            for sf in src_files[:20]:
                content = FileManager.read_file(str(sf))
                if "sm:" in content or "md:" in content or "lg:" in content:
                    responsive = True
                    break
            checks.append({"check": "mobile_responsive", "passed": responsive, "weight": 1.0})
        else:
            checks = [{"check": "frontend_exists", "passed": False, "weight": 0}]
        
        # Calculate weighted score
        total_weight = sum(c.get("weight", 1.0) for c in checks)
        passed_weight = sum(c.get("weight", 1.0) for c in checks if c["passed"])
        compliance_score = round((passed_weight / total_weight) * 100, 1) if total_weight > 0 else 0
        
        # Pass if at least 75% weighted score
        passed = compliance_score >= 75
        
        return {
            "passed": passed,
            "checks": checks,
            "compliance_score": compliance_score,
            "international_ready": passed,
            "weighted_threshold": 75
        }

    def _check_accessibility(self, p_dir: Path) -> Dict[str, Any]:
        """Apply a lightweight WCAG artifact gate before expensive browser checks."""
        frontend = p_dir / "frontend"
        from .intelligence.source_index import get_source_index
        index = get_source_index(str(p_dir.resolve()))
        files = [Path(p) for p in
                 index.files(".jsx", ".tsx")] if frontend.exists() else []
        content = "\n".join(FileManager.read_file(str(path)) for path in files[:100])
        checks = [
            {"check": "semantic_landmarks", "passed": any(tag in content for tag in ("<main", "<header", "<nav"))},
            {"check": "accessible_labels", "passed": "aria-label" in content or "<label" in content},
            {"check": "keyboard_focus", "passed": "focus:" in content or "focus-visible" in content},
            {"check": "reduced_motion", "passed": "prefers-reduced-motion" in content},
        ]
        passed = sum(item["passed"] for item in checks)
        return {"passed": passed >= 3, "checks": checks, "score": round(passed / len(checks) * 100, 1)}

    def _check_deployment_readiness(self, p_dir: Path) -> Dict[str, Any]:
        """Verify the minimum artifacts required to deploy the generated full stack."""
        required = [
            p_dir / "frontend" / "package.json",
            p_dir / "backend" / "package.json",
            p_dir / "backend" / "server.js",
            p_dir / "database" / "schema.sql",
            p_dir / "docker-compose.yml",
            p_dir / "frontend" / "Dockerfile",
        ]
        checks = [{"check": str(path.relative_to(p_dir)), "passed": path.exists()} for path in required]
        passed = sum(item["passed"] for item in checks)
        return {"passed": passed == len(checks), "checks": checks, "score": round(passed / len(checks) * 100, 1)}

    def _check_marketplace_docs(self, p_dir: Path) -> Dict[str, Any]:
        """README + license + env template required for international sales."""
        from .marketplace_readme import readme_has_required_sections

        readme_path = p_dir / "README.md"
        readme_text = FileManager.read_file(str(readme_path)) if readme_path.exists() else ""
        missing = readme_has_required_sections(readme_text) if readme_text else ["readme"]
        env_ok = any(
            (p_dir / rel).exists()
            for rel in (".env.example", "frontend/.env.example", "backend/.env.example")
        )
        license_ok = (p_dir / "LICENSE.md").exists() or (p_dir / "LICENSE").exists()
        checks = [
            {"check": "readme_present", "passed": readme_path.exists() and len(readme_text) > 400},
            {"check": "readme_sections", "passed": not missing, "missing": missing},
            {"check": "license", "passed": license_ok},
            {"check": "env_example", "passed": env_ok},
        ]
        passed = all(item["passed"] for item in checks)
        return {"passed": passed, "checks": checks}

    def _check_pro_ui(self, p_dir: Path) -> Dict[str, Any]:
        """Block hobby-grade UI: branding, dark mode, lucide, responsive tokens."""
        frontend = p_dir / "frontend"
        pkg_text = ""
        pkg = frontend / "package.json"
        if pkg.exists():
            pkg_text = FileManager.read_file(str(pkg))
        files = []
        src = frontend / "src"
        if src.exists():
            files = list(src.rglob("*.jsx")) + list(src.rglob("*.tsx")) + list(src.rglob("*.js"))
        content = "\n".join(FileManager.read_file(str(path)) for path in files[:80])
        checks = [
            {"check": "lucide_icons", "passed": "lucide-react" in pkg_text or "lucide-react" in content},
            {
                "check": "brand_logo",
                "passed": any(token in content for token in ("UniqueLogo", "BrandLogo", "<svg")),
            },
            {"check": "dark_mode", "passed": "dark:" in content or "darkMode" in content},
            {"check": "responsive", "passed": "md:" in content or "lg:" in content},
            {
                "check": "pro_footer_or_nav",
                "passed": any(
                    token in content
                    for token in ("ModernFooter", "GlassNavbar", "newsletter", "<footer")
                ),
            },
        ]
        passed_count = sum(1 for item in checks if item["passed"])
        return {
            "passed": passed_count >= 3,
            "checks": checks,
            "score": round(passed_count / len(checks) * 100, 1),
        }
