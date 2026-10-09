"""Documentation metadata for every environment variable the code reads.

`hint` is the comment written above the key. `default` is the value shipped in
.env.example — always empty or an obviously non-secret placeholder, never a
value that could be mistaken for a working credential.
"""

SECRETS = "secret"

# group -> (heading, blurb)
GROUPS = [
    ("core", "Core server", "Where the API listens and what it trusts."),
    ("database", "Database", "PostgreSQL is the production database. Leave "
     "DATABASE_URL empty to fall back to a local SQLite file for demos."),
    ("cache", "Cache and queues", "Redis backs the cache, the rate limiter and "
     "the job queue. The app degrades to in-memory cache when Redis is absent."),
    ("jwt", "Authentication tokens", "Generate each secret with "
     "`node -e \"console.log(require('crypto').randomBytes(48).toString('hex'))\"`. "
     "The server refuses to start if JWT_SECRET is missing, short or a known "
     "placeholder."),
    ("oauth", "OAuth social login", "Optional. Leave blank to disable Google or "
     "GitHub sign-in. Redirect URIs are "
     "<BACKEND_URL>/api/auth/google/callback and /api/auth/github/callback."),
    ("email", "Transactional email", "SMTP credentials for verification, password "
     "reset and receipt email. Without them those emails log to the console."),
    ("frontend", "Frontend origin", "Used for CORS, payment redirects and links "
     "inside emails."),
    ("ai", "AI provider", "Optional. Used by the AI routes and the usage guard. "
     "No AI key means the AI endpoints answer with a clear 'not configured'."),
    ("security", "Security services", "Cloudflare Turnstile CAPTCHA and Sentry "
     "error reporting. Both optional."),
    ("license", "Licensing", "Optional self-hosted licence gate. Blank disables "
     "the check entirely."),
    ("demo", "Demo seed", "Creates fixed-credential demo users for the live "
     "demo. ALWAYS skipped when NODE_ENV=production, and additionally requires "
     "both ENABLE_DEMO_SEED=true and a DEMO_USER_PASSWORD."),
    ("limits", "Rate limits and body size", "Applied globally, with stricter "
     "per-route limits on auth and AI."),
    ("audit", "Audit log", "Every admin mutation is written to the audit log. "
     "Set AUDIT_LOG=false to disable."),
    ("waitlist", "Waitlist", "Optional pre-launch gate for contact and register "
     "forms."),
]

