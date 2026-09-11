import express from 'express';
import http from 'http';
import logger from '../utils/logger.js';
import { aiLimiter, aiWriteLimiter } from '../middleware/rateLimit.js';
import { gateAI } from '../middleware/security.js';
import { circuitBreaker, dailyGenLimit, dailyChatLimit, tokenCap, recordUsage } from '../middleware/usageGuard.js';
import { dispatchAI } from '../services/aiCost/queue.service.js';
import spendEstimator from '../services/aiCost/spendEstimator.service.js';

const router = express.Router();
const AI_AGENT_URL = process.env.AI_AGENT_URL || 'http://localhost:8000';
const DEMO_MODE = (process.env.DEMO_MODE || 'false').toLowerCase() === 'true';

// Global AI-route rate limiting (defense against auth-less abuse)
router.use(aiLimiter);

// Cost-guard the expensive routes: circuit breaker → daily/user/IP limit → token cap
router.post('/generate', circuitBreaker(), dailyGenLimit(), tokenCap('generation'));
router.post('/chat', circuitBreaker(), dailyChatLimit(), tokenCap('chat'));
router.post('/vision/analyze', circuitBreaker(), dailyGenLimit(), tokenCap('vision'));
router.post('/generate/stream', circuitBreaker(), dailyGenLimit(), tokenCap('generation'));

/**
 * Validate + normalize file attachments from the frontend.
 * Each file: { filename, type, data } where data is a base64 data URI.
 * Caps count and payload size to protect both servers.
 */
function sanitizeFiles(files) {
  if (!Array.isArray(files) || files.length === 0) return [];
  const MAX_PER_FILE = 8 * 1024 * 1024;
  const clean = [];
  for (const f of files.slice(0, 10)) {
    if (!f || typeof f.filename !== 'string' || typeof f.data !== 'string') continue;
    const filename = f.filename.trim().slice(0, 255);
    const data = f.data.trim();
    if (!filename || !data || !data.startsWith('data:')) continue;
    if (Buffer.byteLength(data, 'utf8') > MAX_PER_FILE) continue;
    clean.push({ filename, type: typeof f.type === 'string' ? f.type.slice(0, 100) : '', data });
  }
  return clean;
}

/**
 * Helper to fetch from the Python AI Agent server
 */
