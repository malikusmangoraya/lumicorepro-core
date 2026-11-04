/**
 * Email delivery.
 *
 * The template does not ship a provider. Every call site already fires the
 * right message; drop a key in and it starts sending. Until then the call is a
 * no-op that logs the subject, so nothing breaks and nothing silently claims a
 * customer was emailed.
 *
 * Wiring a provider:
 *   1. Create an account (Resend, Postmark, SES, Mailgun…).
 *   2. Set RESEND_API_KEY and EMAIL_FROM in .env.
 *   3. If the provider is not Resend, replace the fetch below — the function
 *      signature is the only contract callers depend on.
 */

export type EmailMessage = {
  to: string;
  subject: string;
  text: string;
};

export function emailConfigured(): boolean {
  return Boolean(process.env.RESEND_API_KEY && process.env.EMAIL_FROM);
}

export async function sendEmail(
  message: EmailMessage,
): Promise<{ ok: true } | { ok: false; reason: string }> {
  if (!emailConfigured()) {
    // Deliberately a no-op: a template without credentials must not pretend it
    // sent an email, and must not fail a checkout because it could not.
    console.info(`[email] not configured — skipped "${message.subject}" to ${message.to}`);
    return { ok: false, reason: 'not-configured' };
  }

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: process.env.EMAIL_FROM,
        to: message.to,
        subject: message.subject,
        text: message.text,
      }),
    });

    if (!response.ok) return { ok: false, reason: `provider ${response.status}` };
    return { ok: true };
  } catch {
    return { ok: false, reason: 'network' };
  }
}

export function orderConfirmationEmail(input: {
  to: string;
  orderNumber: string;
  total: number;
  currency: string;
}): EmailMessage {
  return {
    to: input.to,
    subject: `Order ${input.orderNumber} received`,
    text: [
      `Thank you — we have your order ${input.orderNumber}.`,
      '',
      `Total: ${input.currency} ${input.total.toFixed(2)}`,
      '',
      'No payment has been taken yet. A specialist will confirm stock, shipping and payment.',
      '',
      'Apex Motor Collective',
    ].join('\n'),
  };
}

export function leadNotificationEmail(input: {
  to: string;
  name: string;
  email: string;
  type: string;
  message: string;
}): EmailMessage {
  return {
    to: input.to,
    subject: `New ${input.type.replace('_', ' ')} lead: ${input.name}`,
    text: [
      `Type: ${input.type}`,
      `Name: ${input.name}`,
      `Email: ${input.email}`,
      '',
      input.message,
    ].join('\n'),
  };
}
