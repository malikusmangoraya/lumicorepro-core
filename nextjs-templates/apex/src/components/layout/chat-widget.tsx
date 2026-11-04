'use client';

import { useEffect } from 'react';

const SRC = process.env.NEXT_PUBLIC_CHAT_SCRIPT_URL ?? '';

/**
 * Live chat slot.
 *
 * Chat is a third-party widget (Crisp, Intercom, Tawk…). Set
 * NEXT_PUBLIC_CHAT_SCRIPT_URL to the provider's embed URL and it loads; with no
 * value the component renders nothing at all, so a template without a chat
 * account does not show an empty button that goes nowhere.
 */
export function ChatWidget() {
  useEffect(() => {
    if (!SRC) return;
    if (document.getElementById('chat-widget')) return;

    const script = document.createElement('script');
    script.id = 'chat-widget';
    script.async = true;
    script.src = SRC;
    document.body.appendChild(script);
  }, []);

  return null;
}
