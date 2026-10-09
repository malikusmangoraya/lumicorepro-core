# Webhook Integration Guide — Saas

## Inbound Endpoints

| Endpoint                            | Source   | Description                  |
| ----------------------------------- | -------- | ---------------------------- |
| `POST /api/webhooks/stripe`         | Stripe   | Payment events               |
| `POST /api/webhooks/custom/:source` | Any      | Generic HMAC-signed webhooks |
| `POST /api/webhooks/emit`           | Internal | Programmatic event emission  |
| `GET /api/webhooks/logs`            | Internal | Delivery audit log           |

## Registered Events

| Event                     | Source   | Description               |
| ------------------------- | -------- | ------------------------- |
| `subscription.created`    | stripe   | New subscription          |
| `subscription.upgraded`   | stripe   | Plan upgraded             |
| `subscription.downgraded` | stripe   | Plan downgraded           |
| `subscription.cancelled`  | stripe   | Subscription cancelled    |
| `invoice.paid`            | stripe   | Invoice payment succeeded |
| `invoice.failed`          | stripe   | Invoice payment failed    |
| `user.registered`         | internal | New user signup           |
| `user.trial_started`      | internal | Trial period started      |
| `user.trial_expiring`     | internal | Trial ending in 3 days    |
| `feature.limit_reached`   | internal | Usage limit hit           |

## Environment Variables

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxx  # From Stripe Dashboard
INTERNAL_WEBHOOK_SECRET=your_secret
WEBHOOK_ENDPOINTS='[{"url":"https://hooks.slack.com/xxx","events":["order.created"],"secret":"xxx"}]'
```

## Usage Example

```javascript
import { eventBus } from './utils/event-bus.js';

// Emit an event after order is created:
eventBus.emit('order.created', { orderId: order._id, total: order.total });

// Listen for an event:
eventBus.on('order.created', async (data) => {
  await sendOrderConfirmationEmail(data.orderId);
  await notifySlack(data);
});
```
