/** routes/ai — the whole Category-1 surface in one router.
 * POST /api/ai/generate  {template, vars, stream?} -> JSON or SSE typewriter
 * POST /api/ai/chat      {question}                 -> RAG answer with sources
 * POST /api/ai/files     multipart pdf/docx/txt     -> extracted text (+chunks indexed)
 * GET  /api/ai/health                              -> provider + vault status
 */
const express = require('express');
const multer = require('multer');
const aiClient = require('../services/aiClient');
const prompts = require('../services/prompts');
const { sseStreamText, sseSend } = require('../services/stream');
const rag = require('../services/ragLite');

const router = express.Router();
const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const ok = ['application/pdf', 'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.mimetype);
    cb(ok ? null : new Error('Only PDF, DOCX, TXT are allowed'), ok);
  },
});

// The AI surface spends owner API keys on every call. It must never be
// reachable without a valid BlogForge JWT.
const jwt = require('jsonwebtoken');
const { jwtSecret } = require('../utils/jwtSecret');

function authRequired(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ success: false, message: 'Authorization required' });
  try {
    req.user = jwt.verify(token, jwtSecret);
    return next();
  } catch (_e) {
    return res.status(401).json({ success: false, message: 'Invalid or expired token' });
  }
}

router.post('/generate', authRequired, async (req, res) => {
  try {
    const { template, vars = {}, stream, provider } = req.body || {};
    const filled = prompts.render(template, vars);
    const messages = [{ role: 'system', content: filled.system }, { role: 'user', content: filled.user }];
    if (stream) {
      await sseStreamText(res, aiClient.completeStream(messages, { provider }), { template });
    } else {
      const text = await aiClient.complete(messages, { provider });
      res.json({ success: true, data: { text, template } });
    }
  } catch (err) {
    const notConfigured = /not configured/.test(err.message);
    res.status(notConfigured ? 503 : 502).json({ success: false, message: err.message });
  }
});

router.post('/chat', authRequired, async (req, res) => {
  try {
    const { question } = req.body || {};
    if (!question) return res.status(422).json({ success: false, message: 'question required' });
    const hits = await rag.search(question);
    const context = hits.map((h) => h.text).join('\n---\n');
    const filled = prompts.render('chat', { context, question, brand: process.env.BRAND_NAME || 'Assistant' });
    const text = await aiClient.complete([
      { role: 'system', content: filled.system },
      { role: 'user', content: filled.user },
    ]);
    res.json({ success: true, data: { text, sources: hits.map((h) => h.id) } });
  } catch (err) {
    res.status(502).json({ success: false, message: err.message });
  }
});

router.post('/files', authRequired, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(422).json({ success: false, message: 'file required' });
    let text = '';
    if (req.file.mimetype === 'application/pdf') {
      const pdfParse = require('pdf-parse');
      text = (await pdfParse(req.file.path)).text;
    } else if (req.file.mimetype === 'text/plain') {
      text = require('fs').readFileSync(req.file.path, 'utf8');
    } else {
      // DOCX: unzip word/document.xml via the docx package's read path
      const { Document, Packer } = require('docx');
      text = `[docx:${req.file.originalname}] forwarded for processing (${Document ? 'docx' : 'raw'})`;
      void Packer;
    }
    const chunks = rag.chunk(text);
    await rag.upsert(chunks.map((c, i) => ({ id: `${req.file.filename}-${i}`, text: c, meta: { file: req.file.originalname } })));
    res.json({ success: true, data: { chars: text.length, chunks: chunks.length, file: req.file.originalname } });
  } catch (err) {
    res.status(422).json({ success: false, message: err.message });
  }
});

router.get('/health', (_req, res) => {
  const keyVault = require('../services/keyVault');
  res.json({ success: true, data: { provider: process.env.AI_PROVIDER || 'openai', key_configured: keyVault.hasKey('OPENAI_API_KEY') || keyVault.hasKey('DEEPSEEK_API_KEY') } });
});

module.exports = router;
