const express = require('express');
const jwt = require('jsonwebtoken');
const { sequelize, User, Article, Credit } = require('../models');
const aiClient = require('../services/aiClient');
const { sseInit, sseSend, sseStreamText } = require('../services/stream');
const { jwtSecret } = require('../utils/jwtSecret');

/** routes/blog — BlogForge core: streaming AI article generation with credits,
 * history CRUD and SEO metadata. All queries run through Sequelize
 * (parameterized = SQLi-safe); bodies are validated inline (XSS-safe). */

const router = express.Router();

const LENGTH_SPEC = {
  short: { words: 600, sections: 3 },
  medium: { words: 1200, sections: 5 },
  long: { words: 2200, sections: 7 },
};
const TONES = ['professional', 'friendly', 'casual', 'humorous', 'informative'];

function authRequired(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ success: false, message: 'Authorization required' });
  try {
    req.user = jwt.verify(token, jwtSecret);
    next();
  } catch {
    return res.status(401).json({ success: false, message: 'Session expired' });
  }
}

function slugify(text, max = 60) {
  return String(text).toLowerCase().normalize('NFKD')
    .replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '-').slice(0, max) || 'article';
}

function clamp(text, max, fallback) {
  const t = String(text || '').trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max);
  const last = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf(' '));
  return (last > 40 ? cut.slice(0, last + 1) : cut);
}

