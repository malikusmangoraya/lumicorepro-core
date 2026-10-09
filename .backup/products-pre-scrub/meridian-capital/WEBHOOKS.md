# Webhook Integration Guide — Dashboard

## Inbound Endpoints

| Endpoint                            | Source   | Description                  |
| ----------------------------------- | -------- | ---------------------------- |
| `POST /api/webhooks/stripe`         | Stripe   | Payment events               |
| `POST /api/webhooks/custom/:source` | Any      | Generic HMAC-signed webhooks |
| `POST /api/webhooks/emit`           | Internal | Programmatic event emission  |
| `GET /api/webhooks/logs`            | Internal | Delivery audit log           |

## Registered Events

| Event                   | Source   | Description            |
| ----------------------- | -------- | ---------------------- |
| `user.registered`       | internal | New user registration  |
| `contact.submitted`     | internal | Contact form submitted |
| `payment.received`      | stripe   | Payment received       |
| `newsletter.subscribed` | internal | Newsletter signup      |

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