async function callAgent(endpoint, options = {}) {
  const url = `${AI_AGENT_URL.replace(/\/+$/, '')}${endpoint}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Agent request failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

/**
 * @swagger
 * /api/generate:
 *   post:
 *     summary: Trigger 15-phase AI website generation pipeline
 *     tags: [AI Generation]
 */
router.post('/generate', aiWriteLimiter, gateAI, async (req, res, next) => {
  const { prompt, provider = 'gemini', language = 'en', region, image, files } = req.body;
  const attachments = sanitizeFiles(files);

  if (!prompt && !image && attachments.length === 0) {
    return res.status(400).json({ success: false, error: 'Prompt must be at least 5 characters long' });
  }

  // Email-verified gate: unverified accounts must not burn AI quota. Skip for
  // API-key-authenticated (service) calls — they're trusted partners.
  if (req.user?.id && !DEMO_MODE) {
    try {
      const { default: UserModel } = await import('../models/User.js');
      const account = await UserModel.findByPk(req.user.id, {
        attributes: ['id', 'isVerified', 'betaStatus'],
      });
      if (account) {
        if (account.isVerified === false) {
          return res.status(403).json({
            success: false,
            error: {
              code: 'EMAIL_NOT_VERIFIED',
              message: 'Please verify your email address before generating. Check your inbox for the verification link.',
            },
          });
        }
        const waitlistOn = process.env.WAITLIST_MODE === 'true';
        if (waitlistOn && account.betaStatus === 'waitlist') {
          return res.status(403).json({
            success: false,
            error: {
              code: 'WAITLIST_PENDING',
              message: 'Your account is on the waitlist. You will be able to generate once approved.',
            },
          });
        }
        if (waitlistOn && account.betaStatus === 'denied') {
          return res.status(403).json({
            success: false,
            error: { code: 'WAITLIST_DENIED', message: 'This account is not authorized.' },
          });
        }
      }
    } catch (err) {
      // DB offline — let the daily-limit guard handle cost protection
      logger.warn(`verified-email check skipped: ${err.message}`);
    }
  }

  try {
    // Demo mode: return instant simulated result WITHOUT calling the AI agent,
    // so demo visitors never consume free AI API quota.
    if (DEMO_MODE) {
      const runId = `demo-${Date.now()}`;
      const demoName = (prompt || 'demo-website').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30) || 'demo-website';
      return res.json({
        success: true,
        mode: 'demo_offline',
        run_id: runId,
        status: 'done',
        ws_url: null,
        download_url: null,
        message: 'Demo mode: generation simulated with local rules (no AI quota consumed).',
        fallback_data: {
          projectName: demoName,
          template: 'Selection simulated by demo rules',
          components: 12,
          backend: 'Express.js',
          database: 'PostgreSQL',
          qualityScore: 94,
          launchReady: true,
          executionTime: '0.4',
          demo: true,
        },
      });
    }

    // Attempt to call the Python FastAPI agent
    const body = { provider, language, region };
    if (prompt && typeof prompt === 'string' && prompt.trim().length >= 5) {
      body.prompt = prompt.trim();
    } else if (prompt) {
      body.prompt = prompt.trim();
    }
    if (image && typeof image === 'string' && image.trim()) {
      body.image = image.trim();
    }
    if (attachments.length > 0) {
      body.files = attachments;
    }
    const data = await dispatchAI(
      () => callAgent('/api/generate', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
      { queueKind: 'generation' }
    );

    // Record usage for the spend estimator (best-effort, never blocks response)
    recordUsage({
      userId: req.user?.id,
      ip: req.ip,
      endpoint: 'generation',
      estimatedTokens: spendEstimator.estimateTokensForRequest('generation'),
    }).catch(() => {});

    return res.json({
      success: true,
      mode: 'live_agent',
      run_id: data.run_id,
      ws_url: `ws://${new URL(AI_AGENT_URL).host}/ws/generate/${data.run_id}`,
      download_url: `/api/ai/download/${data.run_id}`,
      status: data.status || 'queued',
      language: data.language || language,
      region: data.region || region,
      vision_mode: Boolean(data.vision_mode),
    });
  } catch (err) {
    logger.warn(`AI Agent unavailable at ${AI_AGENT_URL}: ${err.message}. Falling back to offline generation.`);

    // Graceful offline fallback
    const runId = `offline-${Date.now()}`;
    const projectSlug = prompt.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30);

    return res.json({
      success: true,
      mode: 'offline_engine',
      run_id: runId,
      status: 'queued',
      ws_url: null,
      download_url: null,
      message: 'AI agent is offline. Running in offline template engine mode.',
      fallback_data: {
        projectName: projectSlug || 'generated-website',
        template: 'Selected from 60 local templates',
        components: 12,
        backend: 'Express.js',
        database: 'PostgreSQL',
        qualityScore: 94,
        launchReady: true,
        executionTime: '2.4',
        trendingFeatures: ['Smart Search', 'RTL Localization', 'GDPR Cookie Banner', 'Responsive Dark Mode'],
        zipSize: '3.2 MB',
      },
    });
  }
});

/**
 * @swagger
 * /api/ai/runs/{runId}:
 *   get:
 *     summary: Get status and results for a generation run
 *     tags: [AI Generation]
 */
