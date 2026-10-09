/**
 * Client-only cloud-edge form actions (static showcase mode).
 * Provider resolution: Formspree endpoint -> generic webhook -> dev mock.
 * Configure via VITE_FORMSPREE_ENDPOINT, VITE_FORMSPREE_NEWSLETTER_ID,
 * VITE_CONTACT_WEBHOOK_URL (e.g. a Vercel/Netlify edge function fanning out
 * to Resend). No backend server is required for any provider.
 */
const FORMSPREE_ENDPOINT = import.meta.env.VITE_FORMSPREE_ENDPOINT || '';
const NEWSLETTER_ENDPOINT = import.meta.env.VITE_FORMSPREE_NEWSLETTER_ID
  ? `https://formspree.io/f/${import.meta.env.VITE_FORMSPREE_NEWSLETTER_ID}`
  : '';
const WEBHOOK_URL = import.meta.env.VITE_CONTACT_WEBHOOK_URL || '';

export const getFormProvider = () => {
  if (FORMSPREE_ENDPOINT) return 'formspree';
  if (WEBHOOK_URL) return 'webhook';
  return 'mock';
};

const postJSON = async (url, payload) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Endpoint responded with status ${res.status}`);
  return res.json();
};

const mockDelivery = async () => {
  await new Promise((resolve) => setTimeout(resolve, 450));
  return { ok: true, mock: true };
};

/** Submit a contact / lead through the resolved cloud-edge provider. */
export const submitContact = async (data) => {
  const provider = getFormProvider();
  const payload = {
    _subject: data.subject || 'New website lead',
    name: data.name,
    email: data.email,
    message: data.message,
    ...(data.budget ? { budget: data.budget } : {}),
  };
  if (provider === 'formspree') {
    await postJSON(FORMSPREE_ENDPOINT, payload);
    return { ok: true, provider };
  }
  if (provider === 'webhook') {
    await postJSON(WEBHOOK_URL, { ...payload, type: 'contact' });
    return { ok: true, provider };
  }
  return mockDelivery();
};

/** Subscribe an email to the newsletter through the cloud-edge provider. */
export const subscribeNewsletter = async (email) => {
  const provider = getFormProvider();
  if (provider === 'formspree' && NEWSLETTER_ENDPOINT) {
    await postJSON(NEWSLETTER_ENDPOINT, { email });
    return { ok: true, provider };
  }
  if (provider === 'webhook') {
    await postJSON(WEBHOOK_URL, { email, type: 'newsletter' });
    return { ok: true, provider };
  }
  return mockDelivery();
};