# key -> (group, default, hint)
VARS = {
    # --- core ---
    "NODE_ENV": ("core", "development", "development | production | test"),
    "PORT": ("core", "5000", "API port"),
    "API_PREFIX": ("core", "/api", "Mount point for every route"),
    "BASE_URL": ("core", "", "Absolute backend URL, e.g. https://api.example.com"),
    "BACKEND_URL": ("core", "http://localhost:5000", "Public backend origin"),
    "FRONTEND_URL": ("core", "http://localhost:5173", "Public frontend origin"),
    "APP_BRAND": ("core", "", "Product name shown in emails and logs"),
    "APP_DOMAIN": ("core", "", "Sending domain, e.g. example.com"),
    "DEV": ("core", "", "Set to any value for verbose development output"),
    "PROD": ("core", "", "Set to any value to mark a production process"),
    "LOG_LEVEL": ("core", "info", "error | warn | info | debug"),
    "UPLOAD_DIR": ("core", "./uploads", "Where multer writes uploaded files"),
    "MAX_FILE_SIZE": ("core", "5", "Upload size limit in megabytes"),
    "JSON_BODY_LIMIT": ("core", "2mb", "Express JSON body limit"),
    "CORS_ORIGIN": ("core", "http://localhost:5173", "Comma-separated allow-list"),
    "ALLOWED_ORIGINS": ("core", "http://localhost:5173",
     "Comma-separated allow-list; takes precedence over CORS_ORIGIN"),
    "VALID_API_KEYS": ("core", "",
     "Optional comma-separated keys required in the x-api-key header"),
    "INTERNAL_WEBHOOK_SECRET": ("core", "",
     "Shared secret for internal service-to-service webhooks"),
    "WEBHOOK_ENDPOINTS": ("core", "", "Comma-separated webhook URLs to fan out to"),
    "WEBHOOK_BODY_LIMIT": ("core", "1mb", "Body limit for inbound webhooks"),

    # --- database ---
    "DATABASE_URL": ("database", "postgresql://postgres:REPLACE_WITH_A_STRONG_PASSWORD@localhost:5432/app_db",
     "PostgreSQL connection string"),
    "DB_HOST": ("database", "localhost", ""),
    "DB_PORT": ("database", "5432", ""),
    "DB_NAME": ("database", "app_db", ""),
    "DB_USER": ("database", "postgres", ""),
    "DB_PASSWORD": ("database", "", ""),
    "DB_SSL": ("database", "", "Set to true for managed PostgreSQL that requires TLS"),
    "DB_POOL_MAX": ("database", "10", "Sequelize connection pool size"),
    "DB_POOL_MIN": ("database", "0", "Sequelize minimum pool size"),
    "DB_POOL_IDLE_MS": ("database", "10000", "Idle timeout before a connection is released"),
    "DB_POOL_ACQUIRE_MS": ("database", "10000", "How long a request waits for a free connection"),
    "DB_SYNC_ALTER": ("database", "false",
     "Let Sequelize alter the schema on boot. Development only — use migrations in production"),

    # --- cache ---
    "REDIS_URL": ("cache", "redis://localhost:6379", ""),
    "REDIS_DISABLED": ("cache", "false",
     "Set true to force the in-memory cache even when Redis is reachable"),

    # --- jwt ---
    "JWT_SECRET": ("jwt", "", "REQUIRED. Minimum 32 characters"),
    "JWT_REFRESH_SECRET": ("jwt", "",
     "Signing key for refresh tokens. Defaults to JWT_SECRET if blank"),
    "JWT_EXPIRE": ("jwt", "15m", "Access token lifetime"),
    "JWT_EXPIRES_IN": ("jwt", "15m", "Access token lifetime (alternative key)"),
    "JWT_REFRESH_EXPIRE": ("jwt", "30d", "Refresh token lifetime"),
    "BCRYPT_ROUNDS": ("jwt", "12", "Password hashing cost factor"),

    # --- oauth ---
    "GOOGLE_CLIENT_ID": ("oauth", "", ""),
    "GOOGLE_CLIENT_SECRET": ("oauth", "", ""),
    "GITHUB_CLIENT_ID": ("oauth", "", ""),
    "GITHUB_CLIENT_SECRET": ("oauth", "", ""),
    "OAUTH_SUCCESS_REDIRECT": ("oauth", "", "Where to land after social sign-in"),
    "OAUTH_FAILURE_REDIRECT": ("oauth", "", "Where to land after a failed sign-in"),

    # --- email ---
    "SMTP_HOST": ("email", "", "e.g. smtp.postmarkapp.com"),
    "SMTP_PORT": ("email", "587", ""),
    "SMTP_USER": ("email", "", ""),
    "SMTP_PASS": ("email", "", ""),
    "SMTP_SECURE": ("email", "false", "true for implicit TLS on port 465"),
    "EMAIL_FROM_ADDRESS": ("email", "", "Sender address; defaults to APP_DOMAIN"),
    "EMAIL_FROM_NAME": ("email", "", "Sender display name; defaults to APP_BRAND"),

    # --- ai ---
    "ACTIVE_AI_PROVIDER": ("ai", "gemini",
     "gemini | openai | anthropic | mistral | deepseek | openrouter | none"),
    "AI_AGENT_URL": ("ai", "http://localhost:8000",
     "Python AI agent service, when one is running"),
    "GEMINI_API_KEY": ("ai", "", ""),
    "OPENAI_API_KEY": ("ai", "", ""),
    "ANTHROPIC_API_KEY": ("ai", "", ""),
    "MISTRAL_API_KEY": ("ai", "", ""),
    "DEEPSEEK_API_KEY": ("ai", "", ""),
    "OPENROUTER_API_KEY": ("ai", "", ""),
    "AI_MAX_CONCURRENT": ("ai", "2", "Simultaneous AI requests per instance"),
    "AI_MAX_TOKENS_CHAT": ("ai", "1024", ""),
    "AI_MAX_TOKENS_GENERATION": ("ai", "4096", ""),
    "AI_MAX_TOKENS_VISION": ("ai", "1024", ""),
    "AI_AVG_TOKENS_CHAT": ("ai", "2500", "Used to estimate cost, not a hard cap"),
    "AI_AVG_TOKENS_GENERATION": ("ai", "18000", "Used to estimate cost, not a hard cap"),
    "AI_AVG_TOKENS_VISION": ("ai", "1200", "Used to estimate cost, not a hard cap"),
    "AI_TOKEN_COST_PER_1K": ("ai", "0.02", "USD per 1000 tokens, for the budget guard"),
    "AI_TOKEN_BUDGET": ("ai", "0", "Hard token cap; 0 means unlimited"),
    "AI_DAILY_CHAT_LIMIT": ("ai", "0", "Requests per day; 0 means unlimited"),
    "AI_DAILY_GEN_LIMIT": ("ai", "0", "Requests per day; 0 means unlimited"),
    "AI_DAILY_VISION_LIMIT": ("ai", "0", "Requests per day; 0 means unlimited"),
    "AI_WEEKLY_BUDGET": ("ai", "0", "Spend cap in USD per week; 0 means unlimited"),
    "AI_CB_MAX_REQUESTS": ("ai", "10", "Client-side circuit breaker threshold"),
    "AI_CB_BLOCK_SECS": ("ai", "60", "How long the circuit breaker stays open"),
    "USAGE_LIMITS": ("ai", "", "JSON override of the plan usage limits"),

    # --- security ---
    "TURNSTILE_ENABLED": ("security", "false", ""),
    "TURNSTILE_SITE_KEY": ("security", "", "Public site key, exposed to the browser"),
    "TURNSTILE_SECRET_KEY": ("security", "", "Server-side verification key"),
    "SENTRY_DSN": ("security", "", "Blank disables error reporting"),
    "SENTRY_TRACES_SAMPLE_RATE": ("security", "0.2", "Fraction of transactions traced"),

    # --- license ---
    "LICENSE_PRODUCT": ("license", "", "Product key this deployment validates"),
    "LICENSE_SECRET": ("license", "", "Shared secret used to sign licence keys"),
    "LICENSE_TRIAL_DAYS": ("license", "14", ""),

    # --- demo ---
    "ENABLE_DEMO_SEED": ("demo", "false",
     "Both this and DEMO_USER_PASSWORD must be set to seed demo users"),
    "DEMO_MODE": ("demo", "false", "Shows demo banners in the UI"),
    "DEMO_USER_EMAIL": ("demo", "demo@example.com", ""),
    "DEMO_USER_PASSWORD": ("demo", "", "Leave blank to keep the seed disabled"),
    "DEMO_USER_NAME": ("demo", "Demo User", ""),
    "DEMO_ADMIN_EMAIL": ("demo", "admin@example.com", ""),
    "DEMO_ADMIN_NAME": ("demo", "Admin User", ""),
    "DEFAULT_CURRENCY": ("core", "USD", "Fallback currency before a locale is known"),

    # --- limits ---
    "RATE_LIMIT_WINDOW_MS": ("limits", "900000", "Rate limit window, 15 minutes"),
    "RATE_LIMIT_MAX": ("limits", "100", "Requests per window per IP"),
    "RATE_LIMIT_MAX_REQUESTS": ("limits", "100", "Requests per window per IP"),

    # --- audit ---
    "AUDIT_LOG": ("audit", "true", ""),
    "AUDIT_LOG_FILE": ("audit", "./audit.log", "Ignored when AUDIT_LOG_STDOUT is on"),
    "AUDIT_LOG_STDOUT": ("audit", "true", "Write the audit log to stdout, for containers"),

    # --- waitlist ---
    "WAITLIST_MODE": ("waitlist", "off", "off | collect | gate"),
    "WAITLIST_AUTO_APPROVE_DAILY": ("waitlist", "0", "0 approves every signup"),
}

