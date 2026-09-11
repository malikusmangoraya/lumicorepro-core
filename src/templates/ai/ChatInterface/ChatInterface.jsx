import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input } from '@/components/ui';
import { messages as seed } from './data/mockData';

export default function ChatInterface() {
  const [messages, setMessages] = useState(seed);
  const [text, setText] = useState('');
  const [typing, setTyping] = useState(false);
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const send = () => {
    if (!text.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setText('');
    setTyping(true);
    setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: 'ai',
          text: 'Got it. Here is a clear, concise answer based on your prompt.',
        },
      ]);
      setTyping(false);
    }, 900);
  };

  return (
    <TemplateShell
      title="AI Chat"
      description="Clean conversation UI with typing state."
      category="AI"
    >
      <Card className="flex flex-col h-[560px]" padding="none">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {typing && (
            <div className="text-sm text-muted-foreground animate-pulse">Lumicore is typing…</div>
          )}
          <div ref={endRef} />
        </div>
        <div className="border-t border-border p-3 flex gap-2">
          <Input
            placeholder="Ask anything…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <Button onClick={send} aria-label="Send" leftIcon={Send}>
            Send
          </Button>
        </div>
      </Card>
    </TemplateShell>
  );
}
