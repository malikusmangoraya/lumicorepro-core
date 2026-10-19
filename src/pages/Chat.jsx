import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Send,
  ImageUp,
  X,
  Bot,
  User,
  Loader2,
  Eye,
  Palette,
  Sparkles,
  Trash2,
  File,
  FileText,
  FileSpreadsheet,
  FileArchive,
  FileCode,
  FilePlus2,
  Hammer,
  Copy,
  Check,
  ExternalLink,
} from 'lucide-react';
import { Badge, Button, Card, IconButton, Textarea } from '@/components/ui';
import { aiAgentAPI } from '@/services/api';
import PageSEO from '@/components/common/PageSEO';
import { cn } from '@/utils';

const SUGGESTIONS = [
  'Generate a landing page for a coffee shop',
  'Build an e-commerce store for electronics',
  'Create a portfolio for a photographer',
  'Make a SaaS pricing page',
];

const VISION_BADGE_COLORS = {
  header: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  hero: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  features: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  test: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  footer: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
};

const MAX_ATTACHMENTS = 10;
const MAX_IMAGE_SEND_DIM = 1100;
const MAX_IMAGE_QUALITY = 0.78;
const MAX_TOTAL_DATA_LENGTH = 8 * 1024 * 1024;
const MAX_FILE_SIZE = 8 * 1024 * 1024;

function attachmentIcon(name) {
  const ext = (name.split('.').pop() || '').toLowerCase();
  if (['pdf'].includes(ext)) return FileText;
  if (['doc', 'docx', 'odt', 'rtf'].includes(ext)) return FileText;
  if (['xls', 'xlsx', 'csv', 'tsv'].includes(ext)) return FileSpreadsheet;
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return FileArchive;
  if (['js', 'jsx', 'ts', 'tsx', 'py', 'html', 'htm', 'css', 'json', 'sql', 'yml', 'yaml', 'sh'].includes(ext))
    return FileCode;
  return File;
}

function formatBytes(bytes) {
  if (bytes > 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes > 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

function downscaleImage(file, maxDim = MAX_IMAGE_SEND_DIM, quality = MAX_IMAGE_QUALITY) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
      const w = Math.max(1, Math.round(img.width * scale));
      const h = Math.max(1, Math.round(img.height * scale));
      const sendCanvas = document.createElement('canvas');
      sendCanvas.width = w;
      sendCanvas.height = h;
      sendCanvas.getContext('2d').drawImage(img, 0, 0, w, h);

      const tw = Math.min(170, w);
      const th = Math.max(1, Math.round((h / w) * tw));
      const thumbCanvas = document.createElement('canvas');
      thumbCanvas.width = tw;
      thumbCanvas.height = th;
      thumbCanvas.getContext('2d').drawImage(img, 0, 0, tw, th);

      URL.revokeObjectURL(url);
      resolve({
        send: sendCanvas.toDataURL('image/webp', quality),
        thumb: thumbCanvas.toDataURL('image/webp', 0.65),
      });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}

function readFileAsDataUrl(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(file);
  });
}

