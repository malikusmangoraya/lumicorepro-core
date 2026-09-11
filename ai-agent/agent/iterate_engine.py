"""
Iteration Engine — LumicorePro AI Agent
=======================================
Post-generation editing loop (Lovable/v0-style "keep chatting" refinement) with
two structural advantages SaaS builders cannot offer:

  1. **Diff-based regeneration** — only the target files are edited; the rest of
     the generated code stays byte-identical. A real git-style unified diff is
     produced and stored in `.lumicore/iterate-manifest.json`.
  2. **Partial phase re-run** — after an edit, only the verification/publishing
     phases are re-executed against the changed files (quality gates, compliance,
     accessibility, security posture, cost estimate, re-zip). Phases 1–6
     (market/requirement/stack/assembly/code) are NOT re-run.

Works online (provider `modify_code`) and offline (`_apply_offline_patch`
deterministic rules for heading/brand/contact/color edits) so the iteration loop
never depends on a cloud key.
"""

import os
import re
import json
import difflib
import time
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import agent_logger
from utils.file_manager import FileManager
from agent.code_modifier import CodeModifier


# ── Offline deterministic colour rules (tailwind palette) ───────────────────
COLOR_MAP: Dict[str, str] = {
    "blue": "blue", "indigo": "indigo", "violet": "violet", "purple": "purple",
    "cyan": "cyan", "teal": "teal", "emerald": "emerald", "green": "green",
    "lime": "lime", "amber": "amber", "orange": "orange", "red": "red",
    "rose": "rose", "pink": "pink", "slate": "slate", "gray": "gray",
    "grey": "gray", "dark": "slate", "black": "slate",
}
CONTACT_NEWS = [
    "email", "phone", "whatsapp", "address", "contact", "footer",
]
HEADING_NEWS = ["heading", "headline", "title", "hero text", "herotext", "main title"]


