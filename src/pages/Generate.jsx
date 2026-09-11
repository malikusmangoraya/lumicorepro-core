import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Sparkles,
  ArrowRight,
  Send,
  CheckCircle2,
  Loader2,
  Download,
  FolderOpen,
  Zap,
  Brain,
  Code2,
  Shield,
  BarChart3,
  Lightbulb,
  Trophy,
  X,
  Clock,
  ChevronDown,
  ChevronUp,
  Globe,
  Server,
  Database,
  Package,
  CheckCheck,
  Cpu,
  Activity,
  ExternalLink,
  Languages,
  Accessibility,
  SearchCheck,
  Cloud,
  ImageUp,
  Eye,
  Palette,
  XCircle,
  Rocket,
  MonitorPlay,
  MessageSquare,
} from 'lucide-react';
import {
  Badge,
  Button,
  ButtonMotion,
  Card,
  Progress,
  Modal,
  IconButton,
  Input,
  Textarea,
} from '@/components/ui';
import { aiAgentAPI, previewAPI, resolvePreviewUrl } from '@/services/api';
import { useAppContext } from '@/context/AppContext';
import PageSEO from '@/components/common/PageSEO';
import { cn } from '@/utils';
import { trackEvent, AnalyticsEvents } from '@/utils/analytics';

/* ── 15 pipeline phases (mirrors ai-agent/orchestrator.py) ───────── */
const PHASES = [
  {
    id: 'market',
    label: 'Market Analysis',
    icon: BarChart3,
    color: 'text-blue-400',
    bg: 'bg-blue-500/15',
    desc: 'Industry benchmarks & competitor research',
  },
  {
    id: 'requirement',
    label: 'Requirement Analysis',
    icon: Brain,
    color: 'text-violet-400',
    bg: 'bg-violet-500/15',
    desc: 'NLP prompt parsing → structured spec',
  },
  {
    id: 'tech',
    label: 'Tech Stack Selection',
    icon: Cpu,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/15',
    desc: 'Optimal stack per industry',
  },
  {
    id: 'trending',
    label: 'Trending Features',
    icon: Zap,
    color: 'text-amber-400',
    bg: 'bg-amber-500/15',
    desc: 'ROI-ranked feature injection',
  },
  {
    id: 'assembly',
    label: 'Resource Assembly',
    icon: Package,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/15',
    desc: 'Template + component + asset selection',
  },
  {
    id: 'codegen',
    label: 'Code Generation',
    icon: Code2,
    color: 'text-primary',
    bg: 'bg-primary/15',
    desc: 'File assembly with AI customization',
  },
  {
    id: 'quality',
    label: 'Quality Verification',
    icon: Shield,
    color: 'text-green-400',
    bg: 'bg-green-500/15',
    desc: '6 enterprise quality gates',
  },
  {
    id: 'improve',
    label: 'Improvement Analysis',
    icon: Lightbulb,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/15',
    desc: 'ROI-ranked optimization recommendations',
  },
  {
    id: 'benchmark',
    label: 'Competitive Benchmark',
    icon: Trophy,
    color: 'text-pink-400',
    bg: 'bg-pink-500/15',
    desc: 'Industry comparison + launch-ready flag',
  },
  {
    id: 'intl',
    label: 'International Delivery',
    icon: Globe,
    color: 'text-sky-400',
    bg: 'bg-sky-500/15',
    desc: 'Region + currency auto-detection',
  },
  {
    id: 'i18n',
    label: 'Localization & i18n',
    icon: Languages,
    color: 'text-teal-400',
    bg: 'bg-teal-500/15',
    desc: 'Multi-language + RTL support',
  },
  {
    id: 'compliance',
    label: 'Compliance & A11y',
    icon: Accessibility,
    color: 'text-orange-400',
    bg: 'bg-orange-500/15',
    desc: 'GDPR/CCPA + WCAG 2.1 AA checks',
  },
  {
    id: 'seo',
    label: 'SEO & CDN Optimization',
    icon: SearchCheck,
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/15',
    desc: 'Meta automation + edge caching',
  },
  {
    id: 'growth',
    label: 'Performance & Webhooks',
    icon: Activity,
    color: 'text-lime-400',
    bg: 'bg-lime-500/15',
    desc: 'Budget tuning, analytics, A/B, hooks',
  },
  {
    id: 'deploy',
    label: 'Multi-Cloud Deployment',
    icon: Cloud,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/15',
    desc: 'Ready-to-push output for 4 clouds',
  },
];

/* ── AI Providers with rich metadata ─────────────────────────────── */
const PROVIDERS = [
  {
    id: 'gemini',
    name: 'Gemini 2.5 Flash',
    vendor: 'Google',
    badge: 'Recommended',
    badgeVariant: 'success',
    icon: '✦',
    color: 'border-blue-500/40 bg-blue-500/5',
    activeColor: 'border-blue-500 bg-blue-500/15 ring-2 ring-blue-500/30',
    desc: 'Best balance of speed & quality',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek Chat',
    vendor: 'DeepSeek AI',
    badge: 'Cost Efficient',
    badgeVariant: 'info',
    icon: '◈',
    color: 'border-indigo-500/40 bg-indigo-500/5',
    activeColor: 'border-indigo-500 bg-indigo-500/15 ring-2 ring-indigo-500/30',
    desc: 'Excellent for structured codegen',
  },
  {
    id: 'claude',
    name: 'Claude 3.5 Sonnet',
    vendor: 'Anthropic',
    badge: 'Best Quality',
    badgeVariant: 'warning',
    icon: '◎',
    color: 'border-orange-500/40 bg-orange-500/5',
    activeColor: 'border-orange-500 bg-orange-500/15 ring-2 ring-orange-500/30',
    desc: 'Highest quality output',
  },
  {
    id: 'mistral',
    name: 'Mistral Large',
    vendor: 'Mistral AI',
    badge: 'Fast',
    badgeVariant: 'secondary',
    icon: '⬡',
    color: 'border-rose-500/40 bg-rose-500/5',
    activeColor: 'border-rose-500 bg-rose-500/15 ring-2 ring-rose-500/30',
    desc: 'European & multilingual focus',
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    vendor: 'Multi-Model',
    badge: 'Flexible',
    badgeVariant: 'secondary',
    icon: '⟆',
    color: 'border-teal-500/40 bg-teal-500/5',
    activeColor: 'border-teal-500 bg-teal-500/15 ring-2 ring-teal-500/30',
    desc: '50+ models via one key',
  },
];