# Payment gateways: provider -> (docs, [keys with hints])
PAYMENTS = {
    "lemonsqueezy": ("Lemon Squeezy — merchant of record, so tax and VAT are "
     "handled for you. Overlay checkout needs only the store id; an API key "
     "additionally enables server-side checkout creation. Webhook: "
     "/api/lemonsqueezy/webhook", [
         ("LEMONSQUEEZY_STORE_ID", ""),
         ("LEMONSQUEEZY_STORE_URL", ""),
         ("LEMONSQUEEZY_API_KEY", "Enables server-side checkout creation"),
         ("LEMONSQUEEZY_WEBHOOK_SECRET", "Verifies /api/lemonsqueezy/webhook"),
         ("LEMONSQUEEZY_VARIANT_ID", "Single-variant products"),
         ("LEMONSQUEEZY_VARIANT_STARTER", "Pricing tier 1"),
         ("LEMONSQUEEZY_VARIANT_PRO", "Pricing tier 2"),
         ("LEMONSQUEEZY_VARIANT_ENTERPRISE", "Pricing tier 3"),
     ]),
    "stripe": ("Stripe — card payments and subscriptions. Webhook: "
     "/api/payment/webhook", [
         ("STRIPE_PUBLISHABLE_KEY", "Safe to expose to the browser"),
         ("STRIPE_SECRET_KEY", "Server only"),
         ("STRIPE_WEBHOOK_SECRET", "Verifies /api/payment/webhook"),
         ("STRIPE_PRODUCT_STARTER", ""),
         ("STRIPE_PRICE_STARTER", ""),
         ("STRIPE_PRODUCT_PRO", ""),
         ("STRIPE_PRICE_PRO", ""),
         ("STRIPE_PRODUCT_AGENCY", ""),
         ("STRIPE_PRICE_AGENCY", ""),
         ("STRIPE_PRODUCT_CREDITS_25", ""),
         ("STRIPE_PRICE_CREDITS_25", ""),
         ("STRIPE_PRODUCT_CREDITS_100", ""),
         ("STRIPE_PRICE_CREDITS_100", ""),
     ]),
    "paypal": ("PayPal — Webhook: /api/payment/paypal/webhook", [
         ("PAYPAL_CLIENT_ID", ""),
         ("PAYPAL_CLIENT_SECRET", "Server only"),
         ("PAYPAL_MODE", "sandbox | live"),
         ("PAYPAL_WEBHOOK_ID", "Verifies /api/payment/paypal/webhook"),
     ]),
    "paddle": ("Paddle — merchant of record. Webhook: /api/payment/paddle/webhook", [
         ("PADDLE_API_KEY", ""),
         ("PADDLE_WEBHOOK_SECRET", ""),
         ("PADDLE_ENV", "sandbox | live"),
     ]),
    "razorpay": ("Razorpay — India. Webhook: /api/payment/razorpay/webhook", [
         ("RAZORPAY_KEY_ID", ""),
         ("RAZORPAY_KEY_SECRET", "Server only"),
         ("RAZORPAY_WEBHOOK_SECRET", ""),
     ]),
    "square": ("Square — Webhook: /api/payment/square/webhook", [
         ("SQUARE_ACCESS_TOKEN", "Server only"),
         ("SQUARE_LOCATION_ID", ""),
         ("SQUARE_ENVIRONMENT", "sandbox | production"),
     ]),
    "mollie": ("Mollie — Europe. Webhook: /api/payment/mollie/webhook", [
         ("MOLLIE_API_KEY", ""),
         ("MOLLIE_ORGANIZATION_ID", ""),
     ]),
    "flutterwave": ("FlutterWave — Africa. Webhook: /api/payment/flutterwave/webhook", [
         ("FLUTTERWAVE_PUBLIC_KEY", "Safe to expose to the browser"),
         ("FLUTTERWAVE_SECRET_KEY", "Server only"),
         ("FLUTTERWAVE_ENCRYPTION_KEY", "Server only"),
         ("FLUTTERWAVE_WEBHOOK_SECRET", ""),
     ]),
    "mercadopago": ("Mercado Pago — Latin America. Webhook: "
     "/api/payment/mercadopago/webhook", [
         ("MERCADOPAGO_PUBLIC_KEY", "Safe to expose to the browser"),
         ("MERCADOPAGO_ACCESS_TOKEN", "Server only"),
         ("MERCADOPAGO_WEBHOOK_PASSWORD", ""),
     ]),
    "liqpay": ("LiqPay — Webhook: /api/payment/liqpay/webhook", [
         ("LIQPAY_PUBLIC_KEY", "Safe to expose to the browser"),
         ("LIQPAY_PRIVATE_KEY", "Server only"),
     ]),
    "paytm": ("Paytm — India. Webhook: /api/payment/paytm/webhook", [
         ("PAYTM_MERCHANT_ID", ""),
         ("PAYTM_MERCHANT_KEY", "Server only"),
         ("PAYTM_WEBSITE", "WEBSTAGING for sandbox, WEB for live"),
         ("PAYTM_INDUSTRY_TYPE", "Retail"),
         ("PAYTM_CHANNEL_ID", "WEB"),
         ("PAYTM_MODE", "sandbox | live"),
     ]),
    "bkash": ("bKash — Bangladesh. Webhook: /api/payment/bkash/webhook", [
         ("BKASH_APP_KEY", ""),
         ("BKASH_APP_SECRET", "Server only"),
         ("BKASH_USERNAME", ""),
         ("BKASH_PASSWORD", "Server only"),
         ("BKASH_MERCHANT_ID", ""),
     ]),
}

