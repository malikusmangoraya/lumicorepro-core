# Compliance Report — apex

Prepared: 2026-09-29 | Region: SA

---

## Applicable Regulations

### Prevention of Electronic Crimes Act (Pakistan) (PECA_PK)

**Jurisdictions:** Pakistan
**Cookie Policy:** Recommended opt-in
**Penalty:** Up to PKR 5M and/or 3 years imprisonment

**Key User Rights:**

- Protection of identity
- Protection from data breach

**Implementation Requirements:**

- [ ] No unauthorised interception of data
- [ ] Privacy policy in Urdu or English
- [ ] Data stored on servers accessible to PTA if required
- [ ] Cyber crime reporting mechanism

### General Data Protection Regulation (GDPR)

**Jurisdictions:** EU, EEA, UK
**Cookie Policy:** Opt-in required for non-essential cookies
**Penalty:** Up to €20M or 4% of global annual turnover

**Key User Rights:**

- Right to access personal data
- Right to rectification
- Right to erasure (right to be forgotten)
- Right to restrict processing
- Right to data portability
- Right to object
- Rights related to automated decision-making

**Implementation Requirements:**

- [ ] Cookie consent banner with granular controls
- [ ] Privacy policy in local language
- [ ] Data Processing Agreement (DPA) with processors
- [ ] Data breach notification within 72 hours
- [ ] Lawful basis for processing (consent / legitimate interest)
- [ ] DPO appointment if processing at scale
- [ ] Records of processing activities (ROPA)

---

## Action Checklist

- [x] Cookie Consent Banner — auto-generated `frontend/src/components/common/CookieConsent.jsx`
- [x] Privacy Policy — auto-generated `frontend/public/privacy-policy.html`
- [x] Terms of Service — auto-generated `frontend/public/terms-of-service.html`
- [ ] Mount `<CookieConsent />` once in `App.jsx` (import from `./components/common/CookieConsent`)
- [ ] Link Privacy Policy and Terms of Service in footer
- [ ] Add 'Contact DPO / Privacy Officer' email to footer
- [ ] Enable HTTPS (TLS 1.2+) in production
- [ ] Implement data deletion endpoint `DELETE /api/users/:id`
- [ ] Add rate limiting to all auth endpoints
- [ ] Log all data access for audit trail

---

> ⚠️ **Disclaimer:** This document is provided for informational purposes.
> Always consult a qualified legal professional before deployment.

---

## Verification Evidence (auto-generated)

- Accessibility score: 57.1
- WCAG 2.1 AA compliant: pending review
- Generated artifacts: ['<project-root>', '<project-root>', '<project-root>', '<project-root>', '<project-root>']
- Consent banner required: True
- Security controls verified: 13
- Security review items queued: 6
- Deployment cost estimates: {
  "traffic_tier": "low",
  "estimates": {
  "vercel": {
  "monthly_usd": "$0",
  "class": "static-site"
  },
  "cloudflare": {
  "monthly_usd": "$0",
  "class": "static-site"
  },
  "netlify": {
  "monthly_usd": "$0",
  "class": "static-site"
  },
  "github": {
  "monthly_usd": "$0",
  "class": "static-site"
  },
  "railway": {
  "monthly_usd": "$5",
  "class": "app-server"
  },
  "render": {
  "monthly_usd": "$0",
  "class": "app-server"
  },
  "digitalocean": {
  "monthly_usd": "$12",
  "class": "app-server"
  },
  "aws": {
  "monthly_usd": "$7",
  "class": "app-server"
  },
  "gcp": {
  "monthly_usd": "$6",
  "class": "app-server"
  }
  },
  "cheapest": [
  "github",
  "vercel"
  ],
  "recommended_for_type": [
  "vercel",
  "railway",
  "render"
  ],
  "note": "Planning estimate only \u2014 real cost depends on traffic, storage, and add-ons."
  }
- Verified at: 2026-09-29T15:37:19Z

> Evidence block appended by the validation pipeline during the final QA pass.