export default function Chat() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [sending, setSending] = useState(false);
  const [visionInfo, setVisionInfo] = useState(null);
  const [provider, setProvider] = useState('grok');
  const [sentSnapshot, setSentSnapshot] = useState(null);
  const [buildInfo, setBuildInfo] = useState(null);
  const [copied, setCopied] = useState(false);
  const endRef = useRef(null);
  const fileRef = useRef(null);
  const autoSentRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  useEffect(() => {
    const run = searchParams.get('run');
    if (run) setBuildInfo((prev) => ({ ...(prev || {}), runId: run, status: 'queued' }));
  }, [searchParams]);

  const totalDataLength = attachments.reduce((sum, a) => sum + a.data.length, 0);

  const addFiles = useCallback(async (fileList) => {
    const incoming = Array.from(fileList || []);
    if (incoming.length === 0) return;

    const newOnes = [];
    for (const file of incoming) {
      if (newOnes.length + attachments.length >= MAX_ATTACHMENTS) break;
      if (file.size > MAX_FILE_SIZE) continue;
      try {
        if (file.type.startsWith('image/')) {
          const resized = await downscaleImage(file);
          if (!resized) continue;
          if (totalDataLength + resized.send.length > MAX_TOTAL_DATA_LENGTH) continue;
          newOnes.push({
            id: `${Date.now()}-${file.name}-${Math.random().toString(36).slice(2, 7)}`,
            name: file.name,
            mime: 'image/webp',
            size: file.size,
            isImage: true,
            data: resized.send,
            preview: resized.thumb,
          });
        } else {
          const data = await readFileAsDataUrl(file);
          if (!data) continue;
          if (totalDataLength + data.length > MAX_TOTAL_DATA_LENGTH) continue;
          newOnes.push({
            id: `${Date.now()}-${file.name}-${Math.random().toString(36).slice(2, 7)}`,
            name: file.name,
            mime: file.type || '',
            size: file.size,
            isImage: false,
            data,
            preview: null,
          });
        }
      } catch {
        // skip unreadable file
      }
    }
    if (newOnes.length > 0) {
      setAttachments((a) => [...a, ...newOnes]);
      setVisionInfo(null);
    }
  }, [attachments.length, totalDataLength]);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      addFiles(e.dataTransfer.files);
    },
    [addFiles]
  );

  const removeAttachment = (id) => {
    setAttachments((a) => a.filter((x) => x.id !== id));
    setVisionInfo(null);
  };

  const clearAttachments = () => {
    setAttachments([]);
    setVisionInfo(null);
  };

  const send = useCallback(async (overrideText) => {
    const message = (overrideText ?? text).trim();
    if ((!message && attachments.length === 0) || sending) return;

    const payloadFiles = attachments.map((a) => ({
      filename: a.name,
      type: a.mime,
      data: a.data,
    }));

    const userMsg = {
      id: Date.now(),
      role: 'user',
      text: message,
      attachments,
    };
    setMessages((m) => [...m, userMsg]);
    setText('');
    setSending(true);
    setSentSnapshot({ files: payloadFiles, message });
    setBuildInfo(null);

    try {
      const firstImage = attachments.find((a) => a.isImage);
      if (firstImage) {
        try {
          const vr = await aiAgentAPI.analyzeVision({ image: firstImage.data });
          const analysis = vr?.data?.data || vr?.data;
          if (analysis?.parsed) {
            setVisionInfo({
              regions: analysis.vision_layout_regions || [],
              palette: analysis.palette || [],
              source: analysis.source === 'ai_vision' ? 'AI vision' : 'Local analysis',
            });
          }
        } catch {
          setVisionInfo(null);
        }
      }

      const payload = { message, provider };
      if (firstImage) payload.image = firstImage.data;
      if (payloadFiles.length > 0) payload.files = payloadFiles;

      const res = await aiAgentAPI.visionChat(payload);
      const reply = res?.data?.data?.reply || res?.data?.reply || res?.data?.message;

      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: 'ai',
          text: reply || 'No reply received from the agent. Is the backend running?',
        },
      ]);
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail || err?.response?.data?.error || err?.message || '';
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: 'ai',
          error: true,
          text:
            errMsg || 'AI agent unreachable. Start backend via `npm run dev:all` and retry.',
        },
      ]);
    } finally {
      setSending(false);
    }
  }, [text, attachments, sending, provider]);

  // Latest send() via ref, so the ?go=1 one-shot effect can pass the prompt.
  const sendRef = useRef(send);
  useEffect(() => {
    sendRef.current = send;
  }, [send]);

  useEffect(() => {
    const prompt = searchParams.get('prompt');
    if (!prompt) return;
    if (autoSentRef.current) return;
    autoSentRef.current = true;
    setText(prompt);
    // Deliberately not cleared in cleanup: StrictMode's dev double-run would
    // otherwise cancel the one-shot auto-send before it fires.
    if (searchParams.get('go') === '1') {
      setTimeout(() => sendRef.current(prompt), 250);
    }
  }, []);

  const buildFromFiles = useCallback(async () => {
    if (!sentSnapshot || !sentSnapshot.files.length || buildInfo?.loading) return;
    setBuildInfo({ loading: true });

    const prompt =
      sentSnapshot.message ||
      'Build a production-ready website that faithfully implements the layout, palette, and content from the attached screenshot(s) and documents.';
    const files = sentSnapshot.files;

    try {
      const res = await aiAgentAPI.generate({ prompt, provider, files });
      const d = res?.data || {};
      setBuildInfo({
        loading: false,
        runId: d.run_id,
        status: d.status,
        mode: d.mode,
        visionMode: Boolean(d.vision_mode),
        url: d.ws_url,
      });
    } catch (err) {
      const errMsg = err?.response?.data?.error || err?.message || '';
      setBuildInfo({ loading: false, error: errMsg || 'Generation could not start.' });
    }
  }, [sentSnapshot, provider, buildInfo?.loading]);

  const copyRunId = async () => {
    if (!buildInfo?.runId) return;
    try {
      await navigator.clipboard.writeText(buildInfo.runId);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard unavailable
    }
  };

  const canBuild =
    sentSnapshot && sentSnapshot.files.length > 0 && !sending;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <PageSEO
        title="Lumicore AI Chat — LumicorePro"
        description="Chat with the Lumicore AI agent. Send text, images and documents — it analyses, answers and builds your full website."
        noIndex
      />
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 text-primary">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-foreground">Lumicore AI Chat</h1>
          <p className="text-sm text-muted-foreground">
            Text + images + documents → agent analyses, answers &amp; builds your site
          </p>
        </div>
      </div>

      <Card
        className="flex flex-col overflow-hidden"
        padding="none"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <div className="flex min-h-[420px] flex-col gap-3 overflow-y-auto p-4">
          {messages.length === 0 && attachments.length === 0 && (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 py-8 text-center">
              <Bot className="h-10 w-10 text-muted-foreground/60" />
              <p className="max-w-sm text-sm text-muted-foreground">
                Describe the website you want, upload a screenshot to match, or attach PDFs /
                documents / spreadsheets — the agent extracts the content and can build the
                full site for you.
              </p>
              <div className="mt-2 flex max-w-md flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setText(s)}
                    className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-all duration-200 hover:border-primary/50 hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 self-start">
              {attachments.map((a) => (
                <div
                  key={a.id}
                  className="group relative flex max-w-[220px] items-center gap-2 rounded-xl border border-border bg-card p-1.5 pr-2"
                >
                  {a.isImage ? (
                    <img
                      src={a.preview || a.data}
                      alt={a.name}
                      width={48}
                      height={48}
                      className="h-12 w-12 shrink-0 rounded-lg object-cover"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                      {(() => {
                        const Icon = attachmentIcon(a.name);
                        return <Icon className="h-5 w-5" />;
                      })()}
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="max-w-[120px] truncate text-xs font-medium text-foreground">
                      {a.name}
                    </p>
                    <p className="text-[10px] text-muted-foreground">{formatBytes(a.size)}</p>
                  </div>
                  <IconButton
                    aria-label={`Remove ${a.name}`}
                    size="sm"
                    variant="ghost"
                    onClick={() => removeAttachment(a.id)}
                    className="absolute -right-2 -top-2 bg-background/90 opacity-0 shadow-sm transition-opacity group-hover:opacity-100"
                  >
                    <X className="h-3.5 w-3.5" />
                  </IconButton>
                </div>
              ))}
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                'flex items-end gap-2 animate-fade-in-up',
                m.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {m.role === 'ai' && (
                <div className="mb-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={cn(
                  'max-w-[80%] space-y-2 rounded-2xl px-4 py-2.5 text-sm',
                  m.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-br-md'
                    : ' rounded-bl-md',
                  m.error
                    ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                    : m.role === 'ai'
                      ? 'bg-muted text-foreground'
                      : ''
                )}
              >
                {m.role === 'user' && m.attachments?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {m.attachments.map((a) =>
                      a.isImage ? (
                        <img
                          key={a.id}
                          src={a.preview || a.data}
                          alt={a.name}
                          className="max-h-32 w-auto rounded-lg"
                          loading="lazy"
                          decoding="async"
                        />
                      ) : (
                        <span
                          key={a.id}
                          className="flex items-center gap-1 truncate rounded-full bg-primary-foreground/15 px-2 py-0.5 text-[10px] text-primary-foreground"
                        >
                          {(() => {
                            const Icon = attachmentIcon(a.name);
                            return <Icon className="h-3 w-3" />;
                          })()}
                          <span className="max-w-[140px] truncate">{a.name}</span>
                        </span>
                      )
                    )}
                  </div>
                )}
                <p className="whitespace-pre-wrap">{m.text}</p>
              </div>
              {m.role === 'user' && (
                <div className="mb-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex items-end gap-2">
              <div className="mb-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-2 rounded-2xl rounded-bl-md bg-muted px-4 py-2.5 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                {attachments.length > 0
                  ? 'Analysing images & documents…'
                  : 'Agent is processing…'}
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {visionInfo && (
          <div className="border-t border-border bg-muted/30 px-4 py-3">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5 font-medium text-foreground">
                <Eye className="h-3.5 w-3.5 text-violet-400" />
                Detected layout ({visionInfo.source})
              </span>
              {(visionInfo.regions || []).slice(0, 5).map((r) => (
                <span
                  key={r.id}
                  className={cn(
                    'rounded-full border px-2 py-0.5',
                    VISION_BADGE_COLORS[r.type] || 'bg-muted text-muted-foreground border-border'
                  )}
                >
                  {r.type}
                </span>
              ))}
            </div>
            {(visionInfo.palette || []).length > 0 && (
              <div className="mt-2 flex items-center gap-1.5">
                <Palette className="h-3.5 w-3.5 text-cyan-400" />
                {(visionInfo.palette || []).slice(0, 6).map((c) => (
                  <span
                    key={c}
                    className="h-4 w-4 rounded-full border border-border"
                    style={{ backgroundColor: c }}
                    title={c}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {canBuild && !buildInfo && (
          <div className="border-t border-border bg-primary/5 px-4 py-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="flex items-center gap-2 text-xs text-muted-foreground">
                <Hammer className="h-4 w-4 text-primary" />
                {sentSnapshot.files.some((f) => f.type.startsWith('image/'))
                  ? 'Files attached — build a full website from this layout + content?'
                  : 'Files attached — generate a full website from this content?'}
              </p>
              <Button size="sm" onClick={buildFromFiles}>
                <Sparkles className="h-4 w-4" />
                Build Full Website
              </Button>
            </div>
          </div>
        )}

        {buildInfo && (
          <div className="border-t border-border bg-muted/30 px-4 py-3">
            {buildInfo.loading ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting 15-phase generation pipeline…
              </div>
            ) : buildInfo.error ? (
              <p className="text-xs text-red-400">{buildInfo.error}</p>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Check className="h-4 w-4 text-emerald-400" />
                  <span>
                    Build started — run{' '}
                    <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                      {buildInfo.runId}
                    </code>
                  </span>
                  <IconButton
                    aria-label="Copy run id"
                    size="sm"
                    variant="ghost"
                    onClick={copyRunId}
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  </IconButton>
                  <Badge variant="outline">
                    {buildInfo.visionMode ? 'Vision mode' : buildInfo.mode || 'queued'}
                  </Badge>
                </div>
                <Button size="sm" variant="outline" onClick={() => navigate(`/generate?run=${buildInfo.runId}`)}>
                  <ExternalLink className="h-4 w-4" />
                  Track in Generator
                </Button>
              </div>
            )}
          </div>
        )}

        <div className="border-t border-border p-3">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <label className="text-xs text-muted-foreground" htmlFor="chat-provider">
              Engine
            </label>
            <select
              id="chat-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="rounded-lg border border-border bg-background px-2 py-1 text-xs text-foreground"
            >
              <option value="grok">Groq (fast reasoning)</option>
              <option value="gemini">Gemini</option>
              <option value="openrouter">OpenRouter</option>
              <option value="deepseek">DeepSeek</option>
            </select>
            {attachments.length > 0 && (
              <Button
                size="sm"
                variant="ghost"
                onClick={clearAttachments}
                className="text-muted-foreground"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear {attachments.length}
              </Button>
            )}
          </div>
          <div className="flex items-end gap-2">
            <Textarea
              rows={1}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Type a message… (Shift+Enter for new line)"
              className="flex-1 resize-none"
              aria-label="Chat message"
            />
            <IconButton
              aria-label="Upload files"
              variant="outline"
              onClick={() => fileRef.current?.click()}
              disabled={sending}
              title="Attach images, PDFs, documents, spreadsheets, code (max 10)"
            >
              <ImageUp className="h-4 w-4" />
            </IconButton>
            <Button onClick={send} disabled={sending || (text.trim().length === 0 && attachments.length === 0)}>
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              <span className="sr-only">Send</span>
            </Button>
            <input
              ref={fileRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = '';
              }}
            />
          </div>
          {attachments.length > 0 && (
            <p className="mt-2 flex items-center gap-1.5 text-[10px] text-muted-foreground">
              <FilePlus2 className="h-3 w-3" />
              Images are auto-optimised; images + documents stay under 8 MB total.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}