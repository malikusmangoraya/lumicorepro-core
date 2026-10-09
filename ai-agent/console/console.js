/* LumicorePro Operator Console — page logic
   No framework, no build step. Talks only to this console's own backend.

   Layers:
     1. ambient   — aurora canvas, scroll reveal, pointer glow, clock
     2. telemetry — KPI gauges, tier ribbon, routing bars, sparkline
     3. control   — pipeline launcher, providers, tiers
     4. chrome    — command palette, toasts, theme
   Every number on screen comes from /api/console/overview. Nothing is invented. */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const TIERS = ['fast', 'balanced', 'reasoning'];
  const RING_LEN = 263.9; // 2 * PI * 42, matches .ring-value in console.css
  const SPARK_MAX = 40;

  const state = {
    overview: null,
    pollTimer: null,
    runTimer: null,
    running: false,
    lastRunId: null,
    resultDir: '',
    samples: [],
  };

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ═══ 1. Ambient ═══════════════════════════════════════════════════════ */

  function readPalette() {
    const css = getComputedStyle(document.documentElement);
    const pick = (name, fallback) => (css.getPropertyValue(name) || fallback).trim() || fallback;
    return {
      brand: pick('--t-brand', '#f5a524'),
      accent: pick('--t-accent', '#5eead4'),
      violet: pick('--t-violet', '#a855f7'),
    };
  }

  function hexToRgb(hex) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim());
    return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [245, 165, 36];
  }

  function initFx() {
    const canvas = $('fx');
    if (!canvas || reduced.matches) {
      if (canvas) canvas.style.display = 'none';
      return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let palette = readPalette();
    let w = 0;
    let h = 0;
    let blobs = [];
    let raf = 0;

    const reduce = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = w < 720 ? 3 : 5;
      blobs = Array.from({ length: count }, (_, i) => {
        const angle = (i / count) * Math.PI * 2;
        return {
          base: 0.22 + Math.random() * 0.2,
          ax: 0.1 + Math.random() * 0.16,
          ay: 0.07 + Math.random() * 0.12,
          sx: Math.cos(angle) * (0.12 + Math.random() * 0.2),
          sy: Math.sin(angle) * (0.1 + Math.random() * 0.16),
          phase: Math.random() * Math.PI * 2,
          speed: 0.00006 + Math.random() * 0.00012,
          size: 0.42 + Math.random() * 0.36,
          tint: [palette.brand, palette.violet, palette.accent][i % 3],
          rgb: hexToRgb([palette.brand, palette.violet, palette.accent][i % 3]),
        };
      });
    };

    let t = 0;
    const frame = () => {
      t += 1;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';
      for (const b of blobs) {
        const cx = w * (b.base + Math.sin(t * b.speed + b.phase) * b.ax) + b.sx * w * 0.1;
        const cy = h * (b.base + Math.cos(t * b.speed * 1.3 + b.phase) * b.ay);
        const radius = Math.max(w, h) * b.size * 0.5;
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        grad.addColorStop(0, `rgba(${b.rgb[0]}, ${b.rgb[1]}, ${b.rgb[2]}, 0.16)`);
        grad.addColorStop(0.55, `rgba(${b.rgb[0]}, ${b.rgb[1]}, ${b.rgb[2]}, 0.05)`);
        grad.addColorStop(1, `rgba(${b.rgb[0]}, ${b.rgb[1]}, ${b.rgb[2]}, 0)`);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
      raf = requestAnimationFrame(frame);
    };

    const start = () => {
      if (!raf) raf = requestAnimationFrame(frame);
    };
    const stop = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
    };

    reduce();
    window.addEventListener('resize', reduce, { passive: true });
    window.addEventListener('themechange', () => {
      palette = readPalette();
      const tints = [palette.brand, palette.violet, palette.accent];
      blobs.forEach((b, i) => {
        b.tint = tints[i % 3];
        b.rgb = hexToRgb(b.tint);
      });
    });
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    start();
  }

  function initReveal() {
    if (!('IntersectionObserver' in window) || reduced.matches) return;
    document.documentElement.classList.add('js-reveal');
    const targets = document.querySelectorAll('[data-reveal]');
    if (!targets.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const siblings = Array.from(entry.target.parentElement.children).filter((el) =>
            el.hasAttribute('data-reveal')
          );
          const index = Math.max(0, siblings.indexOf(entry.target));
          entry.target.style.transitionDelay = `${Math.min(index, 5) * 70}ms`;
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }
    );
    targets.forEach((el) => io.observe(el));
  }

  function initPointerGlow() {
    document.querySelectorAll('.kpi').forEach((card) => {
      card.addEventListener('pointermove', (ev) => {
        const box = card.getBoundingClientRect();
        card.style.setProperty('--mx', `${((ev.clientX - box.left) / box.width) * 100}%`);
        card.style.setProperty('--my', `${((ev.clientY - box.top) / box.height) * 100}%`);
      });
    });
  }

  function initClock() {
    const el = $('clock-time');
    if (!el) return;
    const tick = () => {
      el.textContent = new Date().toLocaleTimeString([], { hour12: false });
    };
    tick();
    setInterval(tick, 1000);
  }

  /* ═══ 2. Telemetry ═════════════════════════════════════════════════════ */

  function countTo(el, target, decimals = 0) {
    if (!el) return;
    const from = Number(el.dataset.value || 0);
    const to = Number(target) || 0;
    el.dataset.value = String(to);
    if (reduced.matches || from === to) {
      el.textContent = to.toFixed(decimals);
      return;
    }
    const started = performance.now();
    const duration = 900;
    const step = (now) => {
      const p = Math.min(1, (now - started) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (from + (to - from) * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = to.toFixed(decimals);
    };
    requestAnimationFrame(step);
  }

  function drawSpark() {
    const canvas = $('spark');
    if (!canvas || reduced.matches) {
      if (canvas) canvas.style.display = 'none';
      return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth || 220;
    const h = canvas.clientHeight || 46;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const data = state.samples;
    if (data.length < 2) return;
    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const span = Math.max(max - min, 1);
    const x = (i) => (i / (data.length - 1)) * w;
    const y = (v) => h - 3 - ((v - min) / span) * (h - 8);

    const css = getComputedStyle(document.documentElement);
    const fill = css.getPropertyValue('--t-accent').trim() || '#5eead4';
    const hot = css.getPropertyValue('--t-brand').trim() || '#f5a524';

    const area = ctx.createLinearGradient(0, 0, 0, h);
    area.addColorStop(0, `${fill}55`);
    area.addColorStop(1, `${fill}00`);
    ctx.beginPath();
    ctx.moveTo(0, h);
    data.forEach((v, i) => ctx.lineTo(x(i), y(v)));
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fillStyle = area;
    ctx.fill();

    ctx.beginPath();
    data.forEach((v, i) => (i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v))));
    ctx.strokeStyle = fill;
    ctx.lineWidth = 1.8;
    ctx.lineJoin = 'round';
    ctx.stroke();

    const lastX = x(data.length - 1);
    const lastY = y(data[data.length - 1]);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fillStyle = hot;
    ctx.fill();
    ctx.beginPath();
    ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
    ctx.strokeStyle = `${hot}66`;
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }

  function reportStats() {
    const report = (state.overview && state.overview.router && state.overview.router.report) || {};
    return report.stats || {};
  }

  function renderHero() {
    const providers = (state.overview && state.overview.providers) || [];
    const total = providers.length;
    const ready = providers.filter((p) => p.available).length;
    const pct = total ? Math.round((ready / total) * 100) : 0;

    const stats = reportStats();
    const calls = stats.calls_by_tier || {};
    const avg = stats.avg_seconds_by_tier || {};
    const totalCalls = TIERS.reduce((sum, t) => sum + (calls[t] || 0), 0);
    const weighted = TIERS.reduce((sum, t) => sum + (avg[t] || 0) * (calls[t] || 0), 0);
    const latency = totalCalls ? weighted / totalCalls : 0;
    const hits = Object.values(stats.cache_hits_by_tier || {}).reduce((a, b) => a + b, 0);
    const hitRate = hits + totalCalls ? Math.round((hits / (hits + totalCalls)) * 100) : 0;

    countTo($('kpi-ring-pct'), pct);
    const ring = $('kpi-ring-value');
    if (ring) ring.style.strokeDashoffset = String(RING_LEN * (1 - pct / 100));
    const readySub = $('kpi-ready-sub');
    if (readySub) readySub.textContent = total ? `${ready} of ${total} providers ready` : 'no providers reported';

    countTo($('kpi-calls'), totalCalls);
    const callsSub = $('kpi-calls-sub');
    if (callsSub) {
      callsSub.textContent = totalCalls
        ? TIERS.filter((t) => calls[t]).map((t) => `${t} ${calls[t]}`).join(' · ')
        : 'no routed calls yet';
    }

    countTo($('kpi-latency'), latency, latency < 10 ? 2 : 1);
    const latSub = $('kpi-latency-sub');
    if (latSub) {
      latSub.textContent = totalCalls
        ? `weighted across ${TIERS.filter((t) => calls[t]).length} tier(s)`
        : 'no calls yet';
    }
    const latMeter = $('kpi-latency-meter');
    if (latMeter) latMeter.style.width = `${Math.min(100, (latency / 10) * 100)}%`;

    countTo($('kpi-cache'), hitRate);
    const cacheSub = $('kpi-cache-sub');
    const cacheSize = (state.overview && state.overview.router && state.overview.router.cache) || {};
    if (cacheSub) {
      cacheSub.textContent = totalCalls || hits ? `${hits} hit(s) · ${cacheSize.size || 0} cached` : 'no cache activity yet';
    }
    const cacheMeter = $('kpi-cache-meter');
    if (cacheMeter) cacheMeter.style.width = `${hitRate}%`;

    const sync = $('last-sync');
    if (sync) sync.textContent = (state.overview && state.overview.generated_at) || '—';

    state.samples.push(totalCalls);
    if (state.samples.length > SPARK_MAX) state.samples.shift();
    drawSpark();

    renderRibbon();
    renderBars(calls, totalCalls);
  }

  function renderRibbon() {
    const wrap = $('tier-ribbon');
    if (!wrap) return;
    const tiers = (state.overview && state.overview.router && state.overview.router.tiers) || {};
    wrap.textContent = '';
    const filled = TIERS.filter((tier) => (tiers[tier] || []).length);
    if (!filled.length) {
      const empty = document.createElement('p');
      empty.className = 'ribbon-empty';
      empty.textContent = 'No routing tiers reported — start the agent API to load .router.json.';
      wrap.append(empty);
      return;
    }
    filled.forEach((tier, rowIndex) => {
      const row = document.createElement('div');
      row.className = 'ribbon-row';
      const label = document.createElement('span');
      label.className = 'ribbon-tier';
      label.textContent = tier;
      row.append(label);
      (tiers[tier] || []).forEach((name, index) => {
        if (index) {
          const arrow = document.createElement('span');
          arrow.className = 'ribbon-arrow';
          arrow.textContent = '›';
          arrow.setAttribute('aria-hidden', 'true');
          row.append(arrow);
        }
        const node = document.createElement('span');
        node.className = 'ribbon-node';
        node.dataset.pref = index === 0 ? 'true' : 'false';
        node.textContent = name;
        node.style.animationDelay = `${rowIndex * 60 + index * 40}ms`;
        if (index === 0) node.title = 'preferred provider for this tier';
        row.append(node);
      });
      wrap.append(row);
    });
  }

  function renderBars(calls, totalCalls) {
    const wrap = $('tier-bars');
    if (!wrap) return;
    wrap.textContent = '';
    const max = Math.max(...TIERS.map((t) => calls[t] || 0), 1);
    TIERS.forEach((tier) => {
      const value = calls[tier] || 0;
      const row = document.createElement('div');
      row.className = 'bar-row';
      const label = document.createElement('span');
      label.className = 'bar-label';
      label.textContent = tier;
      const track = document.createElement('span');
      track.className = 'bar-track';
      const fill = document.createElement('span');
      fill.className = 'bar-fill';
      const pctWidth = totalCalls ? (value / max) * 100 : 0;
      requestAnimationFrame(() => {
        fill.style.width = `${pctWidth}%`;
      });
      track.append(fill);
      const readout = document.createElement('span');
      readout.className = 'bar-value';
      readout.textContent = totalCalls
        ? `${value} · ${Math.round((value / totalCalls) * 100)}%`
        : 'no calls';
      row.append(label, track, readout);
      wrap.append(row);
    });
  }

  /* ═══ 3. Control ═══════════════════════════════════════════════════════ */

  function toast(message, kind = 'info') {
    const host = $('toasts');
    if (!host) return;
    const item = document.createElement('div');
    item.className = 'toast';
    item.dataset.kind = kind;
    const text = document.createElement('span');
    text.textContent = message;
    item.append(text);
    host.append(item);
    while (host.childElementCount > 4) host.firstElementChild.remove();
    setTimeout(() => {
      item.dataset.leaving = 'true';
      setTimeout(() => item.remove(), 300);
    }, 4200);
  }

  function log(message, kind = 'info', options = {}) {
    const box = $('log');
    if (box) {
      const line = document.createElement('div');
      line.className = 'log-line';
      const stamp = document.createElement('span');
      stamp.className = 'log-time';
      stamp.textContent = new Date().toLocaleTimeString([], { hour12: false });
      const msg = document.createElement('span');
      msg.className = 'log-msg';
      msg.dataset.kind = kind;
      msg.textContent = message;
      line.append(stamp, msg);
      box.append(line);
      box.scrollTop = box.scrollHeight;
      while (box.childElementCount > 300) box.firstElementChild.remove();
    }
    if (options.toast) toast(message, kind);
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { error: text.slice(0, 200) };
    }
    if (!res.ok) throw new Error((data && data.error) || `HTTP ${res.status}`);
    return data;
  }

  function setAgentStatus(stateName, text) {
    const dot = document.querySelector('#agent-status .dot');
    if (dot) dot.dataset.state = stateName;
    const label = $('agent-status-text');
    if (label) label.textContent = text;
  }

  function tierOf(name) {
    const tiers = (state.overview && state.overview.router && state.overview.router.tiers) || {};
    for (const tier of TIERS) if ((tiers[tier] || []).includes(name)) return tier;
    return null;
  }

  function renderProviders() {
    const wrap = $('provider-cards');
    const providers = (state.overview && state.overview.providers) || [];
    wrap.textContent = '';
    const badge = $('provider-count');
    if (badge) {
      const ready = providers.filter((p) => p.available).length;
      badge.textContent = `${ready}/${providers.length} ready`;
    }
    if (!providers.length) {
      wrap.innerHTML = '<p class="empty">No providers reported by the agent API.</p>';
      return;
    }
    providers.forEach((p, index) => {
      const card = document.createElement('article');
      card.className = 'pcard';
      card.style.animationDelay = `${Math.min(index, 8) * 40}ms`;

      const top = document.createElement('div');
      top.className = 'pcard-top';
      const name = document.createElement('p');
      name.className = 'pcard-name';
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.dataset.state = p.available ? 'ok' : 'err';
      const label = document.createElement('span');
      label.textContent = p.label || p.name;
      name.append(dot, label);
      const tier = tierOf(p.name);
      const chip = tier
        ? Object.assign(document.createElement('span'), { className: 'tier-chip', textContent: tier })
        : document.createElement('span');
      top.append(name, chip);

      const model = document.createElement('p');
      model.className = 'pcard-meta';
      model.textContent = p.model || p.base_url || '—';

      const key = document.createElement('p');
      key.className = 'pcard-meta';
      key.textContent = p.key_masked ? `key ${p.key_masked}` : p.needs_key ? 'no key set' : 'keyless';

      const actions = document.createElement('div');
      actions.className = 'pcard-actions';
      if (p.open_source) actions.append(tag('oss', 'open source'));
      actions.append(tag(p.available ? 'ok' : 'err', p.available ? 'ready' : 'unavailable'));

      const probe = document.createElement('button');
      probe.type = 'button';
      probe.className = 'btn ghost small';
      probe.textContent = 'Probe';
      probe.addEventListener('click', () => probeProvider(p.name, probe));
      actions.append(probe);

      card.append(top, model, key, actions);
      wrap.append(card);
    });
  }

  function tag(kind, text) {
    const el = document.createElement('span');
    el.className = 'tag';
    el.dataset.kind = kind;
    el.textContent = text;
    return el;
  }

  async function probeProvider(name, button) {
    button.disabled = true;
    const original = button.textContent;
    button.textContent = '…';
    log(`probing ${name}…`, 'info');
    try {
      const res = await api('/api/console/probe', { method: 'POST', body: JSON.stringify({ provider: name }) });
      if (res.ok && res.called) {
        log(`${name} responded in ${res.seconds}s (tier ${res.tier}, ${res.provider})`, 'ok', { toast: true });
      } else if (res.ok) {
        log(`${name} is in the ${res.tier} tier; live call skipped`, 'info');
      } else {
        log(`${name} probe failed: ${res.error || 'unavailable'}`, 'warn');
      }
    } catch (err) {
      log(`probe error: ${err.message}`, 'err', { toast: true });
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  }

  function renderTiers() {
    const tiers = (state.overview && state.overview.router && state.overview.router.tiers) || {};
    const known = ((state.overview && state.overview.providers) || []).map((p) => p.name);
    TIERS.forEach((tier) => {
      const box = $(`tier-${tier}`);
      if (!box) return;
      box.textContent = '';
      const members = tiers[tier] || [];
      known.forEach((name) => {
        const index = members.indexOf(name);
        const chip = document.createElement('span');
        chip.className = 'tier-opt';
        chip.dataset.name = name;
        chip.dataset.first = index === 0 ? 'true' : 'false';
        chip.draggable = true;
        chip.title = index === 0 ? 'preferred provider for this tier' : 'click × to remove';

        const text = document.createElement('span');
        text.textContent = name;
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.textContent = '×';
        remove.setAttribute('aria-label', `remove ${name} from ${tier} tier`);
        remove.addEventListener('click', () => {
          members.splice(members.indexOf(name), 1);
          renderTiers();
        });
        chip.append(text, remove);

        chip.addEventListener('dragstart', (ev) => ev.dataTransfer.setData('text/plain', name));
        chip.addEventListener('dragover', (ev) => ev.preventDefault());
        chip.addEventListener('drop', (ev) => {
          ev.preventDefault();
          const moved = ev.dataTransfer.getData('text/plain');
          const from = members.indexOf(moved);
          const to = members.indexOf(name);
          if (from < 0 || to < 0 || from === to) return;
          members.splice(from, 1);
          members.splice(to, 0, moved);
          renderTiers();
        });
        box.append(chip);
      });
    });
  }

  function collectTiers() {
    const out = {};
    TIERS.forEach((tier) => {
      const box = $(`tier-${tier}`);
      out[tier] = box ? Array.from(box.querySelectorAll('.tier-opt')).map((el) => el.dataset.name) : [];
    });
    return out;
  }

  function renderStats() {
    const grid = $('stats-grid');
    const stats = reportStats();
    const calls = stats.calls_by_tier || {};
    const avg = stats.avg_seconds_by_tier || {};
    const cache = (state.overview && state.overview.router && state.overview.router.cache) || {};
    const cacheHits = Object.values(stats.cache_hits_by_tier || {}).reduce((a, b) => a + b, 0);
    const failures = Object.values(stats.failures_by_tier || {}).reduce((a, b) => a + b, 0);

    grid.textContent = '';
    const cards = [
      ...TIERS.map((tier) => [tier, String(calls[tier] || 0), avg[tier] ? `${avg[tier]}s avg` : 'no calls yet']),
      ['cache hits', String(cacheHits), `${cache.size || 0} entries`],
      ['failures', String(failures), 'provider errors'],
      [
        'fan-out width',
        String((state.overview && state.overview.router && state.overview.router.parallelism) || 0),
        'parallel workers',
      ],
      [
        'provider hops',
        String(((state.overview && state.overview.fallback_order) || []).length),
        'internet-only',
      ],
    ];
    cards.forEach(([label, value, sub], index) => {
      const card = statCard(label, value, sub);
      card.style.animationDelay = `${index * 45}ms`;
      grid.append(card);
    });
  }

  function statCard(label, value, sub) {
    const box = document.createElement('div');
    box.className = 'stat';
    const l = document.createElement('p');
    l.className = 'stat-label';
    l.textContent = label;
    const v = document.createElement('p');
    v.className = 'stat-value';
    v.textContent = value;
    const s = document.createElement('p');
    s.className = 'stat-sub';
    s.textContent = sub;
    box.append(l, v, s);
    return box;
  }

  async function loadOverview(silent = false) {
    setAgentStatus('busy', 'Loading state…');
    try {
      state.overview = await api('/api/console/overview');
      const reachable = state.overview.agent && state.overview.agent.reachable;
      setAgentStatus(
        reachable ? 'ok' : 'err',
        reachable ? `agent online · ${state.overview.agent.url}` : 'agent unreachable — start the API'
      );
      renderHero();
      renderProviders();
      renderTiers();
      renderStats();
      const footer = $('footer-agent');
      if (footer) footer.textContent = (state.overview.agent && state.overview.agent.url) || 'the agent API';
      if (!silent) {
        const ready = (state.overview.providers || []).filter((p) => p.available).length;
        log(`state loaded · ${ready} provider(s) ready`, 'ok', { toast: true });
      }
    } catch (err) {
      setAgentStatus('err', `console backend error: ${err.message}`);
      log(`overview failed: ${err.message}`, 'err', { toast: true });
    }
  }

  function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(() => {
      if (!state.running) loadOverview(true);
    }, 20000);
  }

  function stopPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function setRunning(running) {
    state.running = running;
    const btn = $('launch-btn');
    if (btn) {
      btn.disabled = running;
      btn.dataset.busy = running ? 'true' : 'false';
      const label = btn.querySelector('.btn-label') || btn;
      label.textContent = running ? 'Building…' : 'Start build';
    }
    const cancel = $('cancel-btn');
    if (cancel) cancel.hidden = !running;
    setAgentStatus(running ? 'busy' : 'ok', running ? 'build in progress' : 'agent online');
  }

  async function launchRun(event) {
    event.preventDefault();
    const prompt = $('prompt').value.trim();
    if (prompt.length < 8) {
      log('prompt must be at least 8 characters', 'err', { toast: true });
      $('prompt').focus();
      return;
    }
    setRunning(true);
    log(`launching: "${prompt.slice(0, 70)}${prompt.length > 70 ? '…' : ''}"`, 'info');
    try {
      const res = await api('/api/console/launch', {
        method: 'POST',
        body: JSON.stringify({
          prompt,
          project_name: $('project-name').value.trim() || 'console-project',
          industry: $('industry').value,
          design_style: $('design-style').value,
          fast_mode: $('fast-mode').checked,
        }),
      });
      const runId = res && (res.run_id || res.runId || (res.run && res.run.id));
      if (runId) state.lastRunId = runId;
      log(`run accepted${runId ? `: ${runId}` : ''} — poll for progress`, 'ok', { toast: true });
      showResult('running', extractProjectDir(res));
      pollRun();
    } catch (err) {
      log(`launch failed: ${err.message}`, 'err', { toast: true });
      showResult('failed', '');
      setRunning(false);
    }
  }

  function extractProjectDir(res) {
    if (!res || typeof res !== 'object') return '';
    return (
      res.generated_project_dir ||
      (res.report && res.report.generated_project_dir) ||
      (res.data && res.data.generated_project_dir) ||
      (res.run && res.run.generated_project_dir) ||
      ''
    );
  }

  function showResult(status, dir) {
    const box = $('result-box');
    const statusEl = $('result-status');
    const pathEl = $('result-path');
    const openBtn = $('open-folder-btn');
    const copyBtn = $('copy-path-btn');
    box.hidden = false;
    pathEl.textContent = dir || '';
    openBtn.hidden = !dir;
    copyBtn.hidden = !dir;
    if (status === 'running') statusEl.textContent = 'Build is running. The folder appears here when it finishes.';
    else if (status === 'failed') statusEl.textContent = 'Build failed. See the activity log for the reason.';
    else if (status === 'done') statusEl.textContent = 'Build finished.';
    state.resultDir = dir || '';
  }

  async function testAllProviders() {
    const btn = $('probe-all-btn');
    const stateEl = $('probe-all-state');
    btn.disabled = true;
    stateEl.textContent = 'testing every provider, this takes a few seconds.';
    stateEl.dataset.kind = 'info';
    try {
      const res = await api('/api/console/probe-all', { method: 'POST', body: '{}' });
      const working = (res && res.working) || [];
      const total = (res && res.probed) || 0;
      if (working.length) {
        stateEl.textContent = `${working.length}/${total} answering: ${working.join(', ')}`;
        stateEl.dataset.kind = 'ok';
        log(`provider test: ${working.length}/${total} live — ${working.join(', ')}`, 'ok', { toast: true });
      } else {
        stateEl.textContent = `0/${total} answered. Check the provider keys, then probe again.`;
        stateEl.dataset.kind = 'err';
        log('provider test: nothing answered', 'err', { toast: true });
      }
      ((res && res.results) || []).forEach((r) => {
        if (!r.ok) log(`  ${r.name}: ${(r.error || 'failed').slice(0, 90)}`, 'warn');
      });
      await loadOverview(true);
    } catch (err) {
      stateEl.textContent = `test failed: ${err.message}`;
      stateEl.dataset.kind = 'err';
    } finally {
      btn.disabled = false;
    }
  }

  async function openResultFolder() {
    if (!state.resultDir) return;
    try {
      const res = await api('/api/console/open', {
        method: 'POST',
        body: JSON.stringify({ path: state.resultDir }),
      });
      if (res && res.ok) log(`opened ${res.path}`, 'ok', { toast: true });
      else log(`could not open folder: ${(res && res.error) || 'unknown error'}`, 'err', { toast: true });
    } catch (err) {
      log(`could not open folder: ${err.message}`, 'err', { toast: true });
    }
  }

  function pollRun() {
    stopRunPolling();
    state.runTimer = setInterval(async () => {
      if (!state.running) return stopRunPolling();
      try {
        if (state.lastRunId) {
          const run = await api('/api/console/runs');
          const items = (run && (run.runs || run.items)) || [];
          const current = items.find((r) => (r.run_id || r.id) === state.lastRunId);
          if (current) {
            const status = current.status || current.state;
            log(
              `run ${state.lastRunId}: ${status}`,
              status === 'completed' ? 'ok' : status === 'failed' ? 'err' : 'info'
            );
            const finished = ['completed', 'failed', 'cancelled', 'error'].includes(String(status).toLowerCase());
            if (finished) {
              const dir = extractProjectDir(current);
              showResult(String(status).toLowerCase() === 'completed' ? 'done' : 'failed', dir);
              if (dir) log(`project folder: ${dir}`, 'ok', { toast: true });
              setRunning(false);
              return stopRunPolling();
            }
          }
        }
        await loadOverview(true);
      } catch (err) {
        log(`poll error: ${err.message}`, 'warn');
      }
    }, 6000);
  }

  function stopRunPolling() {
    if (state.runTimer) clearInterval(state.runTimer);
    state.runTimer = null;
  }

  /* ═══ 4. Chrome ════════════════════════════════════════════════════════ */

  function toggleTheme() {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('console-theme', next);
    window.dispatchEvent(new Event('themechange'));
    drawSpark();
  }

  function initTheme() {
    const stored = localStorage.getItem('console-theme');
    const system = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    document.documentElement.dataset.theme = stored || system;
    $('theme-btn').addEventListener('click', toggleTheme);
  }

  const COMMANDS = [
    { label: 'Run the pipeline', group: 'section', run: () => jump('sec-launch', 'prompt') },
    { label: 'Activity log', group: 'section', run: () => jump('sec-log') },
    { label: 'AI providers', group: 'section', run: () => jump('sec-providers') },
    { label: 'Routing tiers', group: 'section', run: () => jump('sec-tiers') },
    { label: 'Routing report', group: 'section', run: () => jump('sec-stats') },
    { label: 'Refresh state now', group: 'action', run: () => loadOverview() },
    { label: 'Test all providers', group: 'action', run: () => $('probe-all-btn').click() },
    { label: 'Toggle colour theme', group: 'action', run: toggleTheme },
    { label: 'Clear activity log', group: 'action', run: () => { $('log').textContent = ''; } },
  ];

  function jump(sectionId, focusId) {
    const target = $(sectionId);
    if (!target) return;
    target.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
    if (focusId && $(focusId)) $(focusId).focus({ preventScroll: true });
  }

  function initPalette() {
    const backdrop = $('palette');
    const input = $('palette-input');
    const list = $('palette-list');
    if (!backdrop || !input || !list) return;
    let active = 0;
    let visible = [];

    const paint = () => {
      const query = input.value.trim().toLowerCase();
      visible = COMMANDS.filter((c) => !query || c.label.toLowerCase().includes(query));
      active = Math.min(active, Math.max(visible.length - 1, 0));
      list.textContent = '';
      if (!visible.length) {
        const empty = document.createElement('li');
        empty.className = 'palette-empty';
        empty.textContent = 'No matching command.';
        list.append(empty);
        return;
      }
      visible.forEach((cmd, index) => {
        const item = document.createElement('li');
        item.className = 'palette-item';
        item.setAttribute('role', 'option');
        item.dataset.active = index === active ? 'true' : 'false';
        item.setAttribute('aria-selected', index === active ? 'true' : 'false');
        const name = document.createElement('span');
        name.textContent = cmd.label;
        const group = document.createElement('small');
        group.textContent = cmd.group;
        item.append(name, group);
        item.addEventListener('mouseenter', () => {
          active = index;
          paint();
        });
        item.addEventListener('click', () => {
          close();
          cmd.run();
        });
        list.append(item);
      });
    };

    const open = () => {
      backdrop.hidden = false;
      input.value = '';
      active = 0;
      paint();
      input.focus();
    };
    const close = () => {
      backdrop.hidden = true;
      const trigger = $('palette-btn');
      if (trigger) trigger.focus();
    };

    $('palette-btn').addEventListener('click', open);
    backdrop.addEventListener('click', (ev) => {
      if (ev.target === backdrop) close();
    });
    input.addEventListener('input', () => {
      active = 0;
      paint();
    });
    input.addEventListener('keydown', (ev) => {
      if (ev.key === 'ArrowDown') {
        ev.preventDefault();
        active = Math.min(active + 1, visible.length - 1);
        paint();
      } else if (ev.key === 'ArrowUp') {
        ev.preventDefault();
        active = Math.max(active - 1, 0);
        paint();
      } else if (ev.key === 'Enter') {
        ev.preventDefault();
        const cmd = visible[active];
        if (cmd) {
          close();
          cmd.run();
        }
      }
    });
    document.addEventListener('keydown', (ev) => {
      const combo = (ev.ctrlKey || ev.metaKey) && (ev.key === 'k' || ev.key === 'K');
      if (combo) {
        ev.preventDefault();
        backdrop.hidden ? open() : close();
        return;
      }
      if (ev.key === 'Escape' && !backdrop.hidden) {
        ev.preventDefault();
        close();
      }
    });
  }

  function init() {
    initTheme();
    initClock();
    initFx();
    initReveal();
    initPointerGlow();
    initPalette();
    drawSpark();

    $('run-form').addEventListener('submit', launchRun);
    $('cancel-btn').addEventListener('click', () => {
      log('cancel is not wired to a running server-side job — the agent will finish on its own', 'warn');
      setRunning(false);
      stopRunPolling();
    });
    $('refresh-btn').addEventListener('click', () => loadOverview());
    $('probe-all-btn').addEventListener('click', testAllProviders);
    $('open-folder-btn').addEventListener('click', openResultFolder);
    $('copy-path-btn').addEventListener('click', async () => {
      if (!state.resultDir) return;
      try {
        await navigator.clipboard.writeText(state.resultDir);
        log('project path copied', 'ok', { toast: true });
      } catch (err) {
        log(`clipboard blocked: ${err.message}`, 'warn');
      }
    });
    $('clear-log').addEventListener('click', () => {
      $('log').textContent = '';
    });
    $('tier-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const stateEl = $('tier-state');
      stateEl.dataset.kind = '';
      stateEl.textContent = 'saving…';
      try {
        const res = await api('/api/console/tiers', { method: 'POST', body: JSON.stringify(collectTiers()) });
        if (res.ok) {
          stateEl.dataset.kind = 'ok';
          stateEl.textContent = 'saved to .router.json';
          log('routing tiers updated', 'ok', { toast: true });
          loadOverview(true);
        } else {
          stateEl.dataset.kind = 'err';
          stateEl.textContent = res.error || 'failed';
        }
      } catch (err) {
        stateEl.dataset.kind = 'err';
        stateEl.textContent = err.message;
      }
    });

    log('console ready', 'ok');
    loadOverview();
    startPolling();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
