import express from 'express';

const router = express.Router();

router.get('/', (req, res) => {
  const sellerName = process.env.MARKETPLACE_SELLER_NAME || 'LumiCorePro Seller';

  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Refund Policy</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; background: #f8f9fa; line-height: 1.7; }
    .container { max-width: 720px; margin: 40px auto; padding: 0 24px; }
    h1 { font-size: 2rem; margin-bottom: 8px; }
    .meta { color: #6b7280; margin-bottom: 32px; font-size: 0.9rem; }
    h2 { font-size: 1.25rem; margin: 28px 0 12px; color: #1a1a2e; }
    p, li { font-size: 1rem; color: #374151; margin-bottom: 12px; }
    ul { padding-left: 20px; margin-bottom: 12px; }
    li { margin-bottom: 6px; }
    .highlight { background: #eef2ff; border-left: 4px solid #6366f1; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }
    .highlight strong { color: #4338ca; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Refund Policy</h1>
    <p class="meta">Effective Date: ${new Date().toISOString().split('T')[0]} | Seller: ${sellerName}</p>

    <div class="highlight">
      <strong>30-Day Refund Window:</strong> All refund requests must be submitted within 30 calendar days of the original purchase date.
    </div>

    <h2>1. Digital Goods Policy</h2>
    <p>All products sold through this marketplace are digital goods, including but not limited to software licenses, website templates, source code, digital downloads, and subscription access.</p>
    <p>Due to the nature of digital goods, refunds are subject to the following conditions:</p>
    <ul>
      <li>The product has not been substantially used, modified, or redistributed after delivery.</li>
      <li>Access credentials or license keys have not been shared with third parties.</li>
      <li>The refund request includes a valid reason (e.g., product not as described, technical defect, accidental purchase).</li>
      <li>Support has been contacted first and the issue could not be resolved.</li>
    </ul>

    <h2>2. Non-Refundable Items</h2>
    <p>The following are not eligible for refunds:</p>
    <ul>
      <li>Products delivered more than 30 days ago.</li>
      <li>Custom or bespoke work completed and delivered.</li>
      <li>Digital goods that have been substantially consumed or downloaded in full.</li>
      <li>Services already rendered (e.g., AI generation, consulting).</li>
    </ul>

    <h2>3. How to Request a Refund</h2>
    <p>To request a refund, contact us with your order ID and reason for the refund request. We will review your request within 5 business days.</p>

    <h2>4. Refund Processing</h2>
    <p>Approved refunds are processed to the original payment method within 7-10 business days. You will receive email confirmation once the refund is initiated.</p>

    <h2>5. Contact</h2>
    <p>For refund inquiries, please reach out through the platform support channel with your order details.</p>
  </div>
</body>
</html>`);
});

export default router;
