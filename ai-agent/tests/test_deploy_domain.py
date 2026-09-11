"""
Tests for deploy custom-domain wizard.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.deploy_engine import add_domain, domain_guide


class TestDomainWizard:
    def test_domain_guide_vercel(self):
        guide = domain_guide("vercel", "mybrand.com")
        assert guide["status"] == "ok"
        assert guide["domain"] == "mybrand.com"
        assert any(r["type"] == "CNAME" for r in guide["records"])
        assert len(guide["steps"]) >= 3

    def test_domain_guide_vps_has_nginx(self):
        guide = domain_guide("vps", "mybrand.com")
        assert guide["status"] == "ok"
        assert "server_name mybrand.com" in guide["nginx_block"]

    def test_domain_guide_rejects_invalid(self):
        guide = domain_guide("vercel", "")
        assert guide["status"] == "failed"

    def test_add_domain_guide_when_no_token(self):
        outcome = add_domain("vercel", "mybrand.com")
        assert outcome["status"] in ("guide", "live")
        assert "mybrand.com" in outcome["domain"]