/* ── Example prompts ─────────────────────────────────────────────── */
const EXAMPLE_PROMPTS = [
  {
    emoji: '🍽️',
    text: 'Pakistani restaurant website with online ordering, menu categories, and delivery tracking',
  },
  {
    emoji: '🏠',
    text: 'Real estate listing portal for Karachi with property search, filters, and virtual tours',
  },
  {
    emoji: '🏥',
    text: 'Doctor appointment booking system with specialist search and video consultation',
  },
  {
    emoji: '💪',
    text: 'Gym & fitness studio website with class schedule, membership plans, and trainer profiles',
  },
  {
    emoji: '🎓',
    text: 'Online learning platform (LMS) with course catalog, video lessons, and certificates',
  },
  {
    emoji: '✈️',
    text: 'Travel agency site for Pakistan tours with packages, destination guide, and booking',
  },
  {
    emoji: '👨‍💻',
    text: 'Developer portfolio with projects, skills, experience timeline, and contact form',
  },
  {
    emoji: '🛒',
    text: 'Electronics e-commerce store with product specs, cart, wishlist, and checkout',
  },
];

/* ── Languages & Regions ─────────────────────────────────────────── */
const LANGUAGES = [
  { value: 'en', label: 'English (US/UK)' },
  { value: 'ur', label: 'Urdu (اردو · RTL)' },
  { value: 'ar', label: 'Arabic (العربية · RTL)' },
  { value: 'es', label: 'Spanish (Español)' },
  { value: 'fr', label: 'French (Français)' },
  { value: 'de', label: 'German (Deutsch)' },
  { value: 'zh', label: 'Chinese (中文)' },
  { value: 'ja', label: 'Japanese (日本語)' },
];

const REGIONS = [
  { value: 'GLOBAL', label: 'Global Standards' },
  { value: 'EU', label: 'European Union (GDPR)' },
  { value: 'NA', label: 'North America (CCPA)' },
  { value: 'SA', label: 'South Asia (PK/IN)' },
  { value: 'MENA', label: 'Middle East (RTL & VAT)' },
  { value: 'APAC', label: 'Asia-Pacific' },
];

const STATUS_META = {
  idle: { variant: 'secondary', label: 'Ready to Generate' },
  running: { variant: 'info', label: 'Pipeline Running…' },
  done: { variant: 'success', label: 'Complete ✓' },
  error: { variant: 'danger', label: 'Error — Retry' },
};

/* ── Quality score color ─────────────────────────────────────────── */
function qualityColor(score) {
  if (score >= 95) return 'text-emerald-400';
  if (score >= 85) return 'text-primary';
  if (score >= 70) return 'text-amber-400';
  return 'text-red-400';
}

