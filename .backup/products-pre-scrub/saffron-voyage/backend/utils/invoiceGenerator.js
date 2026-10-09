/**
 * Generate Printable HTML Invoice for Customer Orders
 * @param {Object} order - Populated order object
 * @returns {string} Clean, responsive HTML invoice
 */

const CURRENCY_SYMBOLS = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  PKR: 'Rs',
  INR: '₹',
  AED: 'د.إ',
  SAR: '﷼',
  JPY: '¥',
  CNY: '¥',
  BRL: 'R$',
  MXN: '$',
  CAD: '$',
  AUD: '$',
  SGD: '$',
  HKD: '$',
  KWD: 'د.ك',
  QAR: 'ر.ق',
  UAH: '₴',
  BDT: '৳',
};

const currencySymbol = (code) => CURRENCY_SYMBOLS[(code || 'USD').toUpperCase()] || '$';

export const generateInvoiceHTML = (order) => {
  const sym = currencySymbol(order.currency);
  const itemsRows = order.items
    .map(
      (item) => `
      <tr>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px;">
          <strong>${item.title}</strong>
          ${item.selectedColor ? `<br><small style="color: #6b7280;">Color: ${item.selectedColor}</small>` : ''}
          ${item.selectedSize ? `<br><small style="color: #6b7280;">Size: ${item.selectedSize}</small>` : ''}
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; text-align: center;">
          ${item.quantity}
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; text-align: right;">
          ${sym}${item.price.toFixed(2)}
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; text-align: right; font-weight: 600;">
          ${sym}${(item.price * item.quantity).toFixed(2)}
        </td>
      </tr>
    `
    )
    .join('');

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Invoice #${order.orderNumber}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1f2937; margin: 0; padding: 40px; background-color: #f9fafb; }
    .invoice-card { max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
    .brand { font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }
    .brand span { color: #3b82f6; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; background-color: ${order.isPaid ? '#dcfce7' : '#fef3c7'}; color: ${order.isPaid ? '#15803d' : '#b45309'}; }
    .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; font-size: 14px; }
    .table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
    .table th { background-color: #f8fafc; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #64748b; border-bottom: 2px solid #e2e8f0; }
    .totals { margin-left: auto; width: 300px; font-size: 14px; }
    .totals div { display: flex; justify-content: space-between; padding: 6px 0; }
    .totals .grand-total { font-size: 18px; font-weight: 700; color: #0f172a; border-top: 2px solid #0f172a; margin-top: 8px; padding-top: 8px; }
    .footer { margin-top: 40px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 20px; }
    @media print { body { background: #fff; padding: 0; } .invoice-card { box-shadow: none; border: none; padding: 0; } }
  </style>
</head>
<body>
  <div class="invoice-card">
    <div class="header">
      <div>
        <div class="brand">Lumi<span>Core</span>Pro</div>
        <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Official Tax Invoice & Receipt</p>
      </div>
      <div style="text-align: right;">
        <span class="badge">${order.isPaid ? 'PAID' : 'PENDING'}</span>
        <h2 style="margin: 8px 0 0 0; font-size: 20px; color: #0f172a;">#${order.orderNumber}</h2>
        <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Date: ${new Date(order.createdAt).toLocaleDateString()}</p>
      </div>
    </div>

    <div class="details-grid">
      <div>
        <h4 style="margin: 0 0 8px 0; color: #475569; font-size: 12px; text-transform: uppercase;">Billed To</h4>
        <strong>${order.shippingAddress?.fullName || 'Valued Customer'}</strong><br>
        ${order.shippingAddress?.street || ''}<br>
        ${order.shippingAddress?.city || ''}, ${order.shippingAddress?.state || ''} ${order.shippingAddress?.zipCode || ''}<br>
        ${order.shippingAddress?.country || ''}
      </div>
      <div>
        <h4 style="margin: 0 0 8px 0; color: #475569; font-size: 12px; text-transform: uppercase;">Payment Details</h4>
        <strong>Method:</strong> ${order.paymentMethod.toUpperCase()}<br>
        <strong>Status:</strong> ${order.status.toUpperCase()}<br>
        ${order.trackingNumber ? `<strong>Tracking:</strong> ${order.trackingNumber}<br>` : ''}
      </div>
    </div>

    <table class="table">
      <thead>
        <tr>
          <th>Description</th>
          <th style="text-align: center;">Qty</th>
          <th style="text-align: right;">Unit Price</th>
          <th style="text-align: right;">Amount</th>
        </tr>
      </thead>
      <tbody>
        ${itemsRows}
      </tbody>
    </table>

    <div class="totals">
      <div><span>Subtotal:</span><span>${sym}${order.itemsPrice.toFixed(2)}</span></div>
      <div><span>Tax (8%):</span><span>${sym}${order.taxPrice.toFixed(2)}</span></div>
      <div><span>Shipping:</span><span>${order.shippingPrice === 0 ? 'Free' : `${sym}${order.shippingPrice.toFixed(2)}`}</span></div>
      <div class="grand-total"><span>Total:</span><span>${sym}${order.totalPrice.toFixed(2)} ${order.currency || 'USD'}</span></div>
    </div>

    <div class="footer">
      <p>Thank you for your business. For inquiries, contact support@example.com.</p>
    </div>
  </div>
</body>
</html>
  `;
};