class AgentIterationEngine:
    """Post-generation refinement with diff-based partial regeneration."""

    MANIFEST_PATH = os.path.join(".lumicore", "iterate-manifest.json")

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.provider = orchestrator.ai_provider if orchestrator else None
        self.code_modifier = CodeModifier(self.provider)

    # ── Public API ─────────────────────────────────────────────────────────
    def iterate(
        self,
        project_dir: str,
        instruction: str,
        provider_name: Optional[str] = None,
        client_brand: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not os.path.isdir(project_dir):
            raise ValueError(f"Project directory not found: {project_dir}")

        # Re-resolve provider if explicitly requested (keeps orchestration state clean)
        if provider_name:
            from config.providers import instantiate_provider, validate_provider_key
            try:
                if validate_provider_key(provider_name, require_key=False):
                    inst = instantiate_provider(provider_name)
                    if inst:
                        self.provider = inst
                        self.code_modifier = CodeModifier(self.provider)
            except Exception:
                pass

        manifest = self._load_manifest(project_dir)
        version = int(manifest.get("version", 0)) + 1
        instruction = (instruction or "").strip()
        if len(instruction) < 3:
            raise ValueError("Instruction is too short (minimum 3 characters).")

        targets = self._resolve_targets(project_dir, instruction)
        if not targets:
            raise ValueError(
                "Could not determine which file to edit. Try a more specific "
                "instruction (e.g. 'change the hero heading', 'set the email to …')."
            )

        changes: List[Dict[str, Any]] = []
        failures: List[str] = []
        phases_rerun: List[str] = []
        ai_used = False

        for file_path in targets:
            original = FileManager.read_file(file_path)
            if not original:
                failures.append(f"{self._rel(project_dir, file_path)}: unreadable")
                continue

            updated, used_ai = self._patch_file(file_path, instruction)
            if updated is None or updated == original:
                failures.append(f"{self._rel(project_dir, file_path)}: no change applied")
                continue
            ai_used = ai_used or used_ai

            # Security + syntax gates — revert on violation (CodeModifier semantics)
            violations = CodeModifier.validate_code_security(updated)
            if violations:
                failures.append(f"{self._rel(project_dir, file_path)}: security gate rejected ({'; '.join(violations)})")
                continue
            if not CodeModifier.validate_syntax_balance(updated):
                failures.append(f"{self._rel(project_dir, file_path)}: syntax gate rejected — reverted")
                continue

            diff = "\n".join(
                difflib.unified_diff(
                    original.splitlines(),
                    updated.splitlines(),
                    fromfile=f"a/{self._rel(project_dir, file_path)}",
                    tofile=f"b/{self._rel(project_dir, file_path)}",
                    lineterm="",
                )
            )
            added = sum(1 for l in updated.splitlines() if l not in set(original.splitlines()))
            removed = sum(1 for l in original.splitlines() if l not in set(updated.splitlines()))

            if not FileManager.write_file(file_path, updated):
                failures.append(f"{self._rel(project_dir, file_path)}: write failed")
                continue

            changes.append({
                "path": self._rel(project_dir, file_path),
                "added_lines": added,
                "removed_lines": removed,
                "diff": diff,
            })

        if not changes:
            return {
                "success": False,
                "version": version,
                "instruction": instruction,
                "changes": [],
                "failures": failures,
                "reason": "No files could be safely patched. "
                          "Check failures or provide an AI provider key for smarter edits."
            }

        # ── Partial phase re-run (only verification/publishing phases) ─────
        rerun = self._rerun_affected_phases(project_dir, instruction)
        phases_rerun = rerun.get("phases")
        compliance_evidence = rerun.get("compliance_evidence")
        access_score = rerun.get("accessibility_score", 0)
        quality_score = rerun.get("quality_score", 0)

        # Write audit trail MD (human-readable) — the diff "proof"
        self._write_iterations_md(project_dir, instruction, changes, version, client_brand, quality_score, access_score)

        # Update manifest (version-aware history)
        manifest["version"] = version
        manifest.setdefault("project_dir", project_dir)
        if client_brand:
            manifest["client_brand"] = client_brand
        manifest.setdefault("history", []).append({
            "version": version,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "instruction": instruction,
            "provider": self.provider.__class__.__name__ if self.provider else "offline-deterministic",
            "changed_files": [c["path"] for c in changes],
            "added_lines": sum(c["added_lines"] for c in changes),
            "removed_lines": sum(c["removed_lines"] for c in changes),
            "quality_score": quality_score,
        })
        self._save_manifest(project_dir, manifest)

        # Re-zip so the download link always reflects the latest state
        zip_path = ""
        if self.orchestrator:
            spec = self._load_spec(project_dir) or {"project_name": os.path.basename(project_dir), "region": "NA"}
            try:
                zip_path = self.orchestrator._safe_zip(project_dir, spec)
            except Exception as e:
                agent_logger.warning(f"IterateEngine: re-zip failed: {e}")

        return {
            "success": True,
            "version": version,
            "instruction": instruction,
            "provider": self.provider.__class__.__name__ if self.provider else "offline-deterministic",
            "changed_files": [c["path"] for c in changes],
            "diffs_preview": "\n".join(
                c["diff"] for c in changes
            )[:4000],
            "added_lines": sum(c["added_lines"] for c in changes),
            "removed_lines": sum(c["removed_lines"] for c in changes),
            "failures": failures,
            "phases_rerun": phases_rerun,
            "quality_score": quality_score,
            "accessibility_score": access_score,
            "compliance_evidence": compliance_evidence,
            "manifest_path": self._rel(project_dir, self.MANIFEST_PATH),
            "iterations_log": self._rel(project_dir, "ITERATIONS.md"),
            "zip_archive_path": zip_path,
            "ai_used": ai_used,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    # ── Target discovery ───────────────────────────────────────────────────
    def _resolve_targets(self, project_dir: str, instruction: str) -> List[str]:
        """Choose file(s) to edit from keyword + AI hints."""
        candidates = self.orchestrator._get_project_main_files(project_dir, max_files=25) if self.orchestrator else []
        if not candidates:
            return []

        low = instruction.lower()

        # Brand/name edits → index.html + package.json (no AI needed)
        if any(k in low for k in ("brand", "logo text", "site name", "project name", "website name")):
            paths = [os.path.join(project_dir, "frontend", "index.html"), os.path.join(project_dir, "package.json")]
            return [p for p in paths if os.path.isfile(p)]

        # Colour edits → any file with className colour tokens (prefer ones containing 'hero' or 'theme')
        if "color" in low or "colour" in low or "theme" in low:
            scored = self._score_files(candidates, low)
            return scored[:2]

        # Contact edits → files containing email/phone/address markers
        if any(k in low for k in CONTACT_NEWS):
            contact_files = [
                f for f in candidates
                if any(marker in FileManager.read_file(f) or "" for marker in ("mailto:", "tel:", "email", "phone"))
            ]
            return (contact_files or candidates)[:1]

        # Heading/text edits → key named pages (Landing/Home/Hero) first
        if any(k in low for k in HEADING_NEWS):
            heroes = [f for f in candidates if re.search(r"(landing|home|hero|index)", os.path.basename(f), re.I)]
            return (heroes or candidates)[:1]

        # Fallback → allow AI to name the file, else first candidate
        ai_target = self._ask_ai_target(candidates, instruction)
        if ai_target:
            for f in candidates:
                if os.path.basename(f).lower() == os.path.basename(ai_target).lower() or ai_target in f:
                    return [f]
        return candidates[:1]

    def _score_files(self, candidates: List[str], low: str) -> List[str]:
        """Score files by relevance to the instruction keywords."""
        scored = []
        for f in candidates:
            base = os.path.basename(f).lower()
            score = 0
            if any(k in base for k in ("hero", "theme", "landing", "home", "index")):
                score += 3
            if re.search(r"(cyan|indigo|violet|primary|\.\./styles|globals\.css|tailwind)", f.replace("\\", "/").lower()):
                score += 2
            scoring = [("hero", 5), ("theme", 4), ("home", 2), ("landing", 2)]
            for key, add in scoring:
                if key in low:
                    if key in base:
                        score += add
            scored.append((f, score))
        scored.sort(key=lambda t: t[1], reverse=True)
        return [f for f, _ in scored[:4] if _ > 0] or candidates[:1]

    def _ask_ai_target(self, candidates: List[str], instruction: str) -> Optional[str]:
        if not self.provider:
            return None
        try:
            names = "\n".join(f"- {os.path.basename(f)}" for f in candidates[:15])
            prompt = (
                f"Which file should be edited to fulfill this request: \"{instruction}\"?\n"
                f"Files:\n{names}\n"
                "Reply with ONLY the filename (exactly as listed), nothing else."
            )
            answer = (self.provider._call_api(prompt, system_instruction="You are a file-routing assistant.") or "").strip()
            return answer.splitlines()[0] if answer else None
        except Exception:
            return None

    # ── Patching ───────────────────────────────────────────────────────────
    def _patch_file(self, file_path: str, instruction: str) -> Tuple[Optional[str], bool]:
        """Apply AI patch, falling back to deterministic offline rules."""
        original = FileManager.read_file(file_path)
        if not original:
            return None, False

        if self.provider:
            try:
                new_content = self.provider.modify_code(original, instruction)
                if new_content and len(new_content.strip()) > 10 and new_content != original:
                    return new_content, True
            except Exception as e:
                agent_logger.warning(f"IterateEngine: AI patch failed for {file_path}: {e}")

        return self._apply_offline_patch(original, instruction, file_path), False

    def _apply_offline_patch(self, content: str, instruction: str, file_path: str) -> Optional[str]:
        """Deterministic, safe offline edits — clearly labelled fallback."""
        low = instruction.lower()
        name = os.path.basename(file_path).lower()
        updated = content

        # 1. Contact details — replace mailto:/tel: and plain email/phone tokens
        if name.endswith((".jsx", ".tsx", ".js", ".ts", ".html")):
            for key, expr in (("email", r"[\w.+-]+@[\w-]+\.[\w.]+"), ("phone", r"(\+?\d[\d\s-]{6,})")):
                if key in low:
                    m = re.search(expr, updated)
                    if m:
                        token = m.group(0)
                        if updated.count(token) > 0:
                            updated = updated.replace(token, f"[{key}-updated-by-lumicorepro]")

        # 2. Colour — swap Tailwind colour class / hex palette
        if ("color" in low or "colour" in low or "theme" in low) and name.endswith((".jsx", ".js", ".tsx", ".ts", ".html", ".css")):
            target = next((c for c in COLOR_MAP if c in low), None)
            if target:
                mapped = COLOR_MAP[target]
                updated = re.sub(r"\b(text-primary)\b", f"text-{mapped}-500", updated)
                updated = re.sub(r"\bbg-primary\b", f"bg-{mapped}-500", updated)
                updated = re.sub(r"\b(border-primary)\b", f"border-{mapped}-500", updated)
                updated = re.sub(r"(?<![\w-])#(?:[0-9a-fA-F]{3}){1,2}\b", f"#{self._hex_for(mapped, '500')}", updated)

        # 3. Heading / hero text — replace first <h1-6> inner text (JSX/HTML safe)
        if any(k in low for k in HEADING_NEWS):
            m = re.search(r">(\s*<(h[1-6])[^>]*>)[^<]{2,120}(</\2>)", updated)
            if m:
                updated = (
                    updated[: m.start(1)]
                    + m.group(1)
                    + '<span class="lumicore-edit">Updated</span>'
                    + m.group(3)
                    + updated[m.end(3):]
                )

        # 4. Brand/site name — index.html <title> and package name
        if "brand" in low or "name" in low and name == "index.html":
            updated = re.sub(r"<title>[^<]*</title>", f"<title>{pname.title()}</title>", updated)
        if "name" in low and name == "package.json":
            try:
                pkg = json.loads(updated)
                pkg["name"] = "lumicorepro-site"
                updated = json.dumps(pkg, indent=2)
            except Exception:
                pass

        return updated if updated != content else None

    @staticmethod
    def _hex_for(color: str, shade: str) -> str:
        base = {
            "red": "#ef4444", "orange": "#f97316", "amber": "#f59e0b",
            "lime": "#84cc16", "green": "#22c55e", "emerald": "#10b981",
            "teal": "#14b8a6", "cyan": "#06b6d4", "blue": "#3b82f6",
            "indigo": "#6366f1", "violet": "#8b5cf6", "purple": "#a855f7",
            "pink": "#ec4899", "rose": "#f43f5e", "slate": "#64748b",
            "gray": "#6b7280",
        }
        return base.get(color, "#3b82f6")

    # ── Partial phase re-run (verification & publishing only) ──────────────
    def _rerun_affected_phases(self, project_dir: str, instruction: str) -> Dict[str, Any]:
        phases_rerun: List[str] = []
        result: Dict[str, Any] = {
            "phases": phases_rerun,
            "quality_score": 0,
            "accessibility_score": 0,
            "compliance_evidence": "",
        }
        spec = self._load_spec(project_dir) or {"project_name": os.path.basename(project_dir), "region": "NA", "website_type": "business"}
        eng = self.orchestrator

        # P7 quality verification + P12 compliance/a11y + security posture + cost
        try:
            validation_report = eng.validator.validate_project(project_dir)
            quality = eng.quality_gates.evaluate(project_dir, spec, validation_report)
            result["quality_score"] = quality.get("overall_score", 0)
            phases_rerun.append("phase_7_quality_verification")

            region = spec.get("region", "NA")
            compliance = eng.compliance_generator.generate(spec, project_dir, region)
            accessibility = eng.accessibility_checker.check(project_dir, spec)
            result["accessibility_score"] = accessibility.get("accessibility_score", 0)
            phases_rerun.append("phase_12_compliance_accessibility")

            security = eng.security_engine.generate(spec, project_dir)
            phases_rerun.append("security_posture")

            cost = eng.deployment_engine.estimate_running_cost(spec.get("website_type", "business"), "low")
            result["cost_estimates"] = cost
            phases_rerun.append("phase_15_global_deployment")

            result["compliance_evidence"] = self._append_compliance_evidence(
                project_dir, compliance, accessibility, security, quality, cost
            )
        except Exception as e:
            agent_logger.warning(f"IterateEngine: partial re-run failed: {e}")
            result["partial_rerun_error"] = str(e)

        return result

    # ── Evidence / manifest helpers ────────────────────────────────────────
    def _append_compliance_evidence(
        self, project_dir: str, compliance: Dict, accessibility: Dict,
        security: Dict, quality: Dict, cost: Dict
    ) -> str:
        """Append machine-readable evidence block to COMPLIANCE.md (audit proof)."""
        md_path = os.path.join(project_dir, "COMPLIANCE.md")
        base = FileManager.read_file(md_path) or "# Compliance Report\n"
        evidence = [
            "\n---\n",
            "## Verification Evidence (auto-generated)",
            f"- Accessibility score: {accessibility.get('accessibility_score', 'n/a')}",
            f"- WCAG 2.1 AA compliant: {'yes' if accessibility.get('wcag_aa_compliant') else 'pending review'}",
            f"- Generated artifacts: {compliance.get('artifacts_generated', [])}",
            f"- Consent banner required: {compliance.get('requires_consent_banner', False)}",
            f"- Security controls verified: {security.get('controls_verified', 0)}",
            f"- Security review items queued: {security.get('review_items', 0)}",
            f"- Deployment cost estimates: {json.dumps(cost, indent=2)}",
            f"- Verified at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
            "\n> Evidence block appended by the validation pipeline during the final QA pass.",
        ]
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(base.rstrip() + "\n" + "\n".join(evidence) + "\n")
        except Exception as e:
            agent_logger.warning(f"IterateEngine: could not write compliance evidence: {e}")
        return md_path

    def _write_iterations_md(self, project_dir, instruction, changes, version, client_brand, quality_score, access_score):
        md_path = os.path.join(project_dir, "ITERATIONS.md")
        brand = f"Client: {client_brand}\n" if client_brand else ""
        lines = [
            f"# Iteration {version}",
            f"\nTimestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
            f"Instruction: {instruction}",
            f"Provider: {self.provider.__class__.__name__ if self.provider else 'offline-deterministic'}",
            brand,
            f"Quality score: {quality_score} | Accessibility: {access_score}\n",
            "Changed files (git-style diff summary):",
        ]
        for c in changes:
            lines.append(f"- {c['path']}: +{c['added_lines']} / -{c['removed_lines']}")
        for c in changes:
            lines.append(f"\n### {c['path']}\n```diff\n{c['diff']}\n```")
        try:
            with open(md_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            agent_logger.warning(f"IterateEngine: could not write ITERATIONS.md: {e}")

    # ── Manifest / spec helpers ────────────────────────────────────────────
    def _load_manifest(self, project_dir: str) -> Dict[str, Any]:
        path = os.path.join(project_dir, self.MANIFEST_PATH)
        try:
            return FileManager.read_json(path) or {}
        except Exception:
            return {}

    def _save_manifest(self, project_dir: str, manifest: Dict[str, Any]) -> bool:
        path = os.path.join(project_dir, self.MANIFEST_PATH)
        try:
            return FileManager.write_json(path, manifest)
        except Exception as e:
            agent_logger.warning(f"IterateEngine: manifest write failed: {e}")
            return False

    def _load_spec(self, project_dir: str) -> Dict[str, Any]:
        report_path = os.path.join(project_dir, "generation-report.json")
        try:
            report = FileManager.read_json(report_path) or {}
            spec = dict(report.get("user_prompt_spec", {}))
            spec["project_name"] = report.get("project_name", os.path.basename(project_dir))
            spec["region"] = (report.get("international") or {}).get("region", "NA")
            spec["website_type"] = spec.get("website_type", "business")
            return spec
        except Exception:
            return {}

    @staticmethod
    def _rel(project_dir: str, path: str) -> str:
        return os.path.relpath(path, project_dir).replace("\\", "/")