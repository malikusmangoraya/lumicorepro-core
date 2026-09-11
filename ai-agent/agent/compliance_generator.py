"""
Compliance Generator — LumicorePro AI Agent
============================================
Phase: International Delivery (Phase 11)

Generates legally-aware compliance artifacts for international markets:
  - GDPR (EU/UK)         → Cookie consent, Privacy Policy template, DPA checklist
  - CCPA (California US) → Do Not Sell, Data Subject Rights
  - PDPA (Thailand/SG)   → Personal Data Protection
  - POPIA (South Africa) → Protection of Personal Information
  - PIPEDA (Canada)      → Personal Information Protection
  - LGPD (Brazil)        → Lei Geral de Proteção de Dados
  - KVKK (Turkey)        → Kişisel Verileri Koruma Kanunu
  - PK Data Laws         → PECA 2016 / Pakistan data guidelines
  - MENA region          → Generic privacy template + Arabic localisation

Output:
  - COMPLIANCE.md          written to generated project root
  - privacy-policy.html    written to frontend/public/
  - cookie-config.js       written to frontend/src/config/
  - compliance_report dict returned to orchestrator
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger


class ComplianceGenerator:
    """Generates GDPR/CCPA/PDPA/regional compliance docs & code stubs."""

    # ── Regulation definitions ────────────────────────────────────────────
    REGULATIONS: Dict[str, Dict[str, Any]] = {
        "GDPR": {
            "full_name":    "General Data Protection Regulation",
            "jurisdictions":["EU", "EEA", "UK"],
            "regions":      ["EU"],
            "key_rights":   [
                "Right to access personal data",
                "Right to rectification",
                "Right to erasure (right to be forgotten)",
                "Right to restrict processing",
                "Right to data portability",
                "Right to object",
                "Rights related to automated decision-making",
            ],
            "requirements": [
                "Cookie consent banner with granular controls",
                "Privacy policy in local language",
                "Data Processing Agreement (DPA) with processors",
                "Data breach notification within 72 hours",
                "Lawful basis for processing (consent / legitimate interest)",
                "DPO appointment if processing at scale",
                "Records of processing activities (ROPA)",
            ],
            "penalty":      "Up to €20M or 4% of global annual turnover",
            "cookie_policy": "Opt-in required for non-essential cookies",
        },
        "CCPA": {
            "full_name":    "California Consumer Privacy Act",
            "jurisdictions":["California, USA"],
            "regions":      ["NA"],
            "key_rights":   [
                "Right to know about personal information collected",
                "Right to delete personal information",
                "Right to opt-out of sale of personal information",
                "Right to non-discrimination",
            ],
            "requirements": [
                '"Do Not Sell My Personal Information" link in footer',
                "Privacy policy updated annually",
                "Consumer request fulfillment within 45 days",
                "Opt-out mechanism for data sale",
            ],
            "penalty":      "$2,500–$7,500 per intentional violation",
            "cookie_policy": "Opt-out model (cookies allowed by default)",
        },
        "PDPA": {
            "full_name":    "Personal Data Protection Act",
            "jurisdictions":["Thailand", "Singapore"],
            "regions":      ["APAC"],
            "key_rights":   [
                "Right to access and correct data",
                "Right to withdraw consent",
                "Right to erasure",
                "Right to data portability",
            ],
            "requirements": [
                "Explicit consent before collecting personal data",
                "Data retention policy must be defined",
                "Cross-border transfer restrictions",
                "Appointment of Data Protection Officer (DPO)",
            ],
            "penalty":      "Up to THB 5M / SGD 1M per violation",
            "cookie_policy": "Opt-in required",
        },
        "POPIA": {
            "full_name":    "Protection of Personal Information Act",
            "jurisdictions":["South Africa"],
            "regions":      ["AF"],
            "key_rights":   [
                "Right to be notified",
                "Right to access",
                "Right to correction or deletion",
                "Right to object to processing",
            ],
            "requirements": [
                "Information Officer registration with regulator",
                "PAIA manual must be available",
                "Breach notification within reasonable time",
                "Data minimisation principle",
            ],
            "penalty":      "Up to ZAR 10M or 10 years imprisonment",
            "cookie_policy": "Opt-in required",
        },
        "LGPD": {
            "full_name":    "Lei Geral de Proteção de Dados",
            "jurisdictions":["Brazil"],
            "regions":      ["LATAM"],
            "key_rights":   [
                "Right to confirmation",
                "Right to access",
                "Right to correction",
                "Right to anonymisation or deletion",
                "Right to portability",
                "Right to information about third parties",
                "Right to revoke consent",
            ],
            "requirements": [
                "Explicit purpose for data collection",
                "DPO (Encarregado) must be appointed",
                "Privacy policy in Portuguese",
                "Security incident reporting",
            ],
            "penalty":      "Up to 2% of revenue in Brazil (max R$50M)",
            "cookie_policy": "Opt-in required",
        },
        "PIPEDA": {
            "full_name":    "Personal Information Protection and Electronic Documents Act",
            "jurisdictions":["Canada"],
            "regions":      ["NA"],
            "key_rights":   [
                "Right to access personal information",
                "Right to challenge compliance",
                "Right to withdraw consent",
            ],
            "requirements": [
                "Privacy policy must be publicly available",
                "Accountability principle — designate a privacy officer",
                "Breach of security safeguards reporting",
            ],
            "penalty":      "Up to CAD $100,000",
            "cookie_policy": "Opt-in for sensitive data; opt-out for general",
        },
        "PECA_PK": {
            "full_name":    "Prevention of Electronic Crimes Act (Pakistan)",
            "jurisdictions":["Pakistan"],
            "regions":      ["SA"],
            "key_rights":   [
                "Protection of identity",
                "Protection from data breach",
            ],
            "requirements": [
                "No unauthorised interception of data",
                "Privacy policy in Urdu or English",
                "Data stored on servers accessible to PTA if required",
                "Cyber crime reporting mechanism",
            ],
            "penalty":      "Up to PKR 5M and/or 3 years imprisonment",
            "cookie_policy": "Recommended opt-in",
        },
        "KVKK": {
            "full_name":    "Kişisel Verileri Koruma Kanunu (Turkey)",
            "jurisdictions":["Turkey"],
            "regions":      ["MENA"],
            "key_rights":   [
                "Right to learn whether personal data is processed",
                "Right to access",
                "Right to demand correction",
                "Right to demand deletion",
                "Right to object",
            ],
            "requirements": [
                "Registration with VERBIS system",
                "Explicit consent for special categories",
                "Privacy notice in Turkish",
                "Data breach notification within reasonable time",
            ],
            "penalty":      "Up to TRY 1.8M",
            "cookie_policy": "Opt-in required",
        },
    }

    # ── Region → applicable regulations ──────────────────────────────────
    REGION_REGS: Dict[str, List[str]] = {
        "EU":    ["GDPR"],
        "NA":    ["CCPA", "PIPEDA"],
        "SA":    ["PECA_PK"],
        "MENA":  ["KVKK"],
        "APAC":  ["PDPA"],
        "AF":    ["POPIA"],
        "LATAM": ["LGPD"],
    }

    def generate(self, spec: Dict[str, Any], project_dir: str, region: str = "NA") -> Dict[str, Any]:
        """Generate all compliance artifacts for the given project and region."""
        agent_logger.info(f"ComplianceGenerator: Generating compliance for region={region}...")

        applicable = self._get_applicable_regs(region, spec)
        artifacts = []

        # 1. COMPLIANCE.md in project root
        md_path = os.path.join(project_dir, "COMPLIANCE.md")
        md_content = self._build_compliance_md(applicable, spec, region)
        self._write_file(md_path, md_content)
        artifacts.append(md_path)

        # 2. Privacy Policy HTML
        pp_dir = os.path.join(project_dir, "frontend", "public")
        os.makedirs(pp_dir, exist_ok=True)
        pp_path = os.path.join(pp_dir, "privacy-policy.html")
        pp_content = self._build_privacy_policy(applicable, spec, region)
        self._write_file(pp_path, pp_content)
        artifacts.append(pp_path)

        # 3. Terms of Service HTML
        tos_path = os.path.join(pp_dir, "terms-of-service.html")
        tos_content = self._build_terms_of_service(spec, region)
        self._write_file(tos_path, tos_content)
        artifacts.append(tos_path)

        # 4. Cookie Config JS
        cfg_dir = os.path.join(project_dir, "frontend", "src", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        cookie_path = os.path.join(cfg_dir, "cookie-config.js")
        cookie_content = self._build_cookie_config(applicable, region)
        self._write_file(cookie_path, cookie_content)
        artifacts.append(cookie_path)

        # 5. Cookie Consent Banner component
        banner_dir = os.path.join(project_dir, "frontend", "src", "components", "common")
        banner_path = os.path.join(banner_dir, "CookieConsent.jsx")
        banner_content = self._build_cookie_consent_component(applicable, region)
        self._write_file(banner_path, banner_content)
        artifacts.append(banner_path)

        report = {
            "region":              region,
            "applicable_regs":     [r["full_name"] for r in applicable],
            "reg_codes":           [r["code"] for r in applicable],
            "artifacts_generated": artifacts,
            "cookie_policy_model": self._get_cookie_model(applicable),
            "requires_dpo":        any(
                "DPO" in req or "Data Protection Officer" in req
                for r in applicable for req in r["requirements"]
            ),
            "requires_consent_banner": any(
                r.get("cookie_policy", "").startswith("Opt-in")
                for r in applicable
            ),
            "generated": {
                "cookie_consent_component": "frontend/src/components/common/CookieConsent.jsx",
                "terms_of_service": "frontend/public/terms-of-service.html",
            },
            "penalties":           {r["code"]: r["penalty"] for r in applicable},
        }

        agent_logger.info(
            f"ComplianceGenerator: {len(applicable)} regulations, "
            f"{len(artifacts)} artifacts written."
        )
        return report

    # ── Internal helpers ──────────────────────────────────────────────────
    def _get_applicable_regs(self, region: str, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return regulation dicts applicable to the region."""
        codes = self.REGION_REGS.get(region, ["GDPR"])  # default to strictest
        result = []
        for code in codes:
            if code in self.REGULATIONS:
                entry = {"code": code, **self.REGULATIONS[code]}
                result.append(entry)
        # If international/SaaS — add GDPR as baseline regardless
        if "GDPR" not in codes and spec.get("website_type") in ("saas", "dashboard", "fintech"):
            result.append({"code": "GDPR", **self.REGULATIONS["GDPR"]})
        return result

    def _get_cookie_model(self, applicable: List[Dict]) -> str:
        """Strictest cookie model across applicable regulations."""
        if any(r.get("cookie_policy", "").startswith("Opt-in") for r in applicable):
            return "opt-in"
        return "opt-out"

    def _write_file(self, path: str, content: str) -> None:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            agent_logger.warning(f"ComplianceGenerator: Could not write {path}: {e}")

    def _build_compliance_md(self, applicable: List[Dict], spec: Dict, region: str) -> str:
        project = spec.get("project_name", "Your Project")
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines = [
            f"# Compliance Report — {project}",
            f"\nPrepared: {date} | Region: {region}",
            "\n---\n",
            "## Applicable Regulations\n",
        ]
        for reg in applicable:
            lines.append(f"### {reg['full_name']} ({reg['code']})")
            lines.append(f"**Jurisdictions:** {', '.join(reg['jurisdictions'])}")
            lines.append(f"**Cookie Policy:** {reg.get('cookie_policy', 'N/A')}")
            lines.append(f"**Penalty:** {reg.get('penalty', 'N/A')}\n")
            lines.append("**Key User Rights:**")
            for right in reg["key_rights"]:
                lines.append(f"  - {right}")
            lines.append("\n**Implementation Requirements:**")
            for req in reg["requirements"]:
                lines.append(f"  - [ ] {req}")
            lines.append("")

        lines += [
            "---\n",
            "## Action Checklist\n",
            "- [x] Cookie Consent Banner — auto-generated `frontend/src/components/common/CookieConsent.jsx`",
            "- [x] Privacy Policy — auto-generated `frontend/public/privacy-policy.html`",
            "- [x] Terms of Service — auto-generated `frontend/public/terms-of-service.html`",
            "- [ ] Mount `<CookieConsent />` once in `App.jsx` (import from `./components/common/CookieConsent`)",
            "- [ ] Link Privacy Policy and Terms of Service in footer",
            "- [ ] Add 'Contact DPO / Privacy Officer' email to footer",
            "- [ ] Enable HTTPS (TLS 1.2+) in production",
            "- [ ] Implement data deletion endpoint `DELETE /api/users/:id`",
            "- [ ] Add rate limiting to all auth endpoints",
            "- [ ] Log all data access for audit trail",
            "\n---\n",
            "> ⚠️ **Disclaimer:** This document is provided for informational purposes.",
            "> Always consult a qualified legal professional before deployment.",
        ]
        return "\n".join(lines)

    def _build_privacy_policy(self, applicable: List[Dict], spec: Dict, region: str) -> str:
        project = spec.get("project_name", "Our Platform")
        regs = ", ".join(r["full_name"] for r in applicable)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Privacy Policy — {project}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }}
    h1 {{ color: #0d9488; }} h2 {{ color: #334155; margin-top: 2rem; }}
    a {{ color: #0d9488; }} footer {{ margin-top: 3rem; color: #64748b; font-size: 0.875rem; }}
  </style>
</head>
<body>
  <h1>Privacy Policy</h1>
  <p><strong>Last Updated:</strong> {datetime.now(timezone.utc).strftime("%B %d, %Y")}</p>
  <p>This Privacy Policy explains how <strong>{project}</strong> collects, uses, and protects your personal information.
     This policy is compliant with: <em>{regs}</em>.</p>

  <h2>1. Information We Collect</h2>
  <ul>
    <li>Account information (name, email, password hash)</li>
    <li>Transaction data (order history, payment method type — not card numbers)</li>
    <li>Usage data (pages visited, actions taken) via cookies and analytics</li>
    <li>Device information (IP address, browser type, operating system)</li>
  </ul>

  <h2>2. How We Use Your Information</h2>
  <ul>
    <li>To provide and improve our services</li>
    <li>To process transactions and send related notifications</li>
    <li>To comply with legal obligations</li>
    <li>To send marketing communications (only with your explicit consent)</li>
  </ul>

  <h2>3. Your Rights</h2>
  <p>Depending on your location, you may have the right to:</p>
  <ul>
    <li>Access the personal data we hold about you</li>
    <li>Request correction or deletion of your data</li>
    <li>Object to or restrict processing</li>
    <li>Data portability (receive your data in a machine-readable format)</li>
    <li>Withdraw consent at any time</li>
  </ul>

  <h2>4. Cookies</h2>
  <p>We use cookies to enhance your experience. You can manage cookie preferences via our Cookie Settings panel.
     Essential cookies are required for the site to function; analytics and marketing cookies require your consent.</p>

  <h2>5. Data Retention</h2>
  <p>We retain personal data for as long as necessary to provide our services and comply with legal obligations.
     Account data is retained for 3 years after account closure unless deletion is requested.</p>

  <h2>6. Third-Party Sharing</h2>
  <p>We do not sell your personal data. We may share data with trusted service providers
     (payment processors, cloud hosting, analytics) under strict data processing agreements.</p>

  <h2>7. International Transfers</h2>
  <p>Your data may be processed in countries outside your own. We ensure adequate protection
     through Standard Contractual Clauses (SCCs) or equivalent mechanisms.</p>

  <h2>8. Contact Us</h2>
  <p>For privacy-related requests, contact our Data Protection Officer at:
     <a href="mailto:privacy@{project.lower().replace(' ', '')}.com">
       privacy@{project.lower().replace(' ', '')}.com
     </a>
  </p>

  <footer>
    <p>© {datetime.now(timezone.utc).year} {project}. All rights reserved.</p>
    <p>⚠️ This is a template. Review with a qualified legal professional before publishing.</p>
  </footer>
</body>
</html>"""

    def _build_terms_of_service(self, spec: Dict[str, Any], region: str) -> str:
        project = spec.get("project_name", "Our Platform")
        law, jurisdiction = self._governing_law(region)
        email = f"legal@{project.lower().replace(' ', '')}.com"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Terms of Service — {project}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }}
    h1 {{ color: #0d9488; }} h2 {{ color: #334155; margin-top: 2rem; }}
    a {{ color: #0d9488; }} footer {{ margin-top: 3rem; color: #64748b; font-size: 0.875rem; }}
  </style>
</head>
<body>
  <h1>Terms of Service</h1>
  <p><strong>Last Updated:</strong> {datetime.now(timezone.utc).strftime("%B %d, %Y")}</p>
  <p>These Terms of Service ("Terms") govern your access to and use of <strong>{project}</strong> (the "Service").
     By accessing the Service, you agree to be bound by these Terms. Compliance framework: <em>{law.replace('_', ' ')}</em>.</p>

  <h2>1. Eligibility</h2>
  <p>You must be at least 16 years old (or the minimum legal age in your jurisdiction) to use the Service.
     If you are accessing the Service on behalf of an organization, you represent that you have authority to bind it.</p>

  <h2>2. Accounts</h2>
  <p>You are responsible for safeguarding your account credentials and for all activity under your account.
     You agree to provide accurate information and to notify us of any unauthorized use.</p>

  <h2>3. Acceptable Use</h2>
  <ul>
    <li>You may not use the Service for any unlawful purpose</li>
    <li>You may not attempt to disrupt, probe, or bypass the Service security</li>
    <li>You may not scrape, resell, or redistribute Service data without written consent</li>
    <li>You may not upload malicious code, content infringing third-party rights, or unlawful material</li>
  </ul>

  <h2>4. AI-Generated Content</h2>
  <p>Portions of the Service may use artificial intelligence. AI-generated output is provided on an "as is" basis,
     may be incomplete or inaccurate, and should be independently reviewed before commercial use.</p>

  <h2>5. Payments</h2>
  <p>Subscription and transaction charges are non-refundable except where required by consumer law.
     You authorize the payment method you provide to be charged for all fees due. Prices may change upon renewal with notice.</p>

  <h2>6. Intellectual Property</h2>
  <p>The Service, including its software, design, and content, is owned by {project} or its licensors.
     You retain all rights to content you submit; you grant us a limited license to operate the Service.</p>

  <h2>7. Termination</h2>
  <p>We may suspend or terminate your access for a material breach of these Terms. You may stop using the Service at any time.
     Sections that by their nature survive termination shall do so (payments, IP, liability, governing law).</p>

  <h2>8. Limitation of Liability</h2>
  <p>To the maximum extent permitted by law, {project} shall not be liable for indirect, incidental, special, or consequential damages,
     including lost profits or data, arising out of your use of the Service. Our aggregate liability is limited to the amounts paid by you in the prior 12 months.</p>

  <h2>9. Governing Law</h2>
  <p>These Terms are governed by the laws of <strong>{jurisdiction}</strong>, without regard to conflict-of-law principles.
     Any disputes shall be resolved in the courts of {jurisdiction}.</p>

  <h2>10. Changes to These Terms</h2>
  <p>We may update these Terms from time to time. Material changes will be announced with reasonable notice.
     Continued use of the Service after changes take effect constitutes acceptance.</p>

  <h2>11. Contact</h2>
  <p>Questions about these Terms: <a href="mailto:{email}">{email}</a>.</p>

  <footer>
    <p>© {datetime.now(timezone.utc).year} {project}. All rights reserved.</p>
    <p>⚠️ This is a template. Review with a qualified legal professional before publishing.</p>
  </footer>
</body>
</html>"""

    def _governing_law(self, region: str):
        """Return (regime, jurisdiction) for the ToS governing-law clause."""
        laws = {
            "EU":   ("GDPR_EU_Consumer_Law", "the European Union"),
            "UK":   ("UK_GDPR_Consumer_Rights_Act", "the United Kingdom"),
            "AF":   ("POPIA", "South Africa"),
            "SA":   ("PECA_GDPR", "Saudi Arabia"),
            "MENA": ("KVKK_Consumer_Law", "Turkey"),
            "APAC": ("PDPA", "Singapore"),
            "LATAM": ("LGPD", "Brazil"),
            "IN":   ("PDPB_IT_Act", "India"),
        }
        return laws.get(region, ("jurisdiction_of_operator", "your country of incorporation"))

    def _build_cookie_consent_component(self, applicable: List[Dict], region: str) -> str:
        """Juice the banner component (plain string + tokens to avoid f-string brace pain)."""
        model = self._get_cookie_model(applicable)
        reg_codes = [r["code"] for r in applicable]
        source = """/**
 * CookieConsent — __MODEL_UPPER__ consent banner (project template).
 * Region: __REGION__ | Regulations: __REG_CODES__
 * Mount once in App.jsx: <CookieConsent />
 * Reads the category model from ../config/cookie-config.js.
 */

import { useEffect, useRef, useState } from 'react';
import ButtonMotion from '@/components/ui/ButtonMotion';
import { COOKIE_CONFIG, hasConsent, saveConsent } from '../config/cookie-config';

const styles = {
  overlay: {
    position: 'fixed',
    insetInline: 0,
    bottom: 0,
    zIndex: 2147483000,
    padding: '1rem',
    display: 'flex',
    justifyContent: 'center',
  },
  card: {
    width: '100%',
    maxWidth: 640,
    background: 'var(--color-surface, #ffffff)',
    color: 'var(--color-fg, #0f172a)',
    border: '1px solid var(--color-border, #e2e8f0)',
    borderRadius: 12,
    boxShadow: '0 12px 32px rgba(2, 6, 23, 0.25)',
    padding: '1.25rem',
    fontFamily: 'system-ui, sans-serif',
    fontSize: 14,
    lineHeight: 1.55,
  },
  row: { display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBlockStart: '0.5rem', alignItems: 'center' },
  toggle: { display: 'flex', alignItems: 'center', gap: '0.375rem' },
  button: {
    border: 'none',
    borderRadius: 8,
    padding: '0.5rem 0.875rem',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    marginInlineEnd: '0.5rem',
  },
  primary: { background: '#0d9488', color: '#ffffff' },
  secondary: { background: 'var(--color-muted, #e2e8f0)', color: '#1e293b' },
  link: { color: '#0d9488' },
};

export default function CookieConsent() {
  const [stored] = useState(() => localStorage.getItem(COOKIE_CONFIG.consentCookieName));
  const [open, setOpen] = useState(() => COOKIE_CONFIG.showBanner && !stored);
  const [choices, setChoices] = useState(() => {
    const initial = {};
    Object.values(COOKIE_CONFIG.categories).forEach((cat) => {
      initial[cat.id] = cat.required ? true : hasConsent(cat.id);
    });
    return initial;
  });
  const acceptRef = useRef(null);

  useEffect(() => {
    if (open && acceptRef.current) acceptRef.current.focus();
  }, [open]);

  if (!open) return null;

  const categories = Object.values(COOKIE_CONFIG.categories);
  const set = (id, value) => setChoices((prev) => ({ ...prev, [id]: value }));
  const close = () => setOpen(false);
  const dismiss = () => setOpen(false);

  const finish = (finalChoices) => {
    saveConsent(finalChoices);
    close();
  };

  const onKeyDown = (event) => {
    if (event.key === 'Escape') dismiss();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-consent-title"
      onKeyDown={onKeyDown}
      style={styles.overlay}
    >
      <div style={styles.card}>
        <h2 id="cookie-consent-title" style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
          We value your privacy
        </h2>
        <p style={{ margin: '0.375rem 0 0' }}>
          We use cookies to make our site work and, where you agree, to analyse traffic and personalize content.
          Essential cookies are always active. For details see our{' '}
          <a href={COOKIE_CONFIG.privacyPolicyUrl} style={styles.link}>Privacy Policy</a>{' '}
          and{' '}
          <a href={COOKIE_CONFIG.termsOfServiceUrl} style={styles.link}>Terms of Service</a>.
        </p>

        {categories.map((cat) => (
          <label key={cat.id} style={{ ...styles.toggle, ...styles.row }}>
            <input
              type="checkbox"
              disabled={cat.required}
              checked={cat.required || choices[cat.id]}
              onChange={(e) => set(cat.id, e.target.checked)}
              aria-describedby={cat.required ? undefined : `cat-desc-${cat.id}`}
            />
            <span>{cat.name}</span>
            {cat.required ? null : <small style={{ opacity: 0.7 }}>({cat.description})</small>}
          </label>
        ))}

        <div style={styles.row}>
          <ButtonMotion ref={acceptRef} type="button" style={{ ...styles.button, ...styles.primary }} onClick={() => {
            const all = {};
            categories.forEach((cat) => { all[cat.id] = true; });
            finish(all);
          }}>
            Accept all
          </ButtonMotion>
          <ButtonMotion type="button" style={{ ...styles.button, ...styles.secondary }} onClick={() => {
            const minimal = {};
            categories.forEach((cat) => { minimal[cat.id] = cat.required; });
            finish(minimal);
          }}>
            Reject non-essential
          </ButtonMotion>
          <ButtonMotion type="button" style={styles.button} onClick={() => finish(choices)}>
            Save preferences
          </ButtonMotion>
        </div>
      </div>
    </div>
  );
}
"""
        return (
            source
            .replace("__MODEL_UPPER__", model.upper())
            .replace("__REGION__", region)
            .replace("__REG_CODES__", ", ".join(reg_codes))
        )

    def _build_cookie_config(self, applicable: List[Dict], region: str) -> str:
        model = self._get_cookie_model(applicable)
        opt_in = "true" if model == "opt-in" else "false"
        reg_codes = [r["code"] for r in applicable]
        return f"""/**
 * Cookie Configuration
 * Region: {region} | Regulations: {', '.join(reg_codes)}
 * Model: {model.upper()} — {"Consent required before non-essential cookies" if model == "opt-in" else "Opt-out model — cookies active by default"}
 */

export const COOKIE_CONFIG = {{
  // Consent model
  requireConsent: {opt_in},          // true = GDPR/opt-in, false = CCPA/opt-out
  region: '{region}',
  regulations: {reg_codes},

  // Cookie categories
  categories: {{
    essential: {{
      id: 'essential',
      name: 'Essential Cookies',
      description: 'Required for the website to function. Cannot be disabled.',
      required: true,
      defaultEnabled: true,
    }},
    analytics: {{
      id: 'analytics',
      name: 'Analytics Cookies',
      description: 'Help us understand how visitors use our website (e.g. Google Analytics).',
      required: false,
      defaultEnabled: {'false' if opt_in == 'true' else 'true'},
    }},
    marketing: {{
      id: 'marketing',
      name: 'Marketing Cookies',
      description: 'Used to show you relevant advertising and track ad performance.',
      required: false,
      defaultEnabled: false,
    }},
    preferences: {{
      id: 'preferences',
      name: 'Preference Cookies',
      description: 'Remember your settings like language and currency.',
      required: false,
      defaultEnabled: true,
    }},
  }},

  // Storage
  consentCookieName: 'lumicore_consent',
  consentCookieExpiry: 365,           // days

  // UI
  showBanner: {opt_in},
  position: 'bottom',                 // 'bottom' | 'top' | 'modal'
  privacyPolicyUrl: '/privacy-policy.html',
  termsOfServiceUrl: '/terms-of-service.html',
  cookiePolicyUrl: '/cookie-policy',
}};

/**
 * Check if a cookie category is consented
 * Usage: if (hasConsent('analytics')) {{ loadGA(); }}
 */
export function hasConsent(category) {{
  try {{
    const stored = JSON.parse(localStorage.getItem(COOKIE_CONFIG.consentCookieName) || '{{}}');
    if (COOKIE_CONFIG.categories[category]?.required) return true;
    return stored[category] ?? COOKIE_CONFIG.categories[category]?.defaultEnabled ?? false;
  }} catch {{
    return false;
  }}
}}

/**
 * Save consent choices
 * Usage: saveConsent({{ analytics: true, marketing: false, preferences: true }})
 */
export function saveConsent(choices) {{
  const consent = {{
    essential: true,
    timestamp: new Date().toISOString(),
    ...choices,
  }};
  localStorage.setItem(COOKIE_CONFIG.consentCookieName, JSON.stringify(consent));
  window.dispatchEvent(new CustomEvent('cookieConsentUpdated', {{ detail: consent }}));
}}
"""
