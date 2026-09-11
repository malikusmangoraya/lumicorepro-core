import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.compliance_generator import ComplianceGenerator


class TestComplianceGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lumicore-compliance-")
        self.generator = ComplianceGenerator()
        self.spec = {
            "project_name": "Acme Store",
            "website_type": "ecommerce",
            "industry": "retail",
        }
        self.region = "EU"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_generate_writes_all_artifacts(self):
        report = self.generator.generate(self.spec, self.tmp, region=self.region)
        expected = [
            os.path.join(self.tmp, "COMPLIANCE.md"),
            os.path.join(self.tmp, "frontend", "public", "privacy-policy.html"),
            os.path.join(self.tmp, "frontend", "public", "terms-of-service.html"),
            os.path.join(self.tmp, "frontend", "src", "config", "cookie-config.js"),
            os.path.join(self.tmp, "frontend", "src", "components", "common", "CookieConsent.jsx"),
        ]
        for path in expected:
            self.assertTrue(os.path.exists(path), f"missing {path}")
        self.assertIn("GDPR", report["reg_codes"])
        self.assertTrue(report["requires_consent_banner"])
        self.assertEqual(report["cookie_policy_model"], "opt-in")

    def test_terms_of_service_has_governing_law_and_sections(self):
        self.generator.generate(self.spec, self.tmp, region="EU")
        tos = open(os.path.join(self.tmp, "frontend", "public", "terms-of-service.html"), encoding="utf-8").read()
        self.assertIn("Terms of Service", tos)
        self.assertIn("Governing Law", tos)
        self.assertIn("European Union", tos)
        self.assertIn("AI-Generated Content", tos)

    def test_cookie_consent_component_is_valid_jsx_and_imports_config(self):
        self.generator.generate(self.spec, self.tmp, region="EU")
        jsx = open(
            os.path.join(self.tmp, "frontend", "src", "components", "common", "CookieConsent.jsx"),
            encoding="utf-8",
        ).read()
        self.assertIn("import { COOKIE_CONFIG, hasConsent, saveConsent }", jsx)
        self.assertIn("role=\"dialog\"", jsx)
        self.assertIn("Escape", jsx)
        self.assertIn("Save preferences", jsx)
        self.assertIn("OPT-IN consent banner", jsx)
        # No leftover template tokens
        self.assertNotIn("__REGION__", jsx)

    def test_opt_out_model_uses_opt_out_defaults(self):
        applicable = [{"code": "CCPA", **self.generator.REGULATIONS["CCPA"]}]
        self.assertEqual(self.generator._get_cookie_model(applicable), "opt-out")
        jsx = self.generator._build_cookie_consent_component(applicable, "NA")
        self.assertIn("OPT-OUT consent banner", jsx)
        cfg = self.generator._build_cookie_config(applicable, "NA")
        self.assertIn("requireConsent: false", cfg)
        self.assertIn("showBanner: false", cfg)

    def test_no_ai_fallback_needed_and_artifacts_reported(self):
        report = self.generator.generate(self.spec, self.tmp, region="APAC")
        self.assertEqual(report["region"], "APAC")
        self.assertIn("PDPA", report["reg_codes"])
        self.assertEqual(len(report["artifacts_generated"]), 5)


if __name__ == "__main__":
    unittest.main()