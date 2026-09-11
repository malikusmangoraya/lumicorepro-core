/**
 * Contact & lead submission service.
 * Provider resolution order: Formspree endpoint → generic webhook → dev mock.
 * Configure via VITE_FORMSPREE_ENDPOINT or VITE_CONTACT_WEBHOOK_URL.
 */
const FORMSPREE_ENDPOINT = import.meta.env.VITE_FORMSPREE_ENDPOINT || '';
const WEBHOOK_URL = import.meta.env.VITE_CONTACT_WEBHOOK_URL || '';
const CONTACT_RECIPIENT = import.meta.env.VITE_CONTACT_EMAIL || '';

/**
 * Resolve the active delivery provider for contact forms.
 * @returns {'formspree' | 'webhook' | 'mock'}
 */
export const getContactProvider = () => {
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
  if (!res.ok) {
    throw new Error(`Contact endpoint responded with status ${res.status}`);
  }
  return res.json();
};

export const contactAPI = {
  getProvider: getContactProvider,

  /**
   * Submit a contact / lead message to the configured provider.
   * @param {{name: string, email: string, subject?: string, message: string, budget?: string, consent?: boolean}} data
   * @returns {Promise<{ok: boolean, provider: string, mock?: boolean}>}
   */
  async postLead(data) {
    const provider = getContactProvider();
    const payload = {
      _subject: data.subject || 'New website lead',
      name: data.name,
      email: data.email,
      message: data.message,
      ...(data.budget && { budget: data.budget }),
      ...(CONTACT_RECIPIENT && { _replyto: CONTACT_RECIPIENT }),
    };

    if (provider === 'formspree') {
      await postJSON(FORMSPREE_ENDPOINT, payload);
      return { ok: true, provider };
    }

    if (provider === 'webhook') {
      await postJSON(WEBHOOK_URL, payload);
      return { ok: true, provider };
    }

    // Mock delivery — no provider configured yet (dev/demo friendly).
    await new Promise((resolve) => setTimeout(resolve, 600));
    return { ok: true, provider, mock: true };
  },
};

export default contactAPI;