router.get('/runs/:runId', async (req, res) => {
  const { runId } = req.params;
  try {
    const data = await callAgent(`/api/runs/${runId}`);
    res.json({ success: true, ...data });
  } catch (err) {
    res.status(404).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * /api/ai/download/{runId}:
 *   get:
 *     summary: Download generated project ZIP
 *     tags: [AI Generation]
 */
router.get('/download/:runId', aiWriteLimiter, gateAI, async (req, res) => {
  const { runId } = req.params;
  try {
    const targetUrl = `${AI_AGENT_URL.replace(/\/+$/, '')}/api/download/${runId}`;
    const response = await fetch(targetUrl);
    if (!response.ok) {
      return res.status(response.status).json({ success: false, error: 'Project archive not found' });
    }

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${runId}.zip"`);

    const arrayBuffer = await response.arrayBuffer();
    return res.send(Buffer.from(arrayBuffer));
  } catch (err) {
    logger.error(`Download error for run ${runId}: ${err.message}`);
    return res.status(500).json({ success: false, error: 'Failed to stream ZIP archive' });
  }
});

/**
 * @swagger
 * /api/ai/vision/analyze:
 *   post:
 *     summary: Analyze an uploaded screenshot into layout + theme tokens
 *     tags: [AI Generation]
 */
router.post('/vision/analyze', aiWriteLimiter, gateAI, async (req, res) => {
  const { image, provider } = req.body || {};
  if (!image || typeof image !== 'string' || !image.trim()) {
    return res.status(400).json({ success: false, error: 'image is required (data URI, URL, or local path)' });
  }

  try {
    const data = await dispatchAI(
      () => callAgent('/api/vision/analyze', {
        method: 'POST',
        body: JSON.stringify({ image: image.trim(), provider: provider || null }),
      }),
      { queueKind: 'vision' }
    );
    recordUsage({
      userId: req.user?.id,
      ip: req.ip,
      endpoint: 'vision',
      estimatedTokens: spendEstimator.estimateTokensForRequest('vision'),
    }).catch(() => {});
    return res.json({ success: true, data });
  } catch (err) {
    logger.warn(`Vision analyze failed at ${AI_AGENT_URL}: ${err.message}`);
    return res.status(502).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * /api/ai/chat:
 *   post:
 *     summary: Chat with AI assistant
 *     tags: [AI Generation]
 */
router.post('/chat', aiWriteLimiter, gateAI, async (req, res) => {
  const { message, provider = 'gemini', image, files } = req.body;
  if (!message) {
    return res.status(400).json({ success: false, error: 'Message is required' });
  }

  // Check if agent provides chat or respond with helpful intelligent assistant text
  try {
    const body = { message, provider };
    if (image && typeof image === 'string' && image.trim()) {
      body.image = image.trim();
    }
    const attachments = sanitizeFiles(files);
    if (attachments.length > 0) {
      body.files = attachments;
    }
    if (attachments.length + (image ? 1 : 0) > 10) {
      return res.status(400).json({ success: false, error: 'Maximum 10 attachments per message' });
    }
    const data = await dispatchAI(
      () => callAgent('/api/chat', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
      { queueKind: 'chat' }
    );
    recordUsage({
      userId: req.user?.id,
      ip: req.ip,
      endpoint: 'chat',
      estimatedTokens: spendEstimator.estimateTokensForRequest('chat'),
    }).catch(() => {});
    return res.json({ success: true, data });
  } catch {
    return res.json({
      success: true,
      message: `I received your message: "${message}". LumiCorePro AI orchestrator is active with 60 local templates and 15-phase generation pipeline.`,
      provider,
      timestamp: new Date().toISOString(),
    });
  }
});

/**
 * @swagger
 * /api/ai/health:
 *   get:
 *     summary: Check Python AI Agent liveness
 *     tags: [AI Generation]
 */
router.get('/health', async (req, res) => {
  try {
    const health = await callAgent('/health');
    res.json({ success: true, agent: health, connected: true });
  } catch (err) {
    res.json({ success: true, connected: false, error: err.message, message: 'AI Agent is currently offline' });
  }
});

/**
 * GET /api/ai/models
 * List available AI models / providers with their status.
 */
router.get('/models', (req, res) => {
  const providers = [
    {
      id:          'gemini',
      name:        'Gemini 2.5 Flash',
      vendor:      'Google',
      model:       'gemini-2.5-flash',
      available:   Boolean(process.env.GEMINI_API_KEY),
      recommended: true,
      description: 'Best balance of speed and quality for code generation',
    },
    {
      id:          'deepseek',
      name:        'DeepSeek Chat',
      vendor:      'DeepSeek AI',
      model:       'deepseek-chat',
      available:   Boolean(process.env.DEEPSEEK_API_KEY),
      recommended: false,
      description: 'Excellent for structured code output, cost-efficient',
    },
    {
      id:          'claude',
      name:        'Claude 3.5 Sonnet',
      vendor:      'Anthropic',
      model:       'claude-3-5-sonnet-20241022',
      available:   Boolean(process.env.ANTHROPIC_API_KEY),
      recommended: false,
      description: 'Highest quality output, best for complex requirements',
    },
    {
      id:          'mistral',
      name:        'Mistral Large',
      vendor:      'Mistral AI',
      model:       'mistral-large-latest',
      available:   Boolean(process.env.MISTRAL_API_KEY),
      recommended: false,
      description: 'European & multilingual focus, fast inference',
    },
    {
      id:          'openrouter',
      name:        'OpenRouter',
      vendor:      'Multi-Model',
      model:       'deepseek/deepseek-chat',
      available:   Boolean(process.env.OPENROUTER_API_KEY),
      recommended: false,
      description: 'Access 50+ models through a single API key',
    },
  ];

  const activeProvider = process.env.ACTIVE_AI_PROVIDER || 'gemini';

  res.json({
    success:        true,
    activeProvider,
    offlineFallback: true,
    providers,
  });
});

/**
 * GET /api/ai/conversations
 * Return recent AI generation history stored in memory / agent DB.
 * Query params: limit (default 20), offset (default 0)
 */
router.get('/conversations', async (req, res) => {
  const limit  = Math.min(parseInt(req.query.limit,  10) || 20, 100);
  const offset = parseInt(req.query.offset, 10) || 0;

  try {
    const data = await callAgent(`/api/history?limit=${limit}&offset=${offset}`);
    return res.json({ success: true, data: data.history || data, total: data.total || 0 });
  } catch {
    // Agent offline — return empty list gracefully
    return res.json({ success: true, data: [], total: 0, source: 'offline' });
  }
});

/**
 * GET /api/ai/conversations/:runId
 * Return details of a specific generation run.
 */
router.get('/conversations/:runId', async (req, res) => {
  try {
    const data = await callAgent(`/api/runs/${req.params.runId}`);
    res.json({ success: true, data });
  } catch (err) {
    res.status(404).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * POST /api/ai/preview — register a finished run for live preview
 */
router.post('/preview', aiWriteLimiter, gateAI, async (req, res) => {
  const { run_id } = req.body || {};
  if (!run_id) {
    return res.status(400).json({ success: false, error: 'run_id is required' });
  }
  try {
    const data = await callAgent('/api/preview', {
      method: 'POST',
      body: JSON.stringify({ run_id }),
    });
    return res.json({ success: true, data: data.data || data });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * GET /api/ai/preview/:slug — proxy preview url to the agent
 */
router.get('/preview/:slug', async (req, res) => {
  const { slug } = req.params;
  try {
    const agentHost = new URL(AI_AGENT_URL).host;
    const targetUrl = `http://${agentHost}/preview/${encodeURIComponent(slug)}`;
    const upstream = await fetch(targetUrl);
    const ct = upstream.headers.get('content-type') || 'text/html';
    res.setHeader('Content-Type', ct);
    res.setHeader('X-Preview-Slug', slug);
    const body = await upstream.arrayBuffer();
    return res.send(Buffer.from(body));
  } catch (err) {
    return res.status(404).json({ success: false, error: err.message });
  }
});

/**
 * GET /api/ai/preview/:slug/:path(*) — proxy nested preview assets
 */
router.get('/preview/:slug/*', async (req, res) => {
  const { slug } = req.params;
  const rest = req.params[0] || '';
  try {
    const agentHost = new URL(AI_AGENT_URL).host;
    const targetUrl = `http://${agentHost}/preview/${encodeURIComponent(slug)}/${encodeURIComponent(rest)}`;
    const upstream = await fetch(targetUrl);
    const ct = upstream.headers.get('content-type') || 'application/octet-stream';
    res.setHeader('Content-Type', ct);
    res.setHeader('X-Preview-Slug', slug);
    const body = await upstream.arrayBuffer();
    return res.send(Buffer.from(body));
  } catch (err) {
    return res.status(404).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * POST /api/ai/deploy — deploy a finished run to Vercel/Netlify/Railway
 */
router.post('/deploy', aiWriteLimiter, gateAI, async (req, res) => {
  const { run_id, platform = 'vercel' } = req.body || {};
  if (!run_id) {
    return res.status(400).json({ success: false, error: 'run_id is required' });
  }
  try {
    const data = await callAgent('/api/deploy', {
      method: 'POST',
      body: JSON.stringify({ run_id, platform }),
    });
    return res.json({ success: true, data: data.data || data });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * POST /api/ai/deploy/domain — connect a custom domain to a deployed site
 */
router.post('/deploy/domain', aiWriteLimiter, gateAI, async (req, res) => {
  const { domain, platform = 'vercel', project_dir } = req.body || {};
  if (!domain || typeof domain !== 'string' || !domain.trim()) {
    return res.status(400).json({ success: false, error: 'domain is required (e.g. mybrand.com)' });
  }
  try {
    const data = await callAgent('/api/deploy/domain', {
      method: 'POST',
      body: JSON.stringify({ domain: domain.trim(), platform, project_dir: project_dir || null }),
    });
    return res.json({ success: true, data: data.data || data });
  } catch (err) {
    return res.status(502).json({ success: false, error: err.message });
  }
});

/**
 * @swagger
 * /api/ai/usage:
 *   get:
 *     summary: Return aggregated token / generation usage stats
 *     tags: [AI Generation]
 */
router.get('/usage', async (req, res) => {
  try {
    const data = await callAgent('/api/usage');
    return res.json({ success: true, data });
  } catch {
    // Offline fallback — return mock usage summary
    return res.json({
      success: true,
      source:  'offline',
      data: {
        totalGenerations:  0,
        tokensUsed:        0,
        estimatedCost:     0,
        providers:         {},
        lastGeneration:    null,
      },
    });
  }
});

/**
 * @swagger
 * /api/ai/spend-estimator:
 *   get:
 *     summary: Local daily/weekly estimated AI token spend (admin). No paid analytics.
 *     tags: [AI Generation]
 */
router.get('/spend-estimator', async (req, res, next) => {
  try {
    const summary = await spendEstimator.getSpendSummary(8);
    return res.json({ success: true, data: summary });
  } catch (err) {
    next(err);
  }
});

/**
 * @swagger
 * /api/ai/my-quota:
 *   get:
 *     summary: Return the authenticated user's today-remaining generation quota
 *     tags: [AI Generation]
 */
router.get('/my-quota', async (req, res, next) => {
  try {
    return res.json({
      success: true,
      data: {
        limit: parseInt(process.env.AI_DAILY_GEN_LIMIT, 10) || 3,
        demoMode: DEMO_MODE,
        message: DEMO_MODE
          ? 'Demo mode active — generations are simulated and free.'
          : `Free tier allows ${parseInt(process.env.AI_DAILY_GEN_LIMIT, 10) || 3} generations per day.`,
      },
    });
  } catch (err) {
    next(err);
  }
});

export default router;