PAYMENT_GATEWAYS_ENABLED = (
    "PAYMENT_GATEWAYS_ENABLED", "core",
    "Comma-separated list of gateways to enable, or all. A gateway left out "
    "here is never mounted, and its keys are ignored"
)
# written by hand inside the core block, so keep it out of the leftover pass
EXTRA_CORE_KEYS = {PAYMENT_GATEWAYS_ENABLED[0]}

# Frontend variables: everything here is public by definition and must carry
# the VITE_ prefix so the bundler exposes it deliberately.
FRONTEND_VARS = {
    "VITE_API_URL": ("Backend base URL", "http://localhost:5000/api"),
    "VITE_API_TIMEOUT": ("Request timeout in milliseconds", "15000"),
    "VITE_LEMONSQUEEZY_STORE_ID": ("Lemon Squeezy store for overlay checkout", ""),
    "VITE_LEMONSQUEEZY_STORE_URL": ("Checkout page to redirect to", ""),
    "VITE_LEMONSQUEEZY_VARIANT_ID": ("Single-variant products", ""),
    "VITE_FORMSPREE_ID": ("Formspree form id for contact forms", ""),
    "VITE_FORMSPREE_NEWSLETTER_ID": ("Formspree form id for the newsletter", ""),
    "VITE_FORMSPREE_ENDPOINT": ("Override the Formspree endpoint", ""),
    "VITE_CONTACT_WEBHOOK_URL": ("Webhook that receives contact submissions", ""),
    "VITE_LEADS_WEBHOOK": ("Webhook that receives captured leads", ""),
    "VITE_GA4_ID": ("Google Analytics 4 measurement id, e.g. G-XXXXXXX", ""),
    "VITE_PLAUSIBLE_DOMAIN": ("Plausible site domain", ""),
    "VITE_PLAUSIBLE_HOST": ("Plausible script host for self-hosting", ""),
    "VITE_POSTHOG_KEY": ("PostHog project api key", ""),
    "VITE_POSTHOG_HOST": ("PostHog ingestion host", ""),
    "VITE_MIXPANEL_TOKEN": ("Mixpanel project token", ""),
    "VITE_FATHOM_SITE_ID": ("Fathom site id", ""),
}

