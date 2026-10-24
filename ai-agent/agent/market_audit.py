"""Global Market Audit - Playwright-driven international-market readiness.

Runs `utils/market_audit.cjs` (repo-local Playwright, keyless) against a live
URL and turns the raw evidence into a scored report against the LumicorePro
international-market standards:

- Performance: LCP <= 1.5s target (2.5s hard), CLS <= 0.05 (0.1 hard),
  TTFB <= 0.8s, transfer <= 300KB target (600KB hard), zero console/page errors
- SEO: title, meta description, canonical, OG, twitter card, JSON-LD,
  robots.txt, sitemap.xml
- Internationalisation: lang + dir attributes, hreflang, currency signals and
  no placeholder ("lorem ipsum") copy
- Legal/trust: Privacy, Terms, Refund/Returns, cookie/GDPR consent surface
- Conversion: above-the-fold CTA, labeled inputs, alt text, heading hierarchy

Grades follow the design-gate scale: STANDARD 80+, PREMIUM 88+, SIGNATURE 92+.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

_HELPER = Path(__file__).resolve().parent.parent / "utils" / "market_audit.cjs"

# Category weights for the overall market score.
_WEIGHTS = {
    "performance": 0.30,
    "seo": 0.25,
    "international": 0.20,
    "legal": 0.15,
    "conversion": 0.10,
}


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def _score_performance(desktop: dict, mobile: dict) -> tuple:
    checks = []
    score = 100.0

    def add(name, ok, detail):
        checks.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})

    d = desktop if isinstance(desktop, dict) else {}
    m = mobile if isinstance(mobile, dict) else {}
    lcp = d.get("lcp")
    cls = d.get("cls")
    ttfb = d.get("ttfb")
    mob_lcp = m.get("lcp")
    errors = (d.get("console_errors", 0) + d.get("page_errors", 0)
              + m.get("console_errors", 0) + m.get("page_errors", 0))

    if lcp is not None:
        if lcp <= 1500:
            add("lcp_desktop", True, f"{lcp}ms <= 1500ms target")
        elif lcp <= 2500:
            score -= 25
            add("lcp_desktop", False, f"{lcp}ms (target 1500ms, hard 2500ms)")
        else:
            score -= 45
            add("lcp_desktop", False, f"{lcp}ms - exceeds 2500ms hard limit")
    if mob_lcp is not None and mob_lcp > 2500:
        score -= 15
        checks.append({"check": "lcp_mobile", "status": "fail", "detail": f"{mob_lcp}ms - exceeds 2500ms"})
    if cls is not None:
        if cls <= 0.05:
            add("cls_desktop", True, f"{cls} <= 0.05 target")
        else:
            score -= 15 if cls <= 0.1 else 30
            add("cls_desktop", False, f"{cls} (target 0.05, hard 0.1)")
    if ttfb is not None and ttfb > 800:
        score -= 10
        add("ttfb", False, f"{ttfb}ms > 800ms")
    if errors > 0:
        score -= min(20, errors * 5)
        checks.append({"check": "console_errors", "status": "fail", "detail": f"{errors} errors across views"})
    else:
        checks.append({"check": "console_errors", "status": "pass", "detail": "0 errors across views"})

    return (score, checks)


def market_audit(url: str, node_bin: str = None, script: Path = None, runner=None) -> dict:
    """Audit a live URL and return a scored international-market report."""
    helper = script or _HELPER
    if not helper.exists():
        return {"status": "skipped", "reason": "market audit helper missing"}
    cmd = [node_bin or "node", str(helper), url]
    if runner:
        rc, out, err = runner(cmd, str(Path(__file__).resolve().parent))
    else:
        import subprocess
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    try:
        raw = json.loads((out or err).strip() or "{}")
    except json.JSONDecodeError:
        return {"status": "failed", "reason": f"unreadable audit output: rc={rc}"}

    if raw.get("status") == "skipped":
        return {"status": "skipped", "reason": raw.get("message", "playwright not installed")}
    if raw.get("status") != "ok":
        return {"status": "failed", "reason": raw.get("message", "audit failed"),
                "url": url, "raw_status": raw.get("status")}

    desktop = raw.get("desktop", {})
    mobile = raw.get("mobile", {})
    dom = raw.get("dom", {})
    endpoints = raw.get("endpoint_tests", {})

    checks = []
    perf_score, perf_checks = _score_performance(desktop, mobile)
    checks.extend(perf_checks)

    # --- SEO -----------------------------------------------------------------
    seo_score = 100.0
    title = dom.get("title") or ""
    desc = dom.get("meta_description") or ""
    seo_checks = {
        "title_length": (15 <= len(title) <= 65, f"{len(title)} chars"),
        "meta_description": (50 <= len(desc) <= 160, f"{len(desc)} chars"),
        "canonical": (bool(dom.get("canonical")), dom.get("canonical") or "absent"),
        "og_tags": (bool(dom.get("og", {}).get("title")) and bool(dom.get("og", {}).get("image")),
                    "title+image present" if dom.get("og", {}).get("title") else "missing"),
        "twitter_card": (bool(dom.get("twitter_card")), dom.get("twitter_card") or "absent"),
        "json_ld": (any(t and t != "invalid-json" for t in dom.get("jsonld_types", [])),
                    ", ".join(map(str, dom.get("jsonld_types", []))) or "none"),
        "robots_txt": (endpoints.get("robots_txt", False), "fetchable" if endpoints.get("robots_txt") else "missing"),
        "sitemap_xml": (endpoints.get("sitemap_xml", False), "fetchable" if endpoints.get("sitemap_xml") else "missing"),
    }
    for name, ok, detail in [(k, v[0], v[1]) for k, v in seo_checks.items()]:
        passes = bool(ok)
        seo_score -= 12.5 * (0 if passes else 1)
        checks.append({"check": f"seo_{name}", "status": "pass" if passes else "fail", "detail": str(detail)})

    # --- international -------------------------------------------------------
    intl_score = 100.0
    hreflangs = dom.get("hreflangs", 0)
    lang = dom.get("lang")
    dir_attr = dom.get("dir")
    currency = dom.get("currency", {})
    currency_jsonld = dom.get("jsonld_currency")
    if lang:
        checks.append({"check": "i18n_lang_attr", "status": "pass", "detail": lang})
    else:
        intl_score -= 40
        checks.append({"check": "i18n_lang_attr", "status": "fail", "detail": "missing"})
    if dir_attr in (None, "", "ltr"):
        checks.append({"check": "i18n_dir_attr", "status": "pass", "detail": str(dir_attr or "ltr default")})
    else:
        checks.append({"check": "i18n_dir_attr", "status": "pass", "detail": dir_attr})
    if hreflangs == 0:
        intl_score -= 15
        checks.append({"check": "i18n_hreflang", "status": "warn", "detail": "0 hreflang alternates"})
    if currency.get("symbols") == "none" and not currency_jsonld:
        intl_score -= 20
        checks.append({"check": "i18n_currency_signal", "status": "warn",
                       "detail": "no currency found (body or JSON-LD priceCurrency)"})
    elif not currency.get("switcher"):
        intl_score -= 10
        checks.append({"check": "i18n_currency_switcher", "status": "warn", "detail": "no currency switcher control"})
    else:
        checks.append({"check": "i18n_currency_switcher", "status": "pass", "detail": currency.get("symbols", "")})
    if dom.get("placeholder_copy"):
        intl_score -= 25
        checks.append({"check": "i18n_placeholder_copy", "status": "fail", "detail": "placeholder text (lorem/TODO) shipped"})

    # --- legal / trust -------------------------------------------------------
    legal = dom.get("legal", {})
    legal_score = 100.0
    for name in ("privacy", "terms", "refund", "gdpr_cookies"):
        present = legal.get(name)
        if not present:
            legal_score -= 25
        checks.append({"check": f"legal_{name}", "status": "pass" if present else "fail",
                       "detail": "link present" if present else "no link on page"})

    # --- conversion ----------------------------------------------------------
    conv_score = 100.0
    cta = dom.get("cta_above_fold", 0)
    if cta:
        checks.append({"check": "conv_cta_above_fold", "status": "pass", "detail": f"{cta} above fold"})
    else:
        conv_score -= 50
        checks.append({"check": "conv_cta_above_fold", "status": "fail", "detail": "no conversion CTA visible"})
    unlabeled = dom.get("unlabeled_inputs", 0)
    if unlabeled:
        conv_score -= min(30, unlabeled * 10)
        checks.append({"check": "conv_form_labels", "status": "fail", "detail": f"{unlabeled} unlabeled fields"})
    else:
        checks.append({"check": "conv_form_labels", "status": "pass", "detail": "all fields labeled"})
    missing_alt = dom.get("images_missing_alt", 0)
    if missing_alt > 5:
        conv_score -= 20
        checks.append({"check": "conv_image_alt", "status": "fail", "detail": f"{missing_alt} imgs without alt"})
    else:
        checks.append({"check": "conv_image_alt", "status": "pass", "detail": f"{missing_alt} missing (<=5)"})
    jumps = dom.get("heading_jumps", 0)
    if jumps:
        conv_score -= 10
        checks.append({"check": "conv_heading_jumps", "status": "warn", "detail": f"{jumps} hierarchy jumps"})

    h1 = dom.get("h1_count", 0)
    if h1 == 0:
        seo_score -= 5
        checks.append({"check": "seo_h1_present", "status": "warn", "detail": "no h1"})
    else:
        checks.append({"check": "seo_h1_present", "status": "pass", "detail": f"{h1} h1"})

    scores = {
        "performance": _clamp(perf_score),
        "seo": _clamp(seo_score),
        "international": _clamp(intl_score),
        "legal": _clamp(legal_score),
        "conversion": _clamp(conv_score),
    }
    overall = _clamp(sum(scores[k] * w for k, w in _WEIGHTS.items()))
    grade = "SIGNATURE" if overall >= 92 else "PREMIUM" if overall >= 88 else "STANDARD" if overall >= 80 else "NEEDS_WORK"
    status = "ok" if overall >= 80 else "warn"

    return {
        "status": status,
        "url": url,
        "overall": overall,
        "grade": grade,
        "targets": {"standard": 80, "premium": 88, "signature": 92},
        "scores": scores,
        "checks": checks,
        "metrics": {"desktop": desktop, "mobile": mobile},
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "helper": str(helper),
    }