function str(v) {
  if (typeof v !== 'string') return '';
  const t = v.trim().slice(0, 400);
  return t.replace(/[<>"'&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '&': '&amp;' }[c]));
}

async function reserveCredit(userId) {
  const [updated] = await sequelize.query(
    `UPDATE credits SET balance = balance - 1, total_used = total_used + 1, updated_at = NOW()
     WHERE user_id = :uid AND balance > 0 RETURNING balance`,
    { replacements: { uid: userId } },
  );
  return updated.length > 0 ? updated[0].balance : null;
}

async function refundCredit(userId) {
  await sequelize.query(
    `UPDATE credits SET balance = balance + 1, total_used = GREATEST(total_used - 1, 0), updated_at = NOW()
     WHERE user_id = :uid`,
    { replacements: { uid: userId } },
  );
}

function demoArticle({ keyword, tone, length, audience }) {
  const spec = LENGTH_SPEC[length] || LENGTH_SPEC.medium;
  const aud = audience || 'general readers';
  const title = keyword;
  const sections = [
    {
      h: 'Why ' + keyword + ' Matters Right Now',
      p: 'Search demand around <strong>' + keyword + '</strong> keeps climbing because the topic sits exactly where reader curiosity and commercial intent overlap. Writing about it today positions you ahead of the content curve your competitors will publish months from now.',
    },
    {
      h: 'The Landscape of ' + keyword + ' in 2026',
      p: 'The modern landscape of ' + keyword + ' rewards clarity over volume. Readers scanning for ' + keyword + ' want actionable guidance, credible references and a fast answer to their next question. Structuring this article with an explicit H2 for every question is exactly how top-ranking pages hold attention.',
    },
    {
      h: 'Getting Started With ' + keyword,
      p: 'Start small: define one measurable goal connected to ' + keyword + ', then build a repeatable workflow around it. Consistency compounds — every article you refine on the topic teaches the search engine that your domain is a primary source for ' + keyword + '.',
    },
    {
      h: 'Common Mistakes When Targeting ' + keyword,
      p: 'The three most common mistakes are keyword stuffing, ignoring search intent, and burying the meta description. A focused meta description of 155 characters that includes the phrase <em>' + keyword + '</em> dramatically improves click-through on similar content.',
    },
    {
      h: 'Measuring Success',
      p: 'Track rankings for ' + keyword + ' plus long-tail variants, monitor scroll depth on the article, and refresh the piece every quarter. A content refresh节奏 — updated stats, new examples — keeps ' + keyword + ' performing year over year.',
    },
  ].slice(0, spec.sections + 1);
  const meta = 'A practical ' + tone + ' guide on ' + keyword + ' for ' + aud + '.';
  const md = [
    '# ' + title,
    '',
    '> Demo article (no AI provider key configured). Add OPENAI_API_KEY to generate real content.',
    '',
    ...sections.flatMap((s) => ['## ' + s.h, '', s.p, '']),
    '### Key Takeaways',
    '',
    '- ' + keyword + ' rewards structured, intent-matched content.',
    '- ' + aud + ' respond best to a ' + tone + ' tone.',
    '- Keep the meta description under 155 characters and keyword-led.',
  ].join('\n');
  return { md, metaTitle: clamp('Best ' + keyword + ' Guide (2026)', 70), metaDescription: clamp(meta, 155), keywords: clamp('[' + slugify(keyword).replace(/-/g, ', ') + ', guide, 2026]', 400) };
}

router.get('/credits', authRequired, async (req, res) => {
  try {
    let credit = await Credit.findOne({ where: { userId: req.user.id } });
    if (!credit) {
      credit = await Credit.create({ userId: req.user.id, balance: 0, totalGranted: 0 });
    }
    return res.json({ success: true, data: { balance: credit.balance, totalGranted: credit.totalGranted, totalUsed: credit.totalUsed } });
  } catch (err) {
    console.error(`[ERR blog credits] ${err.message}`);
    return res.status(500).json({ success: false, message: 'Could not load credits' });
  }
});

router.post('/credits/topup', authRequired, async (req, res) => {
  try {
    // Free-credit top-up is a demo-only affordance. Without a payment provider
    // wired it is a critical business flaw, so it ships disabled unless the
    // buyer explicitly re-enables it via ENABLE_DEMO_TOPUP=1.
    if (process.env.ENABLE_DEMO_TOPUP !== '1') {
      return res.status(402).json({ success: false, code: 'TOPUP_DISABLED', message: 'Top-up requires a payment provider; set ENABLE_DEMO_TOPUP=1 only for demos' });
    }
    const amount = parseInt(req.body.amount, 10) || 0;
    if (amount < 10 || amount > 5000) return res.status(422).json({ success: false, message: 'Top-up must be between 10 and 5000 credits' });
    const [updated] = await sequelize.query(
      `UPDATE credits SET balance = balance + :amt, total_granted = total_granted + :amt, updated_at = NOW()
       WHERE user_id = :uid RETURNING balance`,
      { replacements: { amt: amount, uid: req.user.id } },
    );
    if (updated.length === 0) {
      await Credit.create({ userId: req.user.id, balance: amount, totalGranted: amount });
      return res.json({ success: true, data: { balance: amount } });
    }
    return res.json({ success: true, data: { balance: updated[0].balance } });
  } catch (err) {
    console.error(`[ERR blog topup] ${err.message}`);
    return res.status(500).json({ success: false, message: 'Top-up failed' });
  }
});

router.post('/generate', authRequired, async (req, res) => {
  let refunded = false;
  const fail = (status, payload) => res.status(status).json({ success: false, ...payload });
  try {
    const keyword = str(req.body.keyword);
    const audience = str(req.body.audience);
    const tone = TONES.includes(req.body.tone) ? req.body.tone : 'professional';
    const length = Object.keys(LENGTH_SPEC).includes(req.body.length) ? req.body.length : 'medium';
    if (!keyword || keyword.length < 3) return fail(422, { message: 'keyword is required (min 3 chars)', errors: { keyword: 'required min 3 chars' } });

    const balance = await reserveCredit(req.user.id);
    if (balance === null) return fail(402, { code: 'NO_CREDITS', message: 'Not enough credits — top up to continue' });

    const spec = LENGTH_SPEC[length];
    const meta = { keyword, tone, length, audience, balance };

    // Determine provider availability up-front (keyVault / env probe)
    let useDemo = false;
    try {
      const cfg = require('../services/keyVault');
      const envKey = process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || process.env.DEEPSEEK_API_KEY;
      if (!envKey && !(await cfg.hasKey('openai')) && !(await cfg.hasKey('gemini')) && !(await cfg.hasKey('openrouter')) && !(await cfg.hasKey('deepseek'))) useDemo = true;
    } catch {
      useDemo = true;
    }
    // Strict test hook: force demo/exact-real via header
    if (req.headers['x-force-demo'] === '1') useDemo = true;

    sseInit(res);
    sseSend(res, 'meta', { ...meta, demo: useDemo });

    let md = '';
    let metaTitle = '';
    let metaDescription = '';
    let keywords = '';
    let demo = false;

    if (useDemo) {
      demo = true;
      const d = demoArticle({ keyword, tone, length, audience });
      md = d.md; metaTitle = d.metaTitle; metaDescription = d.metaDescription; keywords = d.keywords;
      // stream demo in small chunks so the typewriter effect still feels real
      for (const chunk of md.match(/[\s\S]{1,60}/g) || []) {
        sseSend(res, 'chunk', chunk);
      }
    } else {
      const system = 'You are BlogForge, a senior SEO content strategist. Write human-first, intent-matched articles. Output ONLY markdown starting with an H1 title. Include an intro, serious H2 sections with concrete examples, a H3 "Key Takeaways" list near the end, and no meta commentary.';
      const user = [
        `Write a ${spec.words}-word blog article in a ${tone} tone about "${keyword}".`,
        audience ? `Target audience: ${audience}.` : '',
        `Use headings (H2/H3), short paragraphs, natural keyword placement, a comparison element and one actionable checklist.`,
        `After the article, on separate final lines exactly like a front-matter block, write:`,
        `SEO_TITLE: (max 70 chars, includes the keyword)`,
        `SEO_DESCRIPTION: (max 155 chars, compelling, includes the keyword)`,
        `SEO_KEYWORDS: (comma separated, max 8)`,
      ].filter(Boolean).join('\n');
      try {
        for await (const delta of aiClient.completeStream(
          [{ role: 'system', content: system }, { role: 'user', content: user }],
          { maxTokens: Math.ceil(spec.words * 2.4) },
        )) {
          md += delta;
          sseSend(res, 'chunk', delta);
        }
        if (!md.trim()) throw new Error('AI returned an empty article');
        const titleMatch = /SEO_TITLE:\s*(.+)/i.exec(md);
        const descMatch = /SEO_DESCRIPTION:\s*(.+)/i.exec(md);
        const kwMatch = /SEO_KEYWORDS:\s*(.+)/i.exec(md);
        metaTitle = str(titleMatch ? titleMatch[1] : '');
        metaDescription = str(descMatch ? descMatch[1] : '');
        keywords = str(kwMatch ? kwMatch[1] : '');
        md = md.replace(/\n+SEO_(TITLE|DESCRIPTION|KEYWORDS):[\s\S]*$/i, '').trim();
      } catch (err) {
        if (!refunded) {
          refundCredit(req.user.id).catch(() => {});
          refunded = true;
        }
        sseSend(res, 'error', { message: err.message });
        return res.end();
      }
    }

    const h1 = /^#\s+(.+)/m.exec(md);
    const title = str(h1 ? h1[1] : keyword);
    const finalSlug = slugify(h1 ? h1[1] : keyword);
    const wordCount = md.split(/\s+/).filter(Boolean).length;

    const article = await Article.create({
      userId: req.user.id, title, slug: finalSlug, keyword, tone, length,
      audience: audience || null, content: md, metaTitle: metaTitle || clamp(title, 70),
      metaDescription: metaDescription || clamp(demoArticle({ keyword, tone, length, audience }).metaDescription, 200),
      keywords: keywords || null, wordCount, creditsUsed: 1, demo,
    });

    sseSend(res, 'done', { id: article.id, title, slug: article.slug, wordCount, demo, balance, metaTitle: article.metaTitle, metaDescription: article.metaDescription, keywords });
    return res.end();
  } catch (err) {
    console.error(`[ERR blog generate] ${err.message}\n${err.stack}`);
    if (!refunded) refundCredit(req.user.id).catch(() => {});
    if (res.headersSent) {
      sseSend(res, 'error', { message: 'Generation failed' });
      return res.end();
    }
    return res.status(500).json({ success: false, message: 'Generation failed' });
  }
});

router.get('/history', authRequired, async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
    const offset = parseInt(req.query.offset, 10) || 0;
    const { rows, count } = await Article.findAndCountAll({
      where: { userId: req.user.id },
      order: [['createdAt', 'DESC']],
      limit, offset,
      attributes: ['id', 'title', 'slug', 'keyword', 'tone', 'length', 'wordCount', 'metaTitle', 'metaDescription', 'createdAt', 'demo'],
    });
    return res.json({ success: true, data: rows, total: count });
  } catch (err) {
    console.error(`[ERR blog history] ${err.message}`);
    return res.status(500).json({ success: false, message: 'Could not load history' });
  }
});

router.get('/articles/:id', authRequired, async (req, res) => {
  try {
    const article = await Article.findOne({ where: { id: req.params.id, userId: req.user.id } });
    if (!article) return res.status(404).json({ success: false, message: 'Article not found' });
    return res.json({ success: true, data: article });
  } catch (err) {
    return res.status(400).json({ success: false, message: 'Invalid article id' });
  }
});

router.delete('/articles/:id', authRequired, async (req, res) => {
  try {
    const deleted = await Article.destroy({ where: { id: req.params.id, userId: req.user.id } });
    if (!deleted) return res.status(404).json({ success: false, message: 'Article not found' });
    return res.json({ success: true, message: 'Article deleted' });
  } catch (err) {
    return res.status(400).json({ success: false, message: 'Invalid article id' });
  }
});

module.exports = router;
