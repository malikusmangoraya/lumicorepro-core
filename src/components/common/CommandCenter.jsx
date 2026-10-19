import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Terminal, Send, ArrowRight, Loader2, CircleDot, CheckCircle2 } from 'lucide-react';
import { Card, Textarea, Button } from '@/components/ui';
import { aiAgentAPI } from '@/services/api';
import { cn } from '@/utils';

const SUGGESTION_KEYS = ['store', 'landing', 'portfolio', 'dashboard'];
const SUGGESTION_PROMPTS = {
  store: 'Build a complete e-commerce store for a premium electronics brand with checkout',
  landing: 'Generate a conversion-focused landing page for a SaaS analytics product',
  portfolio: 'Create a portfolio website for a photographer with a gallery',
  dashboard: 'Build an admin dashboard with analytics, users and settings',
};

/**
 * CommandCenter — chat-style prompt console on the Home dashboard.
 * Enter sends, Shift+Enter adds a newline, Ctrl/Cmd+K focuses.
 * Submits the prompt into the AI agent chat with `?prompt=&go=1`.
 */
export default function CommandCenter() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [health, setHealth] = useState('unknown');
  const areaRef = useRef(null);
  const sendingRef = useRef(false);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const res = await aiAgentAPI.checkHealth();
        if (alive) setHealth(res?.status === 200 ? 'online' : 'offline');
      } catch {
        if (alive) setHealth('offline');
      }
    };
    check();
    const timer = setInterval(check, 30000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const submit = useCallback(
    (value) => {
      const prompt = (value ?? text).trim();
      if (!prompt || sendingRef.current) return;
      sendingRef.current = true;
      setSending(true);
      navigate(
        `/chat?prompt=${encodeURIComponent(prompt)}&go=1`,
        { replace: false }
      );
    },
    [navigate, text]
  );

  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        areaRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <Card className="relative overflow-hidden border border-border bg-card/80 backdrop-blur-sm p-4 text-start sm:p-5">
      <div className="flex items-center justify-between gap-3">
        <div
          className="flex items-center gap-2 font-medium text-sm"
          aria-label={t('home.command.title')}
        >
          <Terminal className="h-4 w-4 text-primary" aria-hidden="true" />
          {t('home.command.title')}
        </div>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-all duration-200',
            health === 'online'
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
              : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
          )}
        >
          {health === 'online' ? (
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <CircleDot className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {t(`home.command.${health === 'online' ? 'online' : 'offline'}`)}
        </span>
      </div>

      <div className="mt-3 flex items-start gap-2 rounded-2xl border border-border bg-background/60 p-2 transition-all duration-200 focus-within:ring-2 focus-within:ring-primary/50 sm:p-3">
        <span
          className="mt-2.5 select-none pl-1 font-mono text-sm text-primary"
          aria-hidden="true"
        >
          &gt;
        </span>
        <Textarea
          ref={areaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          aria-label={t('home.command.placeholder')}
          placeholder={t('home.command.placeholder')}
          className="min-h-[2.75rem] resize-none border-0 bg-transparent px-1 py-2 focus-visible:ring-0 dark:bg-transparent"
          maxLength={2000}
        />
        <Button
          variant="primary"
          size="md"
          onClick={() => submit()}
          disabled={!text.trim() || sending}
          aria-label={t('home.command.send')}
          className="mt-0.5 shrink-0"
        >
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="h-4 w-4" aria-hidden="true" />
          )}
          <span className="hidden sm:inline">{t('home.command.send')}</span>
        </Button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {SUGGESTION_KEYS.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setText(SUGGESTION_PROMPTS[key])}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-3 py-1.5 text-xs text-muted-foreground transition-all duration-200 hover:border-primary/40 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          >
            {t(`home.command.suggest.${key}`)}
          </button>
        ))}
        <span className="ml-auto hidden items-center gap-1 text-xs text-muted-foreground sm:flex">
          {t('home.command.enterHint')}
          <ArrowRight className="h-3 w-3" aria-hidden="true" />
        </span>
      </div>
    </Card>
  );
}
