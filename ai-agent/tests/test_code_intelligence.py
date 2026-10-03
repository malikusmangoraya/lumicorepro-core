"""
Tests for Code Intelligence Module.
Run with: pytest ai-agent/tests/test_code_intelligence.py -v
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.code_intelligence import CodeIntelligence, CodeMetrics, CodeIssue, get_code_intelligence

@pytest.fixture
def ci():
    instance = CodeIntelligence()
    instance.enabled = True
    return instance

def test_check_security_sql_injection(ci):
    code = 'db.execute("SELECT * FROM users WHERE id = " + user_id)'
    issues = ci._check_security(code, "test.py")
    assert any("sql injection" in i.message.lower() for i in issues)

def test_check_security_xss(ci):
    code = '<div dangerouslySetInnerHTML={{ __html: userContent }} />'
    issues = ci._check_security(code, "Component.jsx")
    assert any("xss" in i.message.lower() for i in issues)

def test_check_security_hardcoded_secrets(ci):
    code = 'api_key = "sk_live_1234567890abcdef123456"'
    issues = ci._check_security(code, "config.py")
    assert any("secrets" in i.message.lower() for i in issues)

def test_check_security_clean_code(ci):
    code = 'def add(a, b):\n    return a + b'
    issues = ci._check_security(code, "math.py")
    assert len(issues) == 0

def test_check_performance_nested_loops(ci):
    code = "for i in range(10):\n    for j in range(10):\n        print(i, j)"
    issues = ci._check_performance(code, "loop.py")
    assert any("inefficient loop" in i.message.lower() for i in issues)

def test_check_python_quality_long_function(ci):
    body = "\n".join([f"    x_{i} = {i}" for i in range(55)])
    code = f"def very_long_function():\n{body}\n    return x_0\n"
    issues = ci._check_python_quality(code, "long.py")
    assert any("too long" in i.message.lower() for i in issues)

def test_check_javascript_quality_console_and_var(ci):
    code = "var name = 'test';\nconsole.log(name);"
    issues = ci._check_javascript_quality(code, "app.js")
    assert any("console" in i.message.lower() for i in issues)
    assert any("var" in i.message.lower() for i in issues)

def test_generate_report(ci):
    metrics = CodeMetrics(
        lines_of_code=150,
        complexity_average=4.5,
        maintainability_index=75.0,
        test_coverage=85.0,
        security_score=95.0,
        performance_score=90.0,
        issues=[]
    )
    report = ci.generate_report(metrics)
    assert "CODE INTELLIGENCE REPORT" in report
    assert "Lines of Code: 150" in report
    assert "OVERALL ASSESSMENT" in report

def test_get_code_intelligence_singleton():
    c1 = get_code_intelligence()
    c2 = get_code_intelligence()
    assert c1 is c2
