import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User, Copy, ThumbsUp, ThumbsDown, RefreshCw, Mic, Settings, Plus, X, ChevronDown } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Badge, GlassButton, ScrollReveal, StaggerContainer, Avatar } from '@/components/ui';
import { messages as seed, models } from './data/mockData';
import { cn } from '@/utils';

export default function ChatInterface() {
  const [messages, setMessages] = useState(seed);
  const [text, setText] = useState('');
  const [typing, setTyping] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [showModelSelector, setShowModelSelector] = useState(false);
  const endRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const send = () => {
    if (!text.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', text, timestamp: new Date() };
    setMessages((m) => [...m, userMsg]);
    setText('');
    setTyping(true);
    setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: 'ai',
          text: 'Got it. Here is a clear, concise answer based on your prompt. I can help you with coding, writing, analysis, and much more.',
          timestamp: new Date(),
        },
      ]);
      setTyping(false);
    }, 900);
  };

  const handleCopy = (msgText) => {
    navigator.clipboard.writeText(msgText);
  };

  const handleRegenerate = (msgId) => {
    setMessages((m) => m.filter((msg) => msg.id !== msgId));
    setTyping(true);
    setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          id: Date.now(),
          role: 'ai',
          text: 'Here is a regenerated response with a different approach.',
          timestamp: new Date(),
        },
      ]);
      setTyping(false);
    }, 900);
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <TemplateShell
      title="AI Chat Interface"
      description="Modern AI chat with model selection, code blocks, and rich interactions."
      category="AI"
      actions={
        <div className="flex items-center gap-2">
          <GlassButton variant="outline" size="sm" leftIcon={Plus} onClick={() => setMessages(seed)}>
            New Chat
          </GlassButton>
          <div className="relative">
            <GlassButton
              variant="outline"
              size="sm"
              leftIcon={<Sparkles className="h-4 w-4" />}
              rightIcon={ChevronDown}
              onClick={() => setShowModelSelector(!showModelSelector)}
            >
              {selectedModel}
            </GlassButton>
            {showModelSelector && (
              <div className="absolute right-0 top-full mt-1 z-10 rounded-lg border border-border bg-card shadow-lg min-w-[180px] overflow-hidden">
                {models.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => {
                      setSelectedModel(model.id);
                      setShowModelSelector(false);
                    }}
                    className={cn(
                      'w-full px-3 py-2 text-left text-sm transition-colors',
                      selectedModel === model.id
                        ? 'bg-primary/10 text-primary'
                        : 'hover:bg-muted text-foreground'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      <Badge size="xs" variant={model.tier === 'premium' ? 'info' : 'secondary'}>
                        {model.tier}
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      }
    >
      <div className="flex flex-col h-[600px] lg:h-[700px]">
        <Card className="flex-1 flex flex-col overflow-hidden" padding="none">
          {/* Chat Header */}
          <div className="border-b border-border px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar
                src="https://images.unsplash.com/photo-1677442136019-21780ecad995?w=100&h=100&fit=crop"
                alt="AI Assistant"
                size="lg"
                fallback="AI"
              />
              <div>
                <p className="font-semibold">Lumicore AI</p>
                <p className="text-xs text-muted-foreground">Powered by {selectedModel}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="sm" icon={Settings} aria-label="Settings" />
              <Button variant="ghost" size="sm" icon={Mic} aria-label="Voice input" />
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <StaggerContainer stagger={0.05}>
              {messages.map((m, i) => (
                <ScrollReveal key={m.id} animate="fade-up" delay={i * 0.05}>
                  <div className={cn('flex gap-3 animate-fade-in-up', m.role === 'user' ? 'justify-end' : 'justify-start')}>
                    {m.role === 'ai' && (
                      <Avatar
                        src="https://images.unsplash.com/photo-1677442136019-21780ecad995?w=100&h=100&fit=crop"
                        alt="AI"
                        size="sm"
                        fallback="AI"
                        className="mt-1 shrink-0"
                      />
                    )}
                    <div className={cn('max-w-[80%] flex flex-col', m.role === 'user' ? 'items-end' : 'items-start')}>
                      <div
                        className={cn(
                          'rounded-2xl px-4 py-3 text-sm relative group',
                          m.role === 'user'
                            ? 'bg-primary text-primary-foreground rounded-br-md'
                            : 'bg-muted text-foreground rounded-bl-md'
                        )}
                      >
                        {m.text}
                        <div className="absolute bottom-1 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button variant="ghost" size="xs" icon={Copy} onClick={() => handleCopy(m.text)} aria-label="Copy" />
                          {m.role === 'ai' && (
                            <>
                              <Button variant="ghost" size="xs" icon={ThumbsUp} aria-label="Like" />
                              <Button variant="ghost" size="xs" icon={ThumbsDown} aria-label="Dislike" />
                              <Button variant="ghost" size="xs" icon={RefreshCw} onClick={() => handleRegenerate(m.id)} aria-label="Regenerate" />
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{formatTime(m.timestamp)}</span>
                        {m.role === 'ai' && <Badge size="xs" variant="outline">AI</Badge>}
                      </div>
                    </div>
                    {m.role === 'user' && (
                      <Avatar
                        src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop"
                        alt="User"
                        size="sm"
                        fallback="U"
                        className="mt-1 shrink-0"
                      />
                    )}
                  </div>
                </ScrollReveal>
              ))}
            </StaggerContainer>

            {typing && (
              <div className="flex gap-3 animate-fade-in-up">
                <Avatar
                  src="https://images.unsplash.com/photo-1677442136019-21780ecad995?w=100&h=100&fit=crop"
                  alt="AI"
                  size="sm"
                  fallback="AI"
                  className="mt-1 shrink-0"
                />
                <div className="max-w-[80%]">
                  <div className="bg-muted text-foreground rounded-2xl px-4 py-3 text-sm rounded-bl-md">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="h-2 w-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="h-2 w-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="h-2 w-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-muted-foreground">Lumicore is thinking…</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-border p-4">
            <div className="flex items-end gap-2">
              <Button variant="ghost" size="sm" icon={Plus} aria-label="Attach file" className="shrink-0" />
              <div className="flex-1 relative">
                <Input
                  placeholder="Message Lumicore AI…"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), send())}
                  className="pr-12"
                  inputClassName="resize-none min-h-[44px] max-h-[150px]"
                />
                {text && (
                  <button
                    onClick={() => setText('')}
                    className="absolute right-3 bottom-3 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label="Clear input"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <Button
                onClick={send}
                disabled={!text.trim() || typing}
                aria-label="Send message"
                leftIcon={Send}
                className="shrink-0"
              >
                Send
              </Button>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              Press Enter to send, Shift+Enter for new line. Powered by {selectedModel}.
            </p>
          </div>
        </Card>
      </div>
    </TemplateShell>
  );
}