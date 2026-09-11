"""Database Schema Configuration & Structural Contract (TRD #4).

Enforces, for every full-stack generation, the 14-model relational baseline with
accurate foreign-key contracts, plus the row-lock concurrency mandate on
checkout:

1. Relational Entity Definitions (14 Model Baseline)
   User, Product, Order, Payment, Cart, CartItem, Review, Wishlist, Address,
   Coupon, Subscription, Notification, AnalyticsEvent, Category — every model
   must exist with its FK contracts wired in models/index.js associations.

2. Row Lock & Concurrency Mandate
   Order controllers/services in the generated tree must run checkout inside a
   DB transaction with isolated `SELECT ... FOR UPDATE` row locks + guarded
   atomic stock decrement, preventing oversell on concurrent purchases.

Design: the canonical backend-library is READ-ONLY — this module verifies the
hydrated copy in the generated project, patches the structural FK gap
(`Order.coupon_id` is missing from the canonical Order model), documents the
baseline→canonical field aliases, serializes the FK contract as machine +
human-readable artifacts (SCHEMA-CONTRACT.md, database/schemas/schema.sql), and
emits a conformance report. Static (API-less) runtimes are N/A. Idempotent via
marker `LUMICORE_SCHEMA`.
"""
import os
import re
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger
from utils.file_manager import FileManager

_MARKER = "LUMICORE_SCHEMA"

# TRD #4 §1 — the 14-model relational baseline (Category included: Product.category_id contract).
MODEL_BASELINE: List[str] = [
    "User", "Product", "Order", "Payment", "Cart", "CartItem", "Review",
    "Wishlist", "Address", "Coupon", "Subscription", "Notification",
    "AnalyticsEvent", "Category",
]

# Expected FK contracts: (child, column, parent). Verified in models/index.js.
FK_CONTRACT: List[Tuple[str, str, str]] = [
    ("User", "id", None),  # primary key surrogate
    ("Product", "category_id", "Category"),
    ("Product", "vendor_id", "User"),
    ("Order", "user_id", "User"),
    ("Order", "coupon_id", "Coupon"),          # ← structural gap patched in generated copy
    ("Payment", "user_id", "User"),
    ("Payment", "order_id", "Order"),
    ("Cart", "user_id", "User"),
    ("CartItem", "cart_id", "Cart"),
    ("CartItem", "product_id", "Product"),
    ("Review", "user_id", "User"),
    ("Review", "product_id", "Product"),
    ("Wishlist", "user_id", "User"),
    ("Wishlist", "product_id", "Product"),
    ("Address", "user_id", "User"),
    ("Coupon", "user_id", "User"),
    ("Subscription", "user_id", "User"),
    ("Notification", "recipient_id", "User"),
    ("AnalyticsEvent", "user_id", "User"),
]

# TRD §1 baseline field ⇒ canonical field aliases (canonical names stay deployed;
# the contract documents the mapping so money/stock/tracking semantics are explicit).
FIELD_ALIASES: Dict[str, Dict[str, str]] = {
    "User": {
        "id": "id",
        "email": "email",
        "password_hash": "password (bcrypt-hashed, excluded by default scope)",
        "two_factor_secret": "twoFactorSecret",
        "role": "role ('user' | 'admin' | 'vendor')",
    },
    "Product": {
        "id": "id",
        "title": "title",
        "description": "description",
        "price_cents": "price (DECIMAL(10,2), USD dollars)",
        "stock_count": "stock (INTEGER, guarded ≥ 0)",
        "category_id": "category_id (INTEGER FK → categories.id, nullable)",
    },
    "Order": {
        "id": "id",
        "user_id": "user_id (INTEGER FK → users.id, nullable)",
        "coupon_id": "coupon_id (INTEGER FK → coupons.id, patched LUMICORE_SCHEMA)",
        "total_amount": "totalPrice (DECIMAL(10,2))",
        "tracking_status": "status ('pending'|'processing'|'shipped'|'delivered'|'cancelled'|'refunded') + trackingNumber/carrier",
    },
}

_ROW_LOCK_CHECKS: Dict[str, Dict[str, str]] = {
    "transaction": {
        "pattern": r"sequelize\.transaction|transaction\s*\(\s*async",
        "hint": "checkout wrapped in a single DB transaction",
    },
    "row_lock": {
        "pattern": r"lock:\s*t\.LOCK\.UPDATE|LOCK\.UPDATE|FOR UPDATE",
        "hint": "isolated SELECT ... FOR UPDATE row lock on product",
    },
    "stock_guard": {
        "pattern": r"insufficient\s+stock|stock\s*<\s*item\.quantity|<.*stock",
        "hint": "stock guard checked while row is locked",
    },
    "atomic_decrement": {
        "pattern": r"\.update\(\{?\s*stock:|\.decrement\(",
        "hint": "atomic stock decrement inside the same transaction",
    },
}

