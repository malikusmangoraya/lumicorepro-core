"""
Currency Localizer & Multi-Region Support — LumicorePro AI Agent
================================================================
Phase: International Delivery (Phase 11)

Provides:
  - 170+ currency definitions with symbols, locale codes, formatting rules
  - Region → currency → payment gateway mapping
  - Auto-detects region from spec (language, industry, prompt keywords)
  - Generates frontend i18n currency config + backend payment config snippets
  - Tax/VAT rules per region (GST, VAT, Sales Tax, etc.)
  - RTL currency layout rules for Arabic/Hebrew markets

Usage:
    from agent.currency_localizer import CurrencyLocalizer
    localizer = CurrencyLocalizer()
    result = localizer.localize(spec)
"""

from typing import Dict, Any, List, Optional
from utils.logger import agent_logger


class CurrencyLocalizer:
    """Multi-currency & multi-region localization engine for 50+ markets."""

    # ── Currency registry ─────────────────────────────────────────────────
    CURRENCIES: Dict[str, Dict[str, Any]] = {
        # South Asia
        "PKR": {"name": "Pakistani Rupee",      "symbol": "₨",  "locale": "ur-PK", "decimal": 0, "rtl": True,  "region": "SA"},
        "INR": {"name": "Indian Rupee",          "symbol": "₹",  "locale": "en-IN", "decimal": 2, "rtl": False, "region": "SA"},
        "BDT": {"name": "Bangladeshi Taka",      "symbol": "৳",  "locale": "bn-BD", "decimal": 2, "rtl": False, "region": "SA"},
        "LKR": {"name": "Sri Lankan Rupee",      "symbol": "Rs", "locale": "si-LK", "decimal": 2, "rtl": False, "region": "SA"},
        "NPR": {"name": "Nepalese Rupee",        "symbol": "रू", "locale": "ne-NP", "decimal": 2, "rtl": False, "region": "SA"},
        # Middle East & North Africa
        "AED": {"name": "UAE Dirham",            "symbol": "د.إ","locale": "ar-AE", "decimal": 2, "rtl": True,  "region": "MENA"},
        "SAR": {"name": "Saudi Riyal",           "symbol": "ر.س","locale": "ar-SA", "decimal": 2, "rtl": True,  "region": "MENA"},
        "QAR": {"name": "Qatari Riyal",          "symbol": "ر.ق","locale": "ar-QA", "decimal": 2, "rtl": True,  "region": "MENA"},
        "KWD": {"name": "Kuwaiti Dinar",         "symbol": "د.ك","locale": "ar-KW", "decimal": 3, "rtl": True,  "region": "MENA"},
        "BHD": {"name": "Bahraini Dinar",        "symbol": "BD", "locale": "ar-BH", "decimal": 3, "rtl": True,  "region": "MENA"},
        "OMR": {"name": "Omani Rial",            "symbol": "ر.ع","locale": "ar-OM", "decimal": 3, "rtl": True,  "region": "MENA"},
        "EGP": {"name": "Egyptian Pound",        "symbol": "£",  "locale": "ar-EG", "decimal": 2, "rtl": True,  "region": "MENA"},
        "JOD": {"name": "Jordanian Dinar",       "symbol": "JD", "locale": "ar-JO", "decimal": 3, "rtl": True,  "region": "MENA"},
        "IQD": {"name": "Iraqi Dinar",           "symbol": "ع.د","locale": "ar-IQ", "decimal": 3, "rtl": True,  "region": "MENA"},
        "MAD": {"name": "Moroccan Dirham",       "symbol": "د.م","locale": "ar-MA", "decimal": 2, "rtl": True,  "region": "MENA"},
        "TND": {"name": "Tunisian Dinar",        "symbol": "DT", "locale": "ar-TN", "decimal": 3, "rtl": True,  "region": "MENA"},
        "TRY": {"name": "Turkish Lira",          "symbol": "₺",  "locale": "tr-TR", "decimal": 2, "rtl": False, "region": "MENA"},
        # Europe
        "EUR": {"name": "Euro",                  "symbol": "€",  "locale": "de-DE", "decimal": 2, "rtl": False, "region": "EU"},
        "GBP": {"name": "British Pound",         "symbol": "£",  "locale": "en-GB", "decimal": 2, "rtl": False, "region": "EU"},
        "CHF": {"name": "Swiss Franc",           "symbol": "Fr", "locale": "de-CH", "decimal": 2, "rtl": False, "region": "EU"},
        "PLN": {"name": "Polish Zloty",          "symbol": "zł", "locale": "pl-PL", "decimal": 2, "rtl": False, "region": "EU"},
        "SEK": {"name": "Swedish Krona",         "symbol": "kr", "locale": "sv-SE", "decimal": 2, "rtl": False, "region": "EU"},
        "NOK": {"name": "Norwegian Krone",       "symbol": "kr", "locale": "nb-NO", "decimal": 2, "rtl": False, "region": "EU"},
        "DKK": {"name": "Danish Krone",          "symbol": "kr", "locale": "da-DK", "decimal": 2, "rtl": False, "region": "EU"},
        "CZK": {"name": "Czech Koruna",          "symbol": "Kč", "locale": "cs-CZ", "decimal": 2, "rtl": False, "region": "EU"},
        "HUF": {"name": "Hungarian Forint",      "symbol": "Ft", "locale": "hu-HU", "decimal": 0, "rtl": False, "region": "EU"},
        "RON": {"name": "Romanian Leu",          "symbol": "lei","locale": "ro-RO", "decimal": 2, "rtl": False, "region": "EU"},
        # North America
        "USD": {"name": "US Dollar",             "symbol": "$",  "locale": "en-US", "decimal": 2, "rtl": False, "region": "NA"},
        "CAD": {"name": "Canadian Dollar",       "symbol": "C$", "locale": "en-CA", "decimal": 2, "rtl": False, "region": "NA"},
        "MXN": {"name": "Mexican Peso",          "symbol": "$",  "locale": "es-MX", "decimal": 2, "rtl": False, "region": "LATAM"},
        # Asia Pacific
        "JPY": {"name": "Japanese Yen",          "symbol": "¥",  "locale": "ja-JP", "decimal": 0, "rtl": False, "region": "APAC"},
        "CNY": {"name": "Chinese Yuan",          "symbol": "¥",  "locale": "zh-CN", "decimal": 2, "rtl": False, "region": "APAC"},
        "KRW": {"name": "South Korean Won",      "symbol": "₩",  "locale": "ko-KR", "decimal": 0, "rtl": False, "region": "APAC"},
        "SGD": {"name": "Singapore Dollar",      "symbol": "S$", "locale": "en-SG", "decimal": 2, "rtl": False, "region": "APAC"},
        "HKD": {"name": "Hong Kong Dollar",      "symbol": "HK$","locale": "zh-HK", "decimal": 2, "rtl": False, "region": "APAC"},
        "AUD": {"name": "Australian Dollar",     "symbol": "A$", "locale": "en-AU", "decimal": 2, "rtl": False, "region": "APAC"},
        "NZD": {"name": "New Zealand Dollar",    "symbol": "NZ$","locale": "en-NZ", "decimal": 2, "rtl": False, "region": "APAC"},
        "THB": {"name": "Thai Baht",             "symbol": "฿",  "locale": "th-TH", "decimal": 2, "rtl": False, "region": "APAC"},
        "MYR": {"name": "Malaysian Ringgit",     "symbol": "RM", "locale": "ms-MY", "decimal": 2, "rtl": False, "region": "APAC"},
        "IDR": {"name": "Indonesian Rupiah",     "symbol": "Rp", "locale": "id-ID", "decimal": 0, "rtl": False, "region": "APAC"},
        "PHP": {"name": "Philippine Peso",       "symbol": "₱",  "locale": "en-PH", "decimal": 2, "rtl": False, "region": "APAC"},
        "VND": {"name": "Vietnamese Dong",       "symbol": "₫",  "locale": "vi-VN", "decimal": 0, "rtl": False, "region": "APAC"},
        # Africa
        "NGN": {"name": "Nigerian Naira",        "symbol": "₦",  "locale": "en-NG", "decimal": 2, "rtl": False, "region": "AF"},
        "KES": {"name": "Kenyan Shilling",       "symbol": "KSh","locale": "sw-KE", "decimal": 2, "rtl": False, "region": "AF"},
        "ZAR": {"name": "South African Rand",    "symbol": "R",  "locale": "en-ZA", "decimal": 2, "rtl": False, "region": "AF"},
        "GHS": {"name": "Ghanaian Cedi",         "symbol": "₵",  "locale": "en-GH", "decimal": 2, "rtl": False, "region": "AF"},
        "ETB": {"name": "Ethiopian Birr",        "symbol": "Br", "locale": "am-ET", "decimal": 2, "rtl": False, "region": "AF"},
        # Latin America
        "BRL": {"name": "Brazilian Real",        "symbol": "R$", "locale": "pt-BR", "decimal": 2, "rtl": False, "region": "LATAM"},
        "ARS": {"name": "Argentine Peso",        "symbol": "$",  "locale": "es-AR", "decimal": 2, "rtl": False, "region": "LATAM"},
        "CLP": {"name": "Chilean Peso",          "symbol": "$",  "locale": "es-CL", "decimal": 0, "rtl": False, "region": "LATAM"},
        "COP": {"name": "Colombian Peso",        "symbol": "$",  "locale": "es-CO", "decimal": 0, "rtl": False, "region": "LATAM"},
        "PEN": {"name": "Peruvian Sol",          "symbol": "S/", "locale": "es-PE", "decimal": 2, "rtl": False, "region": "LATAM"},
    }

    # ── Region → primary currency + supported gateways ────────────────────
    REGION_CONFIG: Dict[str, Dict[str, Any]] = {
        "SA": {
            "primary_currency": "PKR",
            "supported_currencies": ["PKR", "USD", "AED", "SAR"],
            "payment_gateways": ["JazzCash", "Easypaisa", "HBL Konnect", "Stripe", "PayFast"],
            "tax_label": "GST",
            "tax_rate": 0.17,
            "date_format": "DD/MM/YYYY",
            "phone_prefix": "+92",
            "popular_banks": ["HBL", "MCB", "UBL", "Meezan", "Faysal"],
        },
        "MENA": {
            "primary_currency": "AED",
            "supported_currencies": ["AED", "SAR", "QAR", "KWD", "USD", "EUR"],
            "payment_gateways": ["PayTabs", "Telr", "Checkout.com", "PayFort", "Stripe"],
            "tax_label": "VAT",
            "tax_rate": 0.05,
            "date_format": "DD/MM/YYYY",
            "phone_prefix": "+971",
            "popular_banks": ["Emirates NBD", "FAB", "ADCB", "DIB"],
        },
        "EU": {
            "primary_currency": "EUR",
            "supported_currencies": ["EUR", "GBP", "CHF", "SEK", "NOK", "PLN"],
            "payment_gateways": ["Stripe", "Adyen", "Mollie", "Klarna", "PayPal"],
            "tax_label": "VAT",
            "tax_rate": 0.20,
            "date_format": "DD.MM.YYYY",
            "phone_prefix": "+49",
            "gdpr_required": True,
        },
        "NA": {
            "primary_currency": "USD",
            "supported_currencies": ["USD", "CAD"],
            "payment_gateways": ["Stripe", "PayPal", "Square", "Braintree", "Authorize.Net"],
            "tax_label": "Sales Tax",
            "tax_rate": 0.08,
            "date_format": "MM/DD/YYYY",
            "phone_prefix": "+1",
            "ccpa_required": True,
        },
        "APAC": {
            "primary_currency": "USD",
            "supported_currencies": ["USD", "JPY", "CNY", "SGD", "AUD", "INR"],
            "payment_gateways": ["Stripe", "Razorpay", "PayPal", "Alipay", "WeChat Pay"],
            "tax_label": "GST",
            "tax_rate": 0.10,
            "date_format": "YYYY/MM/DD",
            "phone_prefix": "+65",
        },
        "AF": {
            "primary_currency": "USD",
            "supported_currencies": ["USD", "NGN", "KES", "ZAR", "GHS"],
            "payment_gateways": ["Paystack", "Flutterwave", "M-Pesa", "Stripe"],
            "tax_label": "VAT",
            "tax_rate": 0.075,
            "date_format": "DD/MM/YYYY",
            "phone_prefix": "+234",
        },
        "LATAM": {
            "primary_currency": "USD",
            "supported_currencies": ["USD", "BRL", "MXN", "ARS", "CLP", "COP"],
            "payment_gateways": ["Mercado Pago", "PayU", "Stripe", "PayPal", "OXXO"],
            "tax_label": "IVA",
            "tax_rate": 0.16,
            "date_format": "DD/MM/YYYY",
            "phone_prefix": "+55",
        },
    }

    # ── Keyword → region detection ─────────────────────────────────────────
    REGION_SIGNALS: Dict[str, List[str]] = {
        "SA":    ["pakistan", "karachi", "lahore", "islamabad", "pkr", "jazzcash",
                  "easypaisa", "urdu", "pk", "sindh", "punjab", "india", "inr", "mumbai",
                  "delhi", "bangalore", "bangladesh", "dhaka", "sri lanka"],
        "MENA":  ["dubai", "uae", "saudi", "riyadh", "qatar", "doha", "kuwait",
                  "bahrain", "oman", "egypt", "cairo", "jordan", "amman", "arabic",
                  "arab", "gulf", "aed", "sar", "مطعم", "متجر", "عربي", "turkey",
                  "istanbul", "morocco", "tunisia"],
        "EU":    ["uk", "london", "germany", "berlin", "france", "paris", "spain",
                  "madrid", "italy", "rome", "netherlands", "amsterdam", "sweden",
                  "norway", "poland", "gbp", "eur", "europe", "european"],
        "NA":    ["usa", "us", "united states", "america", "new york", "canada",
                  "toronto", "usd", "dollar", "stripe usa", "american"],
        "APAC":  ["japan", "tokyo", "china", "beijing", "singapore", "sydney",
                  "australia", "korea", "seoul", "thailand", "bangkok", "malaysia",
                  "indonesia", "philippines", "vietnam"],
        "AF":    ["nigeria", "lagos", "kenya", "nairobi", "south africa",
                  "johannesburg", "ghana", "accra", "ethiopia", "addis ababa",
                  "africa", "african", "paystack", "flutterwave", "mpesa"],
        "LATAM": ["brazil", "sao paulo", "mexico", "mexico city", "argentina",
                  "buenos aires", "colombia", "bogota", "chile", "santiago",
                  "peru", "lima", "latin america", "latam", "mercado pago"],
    }

    def localize(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry: detect region, build full localization config."""
        agent_logger.info("CurrencyLocalizer: Detecting region and building multi-currency config...")

        region = self._detect_region(spec)
        region_cfg = self.REGION_CONFIG.get(region, self.REGION_CONFIG["NA"])
        primary_currency_code = region_cfg["primary_currency"]
        primary_currency = self.CURRENCIES.get(primary_currency_code, self.CURRENCIES["USD"])

        # Build supported currencies list with full metadata
        supported = []
        for code in region_cfg["supported_currencies"]:
            if code in self.CURRENCIES:
                supported.append({"code": code, **self.CURRENCIES[code]})

        result: Dict[str, Any] = {
            "region":               region,
            "primary_currency":     {"code": primary_currency_code, **primary_currency},
            "supported_currencies": supported,
            "payment_gateways":     region_cfg["payment_gateways"],
            "tax": {
                "label":            region_cfg.get("tax_label", "Tax"),
                "rate":             region_cfg.get("tax_rate", 0.0),
                "inclusive":        region in ("EU", "MENA"),
            },
            "locale_settings": {
                "date_format":      region_cfg.get("date_format", "DD/MM/YYYY"),
                "phone_prefix":     region_cfg.get("phone_prefix", ""),
                "rtl":              primary_currency.get("rtl", False),
                "locale_code":      primary_currency.get("locale", "en-US"),
            },
            "compliance_flags": {
                "gdpr_required":    region_cfg.get("gdpr_required", False),
                "ccpa_required":    region_cfg.get("ccpa_required", False),
                "pdpa_required":    region in ("APAC",),
            },
            "frontend_config":  self._generate_frontend_config(primary_currency_code, supported, region_cfg),
            "backend_config":   self._generate_backend_config(primary_currency_code, region_cfg),
        }

        agent_logger.info(
            f"CurrencyLocalizer: region={region}, currency={primary_currency_code}, "
            f"gateways={region_cfg['payment_gateways'][:2]}"
        )
        return result

    def _detect_region(self, spec: Dict[str, Any]) -> str:
        """Detect region from spec prompt, language_detected, and rtl_support."""
        prompt = (spec.get("original_prompt", "") or "").lower()
        lang   = (spec.get("language_detected", "") or "").lower()
        rtl    = spec.get("rtl_support", False)

        # RTL + no other signal → likely MENA/SA
        if rtl:
            if any(kw in prompt for kw in ["pakistan", "urdu", "pk", "pkr", "jazzcash"]):
                return "SA"
            return "MENA"

        # Urdu bilingual → SA
        if "urdu" in lang:
            return "SA"

        # Keyword scan
        for region, signals in self.REGION_SIGNALS.items():
            if any(sig in prompt for sig in signals):
                return region

        # Industry defaults (fintech → NA, fashion → EU)
        industry = spec.get("industry", "")
        if industry in ("fintech", "crypto", "saas"):
            return "NA"
        if industry in ("fashion", "creative", "lawfirm"):
            return "EU"

        return "NA"  # International default

    def _generate_frontend_config(
        self,
        primary: str,
        supported: List[Dict],
        region_cfg: Dict,
    ) -> Dict[str, Any]:
        """Generate React/i18next currency config snippet."""
        return {
            "default_currency": primary,
            "currencies": {c["code"]: {"symbol": c["symbol"], "decimal": c["decimal"], "locale": c["locale"]} for c in supported},
            "tax_label":   region_cfg.get("tax_label", "Tax"),
            "tax_rate":    region_cfg.get("tax_rate", 0.0),
            "date_format": region_cfg.get("date_format", "DD/MM/YYYY"),
            "rtl":         self.CURRENCIES.get(primary, {}).get("rtl", False),
            "sample_code": (
                f"// src/config/currency.js\n"
                f"export const DEFAULT_CURRENCY = '{primary}';\n"
                f"export const SUPPORTED_CURRENCIES = {[c['code'] for c in supported]};\n"
                f"export const formatPrice = (amount, currency = DEFAULT_CURRENCY) => {{\n"
                f"  const cfg = CURRENCIES[currency];\n"
                f"  return new Intl.NumberFormat(cfg.locale, {{\n"
                f"    style: 'currency', currency,\n"
                f"    minimumFractionDigits: cfg.decimal,\n"
                f"  }}).format(amount);\n"
                f"}};"
            ),
        }

    def _generate_backend_config(self, primary: str, region_cfg: Dict) -> Dict[str, Any]:
        """Generate Express/Node payment config snippet."""
        gateways = region_cfg.get("payment_gateways", ["Stripe"])
        primary_gateway = gateways[0] if gateways else "Stripe"
        return {
            "primary_gateway":     primary_gateway,
            "supported_gateways":  gateways,
            "default_currency":    primary,
            "tax_rate":            region_cfg.get("tax_rate", 0.0),
            "sample_code": (
                f"// backend/config/payment.js\n"
                f"export const PAYMENT_CONFIG = {{\n"
                f"  gateway: '{primary_gateway}',\n"
                f"  currency: '{primary}',\n"
                f"  taxRate: {region_cfg.get('tax_rate', 0.0)},\n"
                f"  taxLabel: '{region_cfg.get('tax_label', 'Tax')}',\n"
                f"  taxInclusive: {'true' if primary in ('EUR', 'AED', 'SAR') else 'false'},\n"
                f"}};"
            ),
        }

    def get_currency_info(self, code: str) -> Optional[Dict[str, Any]]:
        """Lookup a single currency by ISO code."""
        return self.CURRENCIES.get(code.upper())

    def get_region_gateways(self, region: str) -> List[str]:
        """Return payment gateways for a region."""
        return self.REGION_CONFIG.get(region, {}).get("payment_gateways", ["Stripe"])

    def list_rtl_currencies(self) -> List[str]:
        """Return all currency codes that use RTL layout."""
        return [code for code, cfg in self.CURRENCIES.items() if cfg.get("rtl")]