# Keys that must never appear in a frontend example file, because Vite would
# only expose the VITE_ ones anyway and the rest invite a leak.
SERVER_ONLY_IN_FRONTEND = [
    "JWT_SECRET", "DATABASE_URL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
    "PAYPAL_CLIENT_SECRET", "LEMONSQUEEZY_API_KEY", "LEMONSQUEEZY_WEBHOOK_SECRET",
    "BKASH_APP_SECRET", "RAZORPAY_KEY_SECRET", "SQUARE_ACCESS_TOKEN",
    "FLUTTERWAVE_SECRET_KEY", "FLUTTERWAVE_ENCRYPTION_KEY", "MOLLIE_API_KEY",
    "MERCADOPAGO_ACCESS_TOKEN", "LIQPAY_PRIVATE_KEY", "PAYPAL_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET", "GITHUB_CLIENT_SECRET", "SMTP_PASS", "SMTP_USER",
    "TURNSTILE_SECRET_KEY", "SENTRY_DSN", "LICENSE_SECRET", "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY", "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY", "PADDLE_API_KEY", "RAZORPAY_KEY_ID", "DEMO_USER_PASSWORD",
    "PADDLE_WEBHOOK_SECRET", "PAYPAL_WEBHOOK_ID", "MERCADOPAGO_WEBHOOK_PASSWORD",
    "RAZORPAY_WEBHOOK_SECRET", "FLUTTERWAVE_WEBHOOK_SECRET", "PAYTM_MERCHANT_KEY",
    "BKASH_PASSWORD", "BKASH_USERNAME", "BKASH_APP_KEY", "LIQPAY_PUBLIC_KEY",
    "MERCADOPAGO_PUBLIC_KEY", "FLUTTERWAVE_PUBLIC_KEY",
]

HEADER = """\
# Environment template — copy to .env and fill in the blanks.
#
#   cp .env.example .env
#
# Never commit a real .env. Only keys prefixed with VITE_ reach the browser;
# everything else stays on the server. Secrets are left blank on purpose — a
# value that looks like a working credential is how credentials leak.
#
# Generate a secret:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
"""

FOOTER = """
# ---------------------------------------------------------------------------
# Before going live
#
# 1. Set NODE_ENV=production. The demo seed is hard-disabled in production.
# 2. Set a strong JWT_SECRET and JWT_REFRESH_SECRET (32+ characters each).
# 3. Set FRONTEND_URL to your real frontend origin, or payment redirects and
#    CORS will point at localhost.
# 4. Choose your payment gateways in PAYMENT_GATEWAYS_ENABLED and fill only
#    those providers' keys. Everything else can stay blank.
# 5. Set SMTP_* so verification, password reset and receipt email actually send.
# 6. Run the migrations, not sequelize.sync():
#      npm run migrate
# 7. CORS_ORIGIN and ALLOWED_ORIGINS must list your real origin, not '*'.
# 8. Fill TURNSTILE_* and keep TURNSTILE_ENABLED=true to stop bot signups.
"""