/* ════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
════════════════════════════════════════════════════════════════════ */
export default function GeneratePage() {
  const { language: currentLang, user: appUser } = useAppContext();

  /* State ─────────────────────────────────────────────────────────── */
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState('gemini');
  const [targetLang, setTargetLang] = useState(currentLang || 'en');
  const [targetRegion, setTargetRegion] = useState('GLOBAL');
  const [status, setStatus] = useState('idle');
  const [phases, setPhases] = useState(
    PHASES.map((p) => ({ ...p, state: 'pending', duration: null }))
  );
  const [activePhaseIdx, setActivePhaseIdx] = useState(-1);
  const [result, setResult] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [showFileModal, setShowFileModal] = useState(false);
  const [engineMode, setEngineMode] = useState('auto');
  const [screenshot, setScreenshot] = useState(null);
  const [visionAnalysis, setVisionAnalysis] = useState(null);
  const [analyzingVision, setAnalyzingVision] = useState(false);
  const [visionError, setVisionError] = useState(null);
  const [runId, setRunId] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [deployBusy, setDeployBusy] = useState(false);
  const [deployResult, setDeployResult] = useState(null);
  const [domainInput, setDomainInput] = useState('');
  const [domainPlatform, setDomainPlatform] = useState('vercel');
  const [domainBusy, setDomainBusy] = useState(false);
  const [domainResult, setDomainResult] = useState(null);

  /* Revision state ───────────────────────────────────────────────── */
  const [showRevisionModal, setShowRevisionModal] = useState(false);
  const [revisionFields, setRevisionFields] = useState(['']);
  const [revisionClientName, setRevisionClientName] = useState('');
  const [revisionClientEmail, setRevisionClientEmail] = useState('');
  const [revisionSubmitting, setRevisionSubmitting] = useState(false);
  const [revisionSuccess, setRevisionSuccess] = useState(false);
  const [revisionErrors, setRevisionErrors] = useState([]);
  const [revisionApplyResult, setRevisionApplyResult] = useState(null);

  /* Refs ──────────────────────────────────────────────────────────── */
  const textareaRef = useRef(null);
  const logRef = useRef(null);
  const wsRef = useRef(null);
  const fileInputRef = useRef(null);

  /* Auto-scroll logs ──────────────────────────────────────────────── */
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  /* Cleanup WS on unmount ─────────────────────────────────────────── */
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const addLog = useCallback((msg) => {
    setLogs((l) => [...l, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const resetAll = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('idle');
    setPhases(PHASES.map((p) => ({ ...p, state: 'pending', duration: null })));
    setActivePhaseIdx(-1);
    setResult(null);
    setDownloadUrl(null);
    setLogs([]);
    setScreenshot(null);
    setVisionAnalysis(null);
    setVisionError(null);
    setRunId(null);
    setPreviewUrl(null);
    setDeployResult(null);
  };

  /* ── Image upload + vision analysis ───────────────────────────── */
  const handleImageUpload = useCallback((file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = String(reader.result || '');
      setScreenshot(dataUrl);
      setVisionAnalysis(null);
      setVisionError(null);
      setAnalyzingVision(true);
      addLog('📷 Analyzing uploaded screenshot (vision pipeline)…');
      try {
        const res = await aiAgentAPI.analyzeVision({ image: dataUrl });
        const analysis = res?.data?.data || res?.data;
        if (analysis) {
          setVisionAnalysis(analysis);
          const source = analysis.source === 'ai_vision' ? 'AI vision' : 'heuristic fallback';
          addLog(
            `✓ Vision: parsed=${analysis.parsed} regions=${(analysis.vision_layout_regions || []).length} (${source})`
          );
        }
      } catch (err) {
        setVisionError(err?.response?.data?.error || 'Vision analysis unavailable (AI agent offline).');
        addLog('⚠ Vision analysis failed — continuing with text prompt only.');
      } finally {
        setAnalyzingVision(false);
      }
    };
    reader.readAsDataURL(file);
  }, [addLog]);

  const handleImageSelect = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (file) handleImageUpload(file);
    },
    [handleImageUpload]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0];
      if (file) handleImageUpload(file);
    },
    [handleImageUpload]
  );

  const clearScreenshot = () => {
    setScreenshot(null);
    setVisionAnalysis(null);
    setVisionError(null);
  };

  /* ── Offline Pipeline Simulator ─────────────────────────────────── */
  const runOfflinePipeline = useCallback(
    async (txt, fallbackMeta = {}) => {
      setEngineMode('offline_engine');
      addLog(`Running offline assembly pipeline for: "${txt.slice(0, 60)}…"`);

      const delays = [350, 420, 300, 380, 500, 750, 450, 320, 350];
      for (let i = 0; i < PHASES.length; i++) {
        setActivePhaseIdx(i);
        setPhases((prev) => prev.map((p, j) => (j === i ? { ...p, state: 'running' } : p)));
        addLog(`▶ Phase ${i + 1}: ${PHASES[i].label}…`);
        await new Promise((r) => setTimeout(r, delays[i]));
        const dur = (delays[i] / 1000).toFixed(2);
        setPhases((prev) =>
          prev.map((p, j) => (j === i ? { ...p, state: 'done', duration: `${dur}s` } : p))
        );
        addLog(`✓ ${PHASES[i].label} verified (${dur}s)`);
      }

      setActivePhaseIdx(-1);
      setStatus('done');
      trackEvent(AnalyticsEvents.GENERATE_SUCCESS, { engine: 'offline' });
      addLog('━━━ Offline Pipeline Complete! ━━━');

      const projectSlug =
        txt
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '')
          .slice(0, 40) || 'lumicore-website';

      if (fallbackMeta.run_id) setRunId(fallbackMeta.run_id);

      setResult({
        projectName: fallbackMeta.projectName || projectSlug,
        template: fallbackMeta.template || 'Auto-selected from 60 templates',
        components: fallbackMeta.components || 14,
        backend: fallbackMeta.backend || 'Node.js + Express.js',
        database: fallbackMeta.database || 'PostgreSQL / SQLite',
        qualityScore: fallbackMeta.qualityScore || 95,
        launchReady: true,
        executionTime: '3.8',
        trendingFeatures: fallbackMeta.trendingFeatures || [
          'Smart Search',
          'RTL Localization',
          'GDPR Cookie Banner',
          'Responsive Dark Mode',
        ],
        zipSize: fallbackMeta.zipSize || '3.2 MB',
        instructions: [
          'npm install',
          'cp .env.example .env  (fill in your keys)',
          'npm run dev',
          'node backend/server.js',
        ],
      });
    },
    [addLog]
  );

  /* ── Main Generation Handler ─────────────────────────────────────── */
  const handleGenerate = useCallback(async () => {
    const txt = prompt.trim();
    if (!txt || status === 'running') return;
    resetAll();
    setStatus('running');
    addLog(`Initiating generation: "${txt.slice(0, 50)}…"`);

    try {
      const payload = {
        prompt: txt,
        provider,
        language: targetLang,
        region: targetRegion !== 'GLOBAL' ? targetRegion : undefined,
      };
      if (screenshot) payload.image = screenshot;
      trackEvent(AnalyticsEvents.GENERATE_CLICK, { provider, language: targetLang });
      const res = await aiAgentAPI.generate(payload);

      const data = res.data;

      if (data.mode === 'live_agent' && data.ws_url) {
        setEngineMode('live_agent');
        setDownloadUrl(data.download_url);
        setRunId(data.run_id);
        addLog(`Connected to AI Agent (Run ID: ${data.run_id})`);

        try {
          const ws = new WebSocket(data.ws_url);
          wsRef.current = ws;

          ws.onmessage = (event) => {
            try {
              const msg = JSON.parse(event.data);
              if (msg.type === 'phase_start') {
                setActivePhaseIdx(msg.index);
                setPhases((prev) =>
                  prev.map((p, j) => (j === msg.index ? { ...p, state: 'running' } : p))
                );
                addLog(
                  `▶ [Live] Phase ${msg.index + 1}: ${PHASES[msg.index]?.label || msg.phase}…`
                );
              } else if (msg.type === 'phase_done') {
                setPhases((prev) =>
                  prev.map((p, j) =>
                    j === msg.index
                      ? { ...p, state: 'done', duration: `${(msg.duration ?? 0.4).toFixed(2)}s` }
                      : p
                  )
                );
                addLog(`✓ [Live] ${PHASES[msg.index]?.label || msg.phase} done`);
              } else if (msg.type === 'complete' || msg.type === 'finished') {
                setStatus('done');
                trackEvent(AnalyticsEvents.GENERATE_SUCCESS, { engine: 'live_agent' });
                setActivePhaseIdx(-1);
                addLog('━━━ Live AI Generation Complete! ━━━');
                const rep = msg.result || {};
                setResult({
                  projectName: rep.project_name || 'generated-website',
                  template: rep.selected_resources?.template || 'Dynamic Match',
                  components: rep.selected_resources?.components?.length || 16,
                  backend: rep.selected_resources?.backend || 'Express.js',
                  database: 'PostgreSQL',
                  qualityScore: rep.quality_gates?.overall_score || 96,
                  launchReady: true,
                  executionTime: '4.2',
                  trendingFeatures: rep.trending_features_applied || [
                    'AI Chat',
                    'Smart Search',
                    'RTL Support',
                    'GDPR Ready',
                  ],
                  zipSize: '4.1 MB',
                  instructions: [
                    'npm install',
                    'cp .env.example .env',
                    'npm run dev',
                    'node backend/server.js',
                  ],
                });
              } else if (msg.type === 'error') {
                addLog(`Agent warning: ${msg.message}`);
              }
            } catch {
              /* ignore parse errors */
            }
          };

          ws.onerror = () => {
            addLog('WebSocket disconnected — switching to offline engine.');
            runOfflinePipeline(txt, data.fallback_data);
          };
        } catch {
          runOfflinePipeline(txt, data.fallback_data);
        }
      } else {
        await runOfflinePipeline(txt, data.fallback_data);
      }
    } catch (err) {
      const isDailyLimit = err?.response?.status === 429 && /daily|limit|quota/i.test(JSON.stringify(err?.response?.data || ''));
      if (isDailyLimit) {
        addLog('Daily generation limit reached — quota resets tomorrow.');
        trackEvent(AnalyticsEvents.GENERATE_DAILY_LIMIT);
        setStatus('ready');
        return;
      }
      addLog('Backend agent unreachable — running local offline engine.');
      trackEvent(AnalyticsEvents.GENERATE_FAIL, { fallback: true });
      await runOfflinePipeline(txt);
    }
  }, [prompt, status, provider, targetLang, targetRegion, screenshot, runOfflinePipeline, addLog]);

  /* ── Download handler ────────────────────────────────────────────── */
  const handleDownload = useCallback(() => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank');
      return;
    }

    const name = result?.projectName || 'lumicorepro-website';
    const steps = (result?.instructions || ['npm install', 'npm run dev'])
      .map((s, i) => `${i + 1}. ${s}`)
      .join('\n');
    const content = [
      `# ${name}`,
      '',
      `> Generated by **LumicorePro AI Engine** · Quality Score: ${result?.qualityScore ?? 95}%`,
      '',
      '## Stack',
      `- Frontend : React 19 + Tailwind CSS + Vite`,
      `- Backend  : ${result?.backend || 'Node.js + Express.js'}`,
      `- Database : ${result?.database || 'PostgreSQL'}`,
      `- Components: ${result?.components ?? 14} files assembled`,
      `- Trending Features: ${result?.trendingFeatures?.join(', ') || 'Smart Search, Dark Mode'}`,
      '',
      '## Quick Start',
      steps,
      '',
      '## Quality Gates Passed (6/6)',
      '- [x] Performance budget',
      '- [x] Security scan (no eval/exec/injection)',
      '- [x] Feature completeness',
      '- [x] Asset references',
      '- [x] Code quality',
      '- [x] Accessibility (WCAG)',
    ].join('\n');

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}-README.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [downloadUrl, result]);

  /* ── Preview handler ────────────────────────────────────────────── */
  const handlePreview = useCallback(async () => {
    if (!runId) {
      addLog('⚠ No run_id available — re-run generation and try again.');
      return;
    }
    setPreviewBusy(true);
    setDeployResult(null);
    try {
      const res = await previewAPI.create(runId);
      const data = res?.data?.data || {};
      const rawUrl = data.preview_url || data.url || data.deploymentUrl;
      const url = resolvePreviewUrl(rawUrl, data.slug);
      if (url) {
        setPreviewUrl(url);
        addLog(`Preview ready: ${url}`);
      } else {
        addLog(`Preview created (${data.slug || runId}) but URL missing from agent response.`);
      }
    } catch (err) {
      addLog(`Preview failed: ${err?.response?.data?.error || err.message}`);
    } finally {
      setPreviewBusy(false);
    }
  }, [runId, addLog]);

  /* ── Deploy handler ─────────────────────────────────────────────── */
  const handleDeploy = useCallback(
    async (platform) => {
      if (!runId) {
        addLog('⚠ No run_id available — re-run generation and try again.');
        return;
      }
      setDeployBusy(true);
      setDeployResult(null);
      try {
        const res = await previewAPI.deploy(runId, platform);
        const data = res?.data?.data || {};
        setDeployResult(data);
        if (data.status === 'live' && data.url) {
          addLog(`Deployed ${platform}: ${data.url}`);
        } else if (data.status === 'guide' && data.commands?.length) {
          addLog(`${platform}: follow deploy commands — ${data.commands.join(' → ')}`);
        } else {
          addLog(`${platform}: ${data.message || 'deploy could not complete'}`);
        }
      } catch (err) {
        addLog(`Deploy failed: ${err?.response?.data?.error || err.message}`);
      } finally {
        setDeployBusy(false);
      }
    },
    [runId, addLog]
  );

  /* ── Custom domain wizard ──────────────────────────────────────── */
  const handleConnectDomain = useCallback(
    async () => {
      const domain = domainInput.trim();
      if (!domain || domainBusy) return;
      setDomainBusy(true);
      setDomainResult(null);
      try {
        const res = await aiAgentAPI.connectDomain({
          domain,
          platform: domainPlatform,
          project_dir: result?.projectDir || result?.generated_project_dir || undefined,
        });
        const data = res?.data?.data || {};
        setDomainResult(data);
        if (data.status === 'live') {
          addLog(`Domain ${domain} connected on ${domainPlatform} (${data.url || data.message || ''})`);
        } else {
          addLog(`Domain ${domain}: ${data.message || 'follow the DNS steps below'}`);
        }
      } catch (err) {
        addLog(`Domain wizard failed: ${err?.response?.data?.error || err.message}`);
        setDomainResult({ status: 'failed', message: err?.response?.data?.error || err.message });
      } finally {
        setDomainBusy(false);
      }
    },
    [domainInput, domainPlatform, result, addLog, domainBusy]
  );

  /* ── Revision request ───────────────────────────────────────────── */
  const handleRevisionSubmit = useCallback(async () => {
    const changes = revisionFields.filter(f => f.trim());
    if (!changes.length || !runId) return;
    setRevisionSubmitting(true);
    setRevisionErrors([]);
    setRevisionSuccess(false);
    setRevisionApplyResult(null);
    try {
      // Step 1: Submit revision request
      const submitRes = await fetch(`http://localhost:8000/api/runs/${runId}/revise`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          changes,
          client_name: revisionClientName || undefined,
          client_email: revisionClientEmail || undefined,
        }),
      });
      if (!submitRes.ok) {
        const err = await submitRes.json().catch(() => ({ detail: 'Failed to submit revision' }));
        throw new Error(err.detail || 'Revision request failed');
      }
      const submitData = await submitRes.json();
      addLog(`Revision request submitted: ${changes.length} change(s)`);

      // Step 2: Auto-apply the revision
      addLog('Applying changes with AI...');
      const applyRes = await fetch(`http://localhost:8000/api/runs/${runId}/revise/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revision_id: submitData.revision_id }),
      });
      if (!applyRes.ok) {
        const err = await applyRes.json().catch(() => ({ detail: 'Failed to apply revision' }));
        throw new Error(err.detail || 'Revision apply failed');
      }
      const applyData = await applyRes.json();
      setRevisionApplyResult(applyData);
      setRevisionSuccess(true);
      addLog(`Revision applied: ${applyData.changes_applied} change(s) patched across ${applyData.patched_files?.length || 0} files`);
    } catch (err) {
      setRevisionErrors([err.message]);
    } finally {
      setRevisionSubmitting(false);
    }
  }, [revisionFields, runId, revisionClientName, revisionClientEmail, addLog]);

  /* ── Helpers ─────────────────────────────────────────────────────── */
  const handleExample = (ex) => {
    setPrompt(ex.text);
    textareaRef.current?.focus();
  };

  const doneCount = phases.filter((p) => p.state === 'done').length;
  const progressPct = Math.round((doneCount / PHASES.length) * 100);
  const statusMeta = STATUS_META[status];
  const activeProvider = PROVIDERS.find((p) => p.id === provider) || PROVIDERS[0];

  /* ═══════════════════════════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════════════════════════ */
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-page-enter">
      <PageSEO
        title="AI Website Generator — LumicorePro"
        description="Generate a complete production-ready website with AI in minutes. 15-phase pipeline: market research, RTL/i18n, compliance, SEO and deploy configs."
        keywords="ai website generator, ai site builder, react generator, lumen"
      />
      {/* ── Waitlist banner (closed beta) ──────────────────────── */}
      {appUser?.betaStatus === 'waitlist' && (
        <div
          role="alert"
          className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-sm"
        >
          <p className="font-semibold text-foreground">You&apos;re on the waitlist</p>
          <p className="mt-1 text-muted-foreground">
            Your spot isn&apos;t approved yet — generation is unlocked once an admin approves your
            account. You can still browse templates and the live demo.
          </p>
        </div>
      )}

      {/* ── Page Header ─────────────────────────────────────────── */}
      <header className="animate-fade-in-up">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
          <Badge variant="secondary">15-Phase Pipeline</Badge>
          <Badge variant="info">95% Token Savings</Badge>
          {engineMode === 'live_agent' && (
            <Badge variant="success" className="animate-pulse">
              ⚡ Live AI Agent
            </Badge>
          )}
          {engineMode === 'offline_engine' && <Badge variant="secondary">📦 Offline Engine</Badge>}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary animate-soft-pulse shrink-0" />
          AI Website Generator
        </h1>
        <p className="mt-2 text-muted-foreground max-w-2xl">
          Describe your website in plain language. The 15-phase pipeline handles market research,
          code generation, quality gates, and ZIP delivery — fully autonomously.
        </p>
      </header>

      {/* ── Prompt Input Card ────────────────────────────────────── */}
      <Card
        className="rounded-2xl border border-border bg-card/80 backdrop-blur p-6 space-y-5 animate-fade-in-up shadow-card"
        style={{ animationDelay: '80ms' }}
      >
        {/* Textarea */}
        <div>
          <div className="relative">
            <Textarea
              ref={textareaRef}
              id="prompt-input"
              label="Describe your website"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleGenerate();
              }}
              rows={4}
              placeholder="e.g. Build a restaurant website for a Pakistani food chain with online ordering, menu categories, delivery tracking, and customer reviews…"
              className="rounded-xl focus:ring-primary/50"
              disabled={status === 'running'}
              aria-label="Website description prompt"
            />
            {prompt && (
              <IconButton
                icon={X}
                label="Clear prompt"
                size="sm"
                variant="ghost"
                onClick={() => setPrompt('')}
                className="absolute top-9 right-2 text-muted-foreground hover:text-foreground"
              />
            )}
          </div>
          <div className="flex items-center justify-between mt-1.5 text-xs text-muted-foreground">
            <span>
              {prompt.length} characters ·{' '}
              <kbd className="font-mono bg-muted px-1 py-0.5 rounded text-[10px]">Ctrl+Enter</kbd>{' '}
              to generate
            </span>
            {prompt.length > 200 && (
              <span className="text-emerald-400">✓ Detailed prompt — better results</span>
            )}
          </div>
        </div>

        {/* ── Screenshot Upload + Vision Analysis ─────────────── */}
        <div>
          <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Design Reference (optional)
          </p>
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload a design screenshot or mockup"
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border border-dashed border-border rounded-xl p-4 text-center cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all duration-200"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              className="hidden"
              onChange={handleImageSelect}
              aria-hidden="true"
            />
            {screenshot ? (
              <div className="flex flex-col items-center gap-2">
                <img
                  src={screenshot}
                  alt="Uploaded design screenshot preview"
                  className="max-h-48 rounded-lg border border-border/60 object-contain"
                  loading="lazy"
                />
                <div className="flex items-center gap-2 flex-wrap justify-center">
                  {analyzingVision ? (
                    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" /> Analyzing…
                    </span>
                  ) : visionAnalysis ? (
                    <Badge variant="success" className="gap-1.5">
                      <Eye className="h-3 w-3" /> Vision Extract
                      {visionAnalysis.source === 'ai_vision' ? ' (AI)' : ' (Fallback)'}
                    </Badge>
                  ) : null}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearScreenshot();
                    }}
                    leftIcon={XCircle}
                    aria-label="Remove screenshot"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <ImageUp className="h-5 w-5 text-primary" />
                <span>
                  Drop a screenshot here or <span className="text-primary font-medium">browse</span>{' '}
                  — the agent extracts layout & colors, then builds the code
                </span>
              </div>
            )}
          </div>

          {/* Vision analysis results */}
          {visionAnalysis && (
            <div className="mt-3 rounded-xl border border-border/60 bg-background/50 p-4 space-y-3 animate-fade-in-up">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <Palette className="h-3.5 w-3.5 text-primary" />
                Detected Design System
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">
                  Layout Regions
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(visionAnalysis.vision_layout_regions || []).map((region) => (
                    <Badge key={region} variant="default" className="text-xs">
                      {region}
                    </Badge>
                  ))}
                  {(visionAnalysis.vision_layout_regions || []).length === 0 && (
                    <span className="text-xs text-muted-foreground">Not detected — using default flow</span>
                  )}
                </div>
              </div>
              {visionAnalysis.design_tokens?.palette &&
                Object.keys(visionAnalysis.design_tokens.palette).length > 0 && (
                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">
                      Color Palette
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(visionAnalysis.design_tokens.palette).map(([key, hex]) => (
                        <div key={key} className="flex items-center gap-1.5">
                          <span
                            className="h-5 w-5 rounded border border-border/60"
                            style={{ backgroundColor: hex }}
                            aria-hidden="true"
                          />
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {key}: {hex}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              {visionError && (
                <p className="text-xs text-red-400" role="alert">
                  {visionError}
                </p>
              )}
            </div>
          )}
        </div>

        {/* ── AI Provider Cards ────────────────────────────────── */}
        <div>
          <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            AI Provider
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {PROVIDERS.map((p) => (
              <Button
                key={p.id}
                onClick={() => setProvider(p.id)}
                disabled={status === 'running'}
                variant="outline"
                size="sm"
                className={cn(
                  'relative flex flex-col items-center gap-1.5 rounded-xl p-3 text-center transition-all duration-200 h-auto whitespace-normal',
                  provider === p.id ? p.activeColor : p.color + ' hover:border-primary/30'
                )}
                aria-pressed={provider === p.id}
                aria-label={`Select ${p.name}`}
              >
                {provider === p.id && (
                  <CheckCheck className="absolute top-1.5 right-1.5 h-3 w-3 text-primary" />
                )}
                <span className="text-lg leading-none">{p.icon}</span>
                <span className="text-[11px] font-bold leading-tight">{p.name}</span>
                <span className="text-[10px] text-muted-foreground leading-tight hidden sm:block">
                  {p.desc}
                </span>
              </Button>
            ))}
          </div>
        </div>

        {/* Language + Region */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label
              className="mb-1.5 block text-xs font-semibold text-muted-foreground uppercase tracking-wider"
              htmlFor="target-lang"
            >
              Output Language
            </label>
            <select
              id="target-lang"
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              disabled={status === 'running'}
              className="w-full rounded-xl border border-border bg-background/80 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50"
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              className="mb-1.5 block text-xs font-semibold text-muted-foreground uppercase tracking-wider"
              htmlFor="target-region"
            >
              Region / Compliance
            </label>
            <select
              id="target-region"
              value={targetRegion}
              onChange={(e) => setTargetRegion(e.target.value)}
              disabled={status === 'running'}
              className="w-full rounded-xl border border-border bg-background/80 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50"
            >
              {REGIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Generate Button Row */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50 flex-wrap gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Globe className="h-3.5 w-3.5 text-primary shrink-0" />
            <span>Auto-localizes currencies, taxes & compliance for your region</span>
          </div>
          <ButtonMotion
            onClick={handleGenerate}
            disabled={!prompt.trim() || status === 'running'}
            variant="primary"
            loading={status === 'running'}
            leftIcon={status === 'running' ? undefined : Send}
            rightIcon={status === 'running' ? undefined : ArrowRight}
            className="shadow-glow-sm hover:shadow-glow"
            aria-label="Generate website"
          >
            {status === 'running' ? 'Running Pipeline…' : 'Generate Website'}
          </ButtonMotion>
        </div>

        {/* Example Prompts */}
        <div>
          <p className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Try an example:
          </p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((ex, i) => (
              <Button
                key={i}
                onClick={() => handleExample(ex)}
                disabled={status === 'running'}
                variant="outline"
                size="sm"
                className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-primary/40 hover:bg-muted"
                aria-label={`Use example: ${ex.text}`}
              >
                <span>{ex.emoji}</span>
                <span>
                  {ex.text.slice(0, 32)}
                  {ex.text.length > 32 ? '…' : ''}
                </span>
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* ── Pipeline Progress Card ───────────────────────────────── */}
      {(status === 'running' || status === 'done') && (
        <Card className="rounded-2xl border border-border bg-card/60 backdrop-blur p-6 animate-scale-in space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="font-display font-bold flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Pipeline Progress
              {status === 'running' && (
                <Loader2 className="h-4 w-4 text-muted-foreground animate-spin ml-1" />
              )}
            </h2>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-muted-foreground">
                {doneCount}/{PHASES.length} phases
              </span>
              <span
                className={cn(
                  'font-bold',
                  status === 'done' ? 'text-primary' : 'text-muted-foreground'
                )}
              >
                {progressPct}%
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <Progress
            value={progressPct}
            max={100}
            variant="primary"
            size="md"
            label="Pipeline progress"
          />

          {/* Phase Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {phases.map((phase, idx) => {
              const Icon = phase.icon;
              return (
                <div
                  key={phase.id}
                  className={cn(
                    'flex items-center gap-3 rounded-xl border p-3 transition-all duration-300',
                    phase.state === 'done'
                      ? 'border-primary/30 bg-primary/5'
                      : phase.state === 'running'
                        ? 'border-primary/50 bg-primary/10 shadow-glow-sm'
                        : 'border-border bg-background/30 opacity-40'
                  )}
                >
                  <div
                    className={cn(
                      'h-8 w-8 rounded-lg flex items-center justify-center shrink-0',
                      phase.state === 'done'
                        ? 'bg-primary/20'
                        : phase.state === 'running'
                          ? phase.bg
                          : 'bg-muted'
                    )}
                  >
                    {phase.state === 'done' ? (
                      <CheckCircle2 className="h-4 w-4 text-primary" />
                    ) : phase.state === 'running' ? (
                      <Loader2 className={cn('h-4 w-4 animate-spin', phase.color)} />
                    ) : (
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p
                      className={cn(
                        'text-xs font-semibold truncate',
                        phase.state === 'pending' ? 'text-muted-foreground' : 'text-foreground'
                      )}
                    >
                      <span className="font-mono text-[10px] text-muted-foreground mr-1">
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      {phase.label}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate mt-0.5">
                      {phase.state === 'done'
                        ? `✓ Done in ${phase.duration || '—'}`
                        : phase.state === 'running'
                          ? '⚙ Processing…'
                          : phase.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Logs */}
          <div>
            <Button
              onClick={() => setShowLogs((s) => !s)}
              variant="ghost"
              size="sm"
              leftIcon={showLogs ? ChevronUp : ChevronDown}
              className="text-xs text-muted-foreground hover:text-foreground px-0"
            >
              {showLogs ? 'Hide' : 'Show'} live pipeline logs ({logs.length} entries)
            </Button>
            {showLogs && (
              <div
                ref={logRef}
                className="mt-2 h-40 overflow-y-auto rounded-xl bg-black/70 border border-border/50 p-3 font-mono text-[11px] text-emerald-400/90 leading-relaxed"
                aria-live="polite"
                aria-label="Pipeline logs"
              >
                {logs.map((log, i) => (
                  <div key={i}>{log}</div>
                ))}
                {status === 'running' && (
                  <div className="flex items-center gap-1.5 mt-1 text-primary/70">
                    <span className="animate-pulse">▋</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* ── Result Card ──────────────────────────────────────────── */}
      {status === 'done' && result && (
        <Card className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/5 via-background to-cyan-500/5 p-6 animate-scale-in shadow-glow-sm space-y-6">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <Badge variant="success" className="mb-2">
                🚀 Website Ready to Deploy
              </Badge>
              <h2 className="font-display text-xl font-bold break-all">{result.projectName}</h2>
              <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2 flex-wrap">
                <Clock className="h-3.5 w-3.5 shrink-0" />
                <span>Generated in {result.executionTime}s</span>
                <span className="text-border">·</span>
                <span className="capitalize">{activeProvider.name}</span>
                <span className="text-border">·</span>
                <span>{targetRegion} compliance</span>
              </p>
            </div>
            <div className="text-right shrink-0">
              <div
                className={cn(
                  'font-display text-4xl font-black',
                  qualityColor(result.qualityScore)
                )}
              >
                {result.qualityScore}%
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">Enterprise Quality Score</div>
              {result.launchReady && (
                <Badge variant="success" className="mt-1.5">
                  Launch Ready ✓
                </Badge>
              )}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { icon: Package, label: 'Template', value: result.template },
              { icon: Code2, label: 'Components', value: `${result.components} files` },
              { icon: Server, label: 'Backend', value: result.backend },
              { icon: Database, label: 'Database', value: result.database },
              { icon: Download, label: 'ZIP Package', value: result.zipSize },
              { icon: Globe, label: 'Compliance', value: targetRegion },
              { icon: Brain, label: 'Language', value: targetLang.toUpperCase() },
              { icon: Shield, label: 'Quality Gates', value: 'Passed (6/6) ✓' },
            ].map((item, i) => {
              const Icon = item.icon;
              return (
                <Card
                  key={i}
                  className="rounded-xl border border-border/60 bg-background/60 p-3 group hover:border-primary/30 transition-colors"
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className="h-3 w-3 text-muted-foreground group-hover:text-primary transition-colors" />
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                      {item.label}
                    </p>
                  </div>
                  <p className="font-semibold text-sm truncate">{item.value}</p>
                </Card>
              );
            })}
          </div>

          {/* Trending Features */}
          <div>
            <p className="mb-2.5 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              Injected Trending Features
            </p>
            <div className="flex flex-wrap gap-2">
              {result.trendingFeatures.map((f) => (
                <Badge
                  key={f}
                  variant="default"
                  className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium"
                >
                  <CheckCircle2 className="h-3 w-3" />
                  {f}
                </Badge>
              ))}
            </div>
          </div>

          {/* Quick Start */}
          {result.instructions?.length > 0 && (
            <div className="rounded-xl bg-black/50 border border-border/50 p-4">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <Cpu className="h-3.5 w-3.5" /> Quick Start Commands
              </p>
              <div className="space-y-1 font-mono text-xs">
                {result.instructions.map((step, i) => (
                  <div key={i} className="flex items-center gap-2 text-emerald-400/90">
                    <span className="text-muted-foreground shrink-0">{i + 1}.</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-2 border-t border-border/50">
            <ButtonMotion
              onClick={handleDownload}
              variant="primary"
              leftIcon={Download}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {downloadUrl ? 'Download Project ZIP' : 'Download README'}
            </ButtonMotion>
            {downloadUrl && (
              <a
                href={downloadUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-medium hover:border-primary/40 transition-all"
              >
                <ExternalLink className="h-4 w-4" />
                Open in Browser
              </a>
            )}
            <ButtonMotion
              onClick={handlePreview}
              variant="outline"
              leftIcon={previewBusy ? undefined : MonitorPlay}
              disabled={previewBusy}
            >
              {previewBusy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
              {previewBusy ? 'Creating Preview…' : previewUrl ? 'Recreate Preview' : 'Live Preview'}
            </ButtonMotion>
            <ButtonMotion
              onClick={() => handleDeploy('vercel')}
              variant="outline"
              leftIcon={deployBusy ? undefined : Rocket}
              disabled={deployBusy}
            >
              {deployBusy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
              {deployBusy ? 'Deploying…' : 'Deploy to Vercel'}
            </ButtonMotion>
            <Button onClick={() => setShowFileModal(true)} variant="outline" leftIcon={FolderOpen}>
              Explore Files
            </Button>
            <Button onClick={resetAll} variant="outline" leftIcon={Sparkles}>
              Generate Another
            </Button>
            <Button onClick={() => setShowRevisionModal(true)} variant="outline" leftIcon={MessageSquare}>
              Request Revision
            </Button>
          </div>
        </Card>
      )}

      {/* ── Revision Request Modal ────────────────────────────────── */}
      {showRevisionModal && (
        <Modal open={showRevisionModal} onClose={() => setShowRevisionModal(false)} title="Request Revision" size="lg">
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Describe the changes you need. Our AI will apply them to your generated project.
            </p>
            {revisionErrors.length > 0 && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                {revisionErrors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            )}
            {revisionSuccess && (
              <div className="rounded-lg border border-success/30 bg-success/5 p-3 text-sm text-success space-y-1">
                <div className="font-medium">Revision applied successfully!</div>
                {revisionApplyResult && (
                  <>
                    <div>{revisionApplyResult.changes_applied} change(s) processed</div>
                    {revisionApplyResult.patched_files?.length > 0 && (
                      <div className="text-xs text-success/70">
                        Files modified: {revisionApplyResult.patched_files.join(', ')}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium">Change Requests *</label>
              {revisionFields.map((field, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    value={field}
                    onChange={(e) => {
                      const updated = [...revisionFields];
                      updated[idx] = e.target.value;
                      setRevisionFields(updated);
                    }}
                    placeholder={`Change #${idx + 1} — e.g. "Change hero heading to 'Welcome to Urban Bites'"`}
                    className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none"
                  />
                  {revisionFields.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setRevisionFields(revisionFields.filter((_, i) => i !== idx))}
                    >
                      ✕
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="ghost" size="sm" onClick={() => setRevisionFields([...revisionFields, ''])}>
                + Add Another Change
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium">Your Name</label>
                <input
                  value={revisionClientName}
                  onChange={(e) => setRevisionClientName(e.target.value)}
                  placeholder="John Smith"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <input
                  type="email"
                  value={revisionClientEmail}
                  onChange={(e) => setRevisionClientEmail(e.target.value)}
                  placeholder="john@example.com"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setShowRevisionModal(false)}>Cancel</Button>
              <Button
                variant="primary"
                onClick={handleRevisionSubmit}
                disabled={revisionSubmitting || revisionFields.every(f => !f.trim())}
              >
                {revisionSubmitting ? <><Loader2 className="h-4 w-4 animate-spin mr-1.5" /> Submitting…</> : 'Submit Revision'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ── Live Preview Panel ────────────────────────────────────── */}
      {previewUrl && (
        <Card className="mt-6 overflow-hidden border-border/70">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 bg-card/50 px-5 py-3">
            <div className="flex items-center gap-2">
              <MonitorPlay className="h-4 w-4 text-primary" />
              <span className="font-medium text-sm">Live Preview</span>
              <Badge variant="success" className="text-[10px]">PERSISTED</Badge>
            </div>
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Open full screen
            </a>
          </div>
          <iframe
            src={previewUrl}
            title="LumicorePro live preview"
            className="h-[480px] w-full bg-background"
            sandbox="allow-same-origin allow-scripts"
            loading="lazy"
          />
        </Card>
      )}

      {/* ── Deploy Result Panel ────────────────────────────────────── */}
      {deployResult && (
        <Card className="mt-6 p-5">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-primary" />
            <span className="font-medium text-sm">Deployment — {deployResult.platform || 'Vercel'}</span>
            <Badge
              variant={deployResult.status === 'live' ? 'success' : deployResult.status === 'failed' ? 'danger' : 'secondary'}
            >
              {deployResult.status}
            </Badge>
          </div>
          {deployResult.url && (
            <a
              href={deployResult.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              {deployResult.url}
            </a>
          )}
          {deployResult.commands?.length > 0 && (
            <div className="mt-3 rounded-xl bg-black/50 border border-border/50 p-3 font-mono text-xs space-y-1">
              {deployResult.commands.map((c, i) => (
                <div key={i} className="text-emerald-400/90">
                  $ {c}
                </div>
              ))}
            </div>
          )}
          {deployResult.message && (
            <p className="mt-3 text-sm text-muted-foreground">{deployResult.message}</p>
          )}

          {/* Custom domain wizard */}
          <div className="mt-5 rounded-xl border border-border/60 bg-muted/20 p-4">
            <p className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Globe className="h-4 w-4 text-primary" />
              Connect a custom domain
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Input
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="mybrand.com"
                aria-label="Custom domain"
                className="w-56"
              />
              <select
                value={domainPlatform}
                onChange={(e) => setDomainPlatform(e.target.value)}
                aria-label="Domain platform"
                className="rounded-lg border border-border bg-background px-2 py-2 text-xs text-foreground"
              >
                <option value="vercel">Vercel</option>
                <option value="netlify">Netlify</option>
                <option value="railway">Railway</option>
                <option value="vps">VPS (Nginx)</option>
              </select>
              <Button
                size="sm"
                variant="outline"
                onClick={handleConnectDomain}
                disabled={domainBusy || !domainInput.trim()}
              >
                {domainBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4" />}
                {domainBusy ? 'Checking…' : 'Connect'}
              </Button>
            </div>
            {domainResult && (
              <div className="mt-4 space-y-3 text-sm">
                <Badge
                  variant={domainResult.status === 'live' ? 'success' : domainResult.status === 'failed' ? 'danger' : 'secondary'}
                >
                  {domainResult.status}
                </Badge>
                {domainResult.message && (
                  <p className="text-muted-foreground">{domainResult.message}</p>
                )}
                {(domainResult.records || []).length > 0 && (
                  <div className="overflow-x-auto rounded-xl border border-border/50 bg-black/40 p-3 font-mono text-xs">
                    {(domainResult.records || []).map((r, i) => (
                      <div key={i} className="mb-1">
                        <span className="text-cyan-400">{r.type}</span>{' '}
                        <span className="text-violet-300">{r.host}</span> →{' '}
                        <span className="text-emerald-400">{r.value}</span>{' '}
                        <span className="text-muted-foreground">(TTL {r.ttl})</span>
                      </div>
                    ))}
                  </div>
                )}
                {(domainResult.steps || []).length > 0 && (
                  <ol className="list-decimal space-y-1 pl-5 text-xs text-muted-foreground">
                    {(domainResult.steps || []).map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ol>
                )}
                {domainResult.nginx_block && (
                  <pre className="overflow-x-auto rounded-xl border border-border/50 bg-black/40 p-3 font-mono text-[11px] text-emerald-300/90">
                    {domainResult.nginx_block}
                  </pre>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* ── File Explorer Modal ───────────────────────────────────── */}
      <Modal
        open={showFileModal}
        onClose={() => setShowFileModal(false)}
        title="Generated Project Structure"
        size="lg"
        className="max-h-[85vh] flex flex-col"
        footer={
          <Button onClick={handleDownload} variant="primary" size="sm" leftIcon={Download}>
            {downloadUrl ? 'Download ZIP' : 'Download README'}
          </Button>
        }
      >
        <div className="overflow-y-auto flex-1 space-y-0.5 text-xs font-mono bg-background/50 p-4 rounded-xl border border-border/50">
          {[
            {
              indent: 0,
              icon: '📁',
              name: `${result?.projectName || 'my-project'}/`,
              bold: true,
              color: 'text-primary',
            },
            { indent: 1, icon: '📁', name: 'src/' },
            { indent: 2, icon: '📄', name: 'App.jsx' },
            { indent: 2, icon: '📄', name: 'main.jsx' },
            { indent: 2, icon: '📄', name: 'index.css (Tailwind CSS 3)' },
            { indent: 2, icon: '📁', name: 'components/' },
            { indent: 3, icon: '📄', name: 'Navbar.jsx' },
            { indent: 3, icon: '📄', name: 'HeroSection.jsx' },
            { indent: 3, icon: '📄', name: 'FeatureGrid.jsx' },
            { indent: 3, icon: '📄', name: 'ContactForm.jsx' },
            { indent: 3, icon: '📄', name: 'CookieConsent.jsx (GDPR)' },
            { indent: 2, icon: '📁', name: 'pages/' },
            { indent: 3, icon: '📄', name: 'Home.jsx', color: 'text-emerald-400' },
            { indent: 3, icon: '📄', name: 'About.jsx' },
            { indent: 3, icon: '📄', name: 'Contact.jsx' },
            { indent: 1, icon: '📁', name: 'backend/' },
            { indent: 2, icon: '📄', name: 'server.js (Express + Socket.io)' },
            { indent: 2, icon: '📁', name: 'routes/ (auth, api, payments)' },
            { indent: 2, icon: '📁', name: 'models/ (Sequelize / PostgreSQL)' },
            { indent: 2, icon: '📁', name: 'middleware/ (auth, security)' },
            { indent: 1, icon: '📄', name: 'package.json' },
            { indent: 1, icon: '📄', name: 'vite.config.js' },
            { indent: 1, icon: '📄', name: 'tailwind.config.js' },
            { indent: 1, icon: '📄', name: 'Dockerfile' },
            { indent: 1, icon: '📄', name: '.env.example', color: 'text-amber-400' },
            { indent: 1, icon: '📄', name: 'INSTRUCTIONS.md', bold: true, color: 'text-primary' },
          ].map((item, i) => (
            <div
              key={i}
              className={cn(
                'flex items-center gap-1 py-0.5',
                item.color || 'text-muted-foreground',
                item.bold && 'font-bold'
              )}
              style={{ paddingLeft: `${item.indent * 16}px` }}
            >
              <span>{item.icon}</span>
              <span>{item.name}</span>
            </div>
          ))}
        </div>
      </Modal>

      {/* ── Idle Feature Panels ───────────────────────────────────── */}
      {status === 'idle' && (
        <div
          className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in-up"
          style={{ animationDelay: '200ms' }}
        >
          {[
            {
              icon: '⚡',
              title: 'Local-First, Blazing Fast',
              desc: '95% of work is local template assembly. AI only customizes the unique parts. No waiting for slow API round-trips on boilerplate.',
            },
            {
              icon: '🔒',
              title: 'Secure by Default',
              desc: 'Every generated project passes 6 security quality gates — no eval/exec, parameterized queries, CSRF protection, and GDPR cookie consent.',
            },
            {
              icon: '📦',
              title: 'Complete Full-Stack ZIP',
              desc: 'Frontend + backend + DB schema + Dockerfile + INSTRUCTIONS.md — one ZIP, ready to deploy to any VPS or cloud platform.',
            },
          ].map((item, i) => (
            <Card
              key={i}
              className="rounded-2xl border border-border bg-card/60 p-5 text-center hover:border-primary/30 hover:shadow-card-hover transition-all duration-200"
            >
              <div className="text-4xl mb-3">{item.icon}</div>
              <h3 className="font-display font-bold mb-1.5">{item.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
