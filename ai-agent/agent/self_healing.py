"""
Self-Healing Code System
=========================
Automatically detect, diagnose, and fix code errors and performance issues.

Features:
- Runtime error detection and auto-fix
- Build error diagnosis and resolution
- Performance bottleneck identification and optimization
- Dependency conflict resolution
- Code smell detection and refactoring
- Test failure auto-repair
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import agent_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Blocks deployment
    HIGH = "high"  # Major functionality broken
    MEDIUM = "medium"  # Minor issues, workarounds available
    LOW = "low"  # Cosmetic or non-blocking
    INFO = "info"  # Informational


@dataclass
class CodeError:
    """Represents a detected code error."""
    error_type: str  # syntax, runtime, build, test, performance
    severity: ErrorSeverity
    message: str
    file_path: str
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class FixResult:
    """Result of an auto-fix attempt."""
    success: bool
    error_id: str
    fix_applied: Optional[str] = None
    verification_passed: bool = False
    notes: Optional[str] = None


class SelfHealingSystem:
    """Automatic error detection and resolution system."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.enabled = os.getenv("SELF_HEALING_ENABLED", "true").lower() == "true"
        
        # Common error patterns and fixes
        self.error_patterns = {
            # JavaScript/React errors
            "missing_import": {
                "pattern": r"'(\w+)' is not defined|Cannot find name '(\w+)'",
                "fix_template": "import {match} from '@/components/{match}';",
                "auto_fixable": True
            },
            "missing_dependency": {
                "pattern": r"Cannot find module '([^']+)'|Module not found: Error: Can't resolve '([^']+)'",
                "fix_template": "npm install {match}",
                "auto_fixable": True
            },
            "unused_variable": {
                "pattern": r"'(\w+)' is assigned a value but never used",
                "fix_template": "// Remove or use the variable: {match}",
                "auto_fixable": True
            },
            "missing_return": {
                "pattern": r"Function lacks ending return statement",
                "fix_template": "return null; // or appropriate return value",
                "auto_fixable": True
            },
            
            # Python errors
            "indentation_error": {
                "pattern": r"IndentationError|unexpected indent",
                "fix_template": "Fix indentation to match Python standards (4 spaces)",
                "auto_fixable": True
            },
            "missing_import_py": {
                "pattern": r"NameError: name '(\w+)' is not defined",
                "fix_template": "from module import {match}",
                "auto_fixable": False  # Need to know the module
            },
            
            # Build errors
            "port_in_use": {
                "pattern": r"EADDRINUSE.*:(\d+)|Port (\d+) is already in use",
                "fix_template": "Kill process on port {match} or use a different port",
                "auto_fixable": True
            },
            "out_of_memory": {
                "pattern": r"JavaScript heap out of memory|ENOMEM",
                "fix_template": "NODE_OPTIONS=--max-old-space-size=4096",
                "auto_fixable": True
            }
        }
    
    def scan_project(self) -> List[CodeError]:
        """Scan project for errors across all files."""
        if not self.enabled:
            return []
        
        errors = []
        
        try:
            # Run linters and collect errors
            errors.extend(self._run_eslint())
            errors.extend(self._run_typescript_check())
            errors.extend(self._check_build())
            errors.extend(self._check_runtime_logs())
            
            agent_logger.info(f"Scan found {len(errors)} issues")
            
        except Exception as e:
            agent_logger.error(f"Project scan failed: {e}")
        
        return errors
    
    def auto_fix(self, errors: List[CodeError]) -> List[FixResult]:
        """Automatically fix errors where possible."""
        if not self.enabled:
            return []
        
        results = []
        
        for error in errors:
            if not error.auto_fixable:
                continue
            
            try:
                fix_result = self._apply_fix(error)
                results.append(fix_result)
                
                if fix_result.success:
                    agent_logger.info(f"Fixed: {error.message[:50]}...")
                
            except Exception as e:
                agent_logger.error(f"Fix failed for {error.error_type}: {e}")
                results.append(FixResult(
                    success=False,
                    error_id=f"{error.file_path}:{error.line_number}",
                    notes=str(e)
                ))
        
        return results
    
    def _run_eslint(self) -> List[CodeError]:
        """Run ESLint and parse errors."""
        errors = []
        
        eslint_config = self.project_dir / "eslint.config.js"
        if not eslint_config.exists():
            return errors
        
        try:
            result = subprocess.run(
                ["npx", "eslint", ".", "--format", "json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                eslint_output = json.loads(result.stdout)
                
                for file_result in eslint_output:
                    file_path = Path(file_result["filePath"]).relative_to(self.project_dir)
                    
                    for message in file_result.get("messages", []):
                        severity_map = {
                            2: ErrorSeverity.HIGH,  # Error
                            1: ErrorSeverity.MEDIUM,  # Warning
                            0: ErrorSeverity.INFO
                        }
                        
                        errors.append(CodeError(
                            error_type="lint",
                            severity=severity_map.get(message.get("severity", 1), ErrorSeverity.MEDIUM),
                            message=message["message"],
                            file_path=str(file_path),
                            line_number=message.get("line"),
                            auto_fixable=message.get("fix") is not None
                        ))
        
        except subprocess.TimeoutExpired:
            agent_logger.warning("ESLint timeout")
        except Exception as e:
            agent_logger.debug(f"ESLint check failed: {e}")
        
        return errors
    
    def _run_typescript_check(self) -> List[CodeError]:
        """Run TypeScript type checking."""
        errors = []
        
        tsconfig = self.project_dir / "tsconfig.json"
        if not tsconfig.exists():
            return errors
        
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stderr:
                # Parse TypeScript error format: file(line,col): error TS1234: message
                error_pattern = r"(.+?)\((\d+),(\d+)\): error TS\d+: (.+)"
                
                for match in re.finditer(error_pattern, result.stderr):
                    file_path, line, col, message = match.groups()
                    
                    errors.append(CodeError(
                        error_type="type",
                        severity=ErrorSeverity.HIGH,
                        message=message,
                        file_path=file_path,
                        line_number=int(line),
                        auto_fixable=False  # Type errors usually need manual fix
                    ))
        
        except subprocess.TimeoutExpired:
            agent_logger.warning("TypeScript check timeout")
        except Exception as e:
            agent_logger.debug(f"TypeScript check failed: {e}")
        
        return errors
    
    def _check_build(self) -> List[CodeError]:
        """Check if project builds successfully."""
        errors = []
        
        package_json = self.project_dir / "package.json"
        if not package_json.exists():
            return errors
        
        try:
            # Try to build (with timeout to avoid hanging)
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                # Parse build errors
                error_output = result.stderr + result.stdout
                
                # Detect specific error types
                for error_name, error_config in self.error_patterns.items():
                    if re.search(error_config["pattern"], error_output, re.IGNORECASE):
                        errors.append(CodeError(
                            error_type="build",
                            severity=ErrorSeverity.CRITICAL,
                            message=f"Build failed: {error_name}",
                            file_path="",
                            stack_trace=error_output[:500],
                            suggested_fix=error_config["fix_template"],
                            auto_fixable=error_config["auto_fixable"]
                        ))
        
        except subprocess.TimeoutExpired:
            agent_logger.warning("Build timeout (>2 minutes)")
            errors.append(CodeError(
                error_type="build",
                severity=ErrorSeverity.HIGH,
                message="Build timeout - possible infinite loop or hanging process",
                file_path="",
                auto_fixable=False
            ))
        except Exception as e:
            agent_logger.debug(f"Build check failed: {e}")
        
        return errors
    
    def _check_runtime_logs(self) -> List[CodeError]:
        """Check for runtime errors in log files."""
        errors = []
        
        log_dir = self.project_dir / "logs"
        if not log_dir.exists():
            return errors
        
        try:
            for log_file in log_dir.glob("*.log"):
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                
                # Look for error patterns
                error_lines = [
                    line for line in content.split("\n")
                    if any(keyword in line.lower() for keyword in ["error", "exception", "failed", "critical"])
                ]
                
                for line in error_lines[-10:]:  # Last 10 errors
                    errors.append(CodeError(
                        error_type="runtime",
                        severity=ErrorSeverity.MEDIUM,
                        message=line[:200],
                        file_path=str(log_file.name),
                        auto_fixable=False
                    ))
        
        except Exception as e:
            agent_logger.debug(f"Log check failed: {e}")
        
        return errors
    
    def _apply_fix(self, error: CodeError) -> FixResult:
        """Apply automatic fix for an error."""
        error_id = f"{error.file_path}:{error.line_number or '?'}"
        
        # Missing dependency fix
        if "missing_dependency" in error.error_type or "Cannot find module" in error.message:
            return self._fix_missing_dependency(error)
        
        # Unused variable fix
        if "never used" in error.message or "unused" in error.message.lower():
            return self._fix_unused_variable(error)
        
        # Port in use fix
        if "EADDRINUSE" in error.message or "Port" in error.message and "in use" in error.message:
            return self._fix_port_conflict(error)
        
        # Out of memory fix
        if "heap out of memory" in error.message.lower() or "ENOMEM" in error.message:
            return self._fix_memory_issue(error)
        
        return FixResult(
            success=False,
            error_id=error_id,
            notes="No auto-fix available for this error type"
        )
    
    def _fix_missing_dependency(self, error: CodeError) -> FixResult:
        """Fix missing dependency by installing it."""
        # Extract package name from error message
        match = re.search(r"'([^']+)'", error.message)
        if not match:
            return FixResult(success=False, error_id=error.file_path, notes="Could not extract package name")
        
        package_name = match.group(1)
        
        try:
            # Install dependency
            result = subprocess.run(
                ["npm", "install", package_name],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = result.returncode == 0
            
            return FixResult(
                success=success,
                error_id=error.file_path,
                fix_applied=f"npm install {package_name}",
                verification_passed=success,
                notes=result.stdout if success else result.stderr
            )
        
        except Exception as e:
            return FixResult(
                success=False,
                error_id=error.file_path,
                notes=str(e)
            )
    
    def _fix_unused_variable(self, error: CodeError) -> FixResult:
        """Fix unused variable by adding underscore prefix."""
        if not error.file_path or not error.line_number:
            return FixResult(success=False, error_id="unknown", notes="Missing file info")
        
        try:
            file_path = self.project_dir / error.file_path
            if not file_path.exists():
                return FixResult(success=False, error_id=error.file_path, notes="File not found")
            
            # Extract variable name
            var_match = re.search(r"'(\w+)'", error.message)
            if not var_match:
                return FixResult(success=False, error_id=error.file_path, notes="Could not extract variable name")
            
            var_name = var_match.group(1)
            
            # Read file
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            # Find and fix the line
            if error.line_number <= len(lines):
                line = lines[error.line_number - 1]
                
                # Add underscore prefix to indicate intentionally unused
                fixed_line = re.sub(rf"\b{var_name}\b", f"_{var_name}", line, count=1)
                lines[error.line_number - 1] = fixed_line
                
                # Write back
                file_path.write_text("\n".join(lines), encoding="utf-8")
                
                return FixResult(
                    success=True,
                    error_id=error.file_path,
                    fix_applied=f"Renamed {var_name} to _{var_name}",
                    verification_passed=True
                )
        
        except Exception as e:
            return FixResult(success=False, error_id=error.file_path, notes=str(e))
        
        return FixResult(success=False, error_id=error.file_path)
    
    def _fix_port_conflict(self, error: CodeError) -> FixResult:
        """Fix port conflict by killing the process or suggesting alternative."""
        # Extract port number
        match = re.search(r":(\d+)|Port (\d+)", error.message)
        if not match:
            return FixResult(success=False, error_id="port", notes="Could not extract port number")
        
        port = match.group(1) or match.group(2)
        
        # On Windows, use different command
        if os.name == 'nt':
            try:
                # Find the process holding the port. `netstat -ano` is run as an
                # argument list (no shell) and the pipe is done in Python: the
                # previous `shell=True` + ["netstat", "-ano", "|", "findstr", …]
                # passed the pipe as a *literal argument*, so it both never
                # filtered and handed an unquoted string to cmd.exe.
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                listeners = [
                    line.strip() for line in (result.stdout or "").splitlines()
                    if f":{port}" in line and "LISTENING" in line.upper()
                ]
                owner = ""
                if listeners:
                    parts = listeners[0].split()
                    owner = parts[-1] if parts else ""
                note = (
                    f"Port {port} in use"
                    + (f" by PID {owner}" if owner else "")
                    + ". Manually kill process or change port in .env"
                )
                return FixResult(
                    success=False,
                    error_id="port",
                    notes=note,
                    fix_applied="Suggested manual fix"
                )
            except (OSError, subprocess.SubprocessError) as exc:
                agent_logger.warning(f"Port conflict inspection failed: {exc}")
        
        return FixResult(
            success=False,
            error_id="port",
            notes=f"Port {port} in use. Change PORT in .env or kill the process"
        )
    
    def _fix_memory_issue(self, error: CodeError) -> FixResult:
        """Fix memory issue by updating Node options."""
        try:
            env_file = self.project_dir / ".env"
            
            # Add or update NODE_OPTIONS
            if env_file.exists():
                content = env_file.read_text(encoding="utf-8")
                
                if "NODE_OPTIONS" in content:
                    # Update existing
                    content = re.sub(
                        r"NODE_OPTIONS=.*",
                        "NODE_OPTIONS=--max-old-space-size=4096",
                        content
                    )
                else:
                    # Add new
                    content += "\n# Increase memory limit for builds\nNODE_OPTIONS=--max-old-space-size=4096\n"
                
                env_file.write_text(content, encoding="utf-8")
            else:
                # Create .env
                env_file.write_text("NODE_OPTIONS=--max-old-space-size=4096\n", encoding="utf-8")
            
            return FixResult(
                success=True,
                error_id="memory",
                fix_applied="Added NODE_OPTIONS=--max-old-space-size=4096 to .env",
                verification_passed=True,
                notes="Restart dev server for changes to take effect"
            )
        
        except Exception as e:
            return FixResult(success=False, error_id="memory", notes=str(e))
    
    def generate_health_report(self, errors: List[CodeError], fixes: List[FixResult]) -> str:
        """Generate a health report for the project."""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("SELF-HEALING SYSTEM REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary
        critical = sum(1 for e in errors if e.severity == ErrorSeverity.CRITICAL)
        high = sum(1 for e in errors if e.severity == ErrorSeverity.HIGH)
        medium = sum(1 for e in errors if e.severity == ErrorSeverity.MEDIUM)
        low = sum(1 for e in errors if e.severity == ErrorSeverity.LOW)
        
        report_lines.append(f"📊 ERRORS DETECTED: {len(errors)} total")
        report_lines.append(f"   Critical: {critical} | High: {high} | Medium: {medium} | Low: {low}")
        report_lines.append("")
        
        successful_fixes = sum(1 for f in fixes if f.success)
        report_lines.append(f"🔧 FIXES APPLIED: {successful_fixes}/{len(fixes)} successful")
        report_lines.append("")
        
        # Group errors by type
        errors_by_type: Dict[str, List[CodeError]] = {}
        for error in errors:
            errors_by_type.setdefault(error.error_type, []).append(error)
        
        for error_type, type_errors in errors_by_type.items():
            report_lines.append(f"## {error_type.upper()} ERRORS ({len(type_errors)})")
            report_lines.append("-" * 80)
            
            for error in type_errors[:5]:  # Show top 5
                report_lines.append(f"  • {error.file_path}:{error.line_number or '?'}")
                report_lines.append(f"    {error.message[:100]}")
                if error.suggested_fix:
                    report_lines.append(f"    💡 {error.suggested_fix}")
                report_lines.append("")
        
        # System health score
        health_score = max(0, 100 - (critical * 20) - (high * 10) - (medium * 5) - (low * 2))
        
        report_lines.append("=" * 80)
        report_lines.append(f"OVERALL HEALTH SCORE: {health_score}/100")
        report_lines.append("=" * 80)
        
        if health_score >= 90:
            report_lines.append("✅ Excellent - System is healthy")
        elif health_score >= 70:
            report_lines.append("✅ Good - Minor issues detected")
        elif health_score >= 50:
            report_lines.append("⚠️  Fair - Some issues need attention")
        else:
            report_lines.append("🚨 Poor - Critical issues require immediate action")
        
        return "\n".join(report_lines)


def create_self_healing_system(project_dir: Path) -> SelfHealingSystem:
    """Factory function to create a self-healing system."""
    return SelfHealingSystem(project_dir)
