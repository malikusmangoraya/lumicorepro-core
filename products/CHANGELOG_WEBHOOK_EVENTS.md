# Webhook Event Delivery Parity — per-product backend notes

Last touched: 2026-10-10 (batch review pass)

These notes exist so any future tweak to webhook receivers stays traceable across
the eleven backends. They are product-facing working notes, not a shipped runtime
contract.

## Scope

Each `products/<name>/backend/routes/` folder carries its webhook receivers.
This doc records the current state of webhook parity across products, based on the
routes that are actually present in each backend’s source tree.

## Per-product notes

### apex
- Lemon Squeezy routes present and verified earlier in this session.
- Payment webhook parity uses Lemon Squeezy HMAC verification path.

### flowpilot
- Same Lemon Squeezy webhook route as apex family.
- Payment webhook parity confirmed by earlier audit run.

### resupro
- Payment webhook routes present.
- Same verification posture as apex/flowpilot for Lemon Squeezy webhook ingestion.

### claimflow-ai
- Backend routes include webhook handling for payments.
- Webhook parity consistent with other products using same gateway path.

### aurelia-estates
- Webhook routes available.
- Payment gateway webhook receipt parity aligns with apex family.

### aurum-fitness
- Webhook routes available.
- Same posture as aurelia-estates for payment webhooks.

### meridian-capital
- Webhook routes available.
- Payment webhook receipt parity aligns.

### nuage-events
- Webhook routes available.
- Payment webhook parity aligns with family.

### prestige-studio
- Webhook routes available.
- Payment webhook parity aligns with family.

### saffron-voyage
- Webhook routes available.
- Payment webhook parity aligns with family.

### studio-lumen
- Webhook routes available.
- Payment webhook parity aligns with family.

## Shared contract notes

- Where a backend exposes Lemon Squeezy or equivalent payment webhooks, the
  verification path uses signature checks.
- Idempotency is handled where applicable in the payment webhook receivers.
- Each backend keeps its own webhook registry or route map in
  `backend/webhook-registry.json` or equivalent.

## Remaining work

- If a product’s backend needs a new webhook provider beyond the payment path,
  add the route and update this doc.
- If any webhook parity difference is intentional per product, record it here
  with an explicit reason.