# PostgreSQL DDL — snake_case baseline with FK constraints + checkout lock guidance.
_SCHEMA_SQL = r"""-- Database Schema — Structural Contract (TRD #4)
-- Generated baseline: 14 relational entities with explicit FK contracts.
-- PostgreSQL 14+ / MySQL 8+ compatible (JSONB on Postgres, JSON on MySQL).

CREATE TABLE IF NOT EXISTS categories (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  slug        VARCHAR(180) UNIQUE NOT NULL,
  parent_id   BIGINT NULL REFERENCES categories(id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id                 BIGSERIAL PRIMARY KEY,
  email              VARCHAR(255) UNIQUE NOT NULL,
  password_hash      VARCHAR(255) NOT NULL,        -- bcrypt (12+ rounds)
  role               VARCHAR(50) NOT NULL DEFAULT 'user'
                     CHECK (role IN ('user', 'admin', 'vendor')),
  two_factor_secret  VARCHAR(255) NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
  id           BIGSERIAL PRIMARY KEY,
  title        VARCHAR(255) NOT NULL,
  description  TEXT NOT NULL,
  price_cents  BIGINT NOT NULL CHECK (price_cents >= 0),
  stock_count  INTEGER NOT NULL DEFAULT 0 CHECK (stock_count >= 0),
  category_id  BIGINT NULL REFERENCES categories(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_products_category   ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_title_db   ON products(lower(title));

CREATE TABLE IF NOT EXISTS coupons (
  id         BIGSERIAL PRIMARY KEY,
  code       VARCHAR(50) UNIQUE NOT NULL,
  discount   NUMERIC(10,2) NOT NULL DEFAULT 0,
  user_id    BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  valid_until TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id               BIGSERIAL PRIMARY KEY,
  user_id          BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  coupon_id        BIGINT NULL REFERENCES coupons(id) ON DELETE SET NULL,
  total_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
  tracking_status  VARCHAR(50) NOT NULL DEFAULT 'pending'
                   CHECK (tracking_status IN ('pending','processing','shipped','delivered','cancelled','refunded')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_user    ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_coupon  ON orders(coupon_id);

CREATE TABLE IF NOT EXISTS payments (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  order_id    BIGINT NULL REFERENCES orders(id) ON DELETE SET NULL,
  amount      NUMERIC(12,2) NOT NULL,
  status      VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_user  ON payments(user_id);

CREATE TABLE IF NOT EXISTS carts (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_carts_user ON carts(user_id);

CREATE TABLE IF NOT EXISTS cart_items (
  id          BIGSERIAL PRIMARY KEY,
  cart_id     BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
  product_id  BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  quantity    INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0)
);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart    ON cart_items(cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_product ON cart_items(product_id);

CREATE TABLE IF NOT EXISTS reviews (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  product_id  BIGINT NULL REFERENCES products(id) ON DELETE SET NULL,
  rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment     TEXT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);

CREATE TABLE IF NOT EXISTS wishlists (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  product_id  BIGINT NULL REFERENCES products(id) ON DELETE SET NULL,
  UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS addresses (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  label       VARCHAR(100) NULL,
  line1       VARCHAR(255) NOT NULL,
  city        VARCHAR(120) NOT NULL,
  country     VARCHAR(120) NOT NULL,
  postcode    VARCHAR(20) NULL
);
CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  plan          VARCHAR(50) NOT NULL,
  status        VARCHAR(50) NOT NULL DEFAULT 'active',
  renews_at     TIMESTAMPTZ NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

CREATE TABLE IF NOT EXISTS notifications (
  id           BIGSERIAL PRIMARY KEY,
  recipient_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
  type         VARCHAR(50) NOT NULL,
  title        VARCHAR(255) NOT NULL,
  message      TEXT NULL,
  read_at      TIMESTAMPTZ NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);

CREATE TABLE IF NOT EXISTS analytics_events (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  event       VARCHAR(100) NOT NULL,
  payload     JSONB NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user ON analytics_events(user_id);

-- ═══ Row Lock & Concurrency Mandate (TRD #4 §2) ═══
-- Checkout MUST run inside a single DB transaction that locks each product row:
--
--   BEGIN;
--   SELECT * FROM products WHERE id = $1 AND stock_count >= $qty FOR UPDATE;
--   -- no row → insufficient stock → ROLLBACK
--   UPDATE products SET stock_count = stock_count - $qty WHERE id = $1;
--   INSERT INTO orders (user_id, coupon_id, total_amount, tracking_status) VALUES (...);
--   COMMIT;
--
-- `FOR UPDATE` serializes concurrent checkouts on the same SKU, eliminating
-- oversell without optimistic retry loops.
"""


