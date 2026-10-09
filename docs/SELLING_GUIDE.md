# Selling LumiCorePro on Lemon Squeezy

This guide covers the complete commercial workflow: store setup, packaging,
listing copy, license activation, webhooks and support. Everything here is
implemented in the product — no external tooling is required.

---

## 1. Why Lemon Squeezy

Lemon Squeezy handles merchant-of-record obligations (VAT/sales tax, invoicing,
chargebacks) and pays out to any country with KYC on file. For a digital
product sold internationally that removes the single largest compliance
burden, which is why the product's sales path is built around it rather than
around a self-hosted checkout.

The platform still contains Stripe/PayPal/Razompay integrations, but those are
for the **internal marketplace** (buyers purchasing templates from *you*), not
for selling the platform itself.

---

## 2. Store setup

### 2.1 Create the store

1. Sign up at Lemon Squeezy and complete KYC (identity + payout details).
2. Enable the test mode while you validate the flow; switch to live only after
   a real purchase has been activated end to end.

### 2.2 Create the product and variants

Create one product with variants that map to your licence tiers:

| Variant | Lemon Squeezy name | Suggested price | What the buyer gets |
| --- | --- | --- | --- |
| Lifetime — Single Site | `lifetime-single` | $149 | Full product, one production domain |
| Lifetime — Agency | `lifetime-agency` | $399 | Full product, unlimited client sites |
| Annual Maintenance | `maintenance-annual` | $99/yr | Updates + support for 12 months |

### 2.3 Checkout custom field (this is what activates the buyer)

Add a **text** field named `license_key` to the checkout form. The buyer
pastes the LumiCorePro key they were issued at signup; the webhook then binds
that key to their order. Without this field the purchase cannot be activated
automatically.

Recommended helper text under the field:

> Paste the license key from your LumiCorePro welcome email. Your purchase is
> bound to this key.

### 2.4 Webhook

1. In Lemon Squeezy → **Settings → Webhooks**, add the endpoint:

   ```
   https://<your-domain>/api/lemonsqueezy/webhook
   ```

2. Subscribe to:

   * `license_key_created`
   * `subscription_created`
   * `subscription_cancelled`
   * `subscription_expired`
   * `subscription_paused`
   * `order_refunded`

3. Copy the **signing secret** into your environment and restart the API:

   ```bash
   LEMONSQUEEZY_SIGNING_SECRET=<paste signing secret>
   ```

Every webhook is verified with a constant-time HMAC-SHA256 comparison over
the raw request body. A request with a missing or forged signature is rejected
with `401` and never touches the database.

---

## 3. Packaging a release

```bash
python scripts/package_for_sale.py --dry-run     # review what ships
python scripts/package_for_sale.py               # build
```

Output lands in `release/`:

```
release/lumicorepro-core-7.13.0.zip
release/lumicorepro-core-7.13.0.manifest.json
```

The manifest records the file count, unpacked size and the archive's SHA-256.
Attach both to the Lemon Squeezy product as a **version file** so buyers
receive immutable, verifiable downloads.

The packager deliberately excludes `node_modules`, logs, coverage, local
`.env` files, database volumes and past customer deliveries — only the product
ships.

---

## 4. Listing copy

**Short description (Lemon Squeezy field, ~200 characters):**

> Self-hosted AI website studio. Generate production-ready React + Node
> storefronts, run a template marketplace, and keep every build measurable.

**Long description outline:**

1. **The problem** — agency builds take weeks, cost money, and quality is
   unverifiable.
2. **What it is** — a self-hosted studio: AI generation pipeline, quality gates,
   marketplace, billing and licensing.
3. **Evidence** — every build ships a quality score, a guardrail report and an
   audit trail; SLOs and cost ledger included.
4. **Who it is for** — agencies, freelancers, developers selling websites.
5. **Requirements** — Docker, 2 GB RAM, your own AI provider key.
6. **What is included** — product, documentation, 30 days of support.

---

## 5. Activation flow (end to end)

1. Buyer purchases and enters their `license_key` at checkout.
2. Lemon Squeezy delivers `license_key_created` to your webhook.
3. The API verifies the signature, validates the key with the HMAC license
   engine, and writes a `license_entitlements` row (`status: active`).
4. The buyer activates in the app; `GET /api/lemonsqueezy/entitlement/{key}`
   reports `{ known: true, active: true }`.
5. On cancellation or refund the entitlement moves to `revoked`, and the key
   stops activating.

Operator view (admin):

```
GET /api/lemonsqueezy/entitlements
```

---

## 6. Trial and refund handling

* **Trials:** issue a trial key through the admin API
  (`POST /api/license/issue` with `licenseType: "trial"`). Trials carry their
  own expiry in the key payload — no server state required.
* **Refunds:** Lemon Squeezy sends `order_refunded`; the entitlement is revoked
  automatically. Manual overrides are an admin decision and should be recorded
  in the audit trail.

---

## 7. Support templates

**Purchase confirmation**

> Thank you for your purchase. Your licence is bound to the key you entered at
> checkout and is already active — you can sign in and validate it from
> *Settings → License*. Installation takes about ten minutes on a 2 GB VPS; the
> manual covers Docker and manual setups. Reply to this email if anything is
> unclear.

**"My license key is not recognised"**

> Please confirm three things: the key you entered is the one from your purchase
> email, the deployment has `LICENSE_SECRET` set (it must be the same value
> used when the key was issued), and the API has been restarted since. You can
> verify your key at `GET /api/lemonsqueezy/entitlement/{your-key}`.

**"Generation fails"**

> Generation requires a provider key. Check that at least one of
> `GEMINI_API_KEY`, `GROK_API_KEY`, `DEEPSEEK_API_KEY` or `OPENROUTER_API_KEY`
> is set in your `.env` and that `curl http://localhost:8000/health` responds.
> The run report records every phase, so the failing phase is visible in
> `GET /api/ai/runs/{run_id}`.

---

## 8. Pricing and margin notes

* The product's marginal cost is AI provider spend, which you control: the daily
  budget cap and the semantic cache bound it per customer.
* Lifetime pricing is viable while the semantic cache keeps repeat generations
  free; the ledger (`GET /api/ai/spend/ledger`) shows exactly what each run
  cost, so margin is measurable rather than guessed.
* Annual maintenance is the honest anchor for a product that keeps improving
  itself through autopilot sweeps.

---

## 9. Release checklist

1. `npm run lint && npm run test && npm run build` — frontend
2. `npm --prefix backend run test:ci` — backend
3. `python -m pytest ai-agent/tests -q` — generation engine
4. `python scripts/package_for_sale.py` — build the archive
5. Verify the manifest SHA-256 and attach it to the Lemon Squeezy version
6. Tag the release (`git tag vX.Y.Z`) so the release workflow publishes images