class SchemaContractInjector:
    """Verifies + patches the relational contract and serializes it per project."""

    def generate(self, spec: Dict[str, Any], project_dir: str, mode: str = "") -> Dict[str, Any]:
        backend = os.path.join(project_dir, "backend")
        report: Dict[str, Any] = {"applies": False, "runtime_mode": spec.get("runtime_mode", "transactional")}
        if not os.path.isdir(backend):
            report["reason"] = "no backend/ tree (static runtime or pre-render)"
            return report
        if not os.path.isdir(os.path.join(backend, "models")):
            report["reason"] = "backend present but models/ missing"
            return report
        report["applies"] = True

        report["models"] = self._scan_models(backend)
        # Patch structural gaps FIRST so the FK verdict reflects the enforced contract.
        report["order_coupon_fk"] = self._patch_order_coupon_fk(backend)
        report["fk"] = self._verify_fk_contract(backend)
        report["row_lock"] = self._verify_row_lock(backend)
        report["artifacts"] = self._write_contract_artifacts(spec, project_dir, report)

        agent_logger.info(
            f"SchemaContract: models {report['models']['present']}/{report['models']['total']} "
            f"fk_missing={len(report['fk']['missing'])} "
            f"row_lock={'pass' if report['row_lock']['pass'] else 'gap'}"
        )
        return report

    # ── 1. Model baseline ──────────────────────────────────────────────────
    def _scan_models(self, backend: str) -> Dict[str, Any]:
        models_dir = os.path.join(backend, "models")
        existing = {fname[: -len(".js")] for fname in os.listdir(models_dir) if fname.endswith(".js")}
        missing = [m for m in MODEL_BASELINE if m not in existing]
        return {
            "total": len(MODEL_BASELINE),
            "present": len(MODEL_BASELINE) - len(missing),
            "missing": missing,
            "pass": not bool(missing),
        }

    # ── 2. FK contract (models/index.js associations) ──────────────────────
    def _verify_fk_contract(self, backend: str) -> Dict[str, Any]:
        idx = os.path.join(backend, "models", "index.js")
        if not os.path.isfile(idx):
            return {"pass": False, "missing": [f for _, c, _ in FK_CONTRACT if c] + ["index.js"]}
        content = FileManager.read_file(idx)
        missing = []
        for child, column, parent in FK_CONTRACT:
            if not column or parent is None:
                continue
            if f"foreignKey: '{column}'" not in content:
                missing.append(f"{child}.{column}" + (f" → {parent}" if parent else ""))
        return {"pass": not bool(missing), "missing": missing, "checked": len([1 for _, c, p in FK_CONTRACT if c and p])}

    # ── 3. Structural gap: Order.coupon_id FK (canonical library stays pure) ─
    def _patch_order_coupon_fk(self, backend: str) -> Dict[str, Any]:
        order_path = os.path.join(backend, "models", "Order.js")
        index_path = os.path.join(backend, "models", "index.js")
        patched = []
        if os.path.isfile(order_path) and "coupon_id" not in FileManager.read_file(order_path):
            content = FileManager.read_file(order_path)
            anchor = "createdAt: {"
            if anchor in content:
                field = (
                    "    coupon_id: {\n"
                    "      type: DataTypes.INTEGER,\n"
                    "      allowNull: true,\n"
                    "    }, // LUMICORE_SCHEMA:coupon_fk\n"
                )
                content = content.replace(anchor, field + anchor, 1)
                FileManager.write_file(order_path, content)
                patched.append("Order.js:coupon_id")
        if os.path.isfile(index_path) and "Order.belongsTo(Coupon" not in FileManager.read_file(index_path):
            content = FileManager.read_file(index_path)
            anchor = "Order.hasMany(Payment, { foreignKey: 'order_id', as: 'payments' });"
            assoc = (
                "Order.belongsTo(Coupon, { foreignKey: 'coupon_id', as: 'coupon' }); "
                "// LUMICORE_SCHEMA:coupon_fk\n"
            )
            if anchor in content:
                content = content.replace(anchor, anchor + "\n" + assoc, 1)
            else:
                content = content + "\n" + assoc
            FileManager.write_file(index_path, content)
            patched.append("index.js:Order.belongsTo(Coupon)")
        return {"patched": patched, "status": "ok" if patched else "no-op"}

    # ── 4. Row-lock concurrency mandate ────────────────────────────────────
    def _verify_row_lock(self, backend: str) -> Dict[str, Any]:
        candidates: List[str] = []
        svc = os.path.join(backend, "services")
        if os.path.isdir(svc):
            for root, _, files in os.walk(svc):
                for fname in files:
                    if fname.endswith(".js") and any(k in fname.lower() for k in ("order", "checkout", "inventory")):
                        candidates.append(os.path.join(root, fname))
            # include route handlers that reference checkout/order creation
            routes = os.path.join(backend, "routes")
            if os.path.isdir(routes):
                for fname in os.listdir(routes):
                    if fname.endswith(".js") and "order" in fname.lower():
                        candidates.append(os.path.join(routes, fname))

        content = "\n".join(
            FileManager.read_file(p) for p in candidates
            if os.path.isfile(p) and ("checkout" in p.lower() or "order" in p.lower())
        )
        checks: Dict[str, Dict[str, Any]] = {}
        for key, spec_check in _ROW_LOCK_CHECKS.items():
            found = bool(re.search(spec_check["pattern"], content, flags=re.IGNORECASE))
            checks[key] = {"pass": found, "hint": spec_check["hint"] if found else ""}
        passed = [k for k, v in checks.items() if v["pass"]]
        return {
            "pass": len(passed) == len(_ROW_LOCK_CHECKS),
            "checks": checks,
            "sources": [os.path.relpath(p, backend) for p in candidates],
            "passed": passed,
            "missing": [k for k, v in checks.items() if not v["pass"]],
        }

    # ── Artifacts: SCHEMA-CONTRACT.md + database/schemas/schema.sql ────────
    def _write_contract_artifacts(self, spec: Dict[str, Any], root: str, report: Dict[str, Any]) -> List[str]:
        project = str(spec.get("project_name") or "This project").replace("-", " ").title()
        out: List[str] = []

        fk_rows = []
        for child, column, parent in FK_CONTRACT:
            if not column or parent is None:
                continue
            fk_rows.append(f"| `{child}.{column}` | `{parent or '—'}.id` |")

        doc = f"""# Database Schema Configuration & Structural Contract — {project}

> TRD #4 baseline: 14 relational entities with explicit FK contracts + row-lock
> checkout concurrency. The canonical backend-library stays read-only; the
> generated `backend/` copy is verified and patched below.

## 1. Model Baseline
Models mounted: **{report["models"]["present"]}/{report["models"]["total"]}** {'✓' if report["models"]["pass"] else '✗ — MISSING: ' + ", ".join(report["models"]["missing"])}.

{", ".join(f"`{m}`" for m in MODEL_BASELINE)}

## 2. Foreign-Key Contracts
Verified in `backend/models/index.js`: **{report["fk"]["checked"]}** contracts, {'all wired' if report["fk"]["pass"] else 'gaps: ' + ", ".join(report["fk"]["missing"])}.

{fk_rows}

- Indices: queried columns indexed (`user_id`, `product_id`, `category_id`, `order_id`, `coupon_id`, …).
- `Order.coupon_id` → `coupons.id`: patched into the generated copy
  (**{report["order_coupon_fk"]["status"]}**), canonical library untouched.

## 3. Baseline → Canonical Field Aliases
| Model | Baseline field | Canonical field |
|-------|----------------|-----------------|
"""
        for model, aliases in FIELD_ALIASES.items():
            for base_field, canonical in aliases.items():
                doc += f"| `{model}` | `{base_field}` | `{canonical}` |\n"

        rl = report["row_lock"]
        doc += f"""
## 4. Row Lock & Concurrency Mandate
Order checkout runs in a single DB transaction with isolated row locks:
{'**CONFORMANT**' if rl["pass"] else '**GAP** — missing: ' + ", ".join(rl["missing"])}.

| Control | Status |
|---------|--------|
"""
        for key, check in rl["checks"].items():
            doc += f"| `{key}` | {'✓' if check['pass'] else '✗'} {check['hint']} |\n"
        doc += f"""
Sources scanned: {", ".join("`" + s + "`" for s in rl["sources"]) or "none"}.

Deployable DDL reference: `database/schemas/schema.sql`
"""
        path = os.path.join(root, "SCHEMA-CONTRACT.md")
        FileManager.write_file(path, doc)
        out.append(path)

        ddl_path = os.path.join(root, "database", "schemas", "schema.sql")
        FileManager.ensure_dir(os.path.dirname(ddl_path))
        FileManager.write_file(ddl_path, _SCHEMA_SQL)
        out.append(ddl_path)
        return out


schema_contract_injector = SchemaContractInjector()